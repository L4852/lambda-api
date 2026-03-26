import time
from enum import IntEnum, auto

from constants import Constants
from input_commands import InputCommands
from serial_communication import SerialCommunication


class Axis(IntEnum):
    AXIS_X = auto(),
    AXIS_Y = auto(),
    AXIS_Z = auto(),
    AXIS_A = auto(),
    AXIS_B = auto(),
    AXIS_C = auto()


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

        self.serial_connection = SerialCommunication(Constants.ROBOT_PORT)

        self.current_axis: Axis | None = None

        self.current_speed = Constants.DEFAULT_FEED_RATE

        self.calibration_mode = Constants.CALIBRATION_MODE

        self.set_homing_mask()

        self.enable_wpos()

        self.disable_soft_limits()

        # UNLOCK

        self.unlock_grbl()

        time.sleep(1)

    # =========================
    # Class methods
    # =========================
    def send(self, message: str | bytes, expect_no_response=False):
        response = self.serial_connection.send_message(message, expect_no_response=expect_no_response)
        return response

    def get_status(self) -> dict:
        response = self.serial_connection.send_message(b'?')

        status = response.splitlines()[0].decode('utf-8')

        # response_string = response.decode().rstrip('\r\n')

        status_dict = self.parse_status(status)

        return status_dict

    def update_coordinates(self):
        pass

    # =========================
    # Utility methods
    # =========================
    def print_gcode(self, gcode_bytes: bytes) -> None:
        print(
            f"{str(gcode_bytes).strip()} [{self.serial_connection.bytes_as_hex(gcode_bytes)}] ({len(gcode_bytes)} B)"
        )

    @staticmethod
    def parse_status(status_message: str) -> dict:
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

            status_name = split_field[0]
            value = split_field[1]

            status[status_name] = value

            if status_name == 'WPos':
                coordinates = value.split(',')

                status['WPos'] = {
                    axis: coordinates[index] for index, axis in enumerate(Axis)
                }

        return status

    # =========================
    # G-code generator methods
    # =========================
    def set_homing_mask(self):
        print("Setting homing mask...")
        self.serial_connection.send_message("$25=9")

    def unlock_grbl(self):
        print("Unlocking GRBL...")
        self.serial_connection.send_message("$X")
        print("Unlocked.\n================\n")

    def enable_wpos(self):
        print("Configuring WPos in status...")
        # $10=0 -> Include WPos
        self.serial_connection.send_message("$10=0")
        print("Completed.\n================\n")

    def disable_soft_limits(self):
        print("Disabling soft limits...")
        # $20=0 -> Disable soft limits
        self.serial_connection.send_message("$20=0")
        print("Soft limits disabled.")

    # =========================
    # G-code send / execution
    # =========================
    def execute(self, command: InputCommands):
        # Common shared commands between both calibration and normal control mode
        if command == InputCommands.SPEED_SLOW:
            self.current_speed = 100

        elif command == InputCommands.SPEED_MEDIUM:
            self.current_speed = 500
        elif command == InputCommands.SPEED_HIGH:
            self.current_speed = 1000
        elif command == InputCommands.REQUEST_ROBOT_STATUS:
            status_dict = self.get_status()
            print(status_dict)
        elif command == InputCommands.SOFT_RESET:
            print("Sending soft reset command...")
            response = self.send(b'\x18', True)
            print("Reset successfully.")
            time.sleep(2)

            if response:
                print(response)
        elif command == InputCommands.SEND_JOG_STOP:
            print("Sending jog stop command...")
            response = self.send(b'\x85', True)
            print("Sent successfully.")

            if response:
                print(response)

        # Commands differing between calibration (manual small step) and normal mode.
        if not self.calibration_mode:
            if command == InputCommands.AXIS_RELEASE:
                # gcode = b"\x85"
                gcode = b"\x85"

                self.current_axis = None

                response = self.send(gcode, True)

                self.print_gcode(gcode)
            if self.current_axis is None:
                if command == InputCommands.X_CCW:
                    axis = 'X'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.X_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_X

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.X_CW:
                    axis = 'X'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_X

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Y_UP:
                    axis = 'Y'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.Y_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Y

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Y_DOWN:
                    axis = 'Y'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Y

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Z_UP:
                    axis = 'Z'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Y

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Z_DOWN:
                    axis = 'Z'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.Z_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Z

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.A_CCW:
                    axis = 'A'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.A_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_A

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.A_CW:
                    axis = 'A'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_A

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.B_UP:
                    axis = 'B'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_B

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.B_DOWN:
                    axis = 'B'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.B_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_B

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.C_CCW:
                    axis = 'C'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.C_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_C

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.C_CW:
                    axis = 'C'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_C

                    self.print_gcode(gcode_string.encode('utf-8'))

                elif command == InputCommands.RUN_CALIBRATION:
                    # G92 [{AXIS}0] -> Calibrate by setting given axis to 0.
                    pass
            else:
                pass
        else:
            if command == InputCommands.X_CCW:
                axis = 'X'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CW:
                axis = 'X'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP:
                axis = 'Y'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN:
                axis = 'Y'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP:
                axis = 'Z'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN:
                axis = 'Z'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW:
                axis = 'A'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW:
                axis = 'A'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP:
                axis = 'B'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN:
                axis = 'B'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW:
                axis = 'C'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW:
                axis = 'C'
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
