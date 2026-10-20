
# import cv2
# import numpy as np
# import os

# # Create folder for captured images
# os.makedirs("Photos", exist_ok=True)


# def skeletonize(binary):
#     """Reduce white crack regions to one-pixel-wide centerlines."""
#     img = (binary > 0).astype(np.uint8)
#     changed = True

#     while changed:
#         changed = False

#         for step in (0, 1):
#             p = np.pad(img, 1)
#             P2 = p[:-2, 1:-1]
#             P3 = p[:-2, 2:]
#             P4 = p[1:-1, 2:]
#             P5 = p[2:, 2:]
#             P6 = p[2:, 1:-1]
#             P7 = p[2:, :-2]
#             P8 = p[1:-1, :-2]
#             P9 = p[:-2, :-2]

#             neighbors = [P2, P3, P4, P5, P6, P7, P8, P9]
#             B = sum(neighbors)

#             A = sum(
#                 (
#                     (neighbors[i] == 0) &
#                     (neighbors[(i + 1) % 8] == 1)
#                 ).astype(np.uint8)
#                 for i in range(8)
#             )

#             if step == 0:
#                 condition = (
#                     (P2 * P4 * P6 == 0) &
#                     (P4 * P6 * P8 == 0)
#                 )
#             else:
#                 condition = (
#                     (P2 * P4 * P8 == 0) &
#                     (P2 * P6 * P8 == 0)
#                 )

#             remove = (
#                 (img == 1) &
#                 (B >= 2) & (B <= 6) &
#                 (A == 1) & condition
#             )

#             if np.any(remove):
#                 img[remove] = 0
#                 changed = True

#     return img * 255


# def detect_cracks(original):
#     """Process one captured frame and display crack detection results."""

#     gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

#     # 1. Enhance local contrast
#     clahe = cv2.createCLAHE(
#         clipLimit=2.0,
#         tileGridSize=(8, 8)
#     )
#     enhanced = clahe.apply(gray)

#     # 2. Reduce noise
#     blur = cv2.GaussianBlur(enhanced, (5, 5), 0)

#     # 3. Enhance dark structures
#     kernel = cv2.getStructuringElement(
#         cv2.MORPH_RECT, (15, 15)
#     )
#     blackhat = cv2.morphologyEx(
#         blur, cv2.MORPH_BLACKHAT, kernel
#     )

#     # 4. Threshold crack candidates
#     _, thresh = cv2.threshold(
#         blackhat, 30, 255, cv2.THRESH_BINARY
#     )

#     # 5. Remove isolated noise
#     small_kernel = np.ones((3, 3), np.uint8)
#     clean = cv2.morphologyEx(
#         thresh, cv2.MORPH_OPEN, small_kernel
#     )

#     # 6. Generate centerlines
#     skeleton = skeletonize(clean)

#     # 7. Filter traces and draw centerlines
#     result = original.copy()

#     contours, _ = cv2.findContours(
#         skeleton,
#         cv2.RETR_LIST,
#         cv2.CHAIN_APPROX_NONE
#     )

#     crack_found = False

#     for contour in contours:
#         if len(contour) < 10:
#             continue

#         length = cv2.arcLength(contour, False)

#         if length < 20:
#             continue

#         crack_found = True

#         cv2.polylines(
#             result,
#             [contour],
#             False,
#             (0, 0, 255),
#             2,
#             cv2.LINE_AA
#         )

#     # 8. Print result in VS Code terminal
#     print(
#         "CRACK DETECTED"
#         if crack_found
#         else "NO CRACK DETECTED"
#     )

#     # 9. Display analysis windows
#     cv2.imshow("Captured Specimen", original)
#     cv2.imshow("Threshold", thresh)
#     cv2.imshow("Skeleton Centerlines", skeleton)
#     cv2.imshow("Crack Centerline Overlay", result)

#     return crack_found


# # ---------------- LIVE WEBCAM ----------------

# cap = cv2.VideoCapture(0)

# if not cap.isOpened():
#     raise RuntimeError("Cannot open webcam. Check camera index.")

# print("Live camera started.")
# print("Press S to capture and analyse a specimen.")
# print("Press Q to quit.")

# while True:
#     ret, frame = cap.read()

#     if not ret:
#         print("Failed to capture video.")
#         break

#     cv2.imshow("Live Video - Press S to Capture", frame)

#     key = cv2.waitKey(1) & 0xFF

#     if key == ord('s'):
#         # Capture the current webcam frame
#         captured = frame.copy()

#         # Save the captured image
#         image_path = "Photos/captured_image.jpg"
#         saved = cv2.imwrite(image_path, captured)

#         if saved:
#             print(f"\nImage saved: {image_path}")

#             # Analyse the captured frame directly
#             detect_cracks(captured)
#         else:
#             print("Failed to save the image.")

#     elif key == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()






















# import cv2
# import numpy as np
# import os
# from datetime import datetime

# # ==================================================
# # SETTINGS
# # ==================================================

# CAMERA_INDEX = 0
# SAVE_FOLDER = "Photos"

# THRESHOLD_VALUE = 20
# MIN_COMPONENT_AREA = 12

# MARGIN_X_RATIO = 0.08
# MARGIN_TOP_RATIO = 0.12
# MARGIN_BOTTOM_RATIO = 0.15

# BLACKHAT_KERNEL_SIZE = 21

# os.makedirs(SAVE_FOLDER, exist_ok=True)


# # ==================================================
# # SKELETONIZATION
# # ==================================================

# def skeletonize(binary):
#     """Reduce white crack regions to one-pixel-wide centerlines."""

#     img = (binary > 0).astype(np.uint8)
#     changed = True

#     while changed:
#         changed = False

#         for step in (0, 1):
#             p = np.pad(img, 1)

#             P2 = p[:-2, 1:-1]
#             P3 = p[:-2, 2:]
#             P4 = p[1:-1, 2:]
#             P5 = p[2:, 2:]
#             P6 = p[2:, 1:-1]
#             P7 = p[2:, :-2]
#             P8 = p[1:-1, :-2]
#             P9 = p[:-2, :-2]

#             neighbors = [
#                 P2, P3, P4, P5, P6, P7, P8, P9
#             ]

#             B = sum(neighbors)

#             A = sum(
#                 (
#                     (neighbors[i] == 0) &
#                     (neighbors[(i + 1) % 8] == 1)
#                 ).astype(np.uint8)
#                 for i in range(8)
#             )

#             if step == 0:
#                 condition = (
#                     (P2 * P4 * P6 == 0) &
#                     (P4 * P6 * P8 == 0)
#                 )
#             else:
#                 condition = (
#                     (P2 * P4 * P8 == 0) &
#                     (P2 * P6 * P8 == 0)
#                 )

#             remove = (
#                 (img == 1) &
#                 (B >= 2) &
#                 (B <= 6) &
#                 (A == 1) &
#                 condition
#             )

#             if np.any(remove):
#                 img[remove] = 0
#                 changed = True

#     return img * 255


# # ==================================================
# # CRACK DETECTION
# # ==================================================

# def detect_cracks(original):
#     """Detect crack-like structures in a captured image."""

#     height, width = original.shape[:2]

#     # 1. Define inspection region
#     margin_x = int(width * MARGIN_X_RATIO)
#     margin_top = int(height * MARGIN_TOP_RATIO)
#     margin_bottom = int(height * MARGIN_BOTTOM_RATIO)

#     roi = np.zeros((height, width), dtype=np.uint8)

#     roi[
#         margin_top:height - margin_bottom,
#         margin_x:width - margin_x
#     ] = 255

#     # 2. Convert to grayscale
#     gray = cv2.cvtColor(
#         original, cv2.COLOR_BGR2GRAY
#     )

#     # 3. Enhance local contrast
#     clahe = cv2.createCLAHE(
#         clipLimit=2.0,
#         tileGridSize=(8, 8)
#     )

#     enhanced = clahe.apply(gray)

#     # 4. Reduce noise
#     blur = cv2.GaussianBlur(
#         enhanced, (3, 3), 0
#     )

#     # 5. Enhance dark structures
#     kernel = cv2.getStructuringElement(
#         cv2.MORPH_RECT,
#         (BLACKHAT_KERNEL_SIZE, BLACKHAT_KERNEL_SIZE)
#     )

#     blackhat = cv2.morphologyEx(
#         blur,
#         cv2.MORPH_BLACKHAT,
#         kernel
#     )

#     # 6. Threshold crack candidates
#     _, thresh = cv2.threshold(
#         blackhat,
#         THRESHOLD_VALUE,
#         255,
#         cv2.THRESH_BINARY
#     )

#     # Ignore everything outside the inspection region
#     thresh = cv2.bitwise_and(
#         thresh, roi
#     )

#     # 7. Remove isolated noise conservatively
#     small_kernel = np.ones(
#         (2, 2), np.uint8
#     )

#     clean = cv2.morphologyEx(
#         thresh,
#         cv2.MORPH_OPEN,
#         small_kernel
#     )

#     # 8. Generate centerlines
#     skeleton = skeletonize(clean)

#     # 9. Connected-component filtering
#     count, labels, stats, centroids = (
#         cv2.connectedComponentsWithStats(
#             skeleton,
#             connectivity=8
#         )
#     )

#     result = original.copy()
#     crack_found = False
#     detected_components = 0

#     for i in range(1, count):

#         area = stats[i, cv2.CC_STAT_AREA]
#         x = stats[i, cv2.CC_STAT_LEFT]
#         y = stats[i, cv2.CC_STAT_TOP]
#         w = stats[i, cv2.CC_STAT_WIDTH]
#         h = stats[i, cv2.CC_STAT_HEIGHT]

#         # Reject tiny components
#         if area < MIN_COMPONENT_AREA:
#             continue

#         # Reject long, nearly horizontal boundary lines
#         # Note: genuine horizontal cracks may also be rejected.
#         aspect_ratio = w / max(h, 1)

#         if w > 100 and aspect_ratio > 12:
#             continue

#         # Draw the retained skeleton component in red
#         component_mask = labels == i

#         result[component_mask] = (0, 0, 255)

#         crack_found = True
#         detected_components += 1

#     # 10. Final decision
#     if crack_found:
#         status = "CRACK CANDIDATE DETECTED"
#     else:
#         status = "NO CRACK CANDIDATE DETECTED"

#     print("\n" + "=" * 40)
#     print(f"Result: {status}")
#     print(f"Candidate components: {detected_components}")
#     print("=" * 40)

#     color = (
#         (0, 0, 255) if crack_found
#         else (0, 255, 0)
#     )

#     cv2.putText(
#         result,
#         status,
#         (15, 30),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.65,
#         color,
#         2,
#         cv2.LINE_AA
#     )

#     # 11. Display diagnostic windows
#     cv2.imshow("Captured Specimen", original)
#     cv2.imshow("Inspection ROI", roi)
#     cv2.imshow("Blackhat", blackhat)
#     cv2.imshow("Threshold", thresh)
#     cv2.imshow("Skeleton Centerlines", skeleton)
#     cv2.imshow("Crack Centerline Overlay", result)

#     return crack_found


# # ==================================================
# # LIVE WEBCAM
# # ==================================================

# cap = cv2.VideoCapture(CAMERA_INDEX)

# if not cap.isOpened():
#     raise RuntimeError(
#         "Cannot open webcam. Check CAMERA_INDEX."
#     )

# print("\nLive camera started.")
# print("Press S to capture and analyse a specimen.")
# print("Press Q to quit.")

# try:
#     while True:

#         ret, frame = cap.read()

#         if not ret:
#             print("Failed to capture video.")
#             break

#         cv2.imshow(
#             "Live Video - Press S to Capture",
#             frame
#         )

#         key = cv2.waitKey(1) & 0xFF

#         if key == ord("s"):

#             captured = frame.copy()

#             timestamp = datetime.now().strftime(
#                 "%Y%m%d_%H%M%S_%f"
#             )

#             image_path = os.path.join(
#                 SAVE_FOLDER,
#                 f"specimen_{timestamp}.jpg"
#             )

#             saved = cv2.imwrite(
#                 image_path, captured
#             )

#             if saved:
#                 print(f"\nImage saved: {image_path}")

#                 detect_cracks(captured)

#             else:
#                 print("Failed to save captured image.")

#         elif key == ord("q"):
#             break

# finally:
#     cap.release()
#     cv2.destroyAllWindows()
#     print("Camera closed.")








import cv2
import numpy as np
import os
import time
from pathlib import Path
from datetime import datetime
from picamera2 import Picamera2
from libcamera import controls

# ==================================================
# SETTINGS
# ==================================================

OUTPUT = Path("Photos")
OUTPUT.mkdir(parents=True, exist_ok=True)

CAMERA_WIDTH = 2304
CAMERA_HEIGHT = 1296

QR_MARGIN = 12

THRESHOLD_VALUE = 20
MIN_COMPONENT_AREA = 12
BLACKHAT_KERNEL_SIZE = 21

# Existing fixed inspection margins
MARGIN_X_RATIO = 0.08
MARGIN_TOP_RATIO = 0.12
MARGIN_BOTTOM_RATIO = 0.15

# Preview size for smoother display over VNC
PREVIEW_WIDTH = 960
PREVIEW_HEIGHT = 540

qr_detector = cv2.QRCodeDetector()


# ==================================================
# DISPLAY HELPER
# ==================================================

def show_preview(name, image):
    """Resize display images to reduce VNC rendering lag."""

    h, w = image.shape[:2]

    scale = min(
        PREVIEW_WIDTH / w,
        PREVIEW_HEIGHT / h,
        1.0
    )

    if scale < 1.0:
        display = cv2.resize(
            image,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        )
    else:
        display = image

    cv2.imshow(name, display)


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
    Find QR codes across the full captured image.
    Exclude detected QR regions and a safety margin.
    """

    height, width = image.shape[:2]

    # White = available for crack detection
    # Black = excluded
    qr_mask = np.full(
        (height, width), 255, dtype=np.uint8
    )

    annotated = image.copy()
    decoded_messages = []
    detected_count = 0

    try:
        success, decoded_info, points, _ = (
            qr_detector.detectAndDecodeMulti(image)
        )
    except cv2.error:
        success = False
        decoded_info = []
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
        else:
            points = None
            decoded_info = []

    if points is not None:
        points = np.asarray(points, dtype=np.float32)

        if points.ndim == 2:
            points = points.reshape(1, -1, 2)

        for i, qr_points in enumerate(points):

            corners = np.round(qr_points).astype(np.int32)

            x, y, w, h = cv2.boundingRect(corners)

            # Expand the exclusion area
            x1 = max(0, x - QR_MARGIN)
            y1 = max(0, y - QR_MARGIN)
            x2 = min(width, x + w + QR_MARGIN)
            y2 = min(height, y + h + QR_MARGIN)

            # Exclude the entire QR bounding rectangle
            qr_mask[y1:y2, x1:x2] = 0

            cv2.polylines(
                annotated,
                [corners.reshape(-1, 1, 2)],
                True,
                (0, 255, 0),
                3
            )

            detected_count += 1

            message = (
                decoded_info[i]
                if i < len(decoded_info)
                else ""
            )

            if message:
                decoded_messages.append(message)
                print(f"QR MESSAGE {detected_count}: {message}")

                cv2.putText(
                    annotated,
                    "QR " + str(detected_count),
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )
            else:
                print(
                    f"QR {detected_count} detected, "
                    "but its message could not be decoded."
                )

    print("QR codes detected:", detected_count)

    return annotated, qr_mask, decoded_messages, detected_count


# ==================================================
# CRACK DETECTION
# ==================================================

def detect_cracks(original, qr_mask):

    height, width = original.shape[:2]

    # 1. Create the existing inspection ROI
    margin_x = int(width * MARGIN_X_RATIO)
    margin_top = int(height * MARGIN_TOP_RATIO)
    margin_bottom = int(height * MARGIN_BOTTOM_RATIO)

    roi = np.zeros((height, width), dtype=np.uint8)

    roi[
        margin_top:height - margin_bottom,
        margin_x:width - margin_x
    ] = 255

    # Exclude QR area
    roi = cv2.bitwise_and(roi, qr_mask)

    # 2. Grayscale
    gray = cv2.cvtColor(
        original, cv2.COLOR_BGR2GRAY
    )

    # 3. Enhance local contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # 4. Reduce noise
    blur = cv2.GaussianBlur(
        enhanced, (3, 3), 0
    )

    # 5. Enhance dark structures
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (BLACKHAT_KERNEL_SIZE, BLACKHAT_KERNEL_SIZE)
    )

    blackhat = cv2.morphologyEx(
        blur,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    # 6. Threshold
    _, thresh = cv2.threshold(
        blackhat,
        THRESHOLD_VALUE,
        255,
        cv2.THRESH_BINARY
    )

    # Apply inspection and QR masks
    thresh = cv2.bitwise_and(thresh, roi)

    # 7. Remove isolated noise
    small_kernel = np.ones((2, 2), np.uint8)

    clean = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        small_kernel
    )

    clean = cv2.bitwise_and(clean, roi)

    # 8. Skeletonization
    skeleton = skeletonize(clean)

    skeleton = cv2.bitwise_and(skeleton, roi)

    # 9. Connected component filtering
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

        # Red centerlines
        result[component_mask] = (0, 0, 255)

        crack_found = True
        detected_components += 1

    status = (
        "CRACK CANDIDATE DETECTED"
        if crack_found
        else "NO CRACK CANDIDATE DETECTED"
    )

    print("\n" + "=" * 45)
    print("CRACK RESULT:", status)
    print("Candidate components:", detected_components)
    print("=" * 45)

    color = (0, 0, 255) if crack_found else (0, 255, 0)

    cv2.putText(
        result,
        status,
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
        cv2.LINE_AA
    )

    # Show diagnostic images at a smaller display size
    show_preview("Inspection ROI", roi)
    show_preview("Blackhat", blackhat)
    show_preview("Threshold", thresh)
    show_preview("Skeleton Centerlines", skeleton)
    show_preview("Crack Centerline Overlay", result)

    return crack_found


# ==================================================
# CAMERA MODULE 3
# ==================================================

picam2 = Picamera2()

config = picam2.create_video_configuration(
    main={
        "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
        "format": "RGB888"
    },
    buffer_count=4
)

picam2.configure(config)
picam2.start()

picam2.set_controls({
    "AfMode": controls.AfModeEnum.Continuous
})

time.sleep(2)

print("\nLive Camera Module 3 started.")
print("C = capture, decode QR and analyse cracks")
print("Q = quit")

try:
    while True:

        frame = picam2.capture_array()

        # Use the same colour conversion as your tested code
        frame = cv2.cvtColor(
            frame, cv2.COLOR_RGB2BGR
        )

        # Display a smaller preview for VNC
        preview = cv2.resize(
            frame,
            (PREVIEW_WIDTH, PREVIEW_HEIGHT),
            interpolation=cv2.INTER_AREA
        )

        cv2.imshow("Camera Preview", preview)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == ord("c"):

            captured = frame.copy()

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            image_path = OUTPUT / f"specimen_{timestamp}.jpg"

            saved = cv2.imwrite(
                str(image_path),
                captured,
                [cv2.IMWRITE_JPEG_QUALITY, 95]
            )

            if not saved:
                print("Failed to save captured image.")
                continue

            print("\nImage saved:", image_path)

            # STEP 1: Detect and mask QR code
            (
                qr_annotated,
                qr_mask,
                qr_messages,
                qr_count
            ) = detect_qr_and_create_mask(captured)

            show_preview(
                "QR Detection",
                qr_annotated
            )

            show_preview(
                "QR Exclusion Mask",
                qr_mask
            )

            # STEP 2: Fail safely if QR was not detected
            if qr_count == 0:
                print(
                    "WARNING: Crack analysis skipped. "
                    "No QR code was detected, so its area "
                    "cannot be safely excluded."
                )
                continue

            # STEP 3: Analyse cracks outside the QR mask
            detect_cracks(captured, qr_mask)

finally:
    picam2.stop()
    picam2.close()
    cv2.destroyAllWindows()
    print("Camera closed.")
