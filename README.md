# LambdaAPI  

Supervising controller and API for real-time / high-level control and fault detection layer. Allows control sequences and commands to be written in Python and sent over serial as GRBL G-Code.  
  
Designed for **Lambda**, a robot arm built on *Arctos v2.9.7 (Open Loop)* by **Arctos Robotics**.  
    
`Arctos GRBL firmware (v0.1)` [here](https://github.com/Arctos-Robotics/Arctos-grbl-v0.1)
  
# Core Features  
  
## Remote State  
- Position and state data stored remotely on computer / controlling device  
- Calibrated using homing sequence  
- Reads status from GRBL firmware at frequent intervals  
  
## Command Parsing  
- Methods provided for programming sequences in Python  
- GRBL G-code abstracted away  
- Adds parsed G-code to queue to be processed  

## Keyboard Input
- Actively monitors keystrokes using the `pynput` library in order to allow for real-time manual control of the robot axes and trigger macros / commands.
- Sends inputs to `RobotControl` to convert to G-code and push to serial queue.
  
## Serial Communication  
- Reads from active command queue to send G-code to microcontroller (Arduino Mega 2560 R3).  
  
  
## Classes  
Class methods (blank) and variables. See source code for full implementation.  
  
### GRBLTranslation  
```python  
class GRBLTranslation:  
 @staticmethod
 def parse_status(status_message: str) -> str:
     pass  
```  
### RobotControl  
```python  
class RobotControl:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.a = 0
        self.b = 0
        self.c = 0

        self.unlocked = False
        self.command_queue = []
    
    
    def unlock(self):
        pass
    
    
    def calibrate(self):
        pass
    
    
    def rotate(self):
        pass  
```  
### KeyboardInput  
```python  
class KeyboardInput:
    def __init__(self):
        pass

    def on_press(self, key):
        pass

    def run(self):
        pass
```  
### SerialCommunication  
```python  
def __init__(self, port):
    self.port = port
    self.connection_established = False


def send_packet(queue: List):
    pass  
```  

![layout.jpeg](layout.jpeg)
`Flowchart diagram of software/hardware layout.`

`Last updated: L4852 (026.0320)`
