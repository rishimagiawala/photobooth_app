from typing import Optional
from PySide6.QtCore import QObject
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from time import sleep
import serial, sys, time
import os
from printing import printImages
import json

class Printer(QThread):
    def __init__(self):
        self.currentBatch = []
       
        super().__init__()
        print("Printer Started")
        self.num_of_photos = None
        with open('./config/printing/layout.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            self.num_of_photos = layout_data['num_of_photos']
        
        self.current_print_count = 0
       
           

    def run(self):
        while True:
          
            arr = os.listdir('./photos')
            if len(arr) >= self.num_of_photos:
                print("Sending Job to Printer...")
                printImages(arr)
                
                self.current_print_count += 1

    def updatePhotoCount(self, num_of_photos):
        self.num_of_photos = num_of_photos
    def getPrintCount(self):
        return self.current_print_count
