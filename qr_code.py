import cv2 as cv

cap = cv.VideoCapture(0)
detector = cv.QRCodeDetector()

while True:
    ret,frame = cap.read()
    data, points, _ = detector.detectAndDecode(frame)

    if data:
        print (data)
        print (points)
        print (points[0]) # same as print (points)

        pts=points.astype(int) #stores points as integer in variable pts

        cv.polylines(frame,(pts),True,(255,0,255),2) #to make bounding box

        x = pts[0][0][0]  #storing value of first co-ordinate as x
        y = pts[0][0][1]  #storing value of second co-ordinate as y
        cv.putText(frame,data,(x,y-10),cv.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2)
                             #(x,y-10) to show the text at (x,y-10) 
        print (points.shape) # prints structure (1,4,2) 
                             # 1:Qrcode, 4:four corners, 2:x-y co-ordinates
        print (points[0][1][1]) #prints x of second co-ordinate point
        print (points[0][1]) #prints second co-ordinate point

    cv.imshow("Qr code" , frame)

    if cv.waitKey(1) & 0xff == ord('q'):
     break

cap.release()
cv.destroyAllWindows()