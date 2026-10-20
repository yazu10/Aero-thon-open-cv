
import cv2
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from picamera2 import Picamera2
from libcamera import controls

# ==================================================
# SETTINGS
# ==================================================
WIDTH = 4608
HEIGHT = 2592

OUTPUT_DIR = Path("camera_test")
OUTPUT_DIR.mkdir(exist_ok=True)

# ==================================================
# INITIALIZE CAMERA
# ==================================================
picam2 = Picamera2()

config = picam2.create_still_configuration(
    main={
        "size": (WIDTH, HEIGHT),
        "format": "BGR888"
    }
)

picam2.configure(config)

try:
    print("Starting Raspberry Pi Camera Module 3...")
    picam2.start()

    # Enable autofocus and trigger a focus cycle.
    picam2.set_controls({
        "AfMode": controls.AfModeEnum.Auto
    })

    time.sleep(1)

    picam2.set_controls({
        "AfTrigger": controls.AfTriggerEnum.Start
    })

    print("Autofocusing... please keep the workpiece still.")
    time.sleep(3)

    # Capture a full-resolution still image.
    image = picam2.capture_array("main")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_path = OUTPUT_DIR / f"workpiece_{timestamp}.jpg"

    cv2.imwrite(
        str(original_path),
        image,
        [cv2.IMWRITE_JPEG_QUALITY, 100]
    )

    print(f"\nImage saved: {original_path}")
    print(f"Image resolution: {image.shape[1]} x {image.shape[0]}")

    # ==================================================
    # QR CODE DETECTION
    # ==================================================
    detector = cv2.QRCodeDetector()

    # First attempt: original full-resolution image.
    decoded_text, points, straight_qr = detector.detectAndDecode(image)

    # Second attempt: grayscale image.
    if not decoded_text:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        decoded_text, points, straight_qr = (
            detector.detectAndDecode(gray)
        )

    # Third attempt: adaptive thresholding for uneven lighting.
    if not decoded_text:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        processed = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5
        )

        decoded_text, points, straight_qr = (
            detector.detectAndDecode(processed)
        )

    # ==================================================
    # DISPLAY RESULTS
    # ==================================================
    annotated = image.copy()

    if points is not None:
        corners = np.asarray(points, dtype=np.float32).reshape(-1, 2)
        corners = np.round(corners).astype(np.int32)

        # Green outline indicates the detected QR region.
        cv2.polylines(
            annotated,
            [corners],
            True,
            (0, 255, 0),
            8
        )

    annotated_path = OUTPUT_DIR / f"qr_result_{timestamp}.jpg"
    cv2.imwrite(
        str(annotated_path),
        annotated,
        [cv2.IMWRITE_JPEG_QUALITY, 95]
    )

    print("\n" + "=" * 45)

    if decoded_text:
        print("QR CODE DETECTED AND DECODED!")
        print("Decoded message:")
        print(decoded_text)
    elif points is not None:
        print("QR CODE DETECTED, BUT DECODING FAILED.")
        print("Check focus, lighting, QR size and print quality.")
    else:
        print("NO QR CODE DETECTED.")
        print("Try adjusting the height and lighting.")

    print("=" * 45)
    print(f"Original image: {original_path}")
    print(f"Detection image: {annotated_path}")

    # Resize only for screen display, not for QR detection.
    preview = cv2.resize(
        annotated,
        (1152, 648),
        interpolation=cv2.INTER_AREA
    )

    cv2.imshow("QR Code Test - Green = Detected", preview)
    print("\nPress any key in the image window to exit.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    print("Camera stopped.")
