from datetime import datetime
import json
import os

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QHBoxLayout
from PySide6.QtCore import QObject, Qt, QThread, Signal, QMetaObject
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QImage, QTextCursor, QColor, QPalette
from PySide6.QtWidgets import QTextEdit, QSizePolicy, QCheckBox
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
    def flush(self):
        pass

       




class Dashboard(QMainWindow):

    def __init__(self):
        super(Dashboard, self).__init__()
        self.w = None
        self.layoutWindow = None
        self.current_img = None
        self.queue = 0
        self.readerWindow = None
        self.printer_count = 0
        self.startup_viewer = None
        self.mobile_view = None
        self.save_photos = None
        
        
        with open('./config/printing/count.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            self.printer_count = layout_data['count']
            self.startup_viewer = layout_data['startup_viewer']
            self.mobile_view = layout_data['mobile_view']
            self.save_photos = layout_data['save_photos']


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


        button_action = QAction("Flush Queue", self)
        button_action.setStatusTip("Flush Queue")
        button_action.triggered.connect(self.flushQueue)
        toolbar.addAction(button_action)

        button_action = QAction("Reset Print Count", self)
        button_action.setStatusTip("Reset Print Count")
        button_action.triggered.connect(self.resetPrintCount)
        toolbar.addAction(button_action)



        
        
       

        menu = self.menuBar()


      

        config_menu = menu.addMenu("Configuration")
        testing_menu = menu.addMenu("Testing")

        button_action = QAction("Take Picture", self)
        button_action.setStatusTip("Take Picture")
        button_action.triggered.connect(self.saveImageToFile)
        testing_menu.addAction(button_action)


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

        self.queue_label =QLabel("Queue Count: " + str(self.queue))

        self.viewer_launch_toggle = QCheckBox(text="Start Viewer On Launch")
        self.viewer_launch_toggle.setChecked(self.startup_viewer)
        self.viewer_launch_toggle.stateChanged.connect(self.toggleViewerOnLaunch)

        self.mobile_view_toggle = QCheckBox(text="Enable Mobile View")
        self.mobile_view_toggle.setChecked(self.mobile_view)
        self.mobile_view_toggle.stateChanged.connect(self.toggleMobile)

        self.save_photos_toggle = QCheckBox(text="Enable Saving Photos")
        self.save_photos_toggle.setChecked(self.save_photos)
        self.save_photos_toggle.stateChanged.connect(self.toggleSave)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.text_edit_console)
        layout.addWidget(self.count_label)
        layout.addWidget(self.queue_label)
        layout.addWidget(self.viewer_launch_toggle)
        layout.addWidget(self.mobile_view_toggle)
        layout.addWidget(self.save_photos_toggle)

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

        if self.startup_viewer is True:
            self.startViewer()

    
    def saveImageToFile(self):
        if self.queue == 0:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'./photos/image_{timestamp}.jpg'
            cv2.imwrite(filename,self.current_img)
            print("Picture Taken")
        else:
            print("Please 'Flush Queue' to Take Picture")

    
    def startViewer(self):
        if self.w is None:
            self.w = Viewer(self.addToQueue, self.popFromQueue, self.getQueueCount, self.closeViewer, self.getPrintCount, self.resetPrintCount, self.getSave)
            #Weird behavior
            self.showNormal()
            self.showMinimized()
            
            self.w.show()
            
            if self.layoutWindow is not None:
                self.layoutWindow.close()
                self.layoutWindow = None

            if self.readerWindow is not None:
                self.readerWindow.close()
                self.readerWindow = None

        else:
           print(type(self.w))
           print("Viewer Already Open")
   
    def closeViewer(self):
        self.w.close()
        self.w = None
        self.flushQueue()
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
        #Test this
        if self.queue == 0:
            self.flushQueue()

        self.queue += 1
        print("Queue Count: " + str(self.queue))
        self.queue_label.setText("Queue Count: " + str(self.queue))
    def popFromQueue(self):
        if self.queue > 0:
            self.queue -= 1
        else:
            self.queue = 0
        print("Queue Count: " + str(self.queue))
        self.queue_label.setText("Queue Count: " + str(self.queue))
    def getQueueCount(self):
        return self.queue
    def flushQueue(self):

        self.queue = 0
        for filename in os.listdir('./photos'):
            if os.path.isfile(os.path.join('./photos', filename)):
                os.remove(os.path.join('./photos', filename))
        print("Cleaned Queue | Flushed Previous Photos")
        self.queue_label.setText("Queue Count: " + str(self.queue))

    def openLayoutEditor(self):
        self.layoutWindow = LayoutWindow(self.printerThread)
        self.layoutWindow.show()
    
    def resetPrintCount(self):
        self.printer_count = 0
        self.count_label.setText("Total Prints: " + str(self.printer_count))
    
    def openReaderEditor(self):
        self.readerWindow = ReaderWindow(self.cardThread, self.restartCardThread)
        self.readerWindow.show()

    def restartCardThread(self):
        print("Thread Restarting....")
        self.cardThread.terminate()
        self.cardThread = None
        self.cardThread = Reader()
        self.cardThread.start()
        self.cardThread.begin_session.connect(self.addToQueue)

    def incrementPrintCount(self):
        self.printer_count += 1
        self.count_label.setText("Total Prints: " + str(self.printer_count))
    def getPrintCount(self):
        return self.printer_count

    def savePrintData(self):
    
        layout_data = None
        with open('./config/printing/count.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            layout_data['count'] = self.printer_count
            layout_data['startup_viewer']= self.startup_viewer
            layout_data['mobile_view'] = self.mobile_view
            layout_data['saved_photos'] = self.save_photos
           
        with open('./config/printing/count.json', 'w') as layout_file:
            json.dump(layout_data, layout_file)
    
    def toggleViewerOnLaunch(self):
        self.startup_viewer = self.viewer_launch_toggle.isChecked()
        self.savePrintData()
    def toggleMobile(self):
        self.mobile_view = self.mobile_view_toggle.isChecked()

        if self.mobile_view == True:
            
            os.rename('./assets/images/viewer/not_ready.png', './assets/images/viewer/ready_photobooth.png')
            os.rename('./assets/images/viewer/ready_mobile.png', './assets/images/viewer/not_ready.png')
            
        elif self.mobile_view == False:
            os.rename('./assets/images/viewer/not_ready.png', './assets/images/viewer/ready_mobile.png')
            os.rename('./assets/images/viewer/ready_photobooth.png', './assets/images/viewer/not_ready.png')

        self.savePrintData()

    def toggleSave(self):
        self.save_photos = self.save_photos_toggle.isChecked()
        self.savePrintData()

    def getSave(self):
        return self.save_photos

    #Possible error in redundancy   
    def closeEvent(self, event: QCloseEvent) -> None:
        self.cameraThread.terminate()
        self.printerThread.terminate()
        self.cardThread.terminate()
        self.flushQueue()
        if self.w is not None:
            self.w.close()
            self.w = None
            
        if self.layoutWindow is not None:
            self.layoutWindow.close()
            self.layoutWindow = None

        if self.readerWindow is not None:
            self.readerWindow.close()
            self.readerWindow = None
        self.savePrintData()


        
        return super().closeEvent(event)


app = QApplication(sys.argv)
w = Dashboard()
w.show()
app.exec()


