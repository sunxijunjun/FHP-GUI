import serial
import tkinter as tk
from serial_manager import SerialManager

class SoundControllerApp:
    def __init__(self, enable_sound_var: tk.BooleanVar, serial_manager: SerialManager):
        self.enable_sound_var = enable_sound_var
        self.serial_manager = serial_manager
        self.enable_sound_var.trace_add('write', self.on_check_button_changed)

    def get_sound_command(self) -> str:
        """ Return sensor command to enable or disable the sound
        1. Sound enable: '!s1#'
        2. Sound disable: '!s0#'.
        """
        return '!s1#' if self.enable_sound_var.get() else '!s0#'

    def on_check_button_changed(self, *args):
        # 打印当前复选框的状态
        current_state = self.enable_sound_var.get()
        print(f"[DEBUG] Checkbox state: {current_state}")

        # Step 1: 检查是否能正确生成命令
        command = self.get_sound_command()
        print(f"[DEBUG] Generated command: {command}")

        # Step 2: 检查串口是否已经初始化
        if not self.serial_manager.ser:
            print("[ERROR] Serial port is not initialized.")
            return

        # Step 3: 发送命令
        self.send_command(command)

    def send_command(self, command: str):
        """ A method to send the command using SerialManager """
        print(f"[DEBUG] Attempting to send command: {command}")
        self.send_sound_command(command)

    def send_sound_command(self, command: str):
        """ Send the sound command to the device via SerialManager """
        if self.serial_manager.ser:  # 确保串口已经初始化
            try:
                self.serial_manager.ser.write(command.encode())  # 使用 SerialManager 发送命令
                print(f"[DEBUG] Command sent: {command}")
            except serial.SerialException as e:
                print(f"[ERROR] Error sending command: {e}")
        else:
            print("[ERROR] Serial port is not initialized")
