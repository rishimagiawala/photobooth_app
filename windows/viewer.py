from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QSizePolicy
from PySide6.QtCore import QObject, Qt, QThread, Signal, QPoint, QKeyCombination
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent, QPixmap, QImage, QDesktopServices, QCursor
from time import sleep
import sys
from modules.camera import CameraReader
import cv2
from modules.credit_card import Reader
from modules.photographer import Photographer
from datetime import datetime

class Viewer(QMainWindow):
    def __init__(self, addToQueue, popFromQueue, getQueueCount, closeViewer):
        super().__init__()

        print("Viewer Started")
        # width = self.frameGeometry().width()
        # height = self.frameGeometry().height()
        # print(width)
        # print(height)

       
        self.hidden_cursor = QCursor()
        self.addToQueue = addToQueue
        self.popFromQueue = popFromQueue
        self.getQueueCount = getQueueCount
        self.closeViewer = closeViewer
      
        self.showingCam = False
        self.camImage = None
        self.takenImage = QPixmap()

        self.setWindowTitle("Photobooth Window")
        self.showFullScreen()
       
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()
        self.hidden_cursor.setPos(width+300,0)
        # print(width)
        # print(height)
        self.image_label = QLabel()
        self.im = QPixmap("./assets/images/viewer/not_ready")
        self.image_label.setPixmap(self.im)
        
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.image_label.setScaledContents(True)
        self.centralWidget = self.image_label
        self.setCentralWidget(self.centralWidget)
        self.countdown_label = QLabel(self.image_label)
        self.countdown_label.setScaledContents(True)
        self.countdown_label.resize(100,100)
        self.countdown_label.move(int(width/2)-50, height-120) 

        self.photoThread = Photographer(self.toggleShowingCam, self.saveImageToFile, self.getQueueCount, self.popFromQueue, self.getTakenImage)
        self.photoThread.start()
        self.photoThread.change_image_signal.connect(self.updateImage)
        self.photoThread.change_count_signal.connect(self.updateCountImage)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.photoThread.terminate()
            self.closeViewer()
            self.close()


    def mouseDoubleClickEvent(self, e):
        self.addToQueue()
   
    def updateImage(self,image):
        self.image_label.setPixmap(image)


    def updateViewerCamImage(self, image):
        self.camImage = image
        if self.showingCam is True:
            qt_img = self.convert_cv_qt(image)
            self.takenImage = qt_img
            self.image_label.setPixmap(qt_img)
    def toggleShowingCam(self, toggle):
        self.showingCam =  toggle
    def saveImageToFile(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'./photos/image_{timestamp}.jpg'
        cv2.imwrite(filename,self.camImage)
        print("Picture Taken")
    def updateCountImage(self, image):
        self.countdown_label.setPixmap(image)
    def getTakenImage(self):
        return self.takenImage
        
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(600, 600, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
    #Possible error in redundancy
    
    def closeEvent(self, event: QCloseEvent) -> None:
        
        # print("Viewer was Closed")
        self.photoThread.terminate()
        self.closeViewer()
        self.close()
        
        
        return super().closeEvent(event)
        