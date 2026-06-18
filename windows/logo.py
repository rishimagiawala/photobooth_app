import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config_store import LAYOUT_CONFIG_PATH, load_layout_config, save_json_config
from paths import app_path, display_path, resolve_app_path

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
PREVIEW_SIZE = 280
THUMB_SIZE = 120


class LogoWindow(QMainWindow):
    """A deliberately simple, hard-to-misuse screen for changing the logo.

    Operators can either pick an image from anywhere (it gets copied into the
    logos folder automatically) or click one they've used before. Every change
    asks for confirmation and saves immediately, so there's no separate "Save"
    step to forget and nothing destructive to click by accident.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Change Logo")
        self.resize(520, 640)

        self.logos_dir = app_path("assets", "images", "logos")
        self.logos_dir.mkdir(parents=True, exist_ok=True)

        layout_data = load_layout_config()
        self.logo_path = layout_data["logo_path"]

        root = QVBoxLayout()
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Current Logo")
        title.setAlignment(Qt.AlignHCenter)
        title.setFont(self._font(18, bold=True))
        root.addWidget(title)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.preview.setMinimumHeight(PREVIEW_SIZE)
        self.preview.setStyleSheet("border: 2px solid #cccccc; border-radius: 8px; background: #fafafa;")
        root.addWidget(self.preview)

        choose_button = QPushButton("Choose a New Logo Image…")
        choose_button.setMinimumHeight(64)
        choose_button.setFont(self._font(16, bold=True))
        choose_button.setStyleSheet(
            "QPushButton { background: #2d7d46; color: white; border-radius: 8px; }"
            "QPushButton:hover { background: #36964f; }"
        )
        choose_button.clicked.connect(self.chooseFromFile)
        root.addWidget(choose_button)

        gallery_label = QLabel("…or tap a logo you've used before:")
        gallery_label.setFont(self._font(13))
        root.addWidget(gallery_label)

        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.IconMode)
        self.gallery.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.gallery.setResizeMode(QListWidget.Adjust)
        self.gallery.setMovement(QListWidget.Static)
        self.gallery.setSpacing(10)
        self.gallery.setUniformItemSizes(True)
        self.gallery.itemClicked.connect(self.onGalleryClicked)
        root.addWidget(self.gallery, stretch=1)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignHCenter)
        self.status.setFont(self._font(13, bold=True))
        self.status.setStyleSheet("color: #2d7d46;")
        root.addWidget(self.status)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        self.refreshPreview()
        self.refreshGallery()

    def _font(self, size, bold=False):
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def chooseFromFile(self):
        start_dir = str(Path.home())
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Pick a logo image",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not selected:
            return

        source = Path(selected)
        if source.suffix.lower() not in VALID_EXTENSIONS:
            self._warn("That file isn't a supported image.\nPlease pick a PNG, JPG, BMP, or GIF.")
            return

        if QPixmap(str(source)).isNull():
            self._warn("That image couldn't be opened.\nPlease pick a different file.")
            return

        if not self._confirm("Use this image as your logo?", str(source.name)):
            return

        try:
            destination = self._copy_into_logos(source)
        except OSError as error:
            self._warn(f"Could not copy the image:\n{error}")
            return

        self._apply_logo(destination)
        self.refreshGallery()
        self._flash(f"Logo updated to “{destination.name}”")

    def onGalleryClicked(self, item):
        path = Path(item.data(Qt.UserRole))
        if not path.exists():
            self._warn("That logo file is missing.")
            self.refreshGallery()
            return

        if not self._confirm("Use this logo?", path.name):
            self.gallery.clearSelection()
            return

        self._apply_logo(path)
        self._flash(f"Logo updated to “{path.name}”")

    def _apply_logo(self, path):
        stored = display_path(path)
        layout_data = load_layout_config()
        # Set both logo slots so both halves of the printed strip match.
        layout_data["logo_path"] = stored
        layout_data["logo2_path"] = stored
        save_json_config(LAYOUT_CONFIG_PATH, layout_data)
        self.logo_path = stored
        self.refreshPreview()
        print(f"Logo changed to {stored}")

    def _copy_into_logos(self, source):
        source = source.resolve()
        # Already inside the logos folder? Just use it in place.
        if source.parent == self.logos_dir.resolve():
            return source

        destination = self.logos_dir / source.name
        counter = 1
        while destination.exists():
            destination = self.logos_dir / f"{source.stem}_{counter}{source.suffix}"
            counter += 1

        shutil.copy2(source, destination)
        return destination

    def refreshPreview(self):
        pixmap = QPixmap(str(resolve_app_path(self.logo_path)))
        if pixmap.isNull():
            self.preview.setText("No logo set")
            return
        self.preview.setPixmap(
            pixmap.scaled(PREVIEW_SIZE, PREVIEW_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def refreshGallery(self):
        self.gallery.clear()
        current = str(resolve_app_path(self.logo_path).resolve())
        for image_path in sorted(self.logos_dir.iterdir()):
            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                continue

            item = QListWidgetItem(image_path.name)
            item.setIcon(QIcon(pixmap))
            item.setData(Qt.UserRole, str(image_path))
            item.setTextAlignment(Qt.AlignHCenter)
            self.gallery.addItem(item)
            if str(image_path.resolve()) == current:
                item.setSelected(True)

    def _confirm(self, question, detail):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Please confirm")
        box.setText(question)
        box.setInformativeText(detail)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        return box.exec() == QMessageBox.Yes

    def _warn(self, message):
        QMessageBox.warning(self, "Heads up", message)

    def _flash(self, message):
        self.status.setText(message)
