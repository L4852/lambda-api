from enum import IntEnum
from typing import List

import serial
from pynput import keyboard
from pynput.keyboard import KeyCode, Key


# G92 [{AXIS}0] -> Calibrate by setting given axis to 0.
# $J=G91

class SerialCommunication:
    """
    Sends the parsed GRBL G-Code over serial to the microcontroller. Establishes the serial connection and passes on data from the microcontroller to the robot control.
    """

    def __init__(self, port):
        self.port = port
        self.connection_established = False

    @staticmethod
    def send_packet(queue: List):
        data = bytes('.'.join(queue).encode())
        print(data.hex(sep=" ").upper())

        connection = serial.Serial('/dev/device')

        connection.write(bytes("$$".encode('utf-8')))

        b = connection.readline()

        print(b)


class KeyboardInput:
    def __init__(self):
        self.keyLookup = {
            'a': []
        }

    def on_press(self, key) -> None:
        print(type(key))

        if isinstance(key, KeyCode):
            if key.char == "a":
                pass
            elif key.char == "s":
                pass
        elif isinstance(key, Key):
            if key == keyboard.Key.f1:
                print("F1")

    def on_release(self, key) -> bool | None:
        if key == keyboard.Key.esc:
            # Stop listener
            return False

    def run(self):
        # Blocking
        # with keyboard.Listener(
        #         on_press=self.on_press,
        #         on_release=self.on_release) as listener:
        #     listener.join()

        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        listener.start()


class Axis(IntEnum):
    AXIS_X = 0,
    AXIS_Y = 1,
    AXIS_Z = 2,
    AXIS_A = 3,
    AXIS_B = 4,
    AXIS_C = 5


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

    def unlock(self):
        if not self.unlocked:
            self.unlocked = True

    def calibrate(self):
        # $10=3 -> Send MPos (absolute position) as well in the status message
        commands = ["$25=9", "$10=3"]

        pass


class GRBLTranslation:
    def parse_status(self, status_message: str) -> str:
        """
        Parses the status message received when sending the '?' command to GRBL into a dictionary of the sent data.
        :param status_message: Status message sent from GRBL using the '?' command.
        :return: Returns a dictionary containing the message contents.
        """
        # Split status message into entries
        contents = status_message.strip("<>").split('|')
        print(contents)

        # Split each entry into key value
        # Initialize with state field as it has no key
        status = {'State': contents[0]}

        for field in contents[1:]:
            split_field = field.split(':')
            status[split_field[0]] = split_field[1]

        print(status)


def main():
    # GRBLTranslation().parse_status("")
    # SerialCommunication.send_packet([])

    KeyboardInput().run()

    while True:
        pass


if __name__ == "__main__":
    main()
