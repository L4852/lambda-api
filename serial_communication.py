import signal
import sys
import time

import serial
from serial import Serial

from constants import Constants

from sound import Sound

class SerialCommunication:
    """
    Sends the parsed GRBL G-Code over serial to the microcontroller. Establishes the serial connection and passes on data from the microcontroller to the robot control.
    """

    def __init__(self, port):
        self.port = port

        self.connected = False

        self.connection: Serial | None = None

        self.snd = Sound()

        if Constants.DEBUG_NO_SERIAL:
            print("Debug mode (no serial connection) is active.")
            return

        signal.signal(signal.SIGTERM, self.close_connection)
        signal.signal(signal.SIGINT, self.close_connection)

        for i in range(Constants.CONNECTION_RETRY_MAX):
            self.snd.play_connecting_progress_sound()

            self.snd.say("" if i > 0 else f"({i + 1}) " + f"Attempting serial connection to '{port}'.")
            print(("" if i > 0 else f"({i + 1}) " + f"Attempting serial connection to '{port}'."))


            try:
                print("Connecting...")
                self.snd.say("Connecting...")

                self.connection = serial.Serial(
                    port, baudrate=115200,
                    timeout=Constants.READ_TIMEOUT,
                )

                time.sleep(3)

                print("Clearing serial input and output buffers...")
                self.snd.play_generic_task_sound()

                self.snd.say("Clearing serial input and output buffers...")
                self.connection.reset_input_buffer()
                self.snd.play_generic_task_sound()
                self.connection.reset_output_buffer()
                self.snd.play_generic_task_sound()

                time.sleep(1)

                # PING

                print("Waiting for acknowledgement...")
                self.snd.say("Waiting for acknowledgement...")

                self.connection.write(b'\r\n')
                self.snd.play_generic_task_sound()
                a = self.connection.readline()
                self.snd.play_generic_task_sound()
                ping_response = self.connection.readline()
                self.snd.play_generic_task_sound()

                if len(ping_response) > 0:
                    self.connected = True
                    self.snd.play_connected_sound()
                else:
                    print(f"Connection to serial port '{port}' unsuccessful.")
                    self.snd.say(f"Connection to serial port '{port}' unsuccessful.")
                    self.snd.play_error_sound()
                    time.sleep(3)
                    print("Connection to serial port failed.")
                    self.snd.say("Connection to serial port failed.")

            except serial.SerialException:
                time.sleep(1)
                print(f"Port '{port}' could not be found.")
                self.snd.say(f"Port '{port}' could not be found.")
                self.snd.play_error_sound()
                time.sleep(2)
                self.snd.say(f"Could not connect to serial port '{port}'.")

            if i < Constants.CONNECTION_RETRY_MAX:
                for j in range(Constants.CONNECTION_RETRY_DELAY):
                    self.snd.play_error_sound()
                    print(f"Retrying connection in ({Constants.CONNECTION_RETRY_DELAY - j}) seconds...")
                    time.sleep(1)
                continue
            else:
                time.sleep(1)

                if self.connected:
                    print("Connection successful.")
                    self.snd.say("Connection successful.")
                    self.snd.play_connected_sound()
                    break
                else:
                    self.snd.play_error_sound()
                    self.snd.say("Connection to the serial port was unsuccessful.")
                    raise Exception("Connection to the serial port was unsuccessful.")


    def close_connection(self, signal_number, frame):
        print(f"SIGNAL '{signal.Signals(signal_number).name}' received.")
        if self.connection is not None and self.connection.is_open:
            self.snd.play_disconnect_sound()
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
                self.snd.play_error_sound()
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
            self.snd.play_error_sound()
            response = None

        if response is not None:
            if Constants.PRINT_ALL_RESPONSES:
                response_string = response.decode().rstrip('\r\n')
                print("---------\r\n", response_string, '\r\n---------\r\n')
            self.snd.play_ping2_sound()
            return response
        return None
