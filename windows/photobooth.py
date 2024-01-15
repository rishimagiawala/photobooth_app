from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QPixmap
from time import sleep
import sys
from modules.camera import Camera

from modules.credit_card import Reader

class PhotoboothWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicksCount = 0
        
       
   
        self.setWindowTitle("Photobooth Window")
        self.resize(300, 150)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        # Create and connect widgets
        
        self.stepLabel = QLabel("Credits Entered: 0")
        self.stepLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.countBtn = QPushButton("Click me!", self)
        # self.countBtn.clicked.connect(self.countClicks)
        self.longRunningBtn = QPushButton("Start Photobooth", self)
       
        # Set the layout
        layout = QVBoxLayout()
        
        
        layout.addWidget(self.stepLabel)
        layout.addWidget(self.longRunningBtn)
        self.centralWidget.setLayout(layout)
        self.runLongTask()

   

    def reportProgress(self, n):
        self.stepLabel.setText(f"Credits Entered: {n}")

    def runLongTask(self):
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
        self.worker.progress.connect(self.reportProgress)
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

