import time
from enum import Enum, IntEnum, auto

import serial
from pynput import keyboard
from pynput.keyboard import KeyCode, Key
from serial import Serial

# Constants

DEBUG_NO_SERIAL = True

X_POS_MAX = 10
X_POS_MIN = -10
Y_POS_MAX = 10
Y_POS_MIN = -10
Z_POS_MAX = 10
Z_POS_MIN = -10
A_POS_MAX = 10
A_POS_MIN = -10
B_POS_MAX = 10
B_POS_MIN = -10
C_POS_MAX = 10
C_POS_MIN = -10

MANUAL_STEP_WIDTH = 5

NEWLINE_SEQUENCE = "\r\n"


# =======================

class TelemetryEntry:
    def __init__(self, identifier: str, message: str):
        self.identifier = identifier
        self.message = message

    def get_string(self):
        return f"[{self.identifier}] -> {self.message}"

    def print(self):
        print(self.get_string())


class Telemetry:
    def __init__(self, persistent_path='/telemetry/log.txt'):
        self.entries = []
        self.persistent_path = ""

    def add(self, entry: TelemetryEntry):
        self.entries.append(entry)

    def dump(self):
        with open(self.persistent_path, 'w') as file:
            file.write('\n'.join([k.get_string() for k in self.entries]))


class SerialCommunication:
    """
    Sends the parsed GRBL G-Code over serial to the microcontroller. Establishes the serial connection and passes on data from the microcontroller to the robot control.
    """

    def __init__(self, port, timeout=10):
        self.port = port

        self.connected = False

        self.connection: Serial | None = None

        watchdog = 0

        if DEBUG_NO_SERIAL:
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


class Axis(Enum):
    AXIS_X = 'X',
    AXIS_Y = 'Y',
    AXIS_Z = 'Z',
    AXIS_A = 'A',
    AXIS_B = 'B',
    AXIS_C = 'C'


class InputCommands(IntEnum):
    X_CW = auto(),
    X_CCW = auto(),
    Y_UP = auto(),
    Y_DOWN = auto(),
    Z_UP = auto(),
    Z_DOWN = auto(),
    A_CW = auto(),
    A_CCW = auto(),
    B_UP = auto(),
    B_DOWN = auto(),
    C_CW = auto(),
    C_CCW = auto(),
    AXIS_RELEASE = auto(),
    END_EFF_CLOSE = auto(),
    END_EFF_OPEN = auto(),
    SPEED_SLOW = auto(),
    SPEED_MEDIUM = auto(),
    SPEED_HIGH = auto(),
    AXIS_STOP = auto(),
    REC_TOGGLE = auto(),
    RUN_CALIBRATION = auto(),
    MACRO_1 = auto(),
    MACRO_2 = auto(),
    MACRO_3 = auto(),
    MACRO_4 = auto(),
    MACRO_5 = auto(),
    MACRO_6 = auto(),
    MACRO_7 = auto(),
    MACRO_8 = auto(),
    MACRO_9 = auto(),


class RobotControl:
    """
    Handles the internal reference for the robot axis positions, states, and commands. Stores a queue of commands to be sent over serial to the microcontroller.
    """

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0

        # Homing Mask (Command: $25=9)
        # C (Joint 6)	32
        # B (Joint 5)	16
        # A (Joint 4)	8
        # Z (Joint 3)	4
        # Y (Joint 2)	2
        # X (Joint 1)	1

        # INCLUDE X, A, omit others
        # 001001 -> 9

        self.unlocked = False

        self.serial_connection = SerialCommunication('/dev/cu/serial')

        self.current_axis: Axis | None = None

        self.current_speed = 100

        self.calibration_mode = True

    def print_gcode(self, gcode_bytes: bytes) -> None:
        print(
            f"{str(gcode_bytes).strip()} [{self.serial_connection.bytes_as_hex(gcode_bytes)}] ({len(gcode_bytes)} B)"
        )

    def execute(self, command: InputCommands):
        # Common shared commands between both calibration and normal control mode
        if command == InputCommands.AXIS_RELEASE:
            gcode = b"\x85"

            self.current_axis = None

            self.print_gcode(gcode)

        elif command == InputCommands.SPEED_SLOW:
            self.current_speed = 100

        elif command == InputCommands.SPEED_MEDIUM:
            self.current_speed = 500
        elif command == InputCommands.SPEED_HIGH:
            self.current_speed = 1000

        # Commands differing between calibration (manual small step) and normal mode.
        if not self.calibration_mode:
            if command == InputCommands.X_CCW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{X_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{X_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Y_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Y_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Z_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Z_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{A_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{A_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{B_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{B_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{C_POS_MAX}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{C_POS_MIN}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))

            elif command == InputCommands.RUN_CALIBRATION:
                # G92 [{AXIS}0] -> Calibrate by setting given axis to 0.

                pass

        else:
            if command == InputCommands.X_CCW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{MANUAL_STEP_WIDTH}F{feed_rate}{NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))


class KeyboardInput:
    def __init__(self):
        self.keyMap = {
            'a': InputCommands.A_CCW,
            'd': InputCommands.A_CW,
            'w': InputCommands.Z_UP,
            's': InputCommands.Z_DOWN,
            'q': InputCommands.C_CCW,
            'e': InputCommands.C_CW,
            Key.left.name: InputCommands.X_CCW,
            Key.right.name: InputCommands.X_CW,
            Key.up.name: InputCommands.Y_UP,
            Key.down.name: InputCommands.Y_DOWN,
            'c': InputCommands.END_EFF_CLOSE,
            'v': InputCommands.END_EFF_OPEN,
            '1': InputCommands.SPEED_SLOW,
            '2': InputCommands.SPEED_MEDIUM,
            '3': InputCommands.SPEED_HIGH,
            'r': InputCommands.REC_TOGGLE,
            'h': InputCommands.RUN_CALIBRATION,
            Key.f1.name: InputCommands.MACRO_1,
            Key.f2.name: InputCommands.MACRO_2,
            Key.f3.name: InputCommands.MACRO_3,
            Key.f4.name: InputCommands.MACRO_4,
            Key.f5.name: InputCommands.MACRO_5,
            Key.f6.name: InputCommands.MACRO_6,
            Key.f7.name: InputCommands.MACRO_7,
            Key.f8.name: InputCommands.MACRO_8,
            Key.f9.name: InputCommands.MACRO_9,
        }

        self.robotInstance = RobotControl()

    def on_press(self, key: Key | KeyCode) -> None:
        key_value = key.char if isinstance(key, KeyCode) else key.name

        command: InputCommands | None = None

        try:
            command = self.keyMap[key_value]
        except KeyError:
            # print(f"No mapping is associated with '{key_value}'.")
            return

        self.robotInstance.execute(command)

    def on_release(self, key: Key | KeyCode) -> bool | None:
        key_value = key.char if isinstance(key, KeyCode) else key.name

        try:
            command = self.keyMap[key_value]
        except KeyError:
            # print(f"No mapping is associated with '{key_value}'.")
            return

        # Exit keyboard input loop
        if key == keyboard.Key.esc:
            return False

        if key_value in ['up', 'down', 'left', 'right', 'q', 'w', 'e', 'a', 's', 'd', 'c', 'v']:
            self.robotInstance.execute(InputCommands.AXIS_RELEASE)

    def run(self):
        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()


def parse_status(self, status_message: str) -> dict:
    """
    Parses the status message received when sending the '?' command to GRBL into a dictionary of the sent data.
    :param status_message: Status message sent from GRBL using the '?' command.
    :return: Returns a dictionary containing the message contents.
    """
    # Split status message into entries
    contents = status_message.strip("<>").split('|')

    # Split each entry into key value
    # Initialize with state field as it has no key
    status = {'State': contents[0]}

    for field in contents[1:]:
        split_field = field.split(':')
        status[split_field[0]] = split_field[1]

    return status


def auto_calibrate(self) -> None:
    # Only enabled for X and A axes
    # $10=3 -> Send MPos (absolute position) as well in the status message
    # G90 -> enable absolute positioning mode

    commands = ["$25=9", "$10=3", "$G90"]


def set_home(self, axis: Axis) -> None:
    commands = []


class LiveControl:
    def __init__(self):
        pass

    def run(self):
        KeyboardInput().run()


def main():
    LiveControl().run()


if __name__ == "__main__":
    main()
