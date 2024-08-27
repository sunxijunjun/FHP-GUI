from serial.tools import list_ports
from serial_manager import SerialManager
import tkinter as tk
from tkinter import messagebox

def PopupMessage(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

def WritePortName(serial_port_name):
    try:
        with open('serialPortName', 'w') as file:
            file.write(serial_port_name)
    except:
        print("Failed to save the serial port name.")

def ReadPortName():
    try:
        with open('serialPortName', 'r') as file:
            serial_port_name = file.read()
        return serial_port_name
    except:
        return ""

def CheckPortAvailability(port_name):
    serial_manager = SerialManager(port=port_name)
    return serial_manager.ser is not None

def ComparePorts(initial, updated):
    if len(updated) == len(initial) + 1:
        for element in updated:
            if element not in initial:
                return element
    return ""

def GetPortName():
    serial_port = ReadPortName()
    isPortAvailable = CheckPortAvailability(serial_port)
    while not isPortAvailable:
        PopupMessage("Error", "Device not found. Please ensure the device is disconnected, then press OK.")
        ports_initial = [port.device for port in list(list_ports.comports())]
        PopupMessage("", "Please connect the device now. When the device has booted, press OK.")
        ports_updated = [port.device for port in list(list_ports.comports())]
        serial_port = ComparePorts(ports_initial, ports_updated)
        if CheckPortAvailability(serial_port):
            isPortAvailable = True
            WritePortName(serial_port)
    
    return serial_port
    
if __name__ == "__main__":
    print(f"The port name is: {GetPortName()}")