import threading

from fontTools.merge import timer

from app_ui import App
import time
import ui_config as uc
from serial_manager import SerialManager
import re
from dynamic_labelling import ne_median_g
import psutil
from dymaic_data_collection import PostureDataCollection
import numpy as np
import csv
import os
import datetime
from performance_tester import PerformanceTester


class ThreadManager:
    """ The prototype consists of 2 TOF sensors and 1 image sensor,
    based on their data, we create the graph in one subplot to show
    Procedure: read and store data
    """
    app: App
    alarm_num: int
    time_delay: float
    reading_thread: threading.Thread
    _lock = threading.Lock()
    time_assessor: PerformanceTester
    process: psutil.Process
    data_dict: dict[str, dict]
    prediction_dict: dict
    #notes_dict: dict

    def __init__(self, app_title: str):
        self.process = psutil.Process()
        # self.log_path = self.create_log_file()
        self.app = App(title=app_title, fullscreen=False)  # 先初始化self.app
        self.time_assessor = PerformanceTester(critical_file=False)
        self.reading_thread = threading.Thread(target=self.connect, daemon=False)
        self.time_delay = 0.01  # Set to a shorter delay for faster reading
        self.alarm_num = 0
        self.serial_manager = self.app.serial_manager
        if self.serial_manager.ser is None:
            raise Exception("Failed to open serial port")

    @staticmethod
    def create_log_file() -> str:
        today = datetime.datetime.now()
        file_name = f"/data_{today.strftime('%Y%m%d%H%M%S')}.csv"
        folder_path = uc.FilePaths.logs_folder_path.value
        file_path = folder_path + file_name
        # Create the CSV file
        with open(file_path, 'w', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Timestamp", "LocalTime", "Sensor 2", "Sensor 4", "BBox X1", "BBox Y1", "BBox X2", "BBox Y2",
                "MV 1", "MV 2", "MV 3", "MV 4", "Left Eye X", "Left Eye Y", "Right Eye X",
                "Right Eye Y", "Nose X", "Nose Y", "Mouth Left X", "Mouth Left Y", "Mouth Right X",
                "Mouth Right Y", "FHP", "Posture", "Prediction"
            ])
        print(f"CSV file created: {file_path}")
        return file_path

    def run(self):
        self.start_threads()
        self.app.run_app()

    def start_threads(self):
        self.reading_thread.start()

    def stop_threads(self):
        self.app.is_stopped = True
        if self.reading_thread.is_alive():
            self.reading_thread.join()

    def interrupt(self):
        self.app.is_stopped = True

    def close_app(self):
        self.interrupt()
        time.sleep(0.1)
        self.check_memory_usage()
        self.app.save_last_data()
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join()  # Wait for the thread to finish
        self.app.destroy()

    def connect(self, data_entry=None) -> None:
        """ Connect to the COM port """
        while not self.app.is_stopped:
            if not self.app.is_paused:
                line = self.serial_manager.read_line()
                if line is None:
                    continue
                clean_line = self.clean_line(line)
                timestamp, data_entry = self.parse_line(clean_line)
                if timestamp is None:
                    continue
                if timestamp == self.app.logger.last_timestamp:
                    # full join received data entry and last data entry
                    received_data = data_entry
                    last_data = self.app.logger.get_last_data_entry()
                    data_entry = self.app.data_analyst.custom_dict_update(original_data=last_data,
                                                                          new_data=received_data)
                self.app.logger.add_sensor_entry(data_entry=data_entry,
                                                 timestamp=timestamp,
                                                 user_id=self.app.db_manager.session.user_id)
                self.app.logger.add_to_buffer(data_entry=data_entry,
                                              success_callback=self.app.show_notify_log_success)
                # print("Data Parsed and Logged:")
                # print(data_entry)
            time.sleep(self.time_delay)
        else:
            print("Data Parsing has been stopped")
            self.serial_manager.close()

    @staticmethod
    def clean_line(line):
        # 去除“绿色”设置的乱码
        clean_line = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', line)
        return clean_line

    def parse_line(self, line: str) -> tuple:
        """ Parse the sensor data 
        Return timestamp as str and data entry as dict
        """
        timestamp_match = re.search(r'I \((\d+)\)', line)
        if timestamp_match:
            last_timestamp = timestamp_match.group(1)
            self.app.logger.update_last_timestamp(timestamp=last_timestamp)
            if last_timestamp not in self.app.logger.logs:
                self.app.logger.logs[last_timestamp] = self.get_default_entry(last_timestamp)
        if not self.app.logger.last_timestamp:
            return None, None

        entry = self.app.logger.logs[self.app.logger.last_timestamp]
        entry_modified = self.parse_data(line, entry)
        sens_2, sens_4 = self.app.validate_sens_values(sens_2=entry_modified["sensor_2"],
                                                       sens_4=entry_modified["sensor_4"],
                                                       values=self.app.sensor_values)
        entry_modified["sensor_2"] = sens_2
        entry_modified["sensor_4"] = sens_4

        # 更新 recent_data
        self.app.data_analyst.recent_data["sensor_2"] = entry_modified["sensor_2"]
        self.app.data_analyst.recent_data["sensor_4"] = entry_modified["sensor_4"]

        self.app.update_sensor_values(sens_2=entry_modified["sensor_2"],
                                      sens_4=entry_modified["sensor_4"],
                                      timestamp = int(self.app.logger.last_timestamp),
                                      local_time=entry['local_time'])
        return self.app.logger.last_timestamp, entry_modified

    @staticmethod
    def parse_data(data, data_entry) -> dict:
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

        return data_entry

    def check_memory_usage(self):
        memory_info = self.process.memory_info()
        print(f"Memory usage: {memory_info.rss / (1024 ** 2):.2f} MB (resident set size)")
        print(f"Memory usage: {memory_info.vms / (1024 ** 2):.2f} MB (virtual memory size)")

    @staticmethod
    def get_default_entry(timestamp: str) -> dict:
        entry = {
            'timestamp': timestamp,
            'local_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            'fhp': np.nan,
            'prediction': np.nan,
            #'notes': "",
            'user_id': -1,
            'bad_posture_command': 'no',
            'alarm_notification': 'no',
            'notification_interval': np.nan,
            'feedback': np.nan
        }
        return entry


def start_data_collection():
    app = PostureDataCollection()
    app.mainloop()


def start_main_app():
    test_proc = ThreadManager(app_title="Testing Data Validation")
    sample_data = {"Sensor 2": [], "Sensor 4": []}
    test_proc.app.sensor_values = sample_data
    """ Add buttons """
    pause_graph_txt: str = uc.ElementNames.pause_button_txt.value
    close_app_txt: str = uc.ElementNames.close_button_txt.value
    save_txt: str = uc.ElementNames.save_data_button_txt.value
    time_reminder_txt: str = uc.ElementNames.start_20timer_button_txt.value
    calibration_txt: str = uc.ElementNames.calibration_button_txt.value
    sign_in_txt: str = uc.ElementNames.sign_in_button_txt.value
    register_txt: str = uc.ElementNames.register_button_txt.value
    #add_notes_txt: str = uc.ElementNames.save_selected_button_txt.value

    num_alarms_label: str = uc.ElementNames.alarm_num_label.value #警报计数
    proc_time_label: str = uc.ElementNames.processing_time_label.value

    app_ui = test_proc.app

    app_ui.add_control_button(text=pause_graph_txt, func=app_ui.pause)
    app_ui.add_control_button(text=close_app_txt, func=test_proc.close_app)
    app_ui.add_control_button(text=save_txt, func=app_ui.save_all_log)
    #app_ui.add_control_button(text=add_notes_txt, func=app_ui.show_notes_entry)
    app_ui.add_menu_button(text=sign_in_txt, func=app_ui.show_sign_in_popup)
    app_ui.add_menu_button(text=register_txt, func=app_ui.show_register_popup)
    app_ui.add_menu_button(text=time_reminder_txt, func=app_ui.start_20_timer)  #open 20-20-20 reminder
    app_ui.add_menu_button(text=calibration_txt, func=app_ui.calibration)  # calibration
    
    """ Add info panels """
    test_proc.app.create_alarms_label(num_alarms_label, str(0))
    test_proc.app.create_clock_label(proc_time_label)

    test_proc.run()


if __name__ == '__main__':
    # start_data_collection()
    start_main_app()

