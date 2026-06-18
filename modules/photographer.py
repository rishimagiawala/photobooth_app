from time import monotonic, sleep

from PySide6.QtCore import QThread, Signal

from config_store import load_layout_config
from paths import app_path

COUNTDOWN_IMAGES = (
    "countdown-5.png",
    "countdown-4.png",
    "countdown-3.png",
    "countdown-2.png",
    "countdown-1.png",
)


def _viewer_asset(name):
    return str(app_path("assets", "images", "viewer", name))


class Photographer(QThread):
    def __init__(self, callbackCam, callbackTakePicture, getQueueCount, popFromQueue, getTakenImage, getPrintCount):
        super().__init__()
        self.getQueueCount = getQueueCount
        self.popFromQueue = popFromQueue
        self.toggleCamStream = callbackCam
        self.takePicture = callbackTakePicture
        self.getTakenImage = getTakenImage
        self.getPrintCount = getPrintCount
        self._running = True

    change_image_signal = Signal(str)
    change_count_signal = Signal(str)

    def run(self):
        self.change_image_signal.emit(_viewer_asset("not_ready.png"))

        while self._running:
            try:
                self._run_once()
            except Exception as error:
                print(f"Photographer error: {error}")
                # Reset to a known-safe idle state and keep the thread alive.
                self.toggleCamStream(False)
                self.change_count_signal.emit("")
                self._sleep(1)

    def _run_once(self):
        if self.getQueueCount() <= 0:
            self._sleep(0.1)
            return

        self.change_image_signal.emit(_viewer_asset("msg_start.png"))
        layout_data = load_layout_config()
        num_of_photos = layout_data["num_of_photos"]
        print(f"Session Begun to Take {num_of_photos} Photos")
        self._sleep(2)

        for _ in range(num_of_photos):
            if not self._running:
                break
            self._capture_one_photo()

        self.toggleCamStream(False)
        self.change_count_signal.emit("")
        self.change_image_signal.emit(_viewer_asset("msg_finished.png"))
        self._sleep(2)
        self.popFromQueue()

        if self.getQueueCount() == 0:
            self.change_count_signal.emit("")
            if self.getPrintCount() > 699:
                self.change_image_signal.emit(_viewer_asset("no_paper.png"))
            else:
                self.change_image_signal.emit(_viewer_asset("not_ready.png"))

    def _capture_one_photo(self):
        self.toggleCamStream(True)
        for name in COUNTDOWN_IMAGES:
            if not self._running:
                return
            self.change_count_signal.emit(_viewer_asset(name))
            self._sleep(1)

        if not self._running:
            return

        if not self.takePicture():
            print("Waiting for camera frame before retrying picture")
            self._sleep(1)
            self.takePicture()

        self.change_count_signal.emit("")
        self.toggleCamStream(False)
        self._sleep(2)

    def stop(self):
        self._running = False
        if not self.wait(3000):
            print("Photographer thread did not stop in time; forcing termination")
            self.terminate()
            self.wait(1000)

    def _sleep(self, seconds):
        deadline = monotonic() + seconds
        while self._running:
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            sleep(min(0.05, remaining))
