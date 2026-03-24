from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from input_commands import InputCommands
from robot_control import RobotControl


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
