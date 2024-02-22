import os
from PySide6.QtCore import QMimeData, Qt, Signal, QSize
from PySide6.QtGui import QDrag, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QToolBar,
    QCheckBox,
    QSpinBox
    
)
import json


class ReaderWindow(QMainWindow):
    def __init__(self, reader):
        super().__init__()
        self.reader = reader

        #TOOLBAR
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        

        button_action = QAction("Save Reader Properties", self)
        button_action.setStatusTip("Save Reader")
        button_action.triggered.connect(self.saveReader)
        toolbar.addAction(button_action)

      

        #############
        self.setWindowTitle("Reader Editor")
        self.resize(300,400)
        #Initializing Layout Variables:

        self.com_port = None
        self.credits_trigger = None
        
        with open('./config/card_reader/reader.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            # print(layout_data)

            self.com_port = layout_data['com_port']
            self.credits_trigger = layout_data['credits_trigger']
        ##################################
       


        #COM PORT SELECTOR

        comboHLayout = QHBoxLayout()
        com_label = QLabel("Reader COM Port:")
        self.reader_combobox = QComboBox()
        
        port_array = ['0',"1", "2",'3','4','5','6','7','8','9']
        port_array.remove(self.com_port)
        port_array.insert(0, self.com_port)

        self.reader_combobox.addItems(port_array)

       
        self.reader_combobox.currentTextChanged.connect(self.updateCOM)

        comboHLayout.addWidget(com_label)
        comboHLayout.addWidget(self.reader_combobox)
        comboHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        comboHLayout.addStretch(1)
        ##############################


        #Credit Trigger Selector
        numHLayout = QHBoxLayout()
        credit_label = QLabel("Enter Credit Amount to Trigger: ")
        self.credit_number = QSpinBox()
        self.credit_number.setMinimum(1)
        self.credit_number.setValue(self.credits_trigger)
        self.credit_number.valueChanged.connect(self.updateCreditTrigger)
        numHLayout.addWidget(credit_label)
        numHLayout.addWidget(self.credit_number)
        numHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        numHLayout.addStretch(1)


       


        container = QWidget()
        mainHContainer = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout2.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout = QVBoxLayout()

        
        layout2.addLayout(comboHLayout)
        layout2.addLayout(numHLayout)
        layout2.addWidget(QLabel("Restart Program After Saving Settings"))
       
       
        
       
        mainHContainer.addLayout(layout2)
        container.setLayout(mainHContainer)
        
        self.setCentralWidget(container)
    
    def updateCreditTrigger(self, num):
        # print(num)
        self.credits_trigger = num

    def updateCOM(self, text):
        self.com_port = text
    
    def saveReader(self):
        layout_data = None
        with open('./config/card_reader/reader.json', 'r') as layout_file:
            layout_data = json.load(layout_file)
            layout_data['credits_trigger'] = self.credits_trigger
            layout_data['com_port'] = self.com_port
            

            
           
        with open('./config/card_reader/reader.json', 'w') as layout_file:
            json.dump(layout_data, layout_file)
        
        self.reader.updateCreditAmount(self.credits_trigger)