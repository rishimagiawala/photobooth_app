from typing import Optional
from PySide6.QtCore import QObject
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from time import sleep
import serial, sys, time
import os
from printing import printImages

class Printer(QThread):
    def __init__(self):
        self.currentBatch = []
        super().__init__()

    def run(self):
        while True:
            arr = os.listdir('./photos')
            if len(arr) >= 4:
                printImages(arr)
                print("Printing Strips...")