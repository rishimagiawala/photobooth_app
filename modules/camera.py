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

            self.cap = cv2.VideoCapture(0)
        
        except:
            print("Camera Startup Failed")
            
        self.ret = None
        self.cv_img = None

    image_signal = Signal(np.ndarray)


    def run(self):
        # capture from web cam
       
        while True:
            self.ret, self.cv_img = self.cap.read()
            if self.ret:
                self.image_signal.emit(self.cv_img)
                
            
    
                

    

    