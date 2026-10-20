
import cv2
import numpy as np
import os
import time
from datetime import datetime
from picamera2 import Picamera2

# ==================================================
# SETTINGS
# ==================================================

SAVE_FOLDER = "Photos"

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

THRESHOLD_VALUE = 20
MIN_COMPONENT_AREA = 12
BLACKHAT_KERNEL_SIZE = 21

# Inspection region margins
MARGIN_X_RATIO = 0.08
MARGIN_TOP_RATIO = 0.12
MARGIN_BOTTOM_RATIO = 0.15

# Extra exclusion margin around QR code, in pixels
QR_MARGIN = 12

os.makedirs(SAVE_FOLDER, exist_ok=True)

qr_detector = cv2.QRCodeDetector()


# ==================================================
# SKELETONIZATION
# ==================================================

def skeletonize(binary):
    """Reduce white crack regions to one-pixel-wide centerlines."""

    img = (binary > 0).astype(np.uint8)
    changed = True

    while changed:
        changed = False

        for step in (0, 1):
            p = np.pad(img, 1)

            P2 = p[:-2, 1:-1]
            P3 = p[:-2, 2:]
            P4 = p[1:-1, 2:]
            P5 = p[2:, 2:]
            P6 = p[2:, 1:-1]
            P7 = p[2:, :-2]
            P8 = p[1:-1, :-2]
            P9 = p[:-2, :-2]

            neighbors = [
                P2, P3, P4, P5, P6, P7, P8, P9
            ]

            B = sum(neighbors)

            A = sum(
                (
                    (neighbors[i] == 0) &
                    (neighbors[(i + 1) % 8] == 1)
                ).astype(np.uint8)
                for i in range(8)
            )

            if step == 0:
                condition = (
                    (P2 * P4 * P6 == 0) &
                    (P4 * P6 * P8 == 0)
                )
            else:
                condition = (
                    (P2 * P4 * P8 == 0) &
                    (P2 * P6 * P8 == 0)
                )

            remove = (
                (img == 1) &
                (B >= 2) &
                (B <= 6) &
                (A == 1) &
                condition
            )

            if np.any(remove):
                img[remove] = 0
                changed = True

    return img * 255


# ==================================================
# QR DETECTION AND EXCLUSION MASK
# ==================================================

def detect_qr_and_create_mask(image):
    """
    Detect QR codes, decode their messages, and return:
    - annotated image
    - mask with QR areas set to zero
    - decoded QR messages
    - whether QR detection was successful
    """

    height, width = image.shape[:2]

    # 255 = available for crack detection
    # 0   = excluded QR region
    qr_mask = np.full(
        (height, width), 255, dtype=np.uint8
    )

    annotated = image.copy()
    decoded_messages = []
    detected_count = 0

    # Try detecting multiple QR codes
    try:
        success, decoded_info, points, _ = (
            qr_detector.detectAndDecodeMulti(image)
        )
    except cv2.error:
        success = False
        decoded_info = ()
        points = None

    # Fall back to single QR detection
    if not success or points is None:
        try:
            data, single_points, _ = (
                qr_detector.detectAndDecode(image)
            )
        except cv2.error:
            data, single_points = "", None

        if single_points is not None:
            points = np.asarray(single_points).reshape(
                1, -1, 2
            )
            decoded_info = [data]
            success = True
        else:
            points = None
            decoded_info = []
            success = False

    if points is not None:
        points = np.asarray(points, dtype=np.float32)

        if points.ndim == 2:
            points = points.reshape(1, -1, 2)

        for i, qr_points in enumerate(points):

            corners = np.round(qr_points).astype(np.int32)

            # Expand the QR bounding box for a safety margin
            x, y, w, h = cv2.boundingRect(corners)

            x1 = max(0, x - QR_MARGIN)
            y1 = max(0, y - QR_MARGIN)
            x2 = min(width, x + w + QR_MARGIN)
            y2 = min(height, y + h + QR_MARGIN)

            # Exclude the entire QR rectangle plus its margin
            qr_mask[y1:y2, x1:x2] = 0

            # Draw the actual QR outline
            polygon = corners.reshape(-1, 1, 2)

            cv2.polylines(
                annotated,
                [polygon],
                True,
                (0, 255, 0),
                2
            )

            detected_count += 1

            message = (
                decoded_info[i]
                if i < len(decoded_info)
                else ""
            )

            if message:
                decoded_messages.append(message)

                print(
                    f"QR Code {detected_count}: {message}"
                )

                label = message[:45]

                cv2.putText(
                    annotated,
                    label,
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
            else:
                print(
                    f"QR Code {detected_count} detected "
                    "but could not be decoded."
                )

    # Detection and successful decoding are different:
    # an unreadable QR may still have been masked.
    if detected_count == 0:
        print("WARNING: No QR code detected.")

    return (
        annotated,
        qr_mask,
        decoded_messages,
        detected_count > 0
    )


# ==================================================
# CRACK DETECTION
# ==================================================

def detect_cracks(original, qr_mask):
    """Detect crack-like lines outside all masked QR regions."""

    height, width = original.shape[:2]

    # 1. Define the inspection ROI
    margin_x = int(width * MARGIN_X_RATIO)
    margin_top = int(height * MARGIN_TOP_RATIO)
    margin_bottom = int(height * MARGIN_BOTTOM_RATIO)

    roi = np.zeros(
        (height, width), dtype=np.uint8
    )

    roi[
        margin_top:height - margin_bottom,
        margin_x:width - margin_x
    ] = 255

    # Exclude QR regions from the inspection ROI
    roi = cv2.bitwise_and(roi, qr_mask)

    # 2. Grayscale and contrast enhancement
    gray = cv2.cvtColor(
        original, cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # 3. Reduce noise
    blur = cv2.GaussianBlur(
        enhanced, (3, 3), 0
    )

    # 4. Enhance dark structures
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (BLACKHAT_KERNEL_SIZE, BLACKHAT_KERNEL_SIZE)
    )

    blackhat = cv2.morphologyEx(
        blur,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    # 5. Threshold candidate cracks
    _, thresh = cv2.threshold(
        blackhat,
        THRESHOLD_VALUE,
        255,
        cv2.THRESH_BINARY
    )

    # IMPORTANT: Apply both the inspection ROI
    # and QR exclusion mask before skeletonization.
    thresh = cv2.bitwise_and(thresh, roi)

    # 6. Remove isolated noise
    small_kernel = np.ones(
        (2, 2), np.uint8
    )

    clean = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        small_kernel
    )

    # Reapply the mask after morphological processing
    clean = cv2.bitwise_and(clean, roi)

    # 7. Skeletonization
    skeleton = skeletonize(clean)

    # Ensure excluded regions cannot be drawn
    skeleton = cv2.bitwise_and(skeleton, roi)

    # 8. Filter connected components
    count, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            skeleton,
            connectivity=8
        )
    )

    result = original.copy()
    crack_found = False
    detected_components = 0

    for i in range(1, count):

        area = stats[i, cv2.CC_STAT_AREA]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        if area < MIN_COMPONENT_AREA:
            continue

        # Suppress long, nearly horizontal boundaries.
        # Genuine horizontal cracks may also be rejected.
        if w > 100 and w / max(h, 1) > 12:
            continue

        component_mask = labels == i

        result[component_mask] = (0, 0, 255)

        crack_found = True
        detected_components += 1

    status = (
        "CRACK CANDIDATE DETECTED"
        if crack_found
        else "NO CRACK CANDIDATE DETECTED"
    )

    print("\n" + "=" * 45)
    print("Crack result:", status)
    print("Candidate components:", detected_components)
    print("=" * 45)

    color = (0, 0, 255) if crack_found else (0, 255, 0)

    cv2.putText(
        result,
        status,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA
    )

    # Diagnostic windows
    cv2.imshow("Inspection ROI", roi)
    cv2.imshow("Blackhat", blackhat)
    cv2.imshow("Threshold", thresh)
    cv2.imshow("Skeleton Centerlines", skeleton)
    cv2.imshow("Crack Centerline Overlay", result)

    return crack_found


# ==================================================
# RASPBERRY PI CAMERA MODULE 3
# ==================================================

picam2 = Picamera2()

config = picam2.create_video_configuration(
    main={
        "format": "RGB888",
        "size": (CAMERA_WIDTH, CAMERA_HEIGHT)
    }
)

picam2.configure(config)
picam2.start()

time.sleep(2)

print("\nCamera started.")
print("Press S to capture, decode QR and detect cracks.")
print("Press Q to quit.")

try:
    while True:

        # Picamera2 RGB888 frames are BGR-ordered
        # for OpenCV processing on this configuration.
        frame = picam2.capture_array()

        cv2.imshow(
            "Live Camera - Press S to Capture",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):

            captured = frame.copy()

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            image_path = os.path.join(
                SAVE_FOLDER,
                f"specimen_{timestamp}.jpg"
            )

            if not cv2.imwrite(image_path, captured):
                print("Failed to save captured image.")
                continue

            print("\nSaved:", image_path)

            # STEP 1: Find and decode QR codes
            (
                qr_annotated,
                qr_mask,
                qr_messages,
                qr_detected
            ) = detect_qr_and_create_mask(captured)

            cv2.imshow(
                "QR Detection and Decoding",
                qr_annotated
            )

            cv2.imshow(
                "QR Exclusion Mask",
                qr_mask
            )

            # STEP 2: Run crack detection.
            # Any QR region detected above is excluded.
            detect_cracks(captured, qr_mask)

            if not qr_detected:
                print(
                    "WARNING: QR exclusion could not be "
                    "guaranteed because no QR was detected."
                )

        elif key == ord("q"):
            break

finally:
    picam2.stop()
    picam2.close()
    cv2.destroyAllWindows()
    print("Camera closed.")
