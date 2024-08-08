import json
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from time import sleep
import serial, sys, time

class Reader(QThread):
    def __init__(self):
        super().__init__()
        


        # Initialize instance variables in the __init__ method
        self.credit_amount = None
        self.port = None

        with open('./config/card_reader/reader.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            self.credit_amount = layout_data['credits_trigger']
            self.port = 'COM' + str(layout_data['com_port'])
            print(self.port)
        self.baudrate = 9600
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.001)
            print("Credit Card Reader Module Started")
        except:
            pass
        self.credit = 0
        
       
    begin_session = Signal()
    


    def run(self):
        """Long-running task."""
        

        while True:
            try:
                data = self.ser.read(1)
                
            except:
                print("Credit Card Reader Failed, Please Confirm COM Port Settings and Restart Program")
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

    
