from contextlib import suppress
from pathlib import Path
from threading import Lock
from time import monotonic, sleep

from PySide6.QtCore import QThread, Signal
import cv2
import numpy as np

PREFERRED_CAMERA = "/dev/video1"
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_FPS = 30
REOPEN_DELAY = 2.0
# How many failed reads in a row before we assume the device died and reopen it.
MAX_CONSECUTIVE_FAILURES = 30


class CameraReader(QThread):
    """Continuously grabs frames from a V4L2 camera.

    The capture loop only stores the most recent frame (protected by a lock).
    Consumers pull frames with ``read_latest()`` at their own pace, which keeps
    the GUI event loop from being flooded with per-frame signals.
    """

    # Kept for backwards compatibility; the GUI polls ``read_latest`` instead.
    image_signal = Signal(np.ndarray)

    def __init__(self):
        super().__init__()
        print("Camera Module Started")
        self._running = True
        self._frame_lock = Lock()
        self._latest_frame = None
        self.cap = None

        with suppress(ModuleNotFoundError):
            import pyi_splash  # noqa

            pyi_splash.close()

    def run(self):
        consecutive_failures = 0
        while self._running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    self.cap = self._open_camera()
                    if self.cap is None:
                        self._interruptible_sleep(REOPEN_DELAY)
                        continue
                    consecutive_failures = 0

                ret, frame = self.cap.read()

                if ret and frame is not None and frame.size > 0:
                    consecutive_failures = 0
                    with self._frame_lock:
                        self._latest_frame = frame
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        print("Camera stopped returning frames; reopening device")
                        self._release_capture()
                        consecutive_failures = 0
                        self._interruptible_sleep(REOPEN_DELAY)
                    else:
                        self._interruptible_sleep(0.05)
            except Exception as error:
                # Never let the capture thread die; drop the device and retry.
                print(f"Camera loop error: {error}; recovering")
                self._release_capture()
                consecutive_failures = 0
                self._interruptible_sleep(REOPEN_DELAY)

        self._release_capture()

    def read_latest(self):
        """Return a copy of the most recent frame, or ``None`` if unavailable."""
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def stop(self):
        """Cooperatively stop the capture loop and release the device."""
        self._running = False
        if not self.wait(3000):
            print("Camera thread did not stop in time; forcing termination")
            self.terminate()
            self.wait(1000)
        self._release_capture()

    def _interruptible_sleep(self, seconds):
        deadline = monotonic() + seconds
        while self._running:
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            sleep(min(0.05, remaining))

    def _release_capture(self):
        if self.cap is not None:
            with suppress(Exception):
                self.cap.release()
            self.cap = None

    def _open_camera(self):
        for device in self._camera_devices():
            print(f"Trying camera device {device}")
            cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap.release()
                continue

            # MJPG lets most USB webcams actually deliver 1080p without
            # saturating USB bandwidth (a common cause of stalls/freezes).
            with suppress(Exception):
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
            # Keep only the freshest frame buffered to avoid latency/backlog.
            with suppress(Exception):
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ret, _ = cap.read()
            if ret:
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                print(f"Camera device {device} opened at {width}x{height}")
                return cap

            print(f"Camera device {device} opened but did not return frames")
            cap.release()

        print("Camera Startup Failed: no working V4L2 camera found")
        return None

    def _camera_devices(self):
        devices = sorted(Path("/dev").glob("video*"), key=self._video_device_sort_key)
        device_paths = [str(device) for device in devices]

        if PREFERRED_CAMERA in device_paths:
            device_paths.remove(PREFERRED_CAMERA)
            device_paths.insert(0, PREFERRED_CAMERA)

        return device_paths

    def _video_device_sort_key(self, device):
        suffix = device.name.replace("video", "")
        return int(suffix) if suffix.isdigit() else 999
