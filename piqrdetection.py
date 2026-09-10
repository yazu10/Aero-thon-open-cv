import cv2 as cv
from picamera2 import Picamera2

# Start Raspberry Pi Camera Module 3
picam2 = Picamera2()

picam2.configure(
    picam2.create_video_configuration(
        main={"format": "RGB888", "size": (640, 480)}
    )
)

picam2.start()

# QR code detector
detector = cv.QRCodeDetector()

while True:

    # Get frame from Raspberry Pi camera
    frame = picam2.capture_array()

    # Detect and decode QR code
    data, points, _ = detector.detectAndDecode(frame)

    if data:
        print(data)
        print(points)
        print(points[0])

        pts = points.astype(int)

        # Draw bounding box
        cv.polylines(frame, pts, True, (255, 0, 255), 2)

        # First corner
        x = pts[0][0][0]
        y = pts[0][0][1]

        # Display QR data
        cv.putText(
            frame,
            data,
            (x, y - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            1
        )

        print(points.shape)
        print(points[0][1][1])
        print(points[0][1])

    # Display camera
    cv.imshow("QR code", frame)

    # Press q to quit
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv.destroyAllWindows()