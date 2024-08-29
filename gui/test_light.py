import tkinter as tk
import serial
#设备有一些bug。没法直接关闭LED。
#需要开→闪烁→关
class LightControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Control")

        # 初始化灯光控制状态变量
        self.light_control_var = tk.StringVar(value='disable')

        # 初始化串口通信
        self.serial_port = serial.Serial(port='COM13', baudrate=115200, timeout=1)

        # 创建三个按钮来控制灯光
        self.disable_button = tk.Button(root, text="Disable Light", command=self.disable_light)
        self.enable_button = tk.Button(root, text="Enable Light", command=self.enable_light)
        self.flash_button = tk.Button(root, text="Flash Light", command=self.flash_light)

        # 布局按钮
        self.disable_button.pack(pady=10)
        self.enable_button.pack(pady=10)
        self.flash_button.pack(pady=10)

        # 显示当前状态的标签
        self.status_label = tk.Label(root, text="Current Command: None")
        self.status_label.pack(pady=10)

    def disable_light(self):
        self.light_control_var.set('disable')
        command = self.get_light_command()
        self.send_command(command)

    def enable_light(self):
        self.light_control_var.set('enable')
        command = self.get_light_command()
        self.send_command(command)

    def flash_light(self):
        self.light_control_var.set('flash')
        command = self.get_light_command()
        self.send_command(command)

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

    def send_command(self, command):
        """Send the command to the device via serial port"""
        if self.serial_port.is_open:
            self.serial_port.write(command.encode())
            self.update_status(command)
            print(f"Command sent: {command}")
        else:
            print("Error: Serial port is not open")

    def update_status(self, command):
        self.status_label.config(text=f"Current Command: {command}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LightControlApp(root)
    root.mainloop()
