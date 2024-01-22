from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QSizePolicy
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QImage
from time import sleep
import sys
from modules.camera import CameraReader
import cv2
from modules.credit_card import Reader
from modules.photographer import Photographer

class Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicksCount = 0
        self.showingCam = False
       
        self.setWindowTitle("Photobooth Window")
        self.showFullScreen()
        self.image_label = QLabel()
        self.im = QPixmap("not_ready")
        self.image_label.setPixmap(self.im)
       
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.image_label.setScaledContents(True)
        self.centralWidget = self.image_label
        self.setCentralWidget(self.centralWidget)


    def mouseDoubleClickEvent(self, e):
        print("Booth Session Begun")
        self.takePhotos()
    def takePhotos(self, numOfPhotos = 2):
        self.photoThread = Photographer(self.toggleShowingCam)
        self.photoThread.start()
        self.photoThread.change_pixmap_signal.connect(self.updateImage)
    def updateImage(self,image):
        self.image_label.setPixmap(image)
    def startImageStream(self, image):
        if self.showingCam is True:
            qt_img = self.convert_cv_qt(image)
            self.image_label.setPixmap(qt_img)
    def toggleShowingCam(self):
        self.showingCam =  not (self.showingCam)
        
        
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(600, 600, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)