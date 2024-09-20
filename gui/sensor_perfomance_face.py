import tkinter as tk
from tkinter import messagebox
import time
import csv
from datetime import datetime
import re
import os
from serial_manager import SerialManager
import pandas as pd
import numpy as np


class SensorPerformanceTest(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sensor Performace Test")
        self.geometry("700x700")
        self.serial_manager = SerialManager()
        self.init_ui()
        self.last_timestamp = None  # 用于记录最新的时间戳

    def init_ui(self):
        instruction = (
            "Please test at the following distances:\n"

            "10. 500mm\n"
            "11. 550mm\n"
            "12. 600mm\n"
            "13. 650mm\n"
            "14. 700mm\n"
            "15. 750mm\n"
            "16. 800mm\n"
            "17. 850mm\n"
            "18. 900mm\n"
            "19. 950mm\n"
            "20. 1000mm\n"

        )

        self.instruction_text = tk.Label(self, text=instruction)
        self.instruction_text.pack(pady=15)
        self.start_button = tk.Button(self, text="Start collecting", command=self.on_start)
        self.start_button.pack(pady=15)

    def on_start(self):
        postures = [

            "500mm",
            "550mm",
            "600mm",
            "650mm",
            "700mm",
            "750mm",
            "800mm",
            "850mm",
            "900mm",
            "950mm",
            "1000mm"
        ]

        data = []

        for posture in postures:
            messagebox.showinfo("Instruction", f"Please : measure at {posture} and stay for 10 seconds.")
            time.sleep(1)
            readings = self.read_sensor_data()
            for reading in readings:
                data.append(reading + [posture])

        self.save_data(data)
        messagebox.showinfo("Info", "Data collection done")
        self.destroy()  # Close the window and stop the program

    def read_sensor_data(self):
        readings = []
        end_time = time.time() + 10
        data_dict = {}

        while time.time() < end_time:
            line = self.serial_manager.read_line()
            if line:
                timestamp_match = re.search(r'I \((\d+)\)', line)
                if timestamp_match:
                    self.last_timestamp = timestamp_match.group(1)
                    print(f"Timestamp: {self.last_timestamp}, Raw sensor data: {line}")  # Print timestamp and data line
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
            time.sleep(0.02)  # Adjust sleep to match the sensor frequency

        for key, value in data_dict.items():
            readings.append([key] + list(value.values())[1:])

        return readings

    def parse_data(self, data, data_entry):
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
            data_entry['bbox_x1'], data_entry['bbox_y1'], data_entry['bbox_x2'], data_entry['bbox_y2'] = [
                int(bbox_match.group(i)) for i in range(1, 5)]

        face_match = face_pattern.search(data)
        if face_match:
            data_entry['left_eye_x'], data_entry['left_eye_y'], data_entry['right_eye_x'], data_entry['right_eye_y'], \
                data_entry['nose_x'], data_entry['nose_y'], data_entry['mouth_left_x'], data_entry['mouth_left_y'], \
                data_entry['mouth_right_x'], data_entry['mouth_right_y'] = [int(face_match.group(i)) for i in
                                                                            range(1, 11)]

        mv_match = mv_pattern.search(data)
        if mv_match:
            data_entry['mv_1'], data_entry['mv_2'], data_entry['mv_3'], data_entry['mv_4'] = [int(mv_match.group(i)) for
                                                                                              i in range(1, 5)]

        fhp_match = fhp_pattern.search(data)
        if fhp_match:
            data_entry['fhp'] = int(fhp_match.group(1))

        print(f"Parsed data entry: {data_entry}")  # Debug print for parsed data

    def save_data(self, data):
        directory = os.path.join(os.path.dirname(__file__), 'data', 'dynamic_data_collected')
        os.makedirs(directory, exist_ok=True)  # Ensure the directory exists
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Get current date and time
        filename = os.path.join(directory, f'dynamic_posture_data_{timestamp}.csv')  # Add timestamp to filename
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


if __name__ == '__main__':
    app = SensorPerformanceTest()
    app.mainloop()
