from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar
from PySide6.QtCore import QObject, Qt, QThread, Signal, QMetaObject
from PySide6.QtGui import QAction, QPixmap, QImage, QTextCursor
from PySide6.QtWidgets import QTextEdit, QSizePolicy
from time import sleep
import sys
import cv2
from modules.camera import CameraReader
from modules.credit_card import Reader
from modules.printer import Printer
from windows.photobooth import PhotoboothWindow
from windows.viewer import Viewer

# class OutputConsole(QTextEdit):
#     def _init_(self):
#         super(OutputConsole)


class Stream(QThread):
    newText = Signal(str)

    def write(self, text):
        self.newText.emit(str(text))

       




class Dashboard(QMainWindow):

    def __init__(self):
        super(Dashboard, self).__init__()
        self.w = None
        self.current_img = None

        self.setWindowTitle("PhotoBooth Dashboard")

        label = QLabel('Output Console')
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setCentralWidget(label)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        button_action = QAction("Show Viewer", self)
        button_action.setStatusTip("Show Photobooth Viewer")
        button_action.triggered.connect(self.startViewer)
        toolbar.addAction(button_action)

        button_action = QAction("Take Picture", self)
        button_action.setStatusTip("Take Picture")
        button_action.triggered.connect(self.startViewer)
        toolbar.addAction(button_action)

        self.text_edit_console = QTextEdit(self)
        self.text_edit_console.setSizePolicy(
           QSizePolicy.MinimumExpanding,
            QSizePolicy.MinimumExpanding
        )

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.text_edit_console)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        sys.stdout = Stream(newText=self.onUpdateText)
        # print("Hey")

        #Starting Camera
        self.cameraThread = CameraReader()
        self.cameraThread.start()
        self.cameraThread.change_pixmap_signal.connect(self.updateCurrentImg)
       
        self.printerThread = Printer()
        self.printerThread.start()





    def onMyToolBarButtonClick(self, s):
        print("click", s)
    
    def startViewer(self):
       
        self.w = Viewer()
        self.w.show()
        print("Loaded configuration.")

    def onUpdateText(self, text):
        cursor = self.text_edit_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_edit_console.setTextCursor(cursor)
        self.text_edit_console.ensureCursorVisible()
    def updateCurrentImg(self,img):
        self.current_img = img
        if self.w is not None:
            self.w.startImageStream(image=self.current_img)

    



app = QApplication(sys.argv)
w = Dashboard()
w.show()
app.exec()