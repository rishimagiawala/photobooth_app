import os
from PySide6.QtCore import QMimeData, Qt, Signal, QSize, QUrl
from PySide6.QtGui import QDrag, QPixmap, QAction, QDesktopServices
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
    QColorDialog,
    QPushButton,
    QSpinBox
    
)
import json
from config_store import LAYOUT_CONFIG_PATH, load_layout_config, save_json_config
from printing import printImages
from paths import app_path, display_path, resolve_app_path



class DragTargetIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(25, 5, 25, 5)
        self.setStyleSheet(
            "QLabel { background-color: #ccc; border: 1px solid black; }"
        )


class DragItem(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(25, 5, 25, 5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
        # Store data separately from display label, but use label for default.
        self.data = self.text()
        self.setMinimumSize(QSize(100,100))
        self.setMaximumSize(QSize(400,200))
        
    def set_data(self, data):
        self.data = data

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)


class DragWidget(QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        # Add the drag target indicator. This is invisible by default,
        # we show it and move it around while the drag is active.
        self._drag_target_indicator = DragTargetIndicator()
        self.blayout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dragLeaveEvent(self, e):
        self._drag_target_indicator.hide()
        e.accept()

    def dragMoveEvent(self, e):
        # Find the correct location of the drop target, so we can move it there.
        index = self._find_drop_location(e)
        if index is not None:
            # Inserting moves the item if its alreaady in the layout.
            self.blayout.insertWidget(index, self._drag_target_indicator)
            # Hide the item being dragged.
            e.source().hide()
            # Show the target.
            self._drag_target_indicator.show()
        e.accept()

    def dropEvent(self, e):
        widget = e.source()
        # Use drop target location for destination, then remove it.
        self._drag_target_indicator.hide()
        index = self.blayout.indexOf(self._drag_target_indicator)
        if index is not None:
            self.blayout.insertWidget(index, widget)
            self.orderChanged.emit(self.get_item_data())
            widget.show()
            self.blayout.activate()
        e.accept()

    def _find_drop_location(self, e):
        pos = e.pos()
        spacing = self.blayout.spacing() / 2

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()

            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = (
                    pos.y() >= w.y() - spacing
                    and pos.y() <= w.y() + w.size().height() + spacing
                )
            else:
                # Drag drop horizontally.
                drop_here = (
                    pos.x() >= w.x() - spacing
                    and pos.x() <= w.x() + w.size().width() + spacing
                )

            if drop_here:
                # Drop over this target.
                break

        return n

    def add_item(self, item):
        self.blayout.addWidget(item)
    

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if hasattr(w, "data"):
                # The target indicator has no data.
                data.append(w.data)
        return data


class LayoutWindow(QMainWindow):
    def __init__(self, printer):
        super().__init__()
        self.printer  = printer

        #TOOLBAR
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        button_action = QAction("Open Logo Folder", self)
        button_action.setStatusTip("Open Logo Folder")
        button_action.triggered.connect(self.openLogoFolder)
        toolbar.addAction(button_action)

        button_action = QAction("Open Background Folder", self)
        button_action.setStatusTip("Open Background Folder")
        button_action.triggered.connect(self.openBackgroundFolder)
        # toolbar.addAction(button_action)

        button_action = QAction("Save Layout", self)
        button_action.setStatusTip("Save Layout")
        button_action.triggered.connect(self.saveLayout)
        toolbar.addAction(button_action)

        button_action = QAction("Print Test Strip", self)
        button_action.setStatusTip("Print Test Strip")
        button_action.triggered.connect(self.printTest)
        toolbar.addAction(button_action)

        #############
        self.setWindowTitle("Layout Editor")
        self.resize(300,400)
        #Initializing Layout Variables:
        self.logo2_path = None
        self.logo_position = None
        self.num_of_photos = None
        self.logo_path = None
        self.logo_square = None
        self.background_path = None
        self.include_background = None
        self.background_color = None
        self.angle = None
        layout_data = load_layout_config()
        self.logo2_path = layout_data['logo2_path']
        self.logo_path = layout_data['logo_path']
        self.num_of_photos = layout_data['num_of_photos']
        self.logo_position = layout_data['logo_position']
        self.logo_square = layout_data['logo_square']
        self.background_path = layout_data['background_path']
        self.include_background = layout_data['include_background']
        self.background_color = layout_data['background_color']
        self.angle = layout_data['angle']
        ##################################
        self.logo_arr = os.listdir(app_path('assets', 'images', 'logos'))

        self.logo_arr = [display_path(app_path('assets', 'images', 'logos', element)) for element in self.logo_arr]
        self._move_to_front(self.logo_arr, self.logo_path)

        self.logo2_arr = os.listdir(app_path('assets', 'images', 'logos'))
        self.logo2_arr = [display_path(app_path('assets', 'images', 'logos', element)) for element in self.logo2_arr]
        self._move_to_front(self.logo2_arr, self.logo2_path)


        self.background_arr = os.listdir(app_path('assets', 'images', 'background'))
        self.background_arr = [display_path(app_path('assets', 'images', 'background', element)) for element in self.background_arr]
        self._move_to_front(self.background_arr, self.background_path)

        self.order = []
        for i in range(self.num_of_photos + 1):
            if i == self.logo_position:
                self.order.append("LOGO")

            else:
                self.order.append("PHOTO")

        self.drag = DragWidget(orientation=Qt.Orientation.Vertical)
        for n, l in enumerate(self.order):
            
            
            item = DragItem(l)
            if l == 'LOGO':
                q_img = QPixmap(str(resolve_app_path(self.logo_path)))
               
                item.setPixmap(q_img)
                item.setScaledContents(True)
            item.set_data(l)  # Store the data.
            self.drag.add_item(item)

        # Print out the changed order.
        self.drag.orderChanged.connect(self.updateLogoPosition)
        


        #Number of Photos Selector

        comboHLayout = QHBoxLayout()
        num_photos_label = QLabel("Number of Photos:")
        self.num_photos_combobox = QComboBox()
        
        if self.num_of_photos == 4:
            self.num_photos_combobox.addItems(["4", "3"])
        elif self.num_of_photos == 3:
            self.num_photos_combobox.addItems(["3", "4"])
        self.num_photos_combobox.currentTextChanged.connect(self.updateOrder)

        comboHLayout.addWidget(num_photos_label)
        comboHLayout.addWidget(self.num_photos_combobox)
        comboHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        comboHLayout.addStretch(1)
        ##############################



        #Logo 1 Selector

        logoHLayout = QHBoxLayout()
        logos_label = QLabel("Select Logo:")
        self.logo_combobox = QComboBox()
        
        self.logo_combobox.addItems(self.logo_arr)
        self.logo_combobox.currentTextChanged.connect(self.updateLogo)

        logoHLayout.addWidget(logos_label)
        logoHLayout.addWidget(self.logo_combobox)
        logoHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        logoHLayout.addStretch(1)
        ##############################


         #Logo 2 Selector

        logo2HLayout = QHBoxLayout()
        logos2_label = QLabel("Select Second Logo:")
        self.logo2_combobox = QComboBox()
        
        self.logo2_combobox.addItems(self.logo2_arr)
        self.logo2_combobox.currentTextChanged.connect(self.updateLogo2)

        logo2HLayout.addWidget(logos2_label)
        logo2HLayout.addWidget(self.logo2_combobox)
        logo2HLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        logo2HLayout.addStretch(1)
        ##############################

        #Logo Square Checkbox

        logoSquareHLayout = QHBoxLayout()
        sqlogo_label = QLabel("Logo Square:")
        self.checkBox = QCheckBox()
        self.checkBox.setChecked(self.logo_square)
        logoSquareHLayout.addWidget(sqlogo_label)
        logoSquareHLayout.addWidget(self.checkBox)
        
        logoSquareHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        logoSquareHLayout.addStretch(1)
    ##############################

        #Angle Selection
        angleSquareHLayout = QHBoxLayout()
        angle_label = QLabel("Viewer Image Angle:")
        self.angle_spin = QSpinBox()
        self.angle_spin.setMaximum(359)
        self.angle_spin.setValue(self.angle)
        self.angle_spin.valueChanged.connect(self.updateAngle)
        angleSquareHLayout.addWidget(angle_label)
        angleSquareHLayout.addWidget(self.angle_spin)
        
        
       


    #     #Background Selector

    #     backgroundHLayout = QHBoxLayout()
    #     backgrounds_label = QLabel("Select background:")
    #     self.background_combobox = QComboBox()
        
    #     self.background_combobox.addItems(self.background_arr)
           
    #     self.background_combobox.currentTextChanged.connect(self.updateBackground)

    #     backgroundHLayout.addWidget(backgrounds_label)
    #     backgroundHLayout.addWidget(self.background_combobox)
    #     backgroundHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    #     backgroundHLayout.addStretch(1)
    #     ##############################

    #     #Background Square Checkbox

    #     backgroundSquareHLayout = QHBoxLayout()
    #     sqbackground_label = QLabel("Apply Background:")
    #     self.bcheckBox = QCheckBox()
    #     self.bcheckBox.setChecked(self.include_background)
    #     backgroundSquareHLayout.addWidget(sqbackground_label)
    #     backgroundSquareHLayout.addWidget(self.bcheckBox)
        
    #     backgroundSquareHLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    #     backgroundSquareHLayout.addStretch(1)
    # ##############################

        # Color Dialog Button removed 6/27/2024
        # colorButton = QPushButton("Choose Background Color")

        # colorButton.clicked.connect(self.openColorDialog)





        container = QWidget()
        mainHContainer = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout2.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout = QVBoxLayout()

        
        layout2.addLayout(comboHLayout)
        layout2.addLayout(logoHLayout)
        layout2.addLayout(logo2HLayout)
        layout2.addLayout(logoSquareHLayout)
        layout2.addLayout(angleSquareHLayout)
        
        # layout2.addLayout(backgroundHLayout)
        # layout2.addLayout(backgroundSquareHLayout)
        # layout2.addWidget(colorButton)

        self.layout.addWidget(self.drag)
        
        mainHContainer.addLayout(self.layout)
        mainHContainer.addLayout(layout2)
        container.setLayout(mainHContainer)
        
        self.setCentralWidget(container)

    @staticmethod
    def _move_to_front(items, value):
        # Put the currently-selected value first without crashing if the file
        # it points to no longer exists in the folder.
        if value in items:
            items.remove(value)
        items.insert(0, value)

    def changeLayout(self):
        
        
       
        
        self.layout.removeWidget(self.drag)
        self.drag.deleteLater()
        new_drag = DragWidget(orientation=Qt.Orientation.Vertical)
            
        for n, l in enumerate(self.order):
            item = DragItem(l)
            item.set_data(l)  # Store the data.
            if l == 'LOGO':
                q_img = QPixmap(str(resolve_app_path(self.logo_path)))
               
                item.setPixmap(q_img)
                item.setScaledContents(True)
            new_drag.add_item(item)
        self.drag = new_drag
        self.drag.orderChanged.connect(self.updateLogoPosition)
        self.layout.addWidget(self.drag)

    def updateLogoPosition(self, data):
        print(data)
        self.order = data
    
    def updateOrder(self, text):
        num_of_photos = int(text)
        self.num_of_photos = num_of_photos
        print(num_of_photos)
        
        self.order = []
            
        for i in range(self.num_of_photos + 1):
                
            if i == self.num_of_photos - 1:
                self.order.append("LOGO")
                self.logo_position = i

            else:
                self.order.append("PHOTO")    
        self.changeLayout()
    def updateLogo(self, text):
        self.logo_path = text
        self.changeLayout()

    def updateLogo2(self, text):
        self.logo2_path = text
        self.changeLayout()

    def updateBackground(self, text):
        self.background_path = text
    
    def updateAngle(self, angle):
        self.angle = angle

    def openLogoFolder(self):
        path = app_path("assets", "images", "logos")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def openBackgroundFolder(self):
        path = app_path("assets", "images", "background")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def saveLayout(self):
        layout_data = load_layout_config()
        layout_data['logo_path'] = self.logo_path
        layout_data['logo2_path'] = self.logo2_path
        layout_data['num_of_photos'] = self.num_of_photos
        layout_data['logo_square'] = self.checkBox.isChecked()
        layout_data['angle'] = self.angle
        # layout_data['background_path'] = self.background_path
        # layout_data['include_background'] = self.bcheckBox.isChecked()
        layout_data['background_color'] = self.background_color
        image_height= int(1460/(self.num_of_photos))

        layout_data['image_height'] = image_height
        
       
        for i in range(len(self.order)):
            if self.order[i] == 'LOGO':
                layout_data['logo_position'] = i

        save_json_config(LAYOUT_CONFIG_PATH, layout_data)
        
        self.printer.updatePhotoCount(layout_data['num_of_photos'])
    def printTest(self):
        arr = sorted(os.listdir(app_path('test_photos')))
        arr = arr[:self.num_of_photos]
        # Cant I change this to do just printImages?
        printImages(arr, True)
        self.printer.emitPrint()

    def openColorDialog(self):
        print("Opening")
        color = QColorDialog.getColor(self.background_color)
        

        if color.isValid():
            self.background_color = color.name()