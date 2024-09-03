import serial
from typing import Union
import threading
import re


class SerialManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, port=None, baudrate=115200, timeout=1):
        cls._instance = super(SerialManager, cls).__new__(cls)
        try:
            cls._instance.ser = serial.Serial(port, baudrate, timeout=timeout)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            cls._instance.ser = None
        return cls._instance

    def read_line(self) -> Union[str, None]:
        with self._lock:
            if self.ser and self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').rstrip()
                    # Remove any 'green' characters (e.g., ANSI escape codes)
                    line = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', line)
                    return line
                except serial.SerialException as e:
                    print(f"Error reading line: {e}")
                    return None
        return None

    def close(self):
        with self._lock:
            if self.ser:
                self.ser.close()

    def test_readline(self) -> Union[str, None]:
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').rstrip()
            # Remove any 'green' characters (e.g., ANSI escape codes)
            line = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', line)
            return line
        except serial.SerialException as e:
            print(f"Error reading line: {e}")
            return None
