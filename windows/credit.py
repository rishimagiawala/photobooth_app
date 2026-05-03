import os
from pathlib import Path

from serial.tools import list_ports
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
    QSpinBox,
    QLineEdit,
    QPushButton,
    QListWidget
    
)
import json

from config_store import READER_CONFIG_PATH, load_reader_config, save_json_config


class ReaderWindow(QMainWindow):
    def __init__(self, reader, restartCreditThread):
        super().__init__()
        self.reader = reader
        self.restartCreditThread = restartCreditThread
        #TOOLBAR
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        

        button_action = QAction("Save Reader Properties", self)
        button_action.setStatusTip("Save Reader")
        button_action.triggered.connect(self.saveReader)
        toolbar.addAction(button_action)

        button_action = QAction("Refresh Serial Ports", self)
        button_action.setStatusTip("Refresh detected Linux serial devices")
        button_action.triggered.connect(self.refreshSerialPorts)
        toolbar.addAction(button_action)

      

        #############
        self.setWindowTitle("Reader Editor")
        self.resize(300,400)
        #Initializing Layout Variables:

        self.serial_port = None
        self.credits_trigger = None
        
        self.reader_config_path = READER_CONFIG_PATH
        layout_data = load_reader_config()
        self.serial_port = layout_data['serial_port']
        self.credits_trigger = layout_data['credits_trigger']
        ##################################
       


        #SERIAL PORT SELECTOR

        comboHLayout = QVBoxLayout()
        com_label = QLabel("Reader Serial Port:")
        self.reader_port = QLineEdit()
        self.reader_port.setText(self.serial_port)
        self.reader_port.textChanged.connect(self.updateSerialPort)
        self.reader_port_list = QListWidget()
        self.reader_port_list.setMaximumHeight(140)
        self.reader_port_list.itemClicked.connect(self.selectSerialPort)
        self.refreshSerialPorts()

        comboHLayout.addWidget(com_label)
        comboHLayout.addWidget(self.reader_port)
        comboHLayout.addWidget(self.reader_port_list)
        comboHLayout.addWidget(QLabel("Tip: /dev/serial/by-id entries are more stable than /dev/ttyUSB0."))
        comboHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        ##############################


        #Credit Trigger Selector
        numHLayout = QVBoxLayout()
        credit_label = QLabel("Enter Credit Amount to Trigger: ")
        self.credit_number = QSpinBox()
        self.credit_number.setMinimum(1)
        self.credit_number.setValue(self.credits_trigger)
        self.credit_number.valueChanged.connect(self.updateCreditTrigger)
        numHLayout.addWidget(credit_label)
        numHLayout.addWidget(self.credit_number)
        numHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
       


       


        container = QWidget()
        mainHContainer = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout = QVBoxLayout()

        
        layout2.addLayout(comboHLayout)
        layout2.addLayout(numHLayout)
        layout2.addWidget(QLabel("If there are any issues, restart the program after saving(Not required)"))
       
       
        
       
        mainHContainer.addLayout(layout2)
        container.setLayout(mainHContainer)
        
        self.setCentralWidget(container)
    
    def updateCreditTrigger(self, num):
        # print(num)
        self.credits_trigger = num

    def updateSerialPort(self, text):
        self.serial_port = text

    def selectSerialPort(self, item):
        self.reader_port.setText(item.text())

    def refreshSerialPorts(self):
        current_port = self.serial_port or self.reader_port.text()
        ports = self.getSerialPorts()
        if current_port and current_port not in ports:
            ports.insert(0, current_port)

        self.reader_port_list.clear()
        self.reader_port_list.addItems(ports)
        if current_port:
            matching_items = self.reader_port_list.findItems(current_port, Qt.MatchExactly)
            if matching_items:
                self.reader_port_list.setCurrentItem(matching_items[0])
            self.reader_port.setText(current_port)
        self.serial_port = self.reader_port.text()

    def getSerialPorts(self):
        ports = []
        for port in list_ports.comports():
            ports.append(port.device)

        for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS*"):
            ports.extend(str(path) for path in sorted(Path("/dev").glob(pattern.replace("/dev/", ""))))

        by_id_dir = Path("/dev/serial/by-id")
        if by_id_dir.exists():
            ports.extend(str(path) for path in sorted(by_id_dir.iterdir()))

        return sorted(dict.fromkeys(ports), key=self.serialPortSortKey)

    def serialPortSortKey(self, port):
        if port.startswith("/dev/serial/by-id/"):
            return (0, port)
        if port.startswith("/dev/ttyUSB"):
            return (1, port)
        if port.startswith("/dev/ttyACM"):
            return (2, port)
        if port.startswith("/dev/ttyS"):
            return (3, port)
        return (4, port)
    
    def saveReader(self):
        port_changed = False
        layout_data = load_reader_config()

        if layout_data['serial_port'] != self.serial_port:
            port_changed = True

        layout_data['credits_trigger'] = self.credits_trigger
        layout_data['serial_port'] = self.serial_port
        save_json_config(self.reader_config_path, layout_data)
        
        self.reader.updateCreditAmount(self.credits_trigger)
        if port_changed:
            self.restartCreditThread()