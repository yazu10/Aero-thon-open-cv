import cv2

img = cv2.imread("Photos//man.jpg")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

_, thresh = cv2.threshold(
    gray,
    127,
    255,
    cv2.THRESH_BINARY
)

contours, hierarchy = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

for contour in contours:

    approx = cv2.approxPolyDP(
        contour,
        0.02 * cv2.arcLength(contour, True),
        True
    )

    corners = len(approx)

    if corners == 3:
        shape = "Triangle"

    elif corners == 4:
        shape = "Rectangle/Square"

    else:
        shape = "Circle"

    cv2.drawContours(
        img,
        [contour],
        -1,
        (0, 255, 0),
        2
    )

    x, y, w, h = cv2.boundingRect(contour)

    cv2.putText(
        img,
        shape,
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )

cv2.imshow("Shapes", img)

cv2.waitKey(0)
cv2.destroyAllWindows()