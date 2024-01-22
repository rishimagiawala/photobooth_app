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
        self.change_pixmap_signal = Signal(np.ndarray)
        print("Starting Camera")
        try:

            self.cap = cv2.VideoCapture(0)
        
        except:
            print("Camera Startup Failed")
            
        self.ret = None
        self.cv_img = None

    


    def run(self):
        # capture from web cam
       
        while True:
            self.ret, self.cv_img = self.cap.read()
            if self.ret:
                pass
                # print("Currently Printing Images")
                

    

    