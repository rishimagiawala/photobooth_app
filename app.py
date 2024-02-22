from datetime import datetime
import json
import os

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QHBoxLayout
from PySide6.QtCore import QObject, Qt, QThread, Signal, QMetaObject
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QImage, QTextCursor, QColor, QPalette
from PySide6.QtWidgets import QTextEdit, QSizePolicy
from time import sleep
import sys
import cv2
from modules.camera import CameraReader
from modules.credit_card import Reader
from modules.printer import Printer
from windows.credit import ReaderWindow
from windows.layout import LayoutWindow
from windows.photobooth import PhotoboothWindow
from windows.viewer import Viewer
import webbrowser


# class OutputConsole(QTextEdit):
#     def _init_(self):
#         super(OutputConsole)

class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)



class Stream(QThread):
    newText = Signal(str)

    def write(self, text):
        self.newText.emit(str(text))

       




class Dashboard(QMainWindow):

    def __init__(self):
        super(Dashboard, self).__init__()
        self.w = None
        self.layoutWindow = None
        self.current_img = None
        self.queue = 0
        self.readerWindow = None
        self.printer_count = 0
        with open('./config/printing/count.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            self.printer_count = layout_data['count']


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
        button_action.triggered.connect(self.saveImageToFile)
        toolbar.addAction(button_action)

        button_action = QAction("Reset Queue Count", self)
        button_action.setStatusTip("Reset queue")
        button_action.triggered.connect(self.resetQueueCount)
        toolbar.addAction(button_action)

        button_action = QAction("Reset Print Count", self)
        button_action.setStatusTip("Reset Print Count")
        button_action.triggered.connect(self.showPrintCount)
        toolbar.addAction(button_action)



        
        
       

        menu = self.menuBar()
        config_menu = menu.addMenu("Configuration")


        button_action = QAction("Edit Layout Configuration", self)
        button_action.setStatusTip("Edit layout")
        button_action.triggered.connect(self.openLayoutEditor)
        config_menu.addAction(button_action)

        button_action = QAction("Edit Reader Properties", self)
        button_action.setStatusTip("Edit Reader")
        button_action.triggered.connect(self.openReaderEditor)
        config_menu.addAction(button_action)
        

        self.text_edit_console = QTextEdit(self)


        
        self.count_label = QLabel("Total Prints: " + str(self.printer_count))
      

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.text_edit_console)
        layout.addWidget(self.count_label)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        sys.stdout = Stream(newText=self.onUpdateText)

        #Starting Camera
        self.cameraThread = CameraReader()
        self.cameraThread.start()
        self.cameraThread.image_signal.connect(self.updateCurrentImage)
       
       #Starting Printer    
        self.printerThread = Printer()
        self.printerThread.start()
        self.printerThread.beginPrint.connect(self.incrementPrintCount)

        #Starting Credit Card Thread
        self.cardThread = Reader()
        self.cardThread.start()
        self.cardThread.begin_session.connect(self.addToQueue)



    
    def saveImageToFile(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'./photos/image_{timestamp}.jpg'
        cv2.imwrite(filename,self.current_img)
        print("Picture Taken")

    
    def startViewer(self):
        if self.w is None:
            self.w = Viewer(self.addToQueue, self.popFromQueue, self.getQueueCount, self.closeViewer)
            self.w.show()
        else:
           print(type(self.w))
           print("Viewer Already Open")
   
    def closeViewer(self):
        self.w.close()
        self.w = None
        print("Viewer Closed")
    
    def updateCurrentImage(self,image):
        self.current_img = image
        if self.w is not None:
            self.w.updateViewerCamImage(image=self.current_img)

    #This function has to do with updating the output console
    def onUpdateText(self, text):
        cursor = self.text_edit_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_edit_console.setTextCursor(cursor)
        self.text_edit_console.ensureCursorVisible()

    def addToQueue(self):
        self.queue += 1
        print("Queue Count: " + str(self.queue))
    def popFromQueue(self):
        if self.queue > 0:
            self.queue -= 1
        else:
            self.queue = 0
        print("Queue Count: " + str(self.queue))
    def getQueueCount(self):
        return self.queue
    def resetQueueCount(self):
        self.queue = 0
        print("Queue Reset")

    def openLayoutEditor(self):
        self.layoutWindow = LayoutWindow(self.printerThread)
        self.layoutWindow.show()
    
    def showPrintCount(self):
        self.printer_count = 0
        self.count_label.setText("Total Prints: " + str(self.printer_count))
    
    def openReaderEditor(self):
        self.readerWindow = ReaderWindow(self.cardThread)
        self.readerWindow.show()

    def incrementPrintCount(self):
        self.printer_count += 1
        self.count_label.setText("Total Prints: " + str(self.printer_count))

    def savePrintData(self):
    
        layout_data = None
        with open('./config/printing/count.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            layout_data['count'] = self.printer_count
           
        with open('./config/printing/count.json', 'w') as layout_file:
            json.dump(layout_data, layout_file)
    #Possible error in redundancy   
    def closeEvent(self, event: QCloseEvent) -> None:
        self.cameraThread.terminate()
        self.printerThread.terminate()
        self.cardThread.terminate()
        self.savePrintData()


        
        return super().closeEvent(event)   


app = QApplication(sys.argv)
w = Dashboard()
w.show()
app.exec()


