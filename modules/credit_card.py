from contextlib import suppress
from time import monotonic, sleep

import serial
from PySide6.QtCore import QThread, Signal

from config_store import load_reader_config

RECONNECT_DELAY = 2.0


class Reader(QThread):
    begin_session = Signal()

    def __init__(self):
        super().__init__()
        layout_data = load_reader_config()
        self.credit_amount = layout_data["credits_trigger"]
        self.port = layout_data["serial_port"]
        print(self.port)
        self.baudrate = 9600
        self.credit = 0
        self.ser = None
        self._running = True
        self._open_serial()

    def _open_serial(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print("Credit Card Reader Module Started")
        except (serial.SerialException, OSError) as error:
            self.ser = None
            print(f"Credit Card Reader unavailable at {self.port}: {error}")

    def run(self):
        while self._running:
            try:
                self._poll_once()
            except Exception as error:
                # Never let the reader thread die; reconnect and carry on.
                print(f"Credit Card Reader error ({error}); attempting reconnect")
                self.closeSerial()
                self._sleep(RECONNECT_DELAY)

        self.closeSerial()

    def _poll_once(self):
        if self.ser is None:
            self._sleep(RECONNECT_DELAY)
            if self._running:
                self._open_serial()
            return

        try:
            data = self.ser.read(1)
            data += self.ser.read(self.ser.inWaiting())
        except (serial.SerialException, OSError) as error:
            print(f"Credit Card Reader read failed ({error}); attempting reconnect")
            self.closeSerial()
            self._sleep(RECONNECT_DELAY)
            return

        if not data:
            # No token this cycle; yield a little CPU.
            self._sleep(0.01)
            return

        self.credit += 1
        integer_value = int.from_bytes(data, "big")
        print(f"{self.credit} Tokens | Number {integer_value} | Data {data}")

        if self.credit >= self.credit_amount:
            self.credit = 0
            self.begin_session.emit()

    def stop(self):
        self._running = False
        self.closeSerial()
        if not self.wait(3000):
            print("Reader thread did not stop in time; forcing termination")
            self.terminate()
            self.wait(1000)

    def closeSerial(self):
        if self.ser is not None:
            with suppress(Exception):
                self.ser.close()
            self.ser = None

    def updateCreditAmount(self, credit_amount):
        self.credit_amount = credit_amount
        print("Credit Trigger Updated To: " + str(self.credit_amount))

    def _sleep(self, seconds):
        deadline = monotonic() + seconds
        while self._running:
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            sleep(min(0.05, remaining))
