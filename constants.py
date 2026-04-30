class Constants:
    # Constants

    # Integers / Float
    CONNECTION_RETRY_MAX = 5
    CONNECTION_RETRY_DELAY = 5
    SERVO_TRAVEL_TIME = 0.5

    X_POS_LIMIT: (int, int) = (-27, 27)
    Y_POS_LIMIT: (int, int) = (-125,95)
    Z_POS_LIMIT: (int, int) = (-200, 25)
    A_POS_LIMIT: (int, int) = (-20, 20)
    B_POS_LIMIT: (int, int) = (0, 180)
    C_POS_LIMIT: (int, int) = (-60, 60)

    # Presets
    NEUTRAL_COORDINATE: (int, int, int, int, int, int) = (0, -35, -165, 0, 0, 0)
    STORAGE_COORDINATE: (int, int, int, int, int, int) = (-1, 78, -200, 0, -30, 0)
    # -1 78 -200 0 -30 0

    X_ACCEL: float = 10.0
    Y_ACCEL: float = 10.0
    Z_ACCEL: float = 10.0
    A_ACCEL: float = 10.0
    B_ACCEL: float = 10.0
    C_ACCEL: float = 10.0

    X_STEPS_PER_UNIT: float = 400.0
    Y_STEPS_PER_UNIT: float = 400.0
    Z_STEPS_PER_UNIT: float = 400.0
    A_STEPS_PER_UNIT: float = 640.0
    B_STEPS_PER_UNIT: float = 200.0
    C_STEPS_PER_UNIT: float = 200.0

    READ_TIMEOUT: float = 0.1

    MANUAL_STEP_WIDTH: int = 1.0
    DEFAULT_FEED_RATE: int = 100
    MAX_LINES_READ: int = 50
    CONNECTION_TIMEOUT: int = 10
    WRITE_TIMEOUT_TRIES: int = 50

    # Strings / Bytes
    NEWLINE_SEQUENCE: bytes = b'\r\n'
    ROBOT_PORT_USB: str = '/dev/cu.usbmodem2101'
    ROBOT_PORT_BT: str = '/dev/cu.LambdaRobotArm'

    # Boolean
    USE_BLUETOOTH = True
    DEBUG_NO_SERIAL: bool = False
    PRINT_ALL_RESPONSES: bool = False
    KEY_LOG: bool = False
    CALIBRATION_MODE: bool = True
