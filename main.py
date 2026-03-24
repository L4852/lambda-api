from keyboard_input import KeyboardInput

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


# def auto_calibrate(self) -> None:
#     # Only enabled for X and A axes
#     # $10=3 -> Send MPos (absolute position) as well in the status message
#     # G90 -> enable absolute positioning mode
#
#     commands = ["$25=9", "$10=3", "$G90"]
#
#
# def set_home(self, axis: Axis) -> None:
#     commands = []


class LiveControl:
    def __init__(self):
        pass

    def run(self):
        KeyboardInput().run()


def main():
    LiveControl().run()


if __name__ == "__main__":
    main()
