# import cv2 as cv
# import numpy as np
# from  pyzbar.pyzbar import decode

# # img = cv.imread('Photos//barcode.gif')

# cap = cv.VideoCapture(0)
# cap.set(3,640)
# cap.set(4,480)

# if not cap.isOpened():
#     print("Camera failed to open")
# while True: 
#     success,img = cap.read()
#     for barcode in decode(img) :
#         mydata = barcode.data.decode('utf-8')
#         print(mydata)

#         pts = np.array([barcode.polygon],np.int32)
#         pts = pts.reshape((-1,1,2))
#         cv.polylines(img,[pts],True,(255,0,255), 2)
#         pts2 = barcode.rect
#         cv.putText(img,mydata,(pts2[0],pts2[1]),cv.FONT_HERSHEY_SIMPLEX,0.9,(255,0,255),2)
         
#     cv.imshow('result ',img)
#     cv.waitKey(1)

#     detector = QRCodeDetector()


# import cv2 as cv

# capture = cv.VideoCapture(0)
# detector = cv.QRCodeDetector

# while True:
#     data,frame = capture.read()
#     data, points, _ = detector.detectAndDecode(frame)

#     if data:
#         print (data)

#     cv.imshow("Qr code" , frame)

#     if cv.waitKey(1) & 0xff == ord('q'):
#      break

# capture.release()
# cv.destroyAllWindows()



