import tkinter as tk
from tkinter import messagebox
import time
import csv
from datetime import datetime
import re
import os
import platform
import numpy as np
from serial_manager import SerialManager
import ui_config as uc
from port_detection import GetPortName
import pandas as pd
import numpy as np
from statistics import median
import sys
from database_manager import DatabaseManager, UserDetails

# flexibility collection
class PostureDataCollection(tk.Toplevel):
    def __init__(self, serial_manager: SerialManager,db_manager = DatabaseManager(), main_app = None):
        self.main_app = main_app
        if not tk._default_root:
            root = tk.Tk()
            root.withdraw()
        super().__init__()
        self.title("Dynamic Data Collection")
        self.geometry("580x300")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}+{x}+{y}")
        self.serial_manager = serial_manager
        self.db_manager = db_manager
        self.user_features = dict()
        self.init_ui()
        self.last_timestamp = None

    def init_ui(self):
        instruction = (
            "Dear User, \n "
            "Please calibrate it and follow the instructions below:\n"
            "Please make sure the device is properly placed and the user is in a comfortable sitting position.\n"
            "Calibration will require you to maintain 2 specific static postures, collect data, and process it.\n"
            "This operation will take approximately 30 seconds.\n"
            "Please click start and follow the steps:\n"
        )
        self.instruction_text = tk.Label(self, text=instruction)
        self.instruction_text.pack(pady=15)
        self.start_button = tk.Button(self, text="Start collecting", command=self.on_start)
        self.start_button.pack(pady=15)

    def on_start(self):
        self.withdraw()
        postures = [
            "a round shoulder with poking chin posture",
            "an upright neutral posture"
        ]
        data = []

        def collect_posture_data(posture_index):
            if posture_index < len(postures):
                posture = postures[posture_index]
                print(f"Collecting data for posture: {posture}")
                messagebox.showinfo("Instruction", f"Please maintain posture: {posture} for 10 seconds.\nWill start in 2 seconds after click.")
                time.sleep(2)
                readings = self.read_sensor_data()
                for reading in readings:
                    data.append(reading + [posture])
                self.after(100, collect_posture_data, posture_index + 1)  # Wait for 15 seconds before next posture
            else:
                filename = self.save_data(data)
                # Now, perform the checking
                df = pd.read_csv(filename)
                df = df.dropna(subset=['Sensor 2', 'Sensor 4'])
                df['sensor4_2_diff'] = df['Sensor 4'] - df['Sensor 2']

                median_values = (
                    df.groupby('Posture', group_keys=False)
                    .apply(lambda group: group.iloc[len(group) // 2:]['sensor4_2_diff'].median())
                )
                print(median_values)

                if (median_values <= -50).any():
                    messagebox.showerror("Error", "Please adjust device and sitting position: upper sensor is miss-focusing.")
                    self.restart()
                    return

                if (median_values > 200).any():
                    messagebox.showerror("Error", "Please recalibrate: sensor difference out of range.")
                    self.restart()
                    return

                average_median = median_values.mean() + 8
                print("Average of the two medians is:", average_median)

                if 30 < average_median < 180:
                    print("OK")
                    messagebox.showinfo("Success", "Calibration successful.")
                    # 调用 reset_threshold_from_cali 方法，将 average_median 作为新的阈值存入
                    self.reset_threshold_from_cali(average_median)
                    self.exit()
                    return

                else:
                    messagebox.showerror("Error", "Please recalibrate: sensor difference out of range.")
                    self.restart()
                    return

        collect_posture_data(0)        

    def exit(self):
        if self.main_app:
            self.main_app.resume()
            self.main_app.deiconify()
        self.destroy()

    def restart(self):
        # Re-instantiate the class
        new_instance = self.__class__(self.serial_manager, self.db_manager, self.main_app)
        self.destroy()
        new_instance.mainloop()
    
    def reset_threshold_from_cali(self, new_value: float):
        try:
            self.user_features["threshold"] = new_value
            self.db_manager.modify_user_info("Threshold", new_value)
        except Exception as e:
            print(f"Database error: Threshold update failed. Details: {e}")
            return

        if self.main_app and hasattr(self.main_app, "data_analyst"):
            data_analyst = self.main_app.data_analyst

            old_height = data_analyst.user_features.get('height', np.nan)
            old_weight = data_analyst.user_features.get('weight', np.nan)

            updated_features = np.array([
                np.nan,  # index 0
                np.nan,  # index 1
                old_weight,  # index 2 => weight
                old_height,  # index 3 => height
                np.nan,
                np.nan,
                new_value  # index 6 => threshold
            ])

            data_analyst.set_user_features(updated_features)
            print(f"[CALIBRATION] Updated threshold to {new_value}, re-called set_user_features()")

    def read_sensor_data(self):
        readings = []
        self.data_collection_done = False  # Initialize the flag
        end_time = time.time() + 10
        data_dict = {}

        countdown_window = tk.Toplevel(self)
        countdown_window.geometry("400x200")

        # Update window to ensure correct width and height are used
        countdown_window.update_idletasks()
        # Calculate the position to center the window
        x = (countdown_window.winfo_screenwidth() // 2) - (countdown_window.winfo_width() // 2)
        y = (countdown_window.winfo_screenheight() // 2) - (countdown_window.winfo_height() // 2)
        # Set the window's position
        countdown_window.geometry(f"{countdown_window.winfo_width()}x{countdown_window.winfo_height()}+{x}+{y}")

        label_message = tk.Label(countdown_window, text="Remain position, Collecting data...")
        label_message.pack(pady=10)

        label_countdown = tk.Label(countdown_window, text="")
        label_countdown.pack(pady=10)

        def update_countdown():
            remaining_time = int(end_time - time.time())
            if remaining_time > 0:
                label_countdown.config(text=f"{remaining_time} seconds remaining...")
                countdown_window.after(1000, update_countdown)
            else:
                countdown_window.destroy()

        update_countdown()

        def read_data():
            if time.time() < end_time:
                line = self.serial_manager.read_line()
                if line:
                    timestamp_match = re.search(r'I \((\d+)\)', line)
                    if timestamp_match:
                        self.last_timestamp = timestamp_match.group(1)
                        print(f"Timestamp: {self.last_timestamp}, Raw sensor data: {line}")
                        if self.last_timestamp not in data_dict:
                            data_dict[self.last_timestamp] = {
                                'timestamp': self.last_timestamp,
                                'sensor_2': np.nan,
                                'sensor_4': np.nan,
                                'bbox_x1': np.nan,
                                'bbox_y1': np.nan,
                                'bbox_x2': np.nan,
                                'bbox_y2': np.nan,
                                'mv_1': np.nan,
                                'mv_2': np.nan,
                                'mv_3': np.nan,
                                'mv_4': np.nan,
                                'left_eye_x': np.nan,
                                'left_eye_y': np.nan,
                                'right_eye_x': np.nan,
                                'right_eye_y': np.nan,
                                'nose_x': np.nan,
                                'nose_y': np.nan,
                                'mouth_left_x': np.nan,
                                'mouth_left_y': np.nan,
                                'mouth_right_x': np.nan,
                                'mouth_right_y': np.nan,
                                'fhp': np.nan
                            }
                    if self.last_timestamp and self.last_timestamp in data_dict:
                        self.parse_data(line, data_dict[self.last_timestamp])
                    print(f"Collecting data: {int(end_time - time.time()) + 1} seconds remaining...")
                self.after(10, read_data)  # Schedule the next read
            else:
                for key, value in data_dict.items():
                    readings.append([key] + list(value.values())[1:])
                self.data_collection_done = True  # Data collection is done
                countdown_window.destroy()

        read_data()

        # Wait until data collection is done
        while not self.data_collection_done:
            self.update()
            time.sleep(0.01)  # Prevents freezing the GUI

        return readings

    @staticmethod
    def parse_data(data, data_entry):
        range_pattern = re.compile(r'Range: (\d+)\s+(\d+),')
        bbox_pattern = re.compile(r'detection_result:\s*\[\s*\d+\]:\s*\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
        face_pattern = re.compile(
            r'left eye: \(\s*(\d+),\s*(\d+)\), right eye: \(\s*(\d+),\s*(\d+)\), nose: \(\s*(\d+),\s*(\d+)\), mouth left: \(\s*(\d+),\s*(\d+)\), mouth right: \(\s*(\d+),\s*(\d+)\)')
        fhp_pattern = re.compile(r'FHP detected.*?(\d+), mm')
        mv_pattern = re.compile(r'MV: (\d+), (\d+), (\d+), (\d+)')

        range_match = range_pattern.search(data)
        if range_match:
            data_entry['sensor_2'] = int(range_match.group(1))
            data_entry['sensor_4'] = int(range_match.group(2))

        bbox_match = bbox_pattern.search(data)
        if bbox_match:
            data_entry['bbox_x1'], data_entry['bbox_y1'], data_entry['bbox_x2'], data_entry['bbox_y2'] = [int(bbox_match.group(i)) for i in range(1, 5)]

        face_match = face_pattern.search(data)
        if face_match:
            data_entry['left_eye_x'], data_entry['left_eye_y'], data_entry['right_eye_x'], data_entry['right_eye_y'], \
            data_entry['nose_x'], data_entry['nose_y'], data_entry['mouth_left_x'], data_entry['mouth_left_y'], \
            data_entry['mouth_right_x'], data_entry['mouth_right_y'] = [int(face_match.group(i)) for i in range(1, 11)]

        mv_match = mv_pattern.search(data)
        if mv_match:
            data_entry['mv_1'], data_entry['mv_2'], data_entry['mv_3'], data_entry['mv_4'] = [int(mv_match.group(i)) for i in range(1, 5)]

        fhp_match = fhp_pattern.search(data)
        if fhp_match:
            data_entry['fhp'] = int(fhp_match.group(1))

        print(f"Parsed data entry: {data_entry}")  # Debug print for parsed data

    def save_data(self, data):
        directory = os.path.join(os.path.dirname(__file__), 'calibration_data', 'posture_data_collected')
        os.makedirs(directory, exist_ok=True)  # Ensure the directory exists
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Get current date and time
        filename = os.path.join(directory, f'posture_data_{timestamp}.csv')  # Add timestamp to filename
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Only write the header if the file is empty
            if file.tell() == 0:
                writer.writerow([
                    "Timestamp", "Sensor 2", "Sensor 4", "BBox X1", "BBox Y1", "BBox X2", "BBox Y2",
                    "MV 1", "MV 2", "MV 3", "MV 4", "Left Eye X", "Left Eye Y", "Right Eye X",
                    "Right Eye Y", "Nose X", "Nose Y", "Mouth Left X", "Mouth Left Y", "Mouth Right X",
                    "Mouth Right Y", "FHP", "Posture"
                ])

            for row in data:
                print(f"Writing row: {row}")  # Debug print
                writer.writerow(row)
        return filename

if __name__ == '__main__':
    db_manager = DatabaseManager()
    app = PostureDataCollection(SerialManager(port=GetPortName()),db_manager)
    app.mainloop()
