import signal
import sys
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

        signal.signal(signal.SIGTERM, self.close_connection)
        signal.signal(signal.SIGINT, self.close_connection)

        for i in range(Constants.CONNECTION_RETRY_MAX):
            print(("" if i > 0 else f"({i + 1}) " + f"Attempting serial connection to '{port}'."))

            try:
                print("Connecting...")

                self.connection = serial.Serial(
                    port, baudrate=115200,
                    timeout=Constants.READ_TIMEOUT,
                )

                time.sleep(3)

                print("Clearing serial input and output buffers...")
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()

                time.sleep(1)

                # PING
                print("Waiting for acknowledgement...")
                self.connection.write(b'\r\n')
                a = self.connection.readline()
                ping_response = self.connection.readline()

                if len(ping_response) > 0:
                    self.connected = True
                else:
                    print(f"Connection to serial port '{port}' unsuccessful.")
                    time.sleep(3)
                    print("Connection to serial port failed.")

            except serial.SerialException:
                time.sleep(1)
                print(f"Port '{port}' could not be found.")
                time.sleep(2)
                print(f"Could not connect to serial port '{port}'.")

            if i < Constants.CONNECTION_RETRY_MAX:
                for j in range(Constants.CONNECTION_RETRY_DELAY):
                    print(f"Retrying connection in ({Constants.CONNECTION_RETRY_DELAY - j}) seconds...")
                    time.sleep(1)
                continue
            else:
                time.sleep(1)

                if self.connected:
                    print("Connection successful.")
                    break
                else:
                    raise Exception("Connection to the serial port was unsuccessful.")


    def close_connection(self, signal_number, frame):
        print(f"SIGNAL '{signal.Signals(signal_number).name}' received.")
        if self.connection is not None and self.connection.is_open:
            print(f"Active serial connection found, closing...")

            time.sleep(1)

            self.connection.flush()

            time.sleep(2)

            self.connection.close()
            print(f"Connection closed successfully, exiting program...")
            time.sleep(2)
            sys.exit(0)

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

            while not (
                    (
                            seen_terminator and self.connection.in_waiting == 0) or extracted_line == b'') and lines_read < Constants.MAX_LINES_READ:
                extracted_line = self.connection.readline()
                buffer.extend(extracted_line)

                if extracted_line.decode().startswith(('ok', 'error', 'ALARM', 'MSG', '<')):
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
