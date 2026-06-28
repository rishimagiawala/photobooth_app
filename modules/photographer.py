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
# How long to freeze on the shot that was just taken so people can see it.
PHOTO_REVIEW_SECONDS = 1.0
# Live-preview pause after the review so people can reset their pose.
LIVE_GAP_SECONDS = 1.0
# How long the "your photos are printing" screen stays up at the end.
FINISHED_SCREEN_SECONDS = 3.0


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
        self._show_idle()

        while self._running:
            try:
                if self.getQueueCount() <= 0:
                    self._sleep(0.1)
                    continue
                self._run_session()
            except Exception as error:
                # A session must never get stuck looping on an error; the
                # finally block in _run_session has already cleared the queue.
                print(f"Photographer error: {error}")
                self._sleep(1)

    def _run_session(self):
        try:
            layout_data = load_layout_config()
            num_of_photos = layout_data["num_of_photos"]
            print(f"Session Begun to Take {num_of_photos} Photos")

            self.change_image_signal.emit(_viewer_asset("msg_start.png"))
            self._sleep(2)

            # Camera stays live for the whole session so there's no freeze
            # between shots, only the countdown overlay before each one.
            self.toggleCamStream(True)
            for index in range(num_of_photos):
                if not self._running:
                    break
                self._capture_one_photo(is_last=index == num_of_photos - 1)
        finally:
            self.toggleCamStream(False)
            self.change_count_signal.emit("")
            self._finish_session()

    def _capture_one_photo(self, is_last):
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

        # Freeze on the shot that was just taken (turning the live preview off
        # holds the last frame on screen) so people can see the photo.
        self.toggleCamStream(False)
        self._sleep(PHOTO_REVIEW_SECONDS)

        # Then resume the live preview so they can reset their pose.
        if not is_last:
            self.toggleCamStream(True)
            self._sleep(LIVE_GAP_SECONDS)

    def _finish_session(self):
        # Always run, even if the session errored out, so the queue is cleared
        # and the booth returns to a sane state.
        if self._running:
            self.change_image_signal.emit(_viewer_asset("msg_finished.png"))
            self._sleep(FINISHED_SCREEN_SECONDS)

        self.popFromQueue()

        if self._running and self.getQueueCount() == 0:
            self._show_idle()

    def _show_idle(self):
        self.change_count_signal.emit("")
        if self.getPrintCount() > 699:
            self.change_image_signal.emit(_viewer_asset("no_paper.png"))
        else:
            self.change_image_signal.emit(_viewer_asset("not_ready.png"))

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
