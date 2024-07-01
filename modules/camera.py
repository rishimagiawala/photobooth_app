from contextlib import suppress
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage
from time import sleep
import serial, sys, time
import cv2
import numpy as np
class CameraReader(QThread):
    def __init__(self):
        super().__init__()
        
        print("Camera Module Started")
        try:
            
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
            
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G')) 
            self.cap.set(cv2.CAP_PROP_FPS, 24)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840) 
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160) 
            width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(width, height)
        except:
            print("Camera Startup Failed")
        with suppress(ModuleNotFoundError):
            import pyi_splash  # noqa

            pyi_splash.close()
            
        self.ret = None
        self.cv_img = None

    image_signal = Signal(np.ndarray)


    def run(self):
        # capture from web cam
       
        while True:
            self.ret, self.cv_img = self.cap.read()
            if self.ret:
                self.image_signal.emit(self.cv_img)
                
            
    
                

    

    