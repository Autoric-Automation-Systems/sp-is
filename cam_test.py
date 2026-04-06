from picamera2 import Picamera2
import cv2

picam2 = Picamera2()
picam2.start()

# ROI fixo
x1, y1 = 260, 90
x2, y2 = 410, 170

while True:
    frame = picam2.capture_array()
    frame = cv2.rotate(frame, cv2.ROTATE_180)

    # recorte da região da tampa
    roi = frame[y1:y2, x1:x2]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    edges = cv2.Canny(blur, 50, 150)
    white_pixels = cv2.countNonZero(edges)

    # lógica simples
    if white_pixels > 500:
        status = "COM TAMPA"
        color = (0,255,0)
    else:
        status = "SEM TAMPA"
        color = (0,0,255)

    # desenha ROI
    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

    # texto
    cv2.putText(frame, status, (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("SP-IS", frame)

    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()