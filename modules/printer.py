import os
from time import monotonic, sleep

from PySide6.QtCore import QThread, Signal

from printing import printImages
from config_store import load_layout_config
from paths import app_path, ensure_runtime_dirs

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


class Printer(QThread):
    beginPrint = Signal()

    def __init__(self):
        super().__init__()
        print("Printer Module Started")
        ensure_runtime_dirs()
        layout_data = load_layout_config()
        self.num_of_photos = layout_data["num_of_photos"]
        self.current_print_count = 0
        self._running = True

    def run(self):
        while self._running:
            try:
                self._process_once()
            except Exception as error:
                # A bad/partial photo must never kill the print thread.
                print(f"Printer error: {error}")
            self._sleep(1)

    def _process_once(self):
        photos_dir = app_path("photos")
        if not photos_dir.exists():
            return

        photos = sorted(
            name
            for name in os.listdir(photos_dir)
            if name.lower().endswith(IMAGE_EXTENSIONS) and (photos_dir / name).is_file()
        )

        if len(photos) < self.num_of_photos:
            return

        batch = photos[: self.num_of_photos]
        print("Sending Job to Printer...")
        printImages(batch)
        self.beginPrint.emit()
        self.current_print_count += 1

    def stop(self):
        self._running = False
        if not self.wait(5000):
            print("Printer thread did not stop in time; forcing termination")
            self.terminate()
            self.wait(1000)

    def updatePhotoCount(self, num_of_photos):
        self.num_of_photos = num_of_photos

    def getPrintCount(self):
        return self.current_print_count

    def emitPrint(self):
        self.beginPrint.emit()

    def _sleep(self, seconds):
        deadline = monotonic() + seconds
        while self._running:
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            sleep(min(0.1, remaining))
