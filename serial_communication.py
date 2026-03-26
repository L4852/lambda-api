import time

import serial
from serial import Serial

from constants import Constants


class SerialCommunication:
    """
    Sends the parsed GRBL G-Code over serial to the microcontroller. Establishes the serial connection and passes on data from the microcontroller to the robot control.
    """

    def __init__(self, port):
        self.port = port

        self.connected = False

        self.connection: Serial | None = None

        if Constants.DEBUG_NO_SERIAL:
            print("Debug mode (no serial connection) is active.")
            return

        print(f"Attempting serial connection to '{port}'.")

        try:
            print("Connecting...")
            self.connection = serial.Serial(port, baudrate=115200, timeout=Constants.READ_TIMEOUT)

            time.sleep(1)

            # PING
            print("Waiting for acknowledgement...")
            self.connection.write(b'$')
            self.connection.readline()
            ping_response = self.connection.readline()

            if len(ping_response) > 0:
                self.connected = True
                print("Connected successfully.")
            else:
                print(f"Connection to serial port '{port}' unsuccessful.")
                time.sleep(3)
                raise Exception("Connection to serial port failed. Exiting program.")

        except serial.SerialException:
            print(f"Could not connect to serial port '{port}',")
            time.sleep(2)
            raise Exception(f"Could not connect to serial port '{port}'.")

        time.sleep(1)

    def bytes_as_hex(self, byte_data: bytes) -> str:
        return byte_data.hex(sep=" ").upper()

    def send_message(self, message: str | bytes, expect_no_response: bool = False) -> bytearray | None:
        data = message

        response = bytearray()

        if self.connection is not None and self.connected:
            if isinstance(data, str):
                self.connection.write(data.encode('utf-8') + Constants.NEWLINE_SEQUENCE)
            elif isinstance(data, bytes):
                self.connection.write(data)
            else:
                raise Exception(TypeError("Incorrect type for parameter 'message'. (str | bytes)."))

            if expect_no_response:
                return None

            buffer: bytearray = bytearray()

            extracted_line = b'0'

            seen_terminator = False

            lines_read = 0

            while not ((seen_terminator and self.connection.in_waiting == 0) or extracted_line == b'') and lines_read < Constants.MAX_LINES_READ:
                extracted_line = self.connection.readline()
                buffer.extend(extracted_line)

                if extracted_line.decode().startswith(('ok', 'error', 'ALARM', 'MSG')):
                    seen_terminator = True

                lines_read += 1

            response = buffer
        else:
            print("No serial connection, message send failed.")
            response = None

        if response is not None:
            if Constants.PRINT_ALL_RESPONSES:
                response_string = response.decode().rstrip('\r\n')
                print("---------\r\n", response_string, '\r\n---------\r\n')
            return response
        return None
