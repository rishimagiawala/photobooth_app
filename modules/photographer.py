
import json
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from time import sleep
import serial, sys, time
import cv2
import numpy as np
import os
from paths import app_path
class Photographer(QThread):
    def __init__(self, callbackCam, callbackTakePicture, getQueueCount, popFromQueue, getTakenImage, getPrintCount):
        super().__init__()
        self.getQueueCount = getQueueCount
        self.popFromQueue = popFromQueue
        self.toggleCamStream = callbackCam
        self.takePicture = callbackTakePicture
        self.getTakenImage = getTakenImage
        self.getPrintCount = getPrintCount

    change_image_signal = Signal(str)
    change_count_signal = Signal(str)


    def run(self):




        self.change_image_signal.emit(str(app_path("assets", "images", "viewer", "not_ready.png")))

        while True:

            current_queue_count = self.getQueueCount()
            if current_queue_count > 0:
                self.change_image_signal.emit(str(app_path("assets", "images", "viewer", "msg_start.png")))
                num_of_photos = 4
                with open(app_path('config', 'printing', 'layout.json'), 'r') as layout_file:
                    layout_data = json.load(layout_file)
                    num_of_photos = layout_data['num_of_photos']
                print("Session Begun to Take " + str(num_of_photos) + " Photos")
                sleep(2)
                

                for i in range(num_of_photos):
                    self.toggleCamStream(True)
                    self.change_count_signal.emit(str(app_path('assets', 'images', 'viewer', 'countdown-5.png')))
                    sleep(1)
                    self.change_count_signal.emit(str(app_path('assets', 'images', 'viewer', 'countdown-4.png')))
                    sleep(1)
                    self.change_count_signal.emit(str(app_path('assets', 'images', 'viewer', 'countdown-3.png')))
                    sleep(1)
                    self.change_count_signal.emit(str(app_path('assets', 'images', 'viewer', 'countdown-2.png')))
                    sleep(1)
                    self.change_count_signal.emit(str(app_path('assets', 'images', 'viewer', 'countdown-1.png')))
                    sleep(1)
                    if not self.takePicture():
                        print("Waiting for camera frame before retrying picture")
                        sleep(1)
                        self.takePicture()
                    self.change_count_signal.emit('')
                    self.toggleCamStream(False)
                    sleep(2)
    
                self.toggleCamStream(False)
                self.change_count_signal.emit('')
                self.change_image_signal.emit(str(app_path('assets', 'images', 'viewer', 'msg_finished.png')))
                sleep(2)
                self.popFromQueue()

                if self.getQueueCount() == 0:
                    
                    self.change_count_signal.emit('')
                    if self.getPrintCount() > 699:
                        self.change_image_signal.emit(str(app_path("assets", "images", "viewer", "no_paper.png")))
                    else:
                        self.change_image_signal.emit(str(app_path("assets", "images", "viewer", "not_ready.png")))
            else:
                sleep(0.1)
           
        

        
            
    # def take_picture(self):
    #     return self.cv_img
                
    # def update_image(self, cv_img):
    #     """Updates the image_label with a new opencv image"""
    #     qt_img = self.convert_cv_qt(cv_img)
    #     self.image_label.setPixmap(qt_img)
    
    # def convert_cv_qt(self, cv_img):
    #     """Convert from an opencv image to QPixmap"""
    #     rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    #     h, w, ch = rgb_image.shape
    #     bytes_per_line = ch * w
    #     convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
    #     p = convert_to_Qt_format.scaled(600, 600, Qt.KeepAspectRatio)
    #     return QPixmap.fromImage(p)