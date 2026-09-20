import cv2
import numpy as np

# 1. Read image
img = cv2.imread("Photos//crack.png")  # Replace with the path to your image

# 2. Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 3. Enhance local contrast
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

enhanced = clahe.apply(gray)

# 4. Reduce small noise
blur = cv2.GaussianBlur(
    enhanced,
    (5, 5),
    0
)

# 5. Enhance dark crack-like structures
kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT,
    (15, 15)
)

blackhat = cv2.morphologyEx(
    blur,
    cv2.MORPH_BLACKHAT,
    kernel
)

# 6. Convert crack candidates into binary image
_, thresh = cv2.threshold(
    blackhat,
    30,
    255,
    cv2.THRESH_BINARY
)

# 7. Remove small noise
small_kernel = np.ones(
    (3, 3),
    np.uint8
)

clean = cv2.morphologyEx(
    thresh,
    cv2.MORPH_OPEN,
    small_kernel
)

# 8. Find detected regions
contours, _ = cv2.findContours(
    clean,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

# 9. Analyze regions
crack_found = False

for contour in contours:

    area = cv2.contourArea(contour)

    x, y, w, h = cv2.boundingRect(contour)

    if area > 20 and max(w, h) > 50:
        crack_found = True

        cv2.rectangle(
            img,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            2
        )

# 10. Print final decision
if crack_found:
    print("CRACK DETECTED")
else:
    print("NO CRACK DETECTED")

# 11. Display stages
cv2.imshow("Original", img)
cv2.imshow("Grayscale", gray)
cv2.imshow("Enhanced", enhanced)
cv2.imshow("Blackhat", blackhat)
cv2.imshow("Threshold", thresh)
cv2.imshow("Clean", clean)

cv2.waitKey(0)
cv2.destroyAllWindows()