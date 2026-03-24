import time

import serial
from serial import Serial

from constants import Constants


class SerialCommunication:
    """
    Sends the parsed GRBL G-Code over serial to the microcontroller. Establishes the serial connection and passes on data from the microcontroller to the robot control.
    """

    def __init__(self, port, timeout=10):
        self.port = port

        self.connected = False

        self.connection: Serial | None = None

        watchdog = 0

        if Constants.DEBUG_NO_SERIAL:
            return

        while not self.connected and watchdog < timeout:
            try:
                self.connection = serial.Serial(port)
                self.connected = True
            except serial.SerialException:
                print(f"Connection to serial port '{port}' unsuccessful...\nRetrying. ({watchdog + 1})")
                watchdog += 1
            time.sleep(1)

        if watchdog == timeout:
            raise Exception("Connection to serial port failed. Exiting program.")

    def write(self, message_string: str) -> bytes | None:
        if self.connection is not None and self.connected:
            self.send_message(message_string)
            return self.connection.readline()
        else:
            print("No serial connection, message send failed.")
            return None

    def bytes_as_hex(self, byte_data: bytes) -> str:
        return byte_data.hex(sep=" ").upper()

    def send_message(self, message):
        data = message

        response = self.write(data)

        if response is not None:
            print(self.bytes_as_hex(data.encode('utf-8')), '->', response)
