import serial
import tkinter as tk
from serial_manager import SerialManager

class SoundControllerApp:
    def __init__(self, enable_sound_var: tk.BooleanVar, serial_manager: SerialManager):
        self.enable_sound_var = enable_sound_var
        self.serial_manager = serial_manager
        # Add a trace to the BooleanVar to call on_check_button_changed when its value changes
        self.enable_sound_var.trace_add('write', self.on_check_button_changed)

    def get_sound_command(self) -> str:
        """ Return the command to enable or disable the sound.
        1. Sound enable: '!s1#'
        2. Sound disable: '!s0#'
        """
        return '!s1#' if self.enable_sound_var.get() else '!s0#'

    def on_check_button_changed(self, *args):
        # Print the current state of the checkbox
        current_state = self.enable_sound_var.get()
        print(f"[DEBUG] Checkbox state: {current_state}")

        # Step 1: Generate the command based on the checkbox state
        command = self.get_sound_command()
        print(f"[DEBUG] Generated command: {command}")

        # Step 2: Check if the serial port is initialized
        if not self.serial_manager.ser:
            print("[ERROR] Serial port is not initialized.")
            return

        # Step 3: Send the command
        self.send_command(command)

    def send_command(self, command: str):
        """ Send the command using SerialManager """
        print(f"[DEBUG] Attempting to send command: {command}")
        self.send_sound_command(command)

    def send_sound_command(self, command: str):
        """ Send the sound command to the device via SerialManager """
        if self.serial_manager.ser:  # Ensure the serial port is initialized
            try:
                self.serial_manager.ser.write(command.encode())  # Send the command
                print(f"[DEBUG] Command sent: {command}")
            except serial.SerialException as e:
                print(f"[ERROR] Error sending command: {e}")
        else:
            print("[ERROR] Serial port is not initialized")
