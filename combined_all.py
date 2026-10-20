
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
from datetime import datetime
from picamera2 import Picamera2

# ==================================================
# SETTINGS
# ==================================================

SAVE_FOLDER = "Photos"

THRESHOLD_VALUE = 20
MIN_COMPONENT_AREA = 12
BLACKHAT_KERNEL_SIZE = 21

MARGIN_X_RATIO = 0.08
MARGIN_TOP_RATIO = 0.12
MARGIN_BOTTOM_RATIO = 0.15

# Camera preview and processing resolution
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

os.makedirs(SAVE_FOLDER, exist_ok=True)


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
# CRACK DETECTION
# ==================================================

def detect_cracks(original):

    height, width = original.shape[:2]

    # 1. Define the inspection region
    margin_x = int(width * MARGIN_X_RATIO)
    margin_top = int(height * MARGIN_TOP_RATIO)
    margin_bottom = int(height * MARGIN_BOTTOM_RATIO)

    roi = np.zeros((height, width), dtype=np.uint8)

    roi[
        margin_top:height - margin_bottom,
        margin_x:width - margin_x
    ] = 255

    # 2. Convert to grayscale
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

    # 6. Threshold candidate cracks
    _, thresh = cv2.threshold(
        blackhat,
        THRESHOLD_VALUE,
        255,
        cv2.THRESH_BINARY
    )

    # Ignore detections outside the inspection region
    thresh = cv2.bitwise_and(thresh, roi)

    # 7. Remove isolated noise conservatively
    small_kernel = np.ones((2, 2), np.uint8)

    clean = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        small_kernel
    )

    # 8. Generate centerlines
    skeleton = skeletonize(clean)

    # 9. Find connected components
    count, labels, stats, centroids = (
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

        # Reject very small traces
        if area < MIN_COMPONENT_AREA:
            continue

        # Suppress long, nearly horizontal boundaries
        # Genuine horizontal cracks may also be excluded.
        aspect_ratio = w / max(h, 1)

        if w > 100 and aspect_ratio > 12:
            continue

        # Draw the retained centerline in red
        component_mask = labels == i
        result[component_mask] = (0, 0, 255)

        crack_found = True
        detected_components += 1

    # 10. Final decision
    status = (
        "CRACK CANDIDATE DETECTED"
        if crack_found
        else "NO CRACK CANDIDATE DETECTED"
    )

    print("\n" + "=" * 40)
    print("Result:", status)
    print("Candidate components:", detected_components)
    print("=" * 40)

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

    # 11. Display results
    cv2.imshow("Captured Specimen", original)
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

# Allow auto-exposure and auto-white-balance to settle
time.sleep(2)

print("\nRaspberry Pi Camera Module 3 started.")
print("Press S in the preview window to capture and analyse.")
print("Press Q in the preview window to quit.")

try:
    while True:

        # Picamera2 returns frames as NumPy arrays.
        # RGB888 is arranged as BGR bytes for OpenCV.
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

            saved = cv2.imwrite(
                image_path, captured
            )

            if saved:
                print("\nImage saved:", image_path)

                # Run the same crack detection pipeline
                detect_cracks(captured)

            else:
                print("Failed to save image.")

        elif key == ord("q"):
            break

finally:
    picam2.stop()
    picam2.close()
    cv2.destroyAllWindows()
    print("Camera closed.")
