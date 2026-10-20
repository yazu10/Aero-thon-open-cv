#!/usr/bin/env python3
"""
Pi Camera Module 3 QR test at full resolution (4608x2592)
using OpenCV's built-in cv2.QRCodeDetector.
"""
import time
import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

# ---------------- SETTINGS ----------------
RES              = (4608, 2592)  # Cam Module 3 max resolution
QR_SIZE_MM       = 25.0
ATTEMPTS         = 10
USE_MANUAL_FOCUS = False         # True for a fixed-height rig
FOCUS_DIST_MM    = 150
SAVE_IMAGES      = True
# ------------------------------------------

def main():
    picam2 = Picamera2()
    cfg = picam2.create_still_configuration(
        main={"size": RES, "format": "RGB888"},  # BGR order for OpenCV
        buffer_count=2
    )
    picam2.configure(cfg)
    picam2.start()
    time.sleep(1.5)

    if USE_MANUAL_FOCUS:
        picam2.set_controls({"AfMode": controls.AfModeEnum.Manual,
                             "LensPosition": 1000.0 / FOCUS_DIST_MM})
        time.sleep(0.5)
    else:
        picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})

    qr = cv2.QRCodeDetector()   # built-in OpenCV QR detector
    ok = 0

    for i in range(1, ATTEMPTS + 1):
        if not USE_MANUAL_FOCUS:
            af_ok = picam2.autofocus_cycle()
            print(f"[{i}] Autofocus: {'OK' if af_ok else 'FAIL'}")

        frame = picam2.capture_array("main")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- Step 1: detect (find the QR corners) ---
        t0 = time.time()
        found, pts = qr.detect(gray)
        t_det = (time.time() - t0) * 1000

        if not found or pts is None:
            print(f"    NOT DETECTED | {t_det:.0f} ms")
        else:
            pts = pts.reshape(-1, 2)

            # --- Step 2: decode (read the data) ---
            t1 = time.time()
            data, _ = qr.decode(gray, pts)
            t_dec = (time.time() - t1) * 1000

            side_px = np.mean([np.linalg.norm(pts[k] - pts[(k + 1) % 4]) for k in range(4)])
            color = (0, 255, 0) if data else (0, 0, 255)
            cv2.polylines(frame, [pts.astype(int)], True, color, 8)

            if data:
                ok += 1
                print(f"    DECODED: '{data}' | detect {t_det:.0f} ms + decode {t_dec:.0f} ms "
                      f"| QR {side_px:.0f}px | {side_px/QR_SIZE_MM:.1f} px/mm")
                cv2.putText(frame, data, tuple(pts[0].astype(int) - [0, 20]),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, color, 6)
            else:
                print(f"    DETECTED but NOT DECODED | QR {side_px:.0f}px "
                      f"(check focus/glare)")

        if SAVE_IMAGES:
            cv2.imwrite(f"qr_test_{i:02d}.jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        time.sleep(0.3)

    picam2.stop()
    print(f"\nSuccess rate: {ok}/{ATTEMPTS} ({100*ok/ATTEMPTS:.0f}%)")

if __name__ == "__main__":
    main()