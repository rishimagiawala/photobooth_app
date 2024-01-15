from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QPixmap, QImage
from time import sleep
import sys
import cv2
from modules.credit_card import Reader
from windows.photobooth import PhotoboothWindow
class CameraWindow(QWidget):
    def __init__(self):
        super(CameraWindow, self).__init__()

        self.VBL = QVBoxLayout()

        self.FeedLabel = QLabel()
        self.VBL.addWidget(self.FeedLabel)

        self.CancelBTN = QPushButton("Cancel")
        self.CancelBTN.clicked.connect(self.CancelFeed)
        self.VBL.addWidget(self.CancelBTN)

        self.Worker1 = Worker1()

        self.Worker1.start()
        self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)
        self.setLayout(self.VBL)

    def ImageUpdateSlot(self, Image):
        self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

    def CancelFeed(self):
        self.Worker1.stop()

class Worker1(QThread):
    ImageUpdate = Signal(QImage)
    def run(self):
        self.ThreadActive = True
        Capture = cv2.VideoCapture(0)
        while self.ThreadActive:
            ret, frame = Capture.read()
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                FlippedImage = cv2.flip(Image, 1)
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)
    def stop(self):
        self.quit()
        self.ThreadActive = False
       




class Dashboard(QMainWindow):

    def __init__(self):
        super(Dashboard, self).__init__()

        self.setWindowTitle("PhotoBooth Dashboard")

        label = QLabel('Press "Begin PhotoBooth" ')
        label.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(label)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        button_action = QAction("Photobooth", self)
        button_action.setStatusTip("Begin Photobooth")
        button_action.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(button_action)

        button_action = QAction("Console", self)
        button_action.setStatusTip("Open Console")
        button_action.triggered.connect(self.show_new_window)
        toolbar.addAction(button_action)



    def onMyToolBarButtonClick(self, s):
        print("click", s)
    
    def show_new_window(self, checked):
        w = PhotoboothWindow()
        w.show()



app = QApplication(sys.argv)
w = Dashboard()
w.show()
app.exec()