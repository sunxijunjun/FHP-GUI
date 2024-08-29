import serial
import tkinter as tk
from serial_manager import SerialManager

class LightControllerApp:
    def __init__(self, light_control_var: tk.StringVar, serial_manager: SerialManager):
        self.light_control_var = light_control_var
        self.serial_manager = serial_manager
        self.light_control_var.trace_add('write', self.on_check_button_changed)

    def get_light_command(self) -> str:
        """ Return sensor command to enable or disable the light
        '!le0#': LED disable
        '!le1#': LED enable
        '!lef1#': LED flash 1
        """
        light_state = self.light_control_var.get()
        if light_state == 'disable':
            return '!le0#'
        elif light_state == 'enable':
            return '!le1#'
        elif light_state == 'flash':
            return '!lef1#'
        else:
            print(f"[ERROR] Invalid light control state: {light_state}")
            return ''

    def on_check_button_changed(self, *args):
        # 打印当前复选框的状态
        current_state = self.light_control_var.get()
        print(f"[DEBUG] Checkbox state: {current_state}")

        # Step 1: 检查是否能正确生成命令
        command = self.get_light_command()
        print(f"[DEBUG] Generated command: {command}")

        # Step 2: 检查串口是否已经初始化
        if not self.serial_manager.ser:
            print("[ERROR] Serial port is not initialized.")
            return

        # Step 3: 发送命令
        self.send_command(command)

    def send_command(self, command: str):
        """ A method to send the command using SerialManager """
        if command:  # Ensure the command is valid before sending
            print(f"[DEBUG] Attempting to send command: {command}")
            self.send_light_command(command)

    def send_light_command(self, command: str):
        """ Send the light command to the device via SerialManager """
        if self.serial_manager.ser:  # 确保串口已经初始化
            try:
                self.serial_manager.ser.write(command.encode())  # 使用 SerialManager 发送命令
                print(f"[DEBUG] Command sent: {command}")
            except serial.SerialException as e:
                print(f"[ERROR] Error sending command: {e}")
        else:
            print("[ERROR] Serial port is not initialized")
