import cv2
from picamera2 import Picamera2

class CameraView:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.start()

    def get_frame(self):
        frame = self.picam2.capture_array()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        return frame

    def stop(self):
        try:
            self.picam2.stop()
            self.picam2.close()
        except:
            pass