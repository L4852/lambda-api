import time
from enum import IntEnum, auto, StrEnum

from constants import Constants
from input_commands import InputCommands
from serial_communication import SerialCommunication


class Axis(StrEnum):
    AXIS_X = 'X',
    AXIS_Y = 'Y',
    AXIS_Z = 'Z',
    AXIS_A = 'A',
    AXIS_B = 'B',
    AXIS_C = 'C',


class Servo(IntEnum):
    SERVO_1 = auto()
    SERVO_2 = auto()


class Macro(IntEnum):
    MACRO_1 = auto(),
    MACRO_2 = auto(),
    MACRO_3 = auto(),
    MACRO_4 = auto(),


class RobotControl:
    """
    Handles the internal reference for the robot axis positions, states, and commands. Stores a queue of commands to be sent over serial to the microcontroller.
    """

    def __init__(self):
        init_start_time = time.perf_counter()
        print("Starting robot...")
        self.pos: dict = {
            Axis.AXIS_X: 0.0,
            Axis.AXIS_Y: 0.0,
            Axis.AXIS_Z: 0.0,
            Axis.AXIS_A: 0.0,
            Axis.AXIS_B: 0.0,
            Axis.AXIS_C: 0.0,
            Servo.SERVO_1: 0.0,
            Servo.SERVO_2: 0.0
        }

        self.state = ""

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

        self.recording = False

        self.selected_macro: Macro | None = None

        self.macro_recording_buffer: list = []

        self.saved_macros = {
            Macro.MACRO_1: [],
            Macro.MACRO_2: [],
            Macro.MACRO_3: [],
            Macro.MACRO_4: []
        }

        self.end_eff: float = 0.0

        # sudo pkill bluetoothd

        self.serial_connection = SerialCommunication(Constants.ROBOT_PORT_BT if Constants.USE_BLUETOOTH else Constants.ROBOT_PORT_USB)

        self.current_axis: Axis | None = None

        self.current_speed = Constants.DEFAULT_FEED_RATE

        self.calibration_mode = Constants.CALIBRATION_MODE

        self.set_homing_mask()

        self.enable_wpos()

        self.disable_soft_limits()

        self.initialize_steps_per_unit()

        self.set_acceleration()

        # UNLOCK

        self.unlock_grbl()

        time.sleep(3)

        init_end_time = time.perf_counter()
        print(f"Robot initialized. [{round(init_end_time - init_start_time, 3)}s elapsed]\n=================")

    # =========================
    # Class methods
    # =========================
    def send(self, message: str | bytes, expect_no_response=False):
        response = self.serial_connection.send_message(message, expect_no_response=expect_no_response)
        return response

    def get_status(self) -> dict:
        response = self.serial_connection.send_message(b'?')

        if len(response.splitlines()) > 0:
            status = response.splitlines()[0].decode('utf-8')

            # response_string = response.decode().rstrip('\r\n')

            status_dict = self.parse_status(status)

            return status_dict
        return {}

    def sync_state(self):
        values = self.get_status()

        if len(values.keys()) > 0:
            if 'State' in values.keys() and values['State'] in ['Idle', 'Jog', 'Home', 'Run']:
                print("Setting State:", values['State'])
                self.state = values['State']
            if 'WPos' in values.keys():
                coordinates = values['WPos']

                self.pos = coordinates

    def update_macro(self):
        # sign -> Positive: 0, Negative: 1
        if self.recording:
            if self.selected_macro is not None:
                print("Added to buffer.", self.current_axis)
                self.macro_recording_buffer.append(
                    f"$J=G90{self.current_axis}{self.pos[self.current_axis]}F{self.current_speed}")
            else:
                print("Please select a macro or disable recording mode.")

    def process_macro(self):
        if self.selected_macro is not None and len(self.macro_recording_buffer) > 0:
            print(f"Processing macro [{self.selected_macro}]...")
            self.saved_macros[self.selected_macro] = self.macro_recording_buffer
            self.macro_recording_buffer = []
            print(f"Macro [{self.selected_macro}] successfully saved.")
            print(self.saved_macros[self.selected_macro])
            self.selected_macro = None

    def play_macro(self, macro_id: Macro):
        print("I AM PLAYING")
        if len(self.saved_macros[macro_id]) > 0:
            sequence: list = self.saved_macros[macro_id].copy()

            print(f"MACRO | Playing Macro [{macro_id}]...")

            self.go_to_origin()

            time.sleep(5)

            while len(sequence) > 0:
                print(self.state)
                if self.state == 'Idle':
                    current_command = sequence.pop(0)

                    print(current_command)

                    self.send(current_command, expect_no_response=True)
                    self.sync_state()

                    time.sleep(5)
                    print(self.state, 'AS')
                else:
                    self.sync_state()

            print(f"MACRO | Macro [{macro_id}] completed.")

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
        self.serial_connection.send_message(b"\r\n")
        print("Unlocked...")

    def enable_wpos(self):
        print("Configuring WPos in status...")
        # $10=0 -> Include WPos
        self.serial_connection.send_message("$10=0")
        print("Completed.")

    def disable_soft_limits(self):
        print("Disabling soft limits...")
        # $20=0 -> Disable soft limits
        self.serial_connection.send_message("$20=0")
        print("Soft limits disabled.")

    def go_to_origin(self):
        print("Returning to origin...")
        self.serial_connection.send_message("$J=G90X0Y0Z0A0", expect_no_response=True)

    def set_acceleration(self):
        print("Setting acceleration...")
        self.serial_connection.send_message(f"$120={Constants.X_ACCEL}")
        self.serial_connection.send_message(f"$121={Constants.Y_ACCEL}")
        self.serial_connection.send_message(f"$122={Constants.Z_ACCEL}")
        self.serial_connection.send_message(f"$123={Constants.A_ACCEL}")
        self.serial_connection.send_message(f"$124={Constants.B_ACCEL}")
        self.serial_connection.send_message(f"$125={Constants.C_ACCEL}")

        print("Axis acceleration set.")

    def initialize_steps_per_unit(self):
        print("Initializing steps per unit...")

        self.serial_connection.send_message(f"$100={Constants.X_STEPS_PER_UNIT}")
        self.serial_connection.send_message(f"$101={Constants.Y_STEPS_PER_UNIT}")
        self.serial_connection.send_message(f"$102={Constants.Z_STEPS_PER_UNIT}")
        self.serial_connection.send_message(f"$103={Constants.A_STEPS_PER_UNIT}")
        self.serial_connection.send_message(f"$104={Constants.B_STEPS_PER_UNIT}")
        self.serial_connection.send_message(f"$105={Constants.C_STEPS_PER_UNIT}")

        print("Steps per unit initialized.")

    # =========================
    # G-code send / execution
    # =========================
    def execute(self, command: InputCommands):
        # SERVO M97 B180 T0.2
        # Common shared commands between both calibration and normal control mode
        if command == InputCommands.SPEED_SLOW:
            self.current_speed = 100
        elif command == InputCommands.SPEED_MEDIUM:
            self.current_speed = 500
        elif command == InputCommands.SPEED_HIGH:
            self.current_speed = 750
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

        elif command == InputCommands.REC_TOGGLE:
            if self.recording:
                self.recording = False

                self.process_macro()

                print("REC | MACRO RECORDING MODE DISABLED.")
            else:
                self.recording = True
                print("REC | MACRO RECORDING MODE ENABLED. (Select a macro to start.)")

        elif command == InputCommands.MACRO_1:
            if self.recording:
                self.selected_macro = Macro.MACRO_1
                print("REC | Macro 1 selected.")
                print("REC | Recording started.")
            elif self.saved_macros[Macro.MACRO_1]:
                # Play Macro 1
                self.play_macro(Macro.MACRO_1)
        elif command == InputCommands.MACRO_2:
            if self.recording:
                self.selected_macro = Macro.MACRO_2
                print("REC | Macro 2 selected.")
                print("REC | Recording started.")
            else:
                # Play Macro 2
                self.play_macro(self.selected_macro)
        elif command == InputCommands.MACRO_3:
            if self.recording:
                self.selected_macro = Macro.MACRO_3
                print("REC | Macro 3 selected.")
                print("REC | Recording started.")
            else:
                # Play Macro 3
                self.play_macro(self.selected_macro)
        elif command == InputCommands.MACRO_4:
            if self.recording:
                self.selected_macro = Macro.MACRO_4
                print("REC | Macro 4 selected.")
                print("REC | Recording started.")
            else:
                # Play Macro 4
                self.play_macro(self.selected_macro)

        elif command == InputCommands.END_EFF_CLOSE:
            if self.end_eff < 1.0:
                gcode = f"M97B{self.end_eff * 499}T{Constants.SERVO_TRAVEL_TIME}"
                self.end_eff = round(self.end_eff, 1) + 0.1
                self.send(gcode)

                if self.recording and self.selected_macro is not None:
                    self.macro_recording_buffer += gcode

                self.print_gcode(gcode.encode('utf-8'))
            else:
                gcode = f"M97B499T{Constants.SERVO_TRAVEL_TIME}"
                self.end_eff = 1.0
                self.send(gcode)

                if self.recording and self.selected_macro is not None:
                    self.macro_recording_buffer += gcode

                self.print_gcode(gcode.encode('utf-8'))
        elif command == InputCommands.END_EFF_OPEN:
            if self.end_eff > 0.0:
                gcode = f"M97B{round(self.end_eff * 499)}T{Constants.SERVO_TRAVEL_TIME}"
                self.end_eff = round(self.end_eff, 1) - 0.1
                self.send(gcode)

                if self.recording and self.selected_macro is not None:
                    self.macro_recording_buffer += gcode

                self.print_gcode(gcode.encode('utf-8'))
            else:
                gcode = f"M97B0T{Constants.SERVO_TRAVEL_TIME}"
                self.end_eff = 0.0
                self.send(gcode)

                if self.recording and self.selected_macro is not None:
                    self.macro_recording_buffer += gcode

                self.print_gcode(gcode.encode('utf-8'))

        # Commands differing between calibration (manual small step) and normal mode.
        if not self.calibration_mode:
            # RELEASE KEY
            if command == InputCommands.AXIS_RELEASE:
                # gcode = b"\x85"
                gcode = b"\x85"

                self.send(gcode, True)

                self.sync_state()

                self.update_macro()

                self.print_gcode(gcode)

                self.current_axis = None
            elif self.current_axis is None:
                if command == InputCommands.X_CW:
                    axis = 'X'
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.X_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_X

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.X_CCW:
                    axis = Axis.AXIS_X
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_X

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Y_UP:
                    axis = Axis.AXIS_Y
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.Y_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Y

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Y_DOWN:
                    axis = Axis.AXIS_Y
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Y

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Z_UP:
                    axis = Axis.AXIS_Z
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Z

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.Z_DOWN:
                    axis = Axis.AXIS_Z
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.Z_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_Z

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.A_CCW:
                    axis = Axis.AXIS_A
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}{Constants.A_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_A

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.A_CW:
                    axis = Axis.AXIS_A
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90{axis}0 F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_A

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.B_UP:
                    axis = Axis.AXIS_B
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90C{Constants.B_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_B

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.B_DOWN:
                    axis = Axis.AXIS_B
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90C0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_B

                    self.print_gcode(gcode_string.encode('utf-8'))
                if command == InputCommands.C_CCW:
                    axis = Axis.AXIS_C
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90B0F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_C

                    self.print_gcode(gcode_string.encode('utf-8'))
                elif command == InputCommands.C_CW:
                    axis = Axis.AXIS_C
                    feed_rate = self.current_speed
                    gcode_string = f"$J=G90B{Constants.C_POS_MAX}F{feed_rate}"

                    self.send(gcode_string)

                    self.current_axis = Axis.AXIS_C

                    self.print_gcode(gcode_string.encode('utf-8'))

                elif command == InputCommands.RUN_CALIBRATION:
                    # G92 [{AXIS}0] -> Calibrate by setting given axis to 0.
                    pass
            else:
                pass
        else:
            if command == InputCommands.X_CW:
                axis = Axis.AXIS_X
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.X_CCW:
                axis = Axis.AXIS_X
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_X

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_UP:
                axis = Axis.AXIS_Y
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Y_DOWN:
                axis = Axis.AXIS_Y
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Y

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_UP:
                axis = Axis.AXIS_Z
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.Z_DOWN:
                axis = Axis.AXIS_Z
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_Z

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.A_CCW:
                axis = Axis.AXIS_A
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.A_CW:
                axis = Axis.AXIS_A
                feed_rate = self.current_speed
                gcode_string = f"$J=G91{axis}-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_A

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.B_UP:
                axis = Axis.AXIS_B
                feed_rate = self.current_speed
                gcode_string = f"$J=G91C{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.B_DOWN:
                axis = Axis.AXIS_B
                feed_rate = self.current_speed
                gcode_string = f"$J=G91C-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_B

                self.print_gcode(gcode_string.encode('utf-8'))
            if command == InputCommands.C_CCW:
                axis = Axis.AXIS_C
                feed_rate = self.current_speed
                gcode_string = f"$J=G91B-{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
            elif command == InputCommands.C_CW:
                axis = Axis.AXIS_C
                feed_rate = self.current_speed
                gcode_string = f"$J=G91B{Constants.MANUAL_STEP_WIDTH}F{feed_rate}"

                self.send(gcode_string)

                self.current_axis = Axis.AXIS_C

                self.print_gcode(gcode_string.encode('utf-8'))
