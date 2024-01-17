from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QImage
from time import sleep
import sys
from modules.camera import CameraReader
import cv2
from modules.credit_card import Reader
class PhotoboothWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicksCount = 0
        
       
        self.setWindowTitle("Photobooth Window")
        self.resize(300, 150)
        
        self.image_label = QLabel("Image Splash")
        # self.im = QPixmap("notReady")
        # self.image_label.setPixmap(self.im)
       
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        # Create and connect widgets
        
        self.stepLabel = QLabel("Credits Entered: 0")
        self.stepLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.countBtn = QPushButton("Click me!", self)
        # self.countBtn.clicked.connect(self.countClicks)
        self.longRunningBtn = QPushButton("Start Photobooth", self)
        self.longRunningBtn.clicked.connect(self.runPhotobooth)
    
        # Set the layout
        layout = QVBoxLayout()
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.stepLabel)
        layout.addWidget(self.longRunningBtn)
       
        self.centralWidget.setLayout(layout)
        self.runCredit()

    # def closeEvent(self, event: QCloseEvent) -> None:
    #     self.worker.deleteLater()
    #     self.thread.quit()
    #     return super().closeEvent(event)

   

    def reportCreditProgress(self, n):
        self.stepLabel.setText(f"Credits Entered: {n}")

    def runCredit(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Reader()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportCreditProgress)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.longRunningBtn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Press Begin")
        )
    def runPhotobooth(self):
        self.thread = CameraReader()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.finished.connect(self.thread.deleteLater)
        # start the thread
        self.thread.start()
        
        
       

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

