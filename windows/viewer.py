from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QSizePolicy
from PySide6.QtCore import QObject, Qt, QThread, Signal, QPoint, QKeyCombination, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent, QMouseEvent, QPixmap, QImage, QDesktopServices, QCursor, QTransform
from time import sleep
import sys
from modules.camera import CameraReader
import cv2
from modules.credit_card import Reader
from modules.photographer import Photographer
from datetime import datetime
import imutils
from paths import app_path
class Viewer(QMainWindow):
    def __init__(self, addToQueue, popFromQueue, getQueueCount, closeViewer, getPrintCount, resetPrintCount, getSave, getAngle):
        super().__init__()

        print("Viewer Started")
        # width = self.frameGeometry().width()
        # height = self.frameGeometry().height()
        # print(width)
        # print(height)


        self.addToQueue = addToQueue
        self.popFromQueue = popFromQueue
        self.getQueueCount = getQueueCount
        self.closeViewer = closeViewer
        self.getPrintCount = getPrintCount
        self.resetPrintCount = resetPrintCount
        self.getSave = getSave
        self.getAngle = getAngle
      
        self.showingCam = False
        self.camImage = None
        self.takenImage = QPixmap()
        self._closing = False

        self.setWindowTitle("Photobooth Window")
        self.setFocusPolicy(Qt.StrongFocus)
       
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()

        self.cancel_width = int(.15* width)
        self.cancel_height = int(.1 * height)
        self.setCursor(Qt.BlankCursor)
        # print(width)
        # print(height)
        self.image_label = QLabel()
        self.im = QPixmap(str(app_path("assets", "images", "viewer", "not_ready.png")))
        self.image_label.setPixmap(self.im)
        
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.image_label.setScaledContents(True)
        self.centralWidget = self.image_label
        self.setCentralWidget(self.centralWidget)
        self.countdown_label = QLabel(self.image_label)
        self.countdown_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.countdown_label.setScaledContents(True)
        self.countdown_label.setStyleSheet("background: transparent;")
        self.updateCountdownPosition()
        self.countdown_label.raise_()

        self.photoThread = Photographer(self.toggleShowingCam, self.saveImageToFile, self.getQueueCount, self.popFromQueue, self.getTakenImage, self.getPrintCount)
        self.photoThread.start()
        self.photoThread.change_image_signal.connect(self.updateImage)
        self.photoThread.change_count_signal.connect(self.updateCountImage)

    def showEvent(self, event):
        super().showEvent(event)
        self.showFullScreen()
        self.schedule_focus()

    def schedule_focus(self):
        for delay_ms in (0, 100, 500, 1500):
            QTimer.singleShot(delay_ms, self.grab_viewer_focus)

    def grab_viewer_focus(self):
        if self._closing:
            return

        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)

        app = QApplication.instance()
        if app is not None:
            app.setActiveWindow(self)
    
    def keyPressEvent(self, event) -> None:
        if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter)  and self.getPrintCount() > 699:
            self.resetPrintCount()
            self.updateImage(str(app_path("assets", "images", "viewer", "not_ready.png")))

        if event.key() == Qt.Key_Escape:
            self.close()




    def mouseDoubleClickEvent(self, e):
        self.addToQueue()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        
       

        if event.x() <= self.cancel_width and event.y() <= self.cancel_height:
                self.close()
        else:
                if self.getQueueCount() == 0:
                    self.addToQueue()
                else:
                    print("Session Already In Queue")

        return super().mousePressEvent(event)

   
    def updateImage(self, image):
        self.image_label.setPixmap(QPixmap(image) if image else QPixmap())
        self.countdown_label.raise_()


    def updateViewerCamImage(self, image):
        self.camImage = image
        if self.showingCam is True:
            image = imutils.rotate(image, self.getAngle())
            
            qt_img = self.convert_cv_qt(image)
            
            self.takenImage = qt_img
            self.image_label.setPixmap(qt_img)
    def toggleShowingCam(self, toggle):
        self.showingCam =  toggle
    def saveImageToFile(self):
        if self.camImage is None or self.camImage.size == 0:
            print("Picture skipped: camera frame is not ready")
            return False

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = app_path('photos', f'image_{timestamp}.png')
        if not cv2.imwrite(str(filename),self.camImage):
            print("Picture skipped: failed to save camera frame")
            return False

        if self.getSave() is True:
            permname = app_path('saved_photos', f'image_{timestamp}.png')
            cv2.imwrite(str(permname),self.camImage)
        
        print("Picture Taken")
        return True
    def updateCountImage(self, image):
        self.countdown_label.setPixmap(QPixmap(image) if image else QPixmap())
        self.updateCountdownPosition()
        self.countdown_label.raise_()
    def getTakenImage(self):
        return self.takenImage

    def updateCountdownPosition(self):
        width = self.image_label.width() or self.frameGeometry().width()
        height = self.image_label.height() or self.frameGeometry().height()
        size = max(160, int(min(width, height) * 0.18))
        bottom_margin = max(40, int(height * 0.06))
        self.countdown_label.resize(size, size)
        self.countdown_label.move(int((width - size) / 2), height - size - bottom_margin)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "countdown_label"):
            self.updateCountdownPosition()
        
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
        if not self._closing:
            self._closing = True
            self.photoThread.terminate()
            self.photoThread.wait(1000)
            self.closeViewer()
        
        
        return super().closeEvent(event)
        