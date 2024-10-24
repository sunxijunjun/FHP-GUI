from serial.tools import list_ports
import serial
import tkinter as tk
from tkinter import messagebox

def PopupMessage(title, message, retry = False):
    """ Show a popup message. """
    root = tk.Tk()
    root.withdraw()
    if retry:
        if not messagebox.askretrycancel(title, message):
            quit()
    else:
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
        return None

def CheckPortAvailability(port_name):
    """ Check whether the serial port is available. """
    try:
        serial_port = serial.Serial(port_name, baudrate = 115200, timeout = 1)
        serial_port.close()
        return True
    except:
        return False

def DetectUSBPorts():
    """ Check whether the USB serial port is available and return the port name. """
    ports = list()
    for port in list(list_ports.comports()):
        if 'USB' in port.description:
            ports.append(port.device)
    return ports

def GetPortName():
    """ Detect the USB serial ports automatically. """
    serial_port = ReadPortName()
    isPortAvailable = CheckPortAvailability(serial_port)
    attempts = 0
    while not isPortAvailable:
        ports = DetectUSBPorts()
        if len(ports) > 0:
            for port in ports:
                if CheckPortAvailability(port):
                    serial_port = port
                    WritePortName(serial_port)
                    return serial_port
        else:
            PopupMessage("Error", "Device not found. Please ensure the device is connected.", retry = True)
            attempts += 1
        
        if attempts >= 3:
            return GetPortNameManually()
        
    return serial_port

def GetPortNameManually():
    """ Get the device port name by disconnect and re-connect manually. """
    serial_port = ReadPortName()
    isPortAvailable = CheckPortAvailability(serial_port)
    if not isPortAvailable:
        PopupMessage("Error", "Failed to detect the device automatically. Please follow the instructions to set up manually.")
    while not isPortAvailable:
        PopupMessage("Error", "Please ensure the device is disconnected, then press OK.")
        ports_initial = [port.device for port in list(list_ports.comports())]
        PopupMessage("", "Please connect the device now. When the device has booted, press OK.")
        ports_updated = [port.device for port in list(list_ports.comports())]
        if len(ports_updated) == len(ports_initial) + 1:
            for element in ports_updated:
                if element not in ports_initial:
                    serial_port = element
                    break
        if CheckPortAvailability(serial_port):
            isPortAvailable = True
            WritePortName(serial_port)
        else:
            PopupMessage("Error", "Device not found. Would you like to retry?", retry = True)
    
    return serial_port

if __name__ == "__main__":
    print(f"The port name is: {GetPortName()}")