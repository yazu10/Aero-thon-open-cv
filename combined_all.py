
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
import time
import numpy as np

from pathlib import Path
from datetime import datetime
from picamera2 import Picamera2
from libcamera import controls


# ============================================================
# 1. SETTINGS
# ============================================================

OUTPUT = Path("Photos")
OUTPUT.mkdir(exist_ok=True)

CAMERA_SIZE = (2304, 1296)

PREVIEW_WIDTH = 960
PREVIEW_HEIGHT = 540

QR_MARGIN = 18

# Crack detector settings. These require calibration.
BLACKHAT_KERNEL_SIZE = 25
ADAPTIVE_BLOCK_SIZE = 31
ADAPTIVE_C = -3

MIN_COMPONENT_AREA = 15
MIN_COMPONENT_LENGTH = 10
MIN_ELONGATION = 1.5

CRACK_THRESHOLD = 0.35

# Remove a narrow band around the specimen's detected boundary.
EDGE_MARGIN_PIXELS = 8

# If automatic specimen detection fails, use a central ROI.
# Increase/decrease these values for your camera setup.
FALLBACK_ROI = (0.08, 0.08, 0.92, 0.92)


# ============================================================
# 2. DISPLAY HELPER
# ============================================================

def show_preview(name, image):
    """Display a resized copy to reduce VNC display lag."""

    if image is None:
        return

    h, w = image.shape[:2]

    scale = min(
        PREVIEW_WIDTH / w,
        PREVIEW_HEIGHT / h,
        1.0
    )

    new_size = (
        max(1, int(w * scale)),
        max(1, int(h * scale))
    )

    small = cv2.resize(
        image,
        new_size,
        interpolation=cv2.INTER_AREA
    )

    cv2.imshow(name, small)


# ============================================================
# 3. AUTOMATIC SPECIMEN MASK
# ============================================================

def get_specimen_mask(image):
    """
    Detect a dark specimen against a lighter background.

    Returns a mask where:
        255 = specimen surface
        0   = background

    This works best when the specimen is darker than its
    surroundings and is not touching the image boundaries.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Smooth small texture before thresholding the outline.
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Dark specimen becomes foreground.
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Join gaps caused by shiny areas on the specimen.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (15, 15)
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = gray.shape
    image_area = h * w

    # Only consider large contours that are plausible specimens.
    possible = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area > image_area * 0.03:
            possible.append((area, contour))

    if not possible:
        print("WARNING: Automatic specimen mask failed.")
        print("Using fallback central ROI.")

        x1 = int(w * FALLBACK_ROI[0])
        y1 = int(h * FALLBACK_ROI[1])
        x2 = int(w * FALLBACK_ROI[2])
        y2 = int(h * FALLBACK_ROI[3])

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255

        return mask

    # Select the largest plausible object.
    _, largest_contour = max(possible, key=lambda item: item[0])

    # Convex hull fills small cracks and holes in the detected outline.
    # This is used only for the specimen boundary, not crack detection.
    hull = cv2.convexHull(largest_contour)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, [hull], -1, 255, thickness=cv2.FILLED)

    # Erode slightly so the physical outer edge is not detected as a crack.
    edge_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (EDGE_MARGIN_PIXELS * 2 + 1, EDGE_MARGIN_PIXELS * 2 + 1)
    )

    mask = cv2.erode(mask, edge_kernel, iterations=1)

    return mask


# ============================================================
# 4. QR DETECTION AND EXCLUSION MASK
# ============================================================

def detect_qr_and_make_mask(image):
    """
    Detect QR codes before crack analysis.

    Returns:
        qr_found, qr_texts, qr_mask, annotated_image

    qr_mask:
        255 = area eligible for crack analysis
        0   = QR code and its surrounding margin
    """

    h, w = image.shape[:2]

    qr_mask = np.full((h, w), 255, dtype=np.uint8)
    annotated = image.copy()
    qr_texts = []

    detector = cv2.QRCodeDetector()

    detected_boxes = []

    # Try multiple QR codes first.
    try:
        result = detector.detectAndDecodeMulti(image)

        if result is not None and len(result) == 4:
            success, decoded_info, points, _ = result

            if success and points is not None:
                for i, box in enumerate(points):
                    detected_boxes.append(box)

                    if i < len(decoded_info) and decoded_info[i]:
                        qr_texts.append(decoded_info[i])

    except cv2.error:
        pass

    # Fallback for a single QR code.
    if not detected_boxes:
        try:
            text, points, _ = detector.detectAndDecode(image)

            if points is not None:
                detected_boxes.append(points.reshape(-1, 2))

                if text:
                    qr_texts.append(text)

        except cv2.error:
            pass

    for box in detected_boxes:
        points = np.array(box, dtype=np.float32).reshape(-1, 2)

        x_min = max(0, int(np.floor(points[:, 0].min())) - QR_MARGIN)
        y_min = max(0, int(np.floor(points[:, 1].min())) - QR_MARGIN)

        x_max = min(w - 1, int(np.ceil(points[:, 0].max())) + QR_MARGIN)
        y_max = min(h - 1, int(np.ceil(points[:, 1].max())) + QR_MARGIN)

        # Exclude QR region and its margin.
        cv2.rectangle(
            qr_mask,
            (x_min, y_min),
            (x_max, y_max),
            0,
            thickness=cv2.FILLED
        )

        # Display QR outline.
        polygon = np.round(points).astype(np.int32)
        cv2.polylines(
            annotated,
            [polygon],
            True,
            (0, 255, 0),
            3
        )

        cv2.putText(
            annotated,
            "QR CODE",
            (x_min, max(30, y_min - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    return len(detected_boxes) > 0, qr_texts, qr_mask, annotated


# ============================================================
# 5. CRACK DETECTION
# ============================================================

def detect_cracks(specimen_bgr, valid_mask, debug=True):
    """
    Detect dark, elongated structures within the specimen mask.

    Returns:
        label, score, overlay, candidate_mask
    """

    image = specimen_bgr.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if valid_mask is None:
        valid_mask = np.full(gray.shape, 255, dtype=np.uint8)

    # Make sure the mask dimensions match.
    if valid_mask.shape != gray.shape:
        valid_mask = cv2.resize(
            valid_mask,
            (gray.shape[1], gray.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )

    # Improve local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Suppress high-frequency printing texture.
    smooth = cv2.GaussianBlur(
        enhanced,
        (5, 5),
        0
    )

    # Highlight dark grooves relative to surrounding surface.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (BLACKHAT_KERNEL_SIZE, BLACKHAT_KERNEL_SIZE)
    )

    blackhat = cv2.morphologyEx(
        smooth,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    # Ignore background and QR regions.
    blackhat = cv2.bitwise_and(
        blackhat,
        blackhat,
        mask=valid_mask
    )

    # Adaptive thresholding helps with uneven illumination.
    threshold = cv2.adaptiveThreshold(
        blackhat,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        ADAPTIVE_BLOCK_SIZE,
        ADAPTIVE_C
    )

    threshold = cv2.bitwise_and(
        threshold,
        threshold,
        mask=valid_mask
    )

    # Remove isolated speckles.
    small_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (2, 2)
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        small_kernel
    )

    # Join small gaps along potential cracks.
    join_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3)
    )

    candidates = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        join_kernel
    )

    candidates = cv2.bitwise_and(
        candidates,
        candidates,
        mask=valid_mask
    )

    # Connected-component filtering.
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        candidates,
        connectivity=8
    )

    accepted = np.zeros_like(gray)

    accepted_components = 0
    accepted_pixels = 0

    h, w = gray.shape
    valid_pixels = max(1, cv2.countNonZero(valid_mask))

    min_area = max(
        MIN_COMPONENT_AREA,
        int(h * w * 0.00001)
    )

    for i in range(1, count):
        x, y, cw, ch, area = stats[i]

        if area < min_area:
            continue

        length = max(cw, ch)
        thickness = max(1, min(cw, ch))
        elongation = length / thickness

        if length < MIN_COMPONENT_LENGTH:
            continue

        if elongation < MIN_ELONGATION:
            continue

        component = np.uint8(labels == i) * 255

        component = cv2.bitwise_and(
            component,
            component,
            mask=valid_mask
        )

        pixels = cv2.countNonZero(component)

        if pixels == 0:
            continue

        accepted[component > 0] = 255
        accepted_components += 1
        accepted_pixels += pixels

    # --------------------------------------------------------
    # 6. SPECIMEN-LEVEL CLASSIFICATION SCORE
    # --------------------------------------------------------

    coverage = accepted_pixels / valid_pixels

    component_score = accepted_components / max(
        1.0,
        (h * w) / 100000.0
    )

    # Initial heuristic score, not a probability of having cracks.
    score = (
        0.75 * min(coverage / 0.025, 1.0)
        + 0.25 * min(component_score / 8.0, 1.0)
    )

    label = (
        "CRACK DETECTED"
        if score >= CRACK_THRESHOLD
        else "NO CRACK"
    )

    # Red overlay shows candidate crack pixels.
    overlay = image.copy()
    overlay[accepted > 0] = (0, 0, 255)

    # Draw final classification on the overlay.
    color = (
        (0, 0, 255)
        if label == "CRACK DETECTED"
        else (0, 200, 0)
    )

    cv2.putText(
        overlay,
        label,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        color,
        3
    )

    print("\n========== CRACK ANALYSIS ==========")
    print("Classification:", label)
    print(f"Score: {score:.3f}")
    print(f"Crack coverage: {coverage:.6f}")
    print("Accepted components:", accepted_components)
    print("====================================\n")

    if debug:
        show_preview("01 - Blackhat", blackhat)
        show_preview("02 - Threshold", threshold)
        show_preview("03 - Crack Candidates", candidates)
        show_preview("04 - Filtered Crack Pixels", accepted)
        show_preview("05 - Crack Overlay", overlay)

    return label, score, overlay, accepted


# ============================================================
# 7. PROCESS A CAPTURED SPECIMEN
# ============================================================

def process_specimen(frame):
    """
    Process one full-resolution captured frame.

    QR detection is attempted first. If no QR is detected,
    the crack analysis is skipped to avoid interpreting an
    unmasked QR code as a crack.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    original_path = OUTPUT / f"specimen_{timestamp}.jpg"

    cv2.imwrite(
        str(original_path),
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 95]
    )

    print("\nImage saved:", original_path)

    # 1. Detect QR code.
    qr_found, qr_texts, qr_mask, qr_annotated = (
        detect_qr_and_make_mask(frame)
    )

    show_preview("06 - QR Detection", qr_annotated)
    show_preview("07 - QR Exclusion Mask", qr_mask)

    if qr_found:
        print("QR code detected.")

        if qr_texts:
            for text in qr_texts:
                print("QR MESSAGE:", text)
        else:
            print("QR found, but its message could not be decoded.")

    else:
        print("QR code not detected.")
        print("Crack analysis skipped because QR exclusion failed.")
        print("Check QR visibility, focus, and lighting.")
        return

    # 2. Detect specimen boundary.
    specimen_mask = get_specimen_mask(frame)

    # 3. Combine specimen and QR masks.
    valid_mask = cv2.bitwise_and(
        specimen_mask,
        qr_mask
    )

    show_preview("08 - Specimen Mask", specimen_mask)
    show_preview("09 - Final Analysis Mask", valid_mask)

    if cv2.countNonZero(valid_mask) < frame.shape[0] * frame.shape[1] * 0.03:
        print("ERROR: Usable specimen mask is too small.")
        print("Check specimen boundary detection.")
        return

    # 4. Run crack detection.
    label, score, overlay, crack_mask = detect_cracks(
        frame,
        valid_mask=valid_mask,
        debug=True
    )

    # 5. Save results.
    overlay_path = OUTPUT / f"overlay_{timestamp}.jpg"
    mask_path = OUTPUT / f"crack_mask_{timestamp}.png"

    cv2.imwrite(
        str(overlay_path),
        overlay,
        [cv2.IMWRITE_JPEG_QUALITY, 95]
    )

    cv2.imwrite(
        str(mask_path),
        crack_mask
    )

    print("Overlay saved:", overlay_path)
    print("Crack mask saved:", mask_path)
    print("FINAL RESULT:", label)

    # Show final result.
    show_preview("10 - FINAL RESULT", overlay)


# ============================================================
# 8. CAMERA INITIALIZATION
# ============================================================

def main():
    picam2 = Picamera2()

    config = picam2.create_video_configuration(
        main={
            "size": CAMERA_SIZE,
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

    print("\nCamera started.")
    print("C = capture and analyse specimen")
    print("Q = quit")
    print("")

    try:
        while True:
            frame = picam2.capture_array()

            # Keep the RGB-to-BGR conversion from your tested setup.
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )

            preview = cv2.resize(
                frame,
                (PREVIEW_WIDTH, PREVIEW_HEIGHT),
                interpolation=cv2.INTER_AREA
            )

            cv2.imshow("Live Camera Preview", preview)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("c"):
                process_specimen(frame)

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        picam2.stop()
        picam2.close()
        cv2.destroyAllWindows()
        print("Camera closed.")


# ============================================================
# 9. RUN
# ============================================================

if __name__ == "__main__":
    main()
