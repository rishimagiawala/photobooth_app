
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from time import sleep
import serial, sys, time
import cv2
import numpy as np
class Photographer(QThread):
    def __init__(self, callbackCam, callbackTakePicture):
        super().__init__()
        self.toggleCamStream = callbackCam
        self.takePicture = callbackTakePicture

    change_pixmap_signal = Signal(QPixmap)
    change_count_signal = Signal(QPixmap)


    def run(self):
        # capture from web cam
       
        im = QPixmap("msg_start")
        self.change_pixmap_signal.emit(im)

        sleep(2)
        im = QPixmap("countdown-0")
        self.change_pixmap_signal.emit(im)
        sleep(1)
        self.toggleCamStream()
        self.change_count_signal.emit(QPixmap('countdown-2.png'))

        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-1.png'))
        sleep(1)
        self.takePicture()
        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-2.png'))

        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-1.png'))
        sleep(1)
        self.takePicture()
        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-2.png'))

        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-1.png'))
        sleep(1)
        self.takePicture()
        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-2.png'))

        sleep(1)
        self.change_count_signal.emit(QPixmap('countdown-1.png'))
        sleep(1)
        self.takePicture()
        sleep(1)
        self.toggleCamStream()
        self.change_pixmap_signal.emit(QPixmap('msg_finished.png'))
        

        
            
    def take_picture(self):
        return self.cv_img
                
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(600, 600, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)