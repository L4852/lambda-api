from enum import Enum

from constants import Constants
from input_commands import InputCommands
from serial_communication import SerialCommunication


class Axis(Enum):
    AXIS_X = 'X',
    AXIS_Y = 'Y',
    AXIS_Z = 'Z',
    AXIS_A = 'A',
    AXIS_B = 'B',
    AXIS_C = 'C'


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
                gcode_string = f"$J=G90{axis}{Constants.X_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.X_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.Y_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.Y_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.Z_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.Z_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.A_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.A_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.B_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.B_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.C_POS_MAX}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G90{axis}{Constants.C_POS_MIN}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

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
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CW and self.current_axis is None:
                axis = 'X'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN and self.current_axis is None:
                axis = 'Y'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN and self.current_axis is None:
                axis = 'Z'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW and self.current_axis is None:
                axis = 'A'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN and self.current_axis is None:
                axis = 'B'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW and self.current_axis is None:
                axis = 'C'
                feed_rate = 500
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}{Constants.NEWLINE_SEQUENCE}"

                self.serial_connection.send_message(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
