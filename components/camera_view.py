from picamera2 import Picamera2
import numpy as np

class CameraView:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraView, cls).__new__(cls)
            cls._instance.init_camera()
        return cls._instance

    def init_camera(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration()
        self.picam2.configure(config)
        # Força modo automático de exposição e ganho
        self.picam2.set_controls({
            "ExposureTime": 0,
            "AnalogueGain": 0,
            "AeEnable": True,
            "AwbEnable": True
        })
        self.picam2.start()
        

    def get_frame(self):
        return self.picam2.capture_array()

    def stop(self):
        pass