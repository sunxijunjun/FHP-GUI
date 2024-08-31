from serial.tools import list_ports
import serial
import tkinter as tk
from tkinter import messagebox

def PopupMessage(title, message):
    """ Show a popup message. """
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()

def WritePortName(serial_port_name):
    """ Save the serial port name to the file 'serialPortName'. """
    try:
        with open('serialPortName', 'w') as file:
            file.write(serial_port_name)
    except:
        print("Failed to save the serial port name.")

def ReadPortName():
    """ Read the serial port name from the file 'serialPortName'. """
    try:
        with open('serialPortName', 'r') as file:
            serial_port_name = file.read()
        return serial_port_name
    except:
        return ""

def CheckPortAvailability(port_name):
    """ Check whether the port is available. """
    try:
        serial_port = serial.Serial(port_name, baudrate = 115200, timeout = 1)
        serial_port.close()
        return True
    except:
        return False

def ComparePorts(initial, updated):
    """ Compare the initial and updated ports connected to the computer and return the new port name. """
    if len(updated) == len(initial) + 1:
        for element in updated:
            if element not in initial:
                return element
    return ""

def DetectUSBPort():
    """ Check whether the USB port is available and return the port name. """
    for port in list(list_ports.comports()):
        if 'USB' in port.description:
            return port.device
    return None

def GetPortNameManually():
    """ Get the device port name by disconnect and re-connect manually. """
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

def GetPortName():
    """ Detect the USB port automatically. If not working, change GetPortName() to GetPortNameManually(). """
    serial_port = ReadPortName()
    isPortAvailable = CheckPortAvailability(serial_port)
    while not isPortAvailable:
        if DetectUSBPort() and CheckPortAvailability(DetectUSBPort()):
            serial_port = DetectUSBPort()
            WritePortName(serial_port)
            isPortAvailable = True
            return serial_port
        else:
            PopupMessage("Error", "Device not found. Please ensure the device is connected.")
    
    return serial_port

if __name__ == "__main__":
    print(f"The port name is: {GetPortName()}")