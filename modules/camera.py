from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage
from time import sleep
import serial, sys, time
import cv2
import numpy as np
class CameraReader(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    ret = None
    cv_img = None


    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while True:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)

    def takePhotos(self, num_of_photos = 4):
        pass

    