import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pystray
from pystray import MenuItem as Item
from PIL import Image, ImageTk
import time
import platform

# Detect the operating system
current_os = platform.system()

# Conditional import based on the operating system
if current_os == "Windows":
    import winsound
elif current_os == "Darwin":  # macOS
    import os
    import subprocess
elif current_os == "Linux":
    import os
    import subprocess
else:
    print(f"Unsupported operating system for sound playing: {current_os}")

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("20-20-20 Reminder")
        self.root.geometry("600x600")

        # Disable window resizing
        self.root.resizable(False, False)

        # Set custom icon for the main window
        self.icon = Image.open("twenty_reminder_icon.png")
        self.tk_icon = ImageTk.PhotoImage(self.icon)
        self.root.iconphoto(False, self.tk_icon)

        self.total_time = 20 * 60  # 20 minutes in seconds
        self.remaining_time = self.total_time
        self.running = False

        # Create a meter to display remaining time
        self.meter = ttk.Meter(root,
                               metersize=250,
                               amounttotal=self.total_time,
                               amountused=self.remaining_time,
                               bootstyle=SUCCESS,
                               showtext=False,
                               subtext=self.format_time(self.remaining_time),
                               subtextstyle=DARK,
                               subtextfont=("Helvetica", 48)
                               )
        self.meter.pack(pady=25)

        # Create a frame for buttons
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        # Start button
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_timer, bootstyle=SUCCESS)
        self.start_button.pack(side=ttk.LEFT, padx=5)

        # Reset button
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_timer, bootstyle=WARNING)
        self.reset_button.pack(side=ttk.LEFT, padx=5)

        # Minimize button
        self.minimize_button = ttk.Button(button_frame, text="Hide", command=self.minimize_window, bootstyle=INFO)
        self.minimize_button.pack(side=ttk.LEFT, padx=5)

        # Quit button
        self.quit_button = ttk.Button(button_frame, text="Quit", command=self.quit_app, bootstyle=DANGER)
        self.quit_button.pack(side=ttk.LEFT, padx=5)

        self.reminder_window = None
        self.setup_tray()
        self.update_timer()

        # Override window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.minimize_window()

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{int(seconds):02}"

    def start_timer(self):
        self.running = True
        self.start_time = time.time()
        self.update_timer()

    def reset_timer(self):
        self.remaining_time = self.total_time  # Reset to 20 minutes
        self.running = False
        self.meter.configure(amountused=self.remaining_time, subtext=self.format_time(self.remaining_time))

    def update_timer(self):
        if self.running:
            elapsed_time = time.time() - self.start_time
            self.remaining_time = max(0, self.total_time - int(elapsed_time))
            self.meter.configure(amountused=self.remaining_time, subtext=self.format_time(self.remaining_time))
            if self.remaining_time == 0:
                self.running = False
                self.show_reminder()
        self.root.after(1000, self.update_timer)

    def minimize_window(self):
        self.root.withdraw()
        self.tray_icon.visible = True

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        if self.reminder_window:
            self.reminder_window.destroy()
        #self.root.quit()    old version use root, but now use toplevel
        self.root.destroy()

    def play_sound(self):
        if current_os == "Windows":
            winsound.PlaySound("twenty_reminder_sound.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif current_os == "Darwin":  # macOS
            subprocess.run(["afplay", "twenty_reminder_sound.wav"])
        elif current_os == "Linux":
            subprocess.run(["aplay", "twenty_reminder_sound.wav"])
        else:
            print("Sound playback is not supported on this operating system.")

    def show_reminder(self):
        if self.reminder_window is not None and self.reminder_window.winfo_exists():
            self.reminder_window.destroy()
        self.reminder_window = ttk.Toplevel()
        self.reminder_window.title("Reminder")

        message_icon = ImageTk.PhotoImage(self.icon)
        self.reminder_window.iconphoto(False, message_icon)

        frame = ttk.Frame(self.reminder_window, padding=20, bootstyle="litera")
        frame.pack(fill="both", expand=True)

        # Add an icon to the reminder window
        message_icon = ImageTk.PhotoImage(self.icon)
        icon_label = ttk.Label(frame, image=message_icon)
        icon_label.image = message_icon  # Keep a reference to avoid garbage collection
        icon_label.pack(side="left", padx=10)

        # Add a label with the reminder message
        label = ttk.Label(frame,
                          text="Time's up!\nTake a 20-second break\nand look at something 20 feet away!",
                          font=("Helvetica", 14),
                          bootstyle="litera")
        label.pack(side="top", padx=10)

        # Add a close button
        close_button = ttk.Button(frame,
                                  text="Close",
                                  command=self.reminder_window.destroy,
                                  bootstyle="danger",
                                  width=10)
        close_button.pack(side="bottom")

        self.play_sound()

        # Update window to get its width and height
        self.reminder_window.update_idletasks()
        window_width = self.reminder_window.winfo_width()
        window_height = self.reminder_window.winfo_height()

        # Get screen width and height
        screen_width = self.reminder_window.winfo_screenwidth()
        screen_height = self.reminder_window.winfo_screenheight()

        # Calculate x and y coordinates to center the window
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Set window position
        self.reminder_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def setup_tray(self):
        self.tray_icon = pystray.Icon("20-20-20 Reminder")
        self.tray_icon.icon = self.icon
        self.tray_icon.menu = pystray.Menu(
            Item('Restore', self.restore_window),
            Item('Quit', self.quit_app)
        )
        self.tray_icon.run_detached()

    def restore_window(self, icon=None, item=None):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        self.root.deiconify()

if __name__ == "__main__":
    root = ttk.Window(themename="litera")  # Choose a theme
    app = TimerApp(root)
    root.mainloop()
