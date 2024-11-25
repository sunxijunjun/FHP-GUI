import csv
import datetime
import sys
import os
import numpy as np
import pandas as pd
import ui_config as uc
import copy
from typing import Union, Callable
import aiofiles
from aiocsv import AsyncWriter
from performance_tester import PerformanceTester


class Buffer:
    head: int
    size: int
    values: list[Union[None, dict]]
    num_entries: int

    def __init__(self):
        self.size = uc.Measurements.graph_x_limit.value  # num of rows per log
        self.values = [None] * self.size
        self.head = 0
        self.num_entries = 0

    def reset(self):
        self.values = [None] * self.size

    def add(self, data_entry: dict):
        self.values[self.head] = data_entry
        self.head = (self.head + 1) % self.size
        self.num_entries += 1

    def update_size(self, new_size: int):
        self.size = new_size


class Logger:
    """ Perform function strictly related to logging all possible data
    Attributes:
        log_path is an absolute path where the logs are stored
        prediction_results are {timestamps as str: Union[1, 0]}
        notes are {timestamp as str: text as str}
        data_dict are {timestamp as str: data_entry as dict}
    """
    session_id: str
    log_path: str
    folder_path: str
    prediction_results: dict
    notes: dict
    logs: dict[str, dict]  # data collector, which saves everything together
    last_timestamp: str
    last_model_threshold: float
    is_test: bool
    show_notification: bool
    tester = PerformanceTester(critical_file=True)
    buffer = Buffer()

    columns = [
            'timestamp', 'local_time', 'sensor_2', 'sensor_4',
            'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
            'mv_1', 'mv_2', 'mv_3', 'mv_4',
            'left_eye_x', 'left_eye_y', 'right_eye_x', 'right_eye_y',
            'nose_x', 'nose_y', 'mouth_left_x', 'mouth_left_y',
            'mouth_right_x', 'mouth_right_y', 'fhp', 'prediction',
            'notes', 'user_id', 'alarm_notification',
            'notification_interval', 'feedback', 'model_threshold', 'model_notes'
            ]

    def __init__(self, session_id: str, test=False):
        self.session_id = session_id
        self.folder_path = self.create_folder_logs(session_id, test)
        # self.log_path = self.create_log_file(session_id=session_id,
        #                                      columns=self.columns,
        #                                      folder_path=self.folder_path)
        self.prediction_results = {}
        self.notes = {}
        self.logs = {}
        self.last_timestamp = ""
        self.last_model_threshold = np.nan
        self.is_test = test
        self.show_notification = True

    def __repr__(self) -> str:
        content = (f"===Logger START===\n"
                   f"File path: {self.log_path}\n"
                   f"Prediction Results:\n"
                   f"{self.prediction_results}\n"
                   f"Notes:\n"
                   f"{self.notes}\n"
                   f"===Logger END===")
        return content

    def add_to_buffer(self, data_entry: dict, success_callback: Union[None, Callable]):
        """ Add the new data to the buffer
        1. New data will be added to the log file
        2. Once the log file is full, it created a new log file to save the data
        3. Buffer gets empty
        """
        self.buffer.add(data_entry)
        # Add data entry to the logs
        # asyncio.run(self.add_row_async(data_entry, file_path=self.log_path))
        self.add_row(data_entry)  # add row in sync
        if self.buffer.head == 0:
            """ Postprocess the data stored in the buffer """
            self.log_buffer()
            self.log_path = self.create_log_file(session_id=self.session_id,
                                                 columns=self.columns,
                                                 folder_path=self.folder_path)
            # self.buffer = [None] * self.buffer_size
            self.buffer.reset()
            # Show success saving notification
            if success_callback and self.show_notification:
                success_callback(subject="Data Logged!")
            print(f"{self.buffer.size} Rows saved to {self.log_path}")

    def log_buffer(self):
        self.tester.end()
        self.tester.show_time_summary(function_name='log_buffer',
                                      notes="See the time interval between creating a new file")
        self.tester.start()
        """ Log the buffer to the file """
        # Convert buffer to DataFrame
        df = pd.DataFrame(columns=self.columns)
        for data_entry in self.buffer.values:
            if data_entry is None:
                continue
            new_row = {}
            for key in df.columns:
                new_row[key] = data_entry.get(key, np.nan)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # Save DataFrame to CSV
        df.to_csv(self.log_path, index=False)
        print(f"Data saved to {self.log_path}")

    @staticmethod
    async def add_row_async(data_entry: dict, file_path: str):
        readings = []
        for key, value in data_entry.items():
            readings.append(value)  # data entry has fixed size M
        async with aiofiles.open(file_path, mode='a', newline='') as f:
            writer = AsyncWriter(f)
            await writer.writerow(readings)

    def log_all_data(self) -> None:
        data = copy.deepcopy(self.logs)
        # Convert to DataFrame
        df = pd.DataFrame(columns=self.columns)
        for timestamp, data in data.items():
            new_row = {'timestamp': timestamp}
            for key in df.columns:
                new_row[key] = data.get(key, np.nan)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # New file path
        new_path = self.create_log_file(session_id=self.session_id,
                                        columns=self.columns,
                                        note='all',
                                        folder_path=self.folder_path)
        # Save DataFrame to CSV
        df.to_csv(new_path, index=False)
        print(f"All Data saved to {new_path}")

    @staticmethod
    def post_process_df(df: pd.DataFrame, notes: Union[None, pd.DataFrame]) -> pd.DataFrame:
        """ It is composed of static functions such as:
        1. Merge DF with the Notes DF
        2. Fill the gaps between user notes
        3. Formatting bad posture commands notes
        4. Fill the gaps between alarm notification notes
        5. Fill in nan values of model threshold used for each prediction
        """
        if notes is not None and notes.shape[0] > 0:
            df = Logger.add_notes(marked_data=notes,
                                  df_collector=df)
            df = Logger.process_notes_gaps(df)
        else:
            print("Warning! No Data Notes found!", file=sys.stderr)
        # df = Logger.process_bad_posture_command_col(df, replace_other_notes=False)
        df = Logger.process_alarm_notifications(df)
        df = Logger.process_models_thresholds_gaps(df)
        return df

    def add_row(self, data_entry: dict):
        """ Simply write add one additional row of data
        Note: 1. the function supposed to be called at the end of iteration
        when all necessary information has been received
        2. Not in use !
        """
        readings = []
        for key, value in data_entry.items():
            readings.append(value)
        row = ','.join(str(r) for r in readings)
        with open(self.log_path, mode='a', newline='', encoding='utf-8') as csv_file:
            csv_file.write(row + '\n')

    def get_last_data_entry(self) -> dict:
        return self.logs[self.last_timestamp]

    def get_last_local_time(self) -> str:
        return self.logs[self.last_timestamp]['local_time']

    def add_sensor_entry(self, data_entry: dict, timestamp: str, user_id: int) -> None:
        """ Function is responsible for processing only data received from the sensor """
        data_entry['user_id'] = user_id
        if timestamp not in self.logs:
            local_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_entry['local_time'] = local_time
            data_entry['local_timestamp'] = datetime.datetime.now().timestamp()
            self.logs[timestamp] = data_entry
        else:
            self.logs[timestamp].update(data_entry)

    @staticmethod
    def create_folder_logs(session_id: str, is_test: bool) -> str:
        relative_path = uc.FilePaths.logs_folder_path.value
        new_folder_name = f'/session_{session_id}'
        if is_test:
            new_folder_name = f'/session_{session_id}_test'
        path = relative_path + new_folder_name
        os.makedirs(path)
        return path

    @staticmethod
    def create_log_file(session_id: str, columns: list[str], folder_path: str, note=None) -> str:
        today = datetime.datetime.now()
        file_name = f"/data_{today.strftime('%Y%m%d%H%M%S')}_{session_id}.csv"
        if note:
            file_name = f"/data_{today.strftime('%Y%m%d%H%M%S')}_{session_id}_{note}.csv"
        file_path = folder_path + file_name
        # Create the CSV file
        with open(file_path, 'w', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)
        print(f"CSV file created: {file_path}")
        return file_path

    def update_prediction(self, timestamp: str, prediction: int):
        """ Update the prediction data for a given timestamp """
        self.prediction_results[timestamp] = prediction
        if timestamp in self.prediction_results:
            # add to the main data collector
            self.logs[timestamp]['prediction'] = prediction

    def update_notes(self, timestamp: str, notes: str):
        """ Update the notes data for a given timestamp """
        self.notes[timestamp] = notes
        if len(timestamp) == 0:
            return None
        if timestamp in self.notes:
            # add to the main data collector
            self.logs[timestamp]['notes'] = notes

    def update_last_timestamp(self, timestamp: str):
        self.last_timestamp = timestamp

    # def update_side_quest_status(self, new_status: str):
    #     timestamp = self.last_timestamp
    #     if timestamp in self.logs:
    #         self.logs[timestamp]['bad_posture_command'] = new_status

    def update_alarm_notification_status(self, interval: int, status='yes'):
        stamp = self.last_timestamp
        if stamp in self.logs:
            self.logs[stamp]['alarm_notification'] = status
            self.logs[stamp]['notification_interval'] = interval

    def update_user_feedback(self, value: int, timestamp: str):
        """ Value 1 and 0 represents True and False, respectively """
        stamp = timestamp
        if stamp in self.logs:
            self.logs[stamp]['feedback'] = value

    def update_model_threshold(self, value: float, timestamp: str):
        if timestamp in self.logs:
            self.logs[timestamp]['model_threshold'] = value
            note = f"Thresholds changed from {self.last_model_threshold} to {value} at {timestamp} local time."
            self.add_model_notes(note, timestamp)
            self.last_model_threshold = value

    def add_model_notes(self, note: str, timestamp: str):
        self.logs[timestamp]['model_notes'] = note
        print("New Model Notes has been successfully added")

    @staticmethod
    def add_notes(df_collector: pd.DataFrame, marked_data: pd.DataFrame) -> pd.DataFrame:
        if len(marked_data) == 0:
            return df_collector
        columns_to_rename = {"Sensor 2": "sensor_2",
                             "Sensor 4": "sensor_4",
                             "Time": "local_time"}
        merging_columns = ["local_time", "sensor_2", "sensor_4"]
        renamed_notes = marked_data.rename(columns=columns_to_rename)
        print("Marked DF:")
        print(renamed_notes[merging_columns])
        result_df = pd.merge(df_collector, renamed_notes,
                             on=merging_columns,
                             how='left')
        print("Data Collector DF:")
        print(df_collector[merging_columns])
        print("Merged DF: ")
        print(result_df[merging_columns+["Notes"]])
        return result_df

    @staticmethod
    def process_notes_gaps(df: pd.DataFrame) -> pd.DataFrame:
        """ Dataframe has rows where notes are NaN, due to NaN values of Sensor 2 and Sensor 4.
        However, the rows are required to be commented as well.
        Therefore, this function is responsible to fill in the rows with Notes as NaN
        """
        # Check if the "Notes" exists
        col = 'Notes'
        if col not in df.columns:
            print(f"Warning! Column '{col}' does not exists in DataFrame", file=sys.stderr)
            return df
        mask = ~pd.isna(df[col])
        rows_with_notes = df.loc[mask].index
        for row in rows_with_notes:
            df.loc[row-2:row-1, col] = df.loc[row, col]
        return df

    # @staticmethod
    # def process_bad_posture_command_col(df: pd.DataFrame, replace_other_notes: bool) -> pd.DataFrame:
    #     """ Function replace 'no' values in col bad_posture_command by 'yes' between notes, such as:
    #     started and ended, which are also replaced by 'yes' comment
    #     """
    #     col_name = "bad_posture_command"
    #     mask = df[col_name] != 'no'
    #     indexes_with_notes = df.loc[mask].index
    #     for i in range(len(indexes_with_notes)-1):
    #         upper, lower = indexes_with_notes[i+1], indexes_with_notes[i]
    #         note = df.iloc[lower][col_name]
    #         if note == "ended":
    #             # After the command is completed, the note should be by default no
    #             # Do not fill out rows after ended
    #             continue
    #         if note == "appeared":
    #             # Although the command is appeared it does not affect on the readings
    #             # Do not fill out rows after appeared
    #             continue
    #         if note == "started":
    #             note = "yes"
    #         if replace_other_notes:
    #             indexes = [i for i in range(lower, upper+1)]
    #         else:
    #             indexes = [i for i in range(lower+1, upper)]
    #         df.loc[indexes, col_name] = note
    #     result = df
    #     return result

    @staticmethod
    def get_timestamps_by_interval(local_time: str, interval: int) -> list[str]:
        """
        Based on the local_time in the format '2024-07-25 17:12:47'
        and acquire previous local times based on the interval in seconds
        """
        time_format = uc.Measurements.time_format.value
        this_time: datetime.datetime = datetime.datetime.strptime(local_time, time_format)
        start_date = this_time - datetime.timedelta(seconds=interval)
        result = []
        while start_date <= this_time:
            result.append(start_date.strftime(time_format))
            start_date += datetime.timedelta(seconds=1)
        return result

    @staticmethod
    def set_status_by_local_time(df: pd.DataFrame, local_times: list[str],
                                 new_statuses: dict[str, Union[str, int]]) -> pd.DataFrame:
        """ Find the rows by local time and set new statuses by new_statuses.
        new_statues is represented as:
        {col_name: value}
        """
        mask = df['local_time'].isin(local_times)
        indexes = df[mask].index
        for i in indexes:
            for col_name, status in new_statuses.items():
                df.loc[i, col_name] = status
        return df

    @staticmethod
    def process_alarm_notifications(df: pd.DataFrame) -> pd.DataFrame:
        # Tested and works
        is_alarm = df['alarm_notification'] == "yes"
        alarm_indexes: list[int] = df[is_alarm].index
        for i in alarm_indexes:
            time = df.loc[i, 'local_time']
            interval = int(df.loc[i, 'notification_interval'])
            indicated_feedback = df.loc[i, 'feedback']
            timestamps = Logger.get_timestamps_by_interval(time, interval)
            df = Logger.set_status_by_local_time(df, local_times=timestamps,
                                                 new_statuses={"alarm_notification": "yes",
                                                               "notification_interval": interval,
                                                               "feedback": indicated_feedback})
        return df

    @staticmethod
    def save_alarm_texts(path: str, texts: list[str]):
        with open(path, 'w') as file:
            file.writelines(texts)
        print(f"Alarm texts has been saved to {path}")

    @staticmethod
    def process_models_thresholds_gaps(df: pd.DataFrame) -> pd.DataFrame:
        col_name = 'model_threshold'
        mask = ~pd.isna(df[col_name])
        indexes = df[mask].index
        if len(indexes) == 0:
            return df
        print(indexes)
        lower = 0  # start with 0
        for i in range(len(indexes)):
            upper: int = indexes[i]  # determine the limits
            threshold = df.loc[lower, col_name]
            selected_indexes = [i for i in range(lower, upper)]
            df.loc[selected_indexes, col_name] = threshold
            lower = upper
        else:
            # the last threshold is fills out the remaining None values in csv
            lower = indexes[-1]
            upper = df.shape[0]
            threshold = df.loc[lower, col_name]
            selected_indexes = [i for i in range(lower, upper)]
            df.loc[selected_indexes, col_name] = threshold
        return df
