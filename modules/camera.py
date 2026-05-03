from contextlib import suppress
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage
from time import sleep
import serial, sys, time
import cv2
import numpy as np

PREFERRED_CAMERA = "/dev/video1"

class CameraReader(QThread):
    def __init__(self):
        super().__init__()
        
        print("Camera Module Started")
        self.cap = self.openCamera()
        with suppress(ModuleNotFoundError):
            import pyi_splash  # noqa

            pyi_splash.close()
            
        self.ret = None
        self.cv_img = None

    image_signal = Signal(np.ndarray)


    def run(self):
        # capture from web cam
       
        while True:
            if self.cap is None or not self.cap.isOpened():
                sleep(1)
                continue

            self.ret, self.cv_img = self.cap.read()
            if self.ret:
                self.image_signal.emit(self.cv_img)
            else:
                sleep(0.1)
                
    def openCamera(self):
        for device in self.cameraDevices():
            print(f"Trying camera device {device}")
            cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap.release()
                continue

            cap.set(cv2.CAP_PROP_FPS, 60)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            ret, _ = cap.read()
            if ret:
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                print(f"Camera device {device} opened at {width}x{height}")
                return cap

            print(f"Camera device {device} opened but did not return frames")
            cap.release()

        print("Camera Startup Failed: no working V4L2 camera found")
        return None

    def cameraDevices(self):
        devices = sorted(Path("/dev").glob("video*"), key=self.videoDeviceSortKey)
        device_paths = [str(device) for device in devices]

        if PREFERRED_CAMERA in device_paths:
            device_paths.remove(PREFERRED_CAMERA)
            device_paths.insert(0, PREFERRED_CAMERA)

        return device_paths

    def videoDeviceSortKey(self, device):
        suffix = device.name.replace("video", "")
        return int(suffix) if suffix.isdigit() else 999

    

    