# import os
# import cv2
# import numpy as np
# from datetime import datetime

# # ---------------- SETTINGS ----------------
# CAM_INDEX = 1                # change to 1 if you have a laptop cam + USB cam
# SAVE_DIR  = "results"

# # Inspection box (fraction of frame) - keep it INSIDE the specimen surface
# CROP_X1, CROP_Y1 = 0.10, 0.20
# CROP_X2, CROP_Y2 = 0.90, 0.80

# WORK_WIDTH = 1000             # crop is resized to this width -> settings don't depend on webcam resolution

# # Crack detection
# BLACKHAT_K       = 21         # bigger than crack width, bigger than texture
# THRESH_VAL       = 45         # raise if smooth part shows traces, lower if cracks are missed
# BORDER           = 15         # ignore pixels this close to the crop edge (specimen edge/shadow)
# MIN_TRACE_LEN    = 150        # shorter traces = surface texture
# MIN_CRACK_COUNT  = 2
# MIN_TOTAL_LENGTH = 400
# QR_PAD           = 25
# # ------------------------------------------

# os.makedirs(SAVE_DIR, exist_ok=True)
# qr_detector = cv2.QRCodeDetector()


# def skeletonize(binary):
#     """Reduce white crack regions to one-pixel-wide centerlines."""
#     img = (binary > 0).astype(np.uint8)
#     changed = True
#     while changed:
#         changed = False
#         for step in (0, 1):
#             p = np.pad(img, 1)
#             P2 = p[:-2, 1:-1]; P3 = p[:-2, 2:];  P4 = p[1:-1, 2:]
#             P5 = p[2:, 2:];    P6 = p[2:, 1:-1]; P7 = p[2:, :-2]
#             P8 = p[1:-1, :-2]; P9 = p[:-2, :-2]
#             neighbors = [P2, P3, P4, P5, P6, P7, P8, P9]
#             B = sum(neighbors)
#             A = sum(((neighbors[i] == 0) & (neighbors[(i + 1) % 8] == 1)).astype(np.uint8)
#                     for i in range(8))
#             if step == 0:
#                 condition = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
#             else:
#                 condition = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
#             remove = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & condition
#             if np.any(remove):
#                 img[remove] = 0
#                 changed = True
#     return img * 255


# def read_qr(img):
#     data, pts, _ = qr_detector.detectAndDecode(img)
#     if not data:
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         data, pts, _ = qr_detector.detectAndDecode(gray)
#     return (data if data else "QR NOT FOUND"), pts


# def crop_box(frame):
#     h, w = frame.shape[:2]
#     return int(CROP_X1 * w), int(CROP_Y1 * h), int(CROP_X2 * w), int(CROP_Y2 * h)


# def detect_crack(frame, qr_pts=None):
#     # 1. Crop + resize to fixed width
#     x1, y1, x2, y2 = crop_box(frame)
#     crop = frame[y1:y2, x1:x2]
#     scale = WORK_WIDTH / crop.shape[1]
#     crop = cv2.resize(crop, None, fx=scale, fy=scale)

#     # 2. Enhance + blur
#     gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
#     enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
#     blur = cv2.GaussianBlur(enhanced, (5, 5), 0)

#     # 3. Black-hat picks out dark thin lines (cracks)
#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (BLACKHAT_K, BLACKHAT_K))
#     blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)
#     _, thresh = cv2.threshold(blackhat, THRESH_VAL, 255, cv2.THRESH_BINARY)

#     # 4. Ignore crop border (edges / shadows)
#     thresh[:BORDER, :] = 0; thresh[-BORDER:, :] = 0
#     thresh[:, :BORDER] = 0; thresh[:, -BORDER:] = 0

#     # 5. Blank out the QR so it's never counted as a crack
#     qr_local = None
#     if qr_pts is not None:
#         qr_local = ((qr_pts.reshape(-1, 2) - [x1, y1]) * scale).astype(np.int32)
#         qx, qy, qw, qh = cv2.boundingRect(qr_local)
#         cv2.rectangle(thresh, (qx - QR_PAD, qy - QR_PAD),
#                       (qx + qw + QR_PAD, qy + qh + QR_PAD), 0, -1)

#     # 6. Clean + skeleton
#     clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
#     skeleton = skeletonize(clean)

#     # 7. Keep only long traces
#     contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
#     valid, total = [], 0
#     for c in contours:
#         if len(c) < 10:
#             continue
#         L = cv2.arcLength(c, False)
#         if L >= MIN_TRACE_LEN:
#             valid.append(c)
#             total += L

#     crack_found = len(valid) >= MIN_CRACK_COUNT and total >= MIN_TOTAL_LENGTH

#     # 8. Draw
#     annotated = crop.copy()
#     cv2.polylines(annotated, valid, False, (0, 0, 255), 2, cv2.LINE_AA)
#     if qr_local is not None:
#         cv2.polylines(annotated, [qr_local], True, (255, 0, 0), 2)

#     return crack_found, annotated, clean, skeleton, len(valid), round(total, 1)


# def inspect(frame):
#     serial_no, qr_pts = read_qr(frame)
#     crack_found, annotated, clean, skeleton, traces, total = detect_crack(frame, qr_pts)
#     result = "CRACK" if crack_found else "NO CRACK"

#     color = (0, 0, 255) if crack_found else (0, 200, 0)
#     cv2.putText(annotated, f"{result} | S/N: {serial_no}", (20, 40),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

#     stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     cv2.imwrite(f"{SAVE_DIR}/{stamp}_raw.jpg", frame)
#     cv2.imwrite(f"{SAVE_DIR}/{stamp}_{result.replace(' ', '_')}.jpg", annotated)

#     print("--------------------------------")
#     print("S/N:", serial_no)
#     print("RESULT:", result)
#     print("Valid crack-like traces:", traces)
#     print("Total trace length:", total)
#     print("--------------------------------")

#     cv2.imshow("Threshold", clean)
#     cv2.imshow("Skeleton", skeleton)
#     cv2.imshow("Result", annotated)


# # ---------------- MAIN ----------------
# cap = cv2.VideoCapture(CAM_INDEX)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# if not cap.isOpened():
#     raise RuntimeError("Webcam not found - check CAM_INDEX.")

# print("SPACE = capture & inspect | Q = quit")

# while True:
#     ok, frame = cap.read()
#     if not ok:
#         break

#     preview = frame.copy()
#     x1, y1, x2, y2 = crop_box(frame)
#     cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
#     cv2.putText(preview, "SPACE = inspect | Q = quit", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
#     cv2.imshow("Live", preview)

#     key = cv2.waitKey(1) & 0xFF
#     if key == ord(' '):
#         inspect(frame.copy())      # analyse the still, not the video
#     elif key == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()














# import os
# import cv2
# import numpy as np
# from datetime import datetime

# try:
#     from pyzbar.pyzbar import decode as zbar_decode   # optional, very reliable
# except Exception:
#     zbar_decode = None

# # ---------------- SETTINGS ----------------
# CAM_INDEX = 1
# SAVE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# # Trigger zone (fixed box, fraction of frame) - also used as the crack crop
# ZONE_X1, ZONE_Y1 = 0.05, 0.10
# ZONE_X2, ZONE_Y2 = 0.95, 0.90
# PRESENCE_THRESH  = 15     # avg difference from empty box = specimen present
# MOTION_THRESH    = 3      # avg difference between frames = still
# STABLE_FRAMES    = 8      # still frames needed before capture

# # Crack detection
# WORK_WIDTH       = 1000
# BLACKHAT_K       = 21
# THRESH_HIGH      = 45     # strong crack pixels (seeds)
# THRESH_LOW       = 30     # faint pixels kept only if connected to a strong one
# BORDER           = 15
# MIN_TRACE_LEN    = 150
# MIN_CRACK_COUNT  = 2
# MIN_TOTAL_LENGTH = 400

# # QR
# QR_BRIGHT_OFFSET = 40     # QR paper is this much brighter than the specimen
# QR_MIN_AREA      = 3000   # px (in 1000-px-wide work image)
# QR_PAD           = 20
# QR_RETRY_FRAMES  = 10
# # ------------------------------------------

# os.makedirs(SAVE_DIR, exist_ok=True)
# print("Saving images to:", SAVE_DIR)
# print("pyzbar active:", zbar_decode is not None)

# try:
#     qr_detector = cv2.QRCodeDetectorAruco()
# except AttributeError:
#     qr_detector = cv2.QRCodeDetector()


# # ---------------- SKELETON ----------------
# def skeletonize(binary):
#     img = (binary > 0).astype(np.uint8)
#     changed = True
#     while changed:
#         changed = False
#         for step in (0, 1):
#             p = np.pad(img, 1)
#             P2 = p[:-2, 1:-1]; P3 = p[:-2, 2:];  P4 = p[1:-1, 2:]
#             P5 = p[2:, 2:];    P6 = p[2:, 1:-1]; P7 = p[2:, :-2]
#             P8 = p[1:-1, :-2]; P9 = p[:-2, :-2]
#             neighbors = [P2, P3, P4, P5, P6, P7, P8, P9]
#             B = sum(neighbors)
#             A = sum(((neighbors[i] == 0) & (neighbors[(i + 1) % 8] == 1)).astype(np.uint8)
#                     for i in range(8))
#             if step == 0:
#                 condition = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
#             else:
#                 condition = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
#             remove = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & condition
#             if np.any(remove):
#                 img[remove] = 0
#                 changed = True
#     return img * 255


# # ---------------- QR ----------------
# def read_qr(img):
#     """Returns (text, pts in frame coords). pts may exist even if not decoded."""
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     # 1. pyzbar (if installed)
#     if zbar_decode:
#         for g in (gray, cv2.resize(gray, None, fx=2, fy=2)):
#             res = zbar_decode(g)
#             if res:
#                 s = g.shape[1] / gray.shape[1]
#                 pts = np.array(res[0].polygon, np.float32) / s
#                 return res[0].data.decode("utf-8", "ignore"), pts

#     # 2. OpenCV on several versions of the image
#     sharp = cv2.addWeighted(gray, 1.5, cv2.GaussianBlur(gray, (0, 0), 3), -0.5, 0)
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
#     otsu  = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
#     big   = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

#     found_pts = None
#     for im, scale in [(img, 1), (gray, 1), (sharp, 1), (clahe, 1), (otsu, 1), (big, 2)]:
#         data, pts, _ = qr_detector.detectAndDecode(im)
#         if pts is not None:
#             pts = pts.astype(np.float32) / scale
#             if data:
#                 return data, pts
#             if found_pts is None:
#                 found_pts = pts
#     return "QR NOT FOUND", found_pts


# def mask_qr_paper(gray, thresh):
#     """Black out large bright-white patches (QR label) even if QR wasn't decoded."""
#     white = (gray > np.median(gray) + QR_BRIGHT_OFFSET).astype(np.uint8) * 255
#     white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
#     contours, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     boxes = []
#     for c in contours:
#         if cv2.contourArea(c) < QR_MIN_AREA:
#             continue
#         x, y, w, h = cv2.boundingRect(c)
#         cv2.rectangle(thresh, (x - QR_PAD, y - QR_PAD), (x + w + QR_PAD, y + h + QR_PAD), 0, -1)
#         boxes.append((x, y, w, h))
#     return boxes


# # ---------------- CRACK ----------------
# def detect_crack(frame, box, qr_pts=None):
#     x1, y1, x2, y2 = box
#     crop = frame[y1:y2, x1:x2]
#     scale = WORK_WIDTH / crop.shape[1]
#     crop = cv2.resize(crop, None, fx=scale, fy=scale)

#     gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
#     enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
#     blur = cv2.GaussianBlur(enhanced, (5, 5), 0)

#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (BLACKHAT_K, BLACKHAT_K))
#     blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)

#     # Two-level threshold: faint crack pixels kept only if connected to strong ones
#     weak = (blackhat > THRESH_LOW).astype(np.uint8)
#     strong = blackhat > THRESH_HIGH
#     _, labels = cv2.connectedComponents(weak, connectivity=8)
#     keep = np.unique(labels[strong])
#     keep = keep[keep > 0]
#     thresh = np.isin(labels, keep).astype(np.uint8) * 255

#     # Ignore crop border
#     thresh[:BORDER, :] = 0; thresh[-BORDER:, :] = 0
#     thresh[:, :BORDER] = 0; thresh[:, -BORDER:] = 0

#     # Mask QR: decoded location + bright paper patch
#     qr_local = None
#     if qr_pts is not None:
#         qr_local = ((qr_pts.reshape(-1, 2) - [x1, y1]) * scale).astype(np.int32)
#         qx, qy, qw, qh = cv2.boundingRect(qr_local)
#         cv2.rectangle(thresh, (qx - QR_PAD, qy - QR_PAD),
#                       (qx + qw + QR_PAD, qy + qh + QR_PAD), 0, -1)
#     paper_boxes = mask_qr_paper(gray, thresh)

#     # Remove specks, then bridge small gaps in cracks
#     clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
#     clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
#     skeleton = skeletonize(clean)

#     contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
#     valid, total = [], 0
#     for c in contours:
#         if len(c) < 10:
#             continue
#         L = cv2.arcLength(c, False)
#         if L >= MIN_TRACE_LEN:
#             valid.append(c)
#             total += L

#     crack_found = len(valid) >= MIN_CRACK_COUNT and total >= MIN_TOTAL_LENGTH

#     annotated = crop.copy()
#     cv2.polylines(annotated, valid, False, (0, 0, 255), 2, cv2.LINE_AA)
#     for (x, y, w, h) in paper_boxes:
#         cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
#     if qr_local is not None:
#         cv2.polylines(annotated, [qr_local], True, (255, 0, 0), 2)

#     return crack_found, annotated, clean, skeleton, len(valid), round(total, 1)


# # ---------------- TRIGGER ZONE ----------------
# def zone_box(frame):
#     h, w = frame.shape[:2]
#     return int(ZONE_X1 * w), int(ZONE_Y1 * h), int(ZONE_X2 * w), int(ZONE_Y2 * h)


# def zone_gray(frame):
#     x1, y1, x2, y2 = zone_box(frame)
#     g = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
#     return cv2.GaussianBlur(cv2.resize(g, (320, 180)), (5, 5), 0)


# # ---------------- INSPECTION ----------------
# def inspect(frame, box):
#     serial_no, qr_pts = read_qr(frame)
#     for _ in range(QR_RETRY_FRAMES):
#         if serial_no != "QR NOT FOUND":
#             break
#         ok, f = cap.read()
#         if not ok:
#             continue
#         s, p = read_qr(f)
#         if s != "QR NOT FOUND":
#             serial_no, qr_pts = s, p
#         elif qr_pts is None and p is not None:
#             qr_pts = p

#     crack_found, annotated, clean, skeleton, traces, total = detect_crack(frame, box, qr_pts)
#     result = "CRACK" if crack_found else "NO CRACK"

#     color = (0, 0, 255) if crack_found else (0, 200, 0)
#     cv2.putText(annotated, f"{result} | S/N: {serial_no}", (20, 40),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

#     stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     cv2.imwrite(f"{SAVE_DIR}/{stamp}_raw.jpg", frame)
#     cv2.imwrite(f"{SAVE_DIR}/{stamp}_{result.replace(' ', '_')}.jpg", annotated)

#     print("--------------------------------")
#     print("S/N:", serial_no)
#     print("RESULT:", result)
#     print("Valid crack-like traces:", traces)
#     print("Total trace length:", total)
#     print("--------------------------------")

#     cv2.imshow("Threshold", clean)
#     cv2.imshow("Skeleton", skeleton)
#     cv2.imshow("Result", annotated)


# # ---------------- MAIN ----------------
# cap = cv2.VideoCapture(CAM_INDEX)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# if not cap.isOpened():
#     raise RuntimeError("Webcam not found - check CAM_INDEX.")

# print("Keep box EMPTY - learning background...")
# for _ in range(30):                     # let exposure settle
#     cap.read()
# ok, frame = cap.read()
# reference = zone_gray(frame)
# prev = reference
# print("Ready. Auto-capture ON | SPACE = manual | R = re-learn empty | Q = quit")

# still, armed = 0, True

# while True:
#     ok, frame = cap.read()
#     if not ok:
#         break

#     cur = zone_gray(frame)
#     presence = cv2.absdiff(cur, reference).mean()
#     motion = cv2.absdiff(cur, prev).mean()
#     prev = cur

#     if presence > PRESENCE_THRESH:
#         if armed:
#             still = still + 1 if motion < MOTION_THRESH else 0
#             status, color = f"Specimen - hold still {still}/{STABLE_FRAMES}", (0, 255, 255)
#             if still >= STABLE_FRAMES:
#                 inspect(frame.copy(), zone_box(frame))
#                 armed, still = False, 0
#         else:
#             status, color = "Captured - remove specimen", (0, 255, 0)
#     else:
#         status, color = "Waiting for specimen", (0, 200, 255)
#         if presence < PRESENCE_THRESH * 0.6:   # clearly empty -> re-arm
#             armed, still = True, 0

#     preview = frame.copy()
#     x1, y1, x2, y2 = zone_box(frame)
#     cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
#     cv2.putText(preview, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
#     cv2.putText(preview, f"presence {presence:.1f}  motion {motion:.1f}", (10, 60),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
#     cv2.imshow("Live", preview)

#     key = cv2.waitKey(1) & 0xFF
#     if key == ord(' '):
#         inspect(frame.copy(), zone_box(frame))
#     elif key == ord('r'):
#         reference = zone_gray(frame)
#         print("Background re-learned.")
#     elif key == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()























import os
import cv2
import time
import numpy as np
from datetime import datetime
from picamera2 import Picamera2
from libcamera import controls

try:
    from pyzbar.pyzbar import decode as zbar_decode   # optional, very reliable
except Exception:
    zbar_decode = None

# ---------------- SETTINGS ----------------
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

CAMERA_SIZE    = (2304, 1296)
PREVIEW_WIDTH  = 960
PREVIEW_HEIGHT = 540

# Trigger zone (fixed box, fraction of frame) - also used as the crack crop
ZONE_X1, ZONE_Y1 = 0.05, 0.10
ZONE_X2, ZONE_Y2 = 0.95, 0.90
PRESENCE_THRESH  = 15     # avg difference from empty box = specimen present
MOTION_THRESH    = 3      # avg difference between frames = still
STABLE_FRAMES    = 8      # still frames needed before capture

# Crack detection
WORK_WIDTH       = 1000
BLACKHAT_K       = 21
THRESH_HIGH      = 45     # strong crack pixels (seeds)
THRESH_LOW       = 30     # faint pixels kept only if connected to a strong one
BORDER           = 15
MIN_TRACE_LEN    = 150
MIN_CRACK_COUNT  = 2
MIN_TOTAL_LENGTH = 400

# QR
QR_BRIGHT_OFFSET = 40     # QR paper is this much brighter than the specimen
QR_MIN_AREA      = 3000   # px (in 1000-px-wide work image)
QR_PAD           = 20
QR_RETRY_FRAMES  = 3      # kept low - full-res QR attempts are slow on the Pi
# ------------------------------------------

os.makedirs(SAVE_DIR, exist_ok=True)
print("Saving images to:", SAVE_DIR)
print("pyzbar active:", zbar_decode is not None)

try:
    qr_detector = cv2.QRCodeDetectorAruco()
except AttributeError:
    qr_detector = cv2.QRCodeDetector()


# ---------------- PREVIEW HELPER ----------------
def show_preview(name, image):
    """Show a resized copy to reduce VNC lag."""
    if image is None:
        return
    h, w = image.shape[:2]
    scale = min(PREVIEW_WIDTH / w, PREVIEW_HEIGHT / h, 1.0)
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    cv2.imshow(name, cv2.resize(image, size, interpolation=cv2.INTER_AREA))


def grab(picam2):
    """Full-res BGR frame."""
    return cv2.cvtColor(picam2.capture_array(), cv2.COLOR_RGB2BGR)


# ---------------- SKELETON ----------------
def skeletonize(binary):
    img = (binary > 0).astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = np.pad(img, 1)
            P2 = p[:-2, 1:-1]; P3 = p[:-2, 2:];  P4 = p[1:-1, 2:]
            P5 = p[2:, 2:];    P6 = p[2:, 1:-1]; P7 = p[2:, :-2]
            P8 = p[1:-1, :-2]; P9 = p[:-2, :-2]
            neighbors = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(neighbors)
            A = sum(((neighbors[i] == 0) & (neighbors[(i + 1) % 8] == 1)).astype(np.uint8)
                    for i in range(8))
            if step == 0:
                condition = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                condition = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            remove = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & condition
            if np.any(remove):
                img[remove] = 0
                changed = True
    return img * 255


# ---------------- QR ----------------
def read_qr(img):
    """Returns (text, pts in frame coords). pts may exist even if not decoded."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. pyzbar (if installed)
    if zbar_decode:
        for g in (gray, cv2.resize(gray, None, fx=2, fy=2)):
            res = zbar_decode(g)
            if res:
                s = g.shape[1] / gray.shape[1]
                pts = np.array(res[0].polygon, np.float32) / s
                return res[0].data.decode("utf-8", "ignore"), pts

    # 2. OpenCV on several versions of the image
    sharp = cv2.addWeighted(gray, 1.5, cv2.GaussianBlur(gray, (0, 0), 3), -0.5, 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    otsu  = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    big   = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    found_pts = None
    for im, scale in [(img, 1), (gray, 1), (sharp, 1), (clahe, 1), (otsu, 1), (big, 2)]:
        data, pts, _ = qr_detector.detectAndDecode(im)
        if pts is not None:
            pts = pts.astype(np.float32) / scale
            if data:
                return data, pts
            if found_pts is None:
                found_pts = pts
    return "QR NOT FOUND", found_pts


def mask_qr_paper(gray, thresh):
    """Black out large bright-white patches (QR label) even if QR wasn't decoded."""
    white = (gray > np.median(gray) + QR_BRIGHT_OFFSET).astype(np.uint8) * 255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    contours, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) < QR_MIN_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(thresh, (x - QR_PAD, y - QR_PAD), (x + w + QR_PAD, y + h + QR_PAD), 0, -1)
        boxes.append((x, y, w, h))
    return boxes


# ---------------- CRACK ----------------
def detect_crack(frame, box, qr_pts=None):
    x1, y1, x2, y2 = box
    crop = frame[y1:y2, x1:x2]
    scale = WORK_WIDTH / crop.shape[1]
    crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    blur = cv2.GaussianBlur(enhanced, (5, 5), 0)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (BLACKHAT_K, BLACKHAT_K))
    blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)

    # Two-level threshold: faint crack pixels kept only if connected to strong ones
    weak = (blackhat > THRESH_LOW).astype(np.uint8)
    strong = blackhat > THRESH_HIGH
    _, labels = cv2.connectedComponents(weak, connectivity=8)
    keep = np.unique(labels[strong])
    keep = keep[keep > 0]
    thresh = np.isin(labels, keep).astype(np.uint8) * 255

    # Ignore crop border
    thresh[:BORDER, :] = 0; thresh[-BORDER:, :] = 0
    thresh[:, :BORDER] = 0; thresh[:, -BORDER:] = 0

    # Mask QR: decoded location + bright paper patch
    qr_local = None
    if qr_pts is not None:
        qr_local = ((qr_pts.reshape(-1, 2) - [x1, y1]) * scale).astype(np.int32)
        qx, qy, qw, qh = cv2.boundingRect(qr_local)
        cv2.rectangle(thresh, (qx - QR_PAD, qy - QR_PAD),
                      (qx + qw + QR_PAD, qy + qh + QR_PAD), 0, -1)
    paper_boxes = mask_qr_paper(gray, thresh)

    # Remove specks, then bridge small gaps in cracks
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    skeleton = skeletonize(clean)

    contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    valid, total = [], 0
    for c in contours:
        if len(c) < 10:
            continue
        L = cv2.arcLength(c, False)
        if L >= MIN_TRACE_LEN:
            valid.append(c)
            total += L

    crack_found = len(valid) >= MIN_CRACK_COUNT and total >= MIN_TOTAL_LENGTH

    annotated = crop.copy()
    cv2.polylines(annotated, valid, False, (0, 0, 255), 2, cv2.LINE_AA)
    for (x, y, w, h) in paper_boxes:
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
    if qr_local is not None:
        cv2.polylines(annotated, [qr_local], True, (255, 0, 0), 2)

    return crack_found, annotated, clean, skeleton, len(valid), round(total, 1)


# ---------------- TRIGGER ZONE ----------------
def zone_box(frame):
    h, w = frame.shape[:2]
    return int(ZONE_X1 * w), int(ZONE_Y1 * h), int(ZONE_X2 * w), int(ZONE_Y2 * h)


def zone_gray(frame):
    x1, y1, x2, y2 = zone_box(frame)
    g = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(cv2.resize(g, (320, 180), interpolation=cv2.INTER_AREA), (5, 5), 0)


# ---------------- INSPECTION ----------------
def inspect(picam2, frame, box):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(f"{SAVE_DIR}/{stamp}_raw.jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

    serial_no, qr_pts = read_qr(frame)
    for _ in range(QR_RETRY_FRAMES):
        if serial_no != "QR NOT FOUND":
            break
        s, p = read_qr(grab(picam2))
        if s != "QR NOT FOUND":
            serial_no, qr_pts = s, p
        elif qr_pts is None and p is not None:
            qr_pts = p

    crack_found, annotated, clean, skeleton, traces, total = detect_crack(frame, box, qr_pts)
    result = "CRACK" if crack_found else "NO CRACK"

    color = (0, 0, 255) if crack_found else (0, 200, 0)
    cv2.putText(annotated, f"{result} | S/N: {serial_no}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    cv2.imwrite(f"{SAVE_DIR}/{stamp}_{result.replace(' ', '_')}.jpg", annotated,
                [cv2.IMWRITE_JPEG_QUALITY, 95])

    print("--------------------------------")
    print("S/N:", serial_no)
    print("RESULT:", result)
    print("Valid crack-like traces:", traces)
    print("Total trace length:", total)
    print("--------------------------------")

    show_preview("Threshold", clean)
    show_preview("Skeleton", skeleton)
    show_preview("Result", annotated)


# ---------------- CAMERA ----------------
def main():
    picam2 = Picamera2()

    config = picam2.create_video_configuration(
        main={"size": CAMERA_SIZE, "format": "RGB888"},
        buffer_count=4
    )
    picam2.configure(config)
    picam2.start()

    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    time.sleep(2)

    print("\nCamera started. Keep box EMPTY - learning background...")
    frame = grab(picam2)
    reference = zone_gray(frame)
    prev = reference
    still, armed = 0, True

    print("Auto-capture ON")
    print("C = capture and process (manual)")
    print("R = re-learn empty box")
    print("Q = quit\n")

    try:
        while True:
            frame = grab(picam2)

            cur = zone_gray(frame)
            presence = cv2.absdiff(cur, reference).mean()
            motion = cv2.absdiff(cur, prev).mean()
            prev = cur

            if presence > PRESENCE_THRESH:
                if armed:
                    still = still + 1 if motion < MOTION_THRESH else 0
                    status, color = f"Specimen - hold still {still}/{STABLE_FRAMES}", (0, 255, 255)
                    if still >= STABLE_FRAMES:
                        inspect(picam2, frame.copy(), zone_box(frame))
                        armed, still = False, 0
                else:
                    status, color = "Captured - remove specimen", (0, 255, 0)
            else:
                status, color = "Waiting for specimen", (0, 200, 255)
                if presence < PRESENCE_THRESH * 0.6:   # clearly empty -> re-arm
                    armed, still = True, 0

            # Draw on the small preview only (less VNC lag)
            preview = cv2.resize(frame, (PREVIEW_WIDTH, PREVIEW_HEIGHT),
                                 interpolation=cv2.INTER_AREA)
            x1, y1, x2, y2 = zone_box(preview)
            cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
            cv2.putText(preview, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(preview, f"presence {presence:.1f}  motion {motion:.1f}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Live Camera Preview", preview)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                inspect(picam2, frame.copy(), zone_box(frame))
            elif key == ord("r"):
                reference = zone_gray(frame)
                print("Background re-learned.")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        picam2.stop()
        picam2.close()
        cv2.destroyAllWindows()
        print("Camera closed.")


if __name__ == "__main__":
    main()