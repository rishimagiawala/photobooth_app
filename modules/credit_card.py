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
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.001)
        except:
            pass
        self.credit = 0
        self.credit_amount = 7
        self.interval = 0.25
        self.console = None
        self.credit_count = 0
    begin_session = Signal()
    


    def run(self):
        """Long-running task."""
        

        while True:
            data = self.ser.read(1)
            data += self.ser.read(self.ser.inWaiting())
            integer_value = int.from_bytes(data) 
            # print(data)
            if len(data) > 0:
                self.credit +=1
                print(str(self.credit) + ' Tokens' + ' | Number ' + str(integer_value) + ' | Data ' + str(data))
            if self.credit == self.credit_amount:

                self.credit = 0
                
                self.begin_session.emit()

        self.quit()
        self.ser.close()
        self.finished.emit()

    def removeCredits(self):
        if self.credit_count >= 3:
            self.credit_count -= 3
    
