class Constants:
    # Constants

    # Integers / Float
    X_POS_MAX: int = 360
    Y_POS_MAX: int = 180
    Z_POS_MAX: int = 180
    A_POS_MAX: int = 360
    B_POS_MAX: int = 180
    C_POS_MAX: int = 360

    READ_TIMEOUT: float = 0.1

    MANUAL_STEP_WIDTH: int = 5
    DEFAULT_FEED_RATE: int = 100
    MAX_LINES_READ: int = 50
    CONNECTION_TIMEOUT: int = 10
    WRITE_TIMEOUT_TRIES: int = 50

    # Strings / Bytes
    NEWLINE_SEQUENCE: bytes = b'\r\n'
    ROBOT_PORT: str = '/dev/cu.usbmodem2101'
    # ROBOT_PORT = '/dev/cu.LambdaRobotArm'

    # Boolean
    DEBUG_NO_SERIAL: bool = False
    PRINT_ALL_RESPONSES: bool = False
    KEY_LOG: bool = False
    CALIBRATION_MODE: bool = False
