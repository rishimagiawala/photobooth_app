from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QSizePolicy
from PySide6.QtCore import QObject, Qt, QThread, Signal, QPoint, QKeyCombination, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent, QKeySequence, QMouseEvent, QPixmap, QImage, QDesktopServices, QCursor, QShortcut, QTransform
from contextlib import suppress
from time import sleep
import os
import sys
from modules.camera import CameraReader
import cv2
import numpy as np
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

        # Application-wide exit shortcuts. On a fullscreen Linux kiosk,
        # keyPressEvent can miss the key (focus lands on a child widget or the
        # window manager grabs it), so bind these at application scope so they
        # always fire while the viewer is open.
        self._exit_shortcuts = []
        for key_sequence in (QKeySequence(Qt.Key_Escape), QKeySequence("Ctrl+Q")):
            shortcut = QShortcut(key_sequence, self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(self.close)
            self._exit_shortcuts.append(shortcut)

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
        # Guard against a double-tap stacking two sessions back-to-back.
        if self.getQueueCount() == 0:
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
        if image is None:
            return
        self.camImage = image
        if self.showingCam is True:
            try:
                # Downscale before rotate/convert so the GUI thread does far
                # less work per frame (the preview is shown small anyway).
                preview = image
                if preview.shape[1] > 800:
                    preview = imutils.resize(preview, width=800)
                preview = imutils.rotate(preview, self.getAngle())
                qt_img = self.convert_cv_qt(preview)
                self.takenImage = qt_img
                self.image_label.setPixmap(qt_img)
            except Exception as error:
                print(f"Preview update failed: {error}")
    def toggleShowingCam(self, toggle):
        self.showingCam =  toggle
    def saveImageToFile(self):
        frame = self.camImage
        if frame is None or frame.size == 0:
            print("Picture skipped: camera frame is not ready")
            return False

        # Encode to PNG in memory so the temp file's extension doesn't matter
        # (cv2.imwrite picks the format from the extension, which broke when
        # writing to a ".tmp" file).
        success, buffer = cv2.imencode('.png', frame)
        if not success:
            print("Picture skipped: failed to encode camera frame")
            return False

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        final_path = app_path('photos', f'image_{timestamp}.png')
        # Write to a temp name first so the printer thread never sees a
        # half-written file, then atomically move it into place.
        temp_path = app_path('photos', f'.image_{timestamp}.png.tmp')
        try:
            buffer.tofile(str(temp_path))
            os.replace(temp_path, final_path)
        except OSError as error:
            print(f"Picture skipped: failed to save camera frame ({error})")
            with suppress(OSError):
                os.remove(temp_path)
            return False

        if self.getSave() is True:
            permname = app_path('saved_photos', f'image_{timestamp}.png')
            with suppress(Exception):
                cv2.imwrite(str(permname), frame)

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
        size = max(120, int(min(width, height) * 0.13))
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
        # Ensure a contiguous buffer so QImage reads valid memory.
        rgb_image = np.ascontiguousarray(rgb_image)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(600, 600, Qt.KeepAspectRatio)
        # Copy so the pixmap doesn't reference the soon-to-be-freed numpy buffer.
        return QPixmap.fromImage(p.copy())
    
    #Possible error in redundancy
    
    def closeEvent(self, event: QCloseEvent) -> None:
        
        # print("Viewer was Closed")
        if not self._closing:
            self._closing = True
            self.photoThread.stop()
            self.closeViewer()
        
        
        return super().closeEvent(event)
        