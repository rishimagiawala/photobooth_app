import json
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from time import sleep
import serial, sys, time
from config_store import load_reader_config
from paths import app_path

class Reader(QThread):
    def __init__(self):
        super().__init__()
        


        # Initialize instance variables in the __init__ method
        self.credit_amount = None
        self.port = None

        layout_data = load_reader_config()
        self.credit_amount = layout_data['credits_trigger']
        self.port = layout_data['serial_port']
        print(self.port)
        self.baudrate = 9600
        self.ser = None
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.001)
            print("Credit Card Reader Module Started")
        except serial.SerialException as error:
            print(f"Credit Card Reader unavailable at {self.port}: {error}")
        self.credit = 0
        
       
    begin_session = Signal()
    


    def run(self):
        """Long-running task."""
        

        while True:
            if self.ser is None:
                sleep(1)
                continue

            try:
                data = self.ser.read(1)
                data += self.ser.read(self.ser.inWaiting())
            except serial.SerialException:
                print("Credit Card Reader Failed, Please Confirm Serial Port Settings and Restart Program")
                sleep(1)
                continue
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

    def closeSerial(self):
        try:
            self.ser.close()
        except:
            pass

    def removeCredits(self):
        if self.credit_count >= 3:
            self.credit_count -= 3
    def updateCreditAmount(self, credit_amount):
        self.credit_amount = credit_amount
        print("Credit Trigger Updated To: " + str(self.credit_amount))

    
