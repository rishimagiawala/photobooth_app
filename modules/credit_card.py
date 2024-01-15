from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from time import sleep
import serial, sys, time

class Reader(QThread):
    def __init__(self):
        super().__init__()

        # Initialize instance variables in the __init__ method
        self.port = 'COM3'
        self.baudrate = 9600
        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.001)
        self.credit = 0
        self.credit_amount = 3
        self.interval = 0.25
        self.console = None
        self.credit_count = 0
    finished = Signal()
    progress = Signal(int)


    def run(self):
        """Long-running task."""
        

        while True:
            data_ser = self.ser.read(1)
            data_ser += self.ser.read(self.ser.inWaiting())
            integer_value = int.from_bytes(data_ser) 
            if integer_value > 0 and integer_value < 256:
                self.credit_count += 1
                self.progress.emit(self.credit_count)
            if self.credit_count == 3:
                break
        self.quit()
        self.ser.close()
        self.finished.emit()

    def removeCredits(self):
        if self.credit_count >= 3:
            self.credit_count -= 3
    
