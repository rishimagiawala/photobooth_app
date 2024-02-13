from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QToolBar, QSizePolicy
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QImage
from time import sleep
import sys
from modules.camera import CameraReader
import cv2
from modules.credit_card import Reader
import json
class LayoutWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layout Editor")
        image_height = None
        logo_height = None
        marginx = None
        marginy = None
        logo_rotate= True
        logo_path = None
        image_marginx =None
        image_marginy =None
        with open('./config/printing/layout.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            print(layout_data)

            image_height = layout_data['image_height']
            logo_height = layout_data['logo_height']
            marginx = layout_data['marginx']
            marginy = layout_data['marginy']
            logo_rotate = layout_data['logo_rotate']
            logo_path = layout_data['logo_path']
            image_marginx = layout_data['image_marginx']
            image_marginy = layout_data['image_marginy']
        