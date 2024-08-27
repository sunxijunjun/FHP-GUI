import datetime
from data_analyst import DataAnalyst
import sys
import ui_config as uc
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes
import numpy as np
from typing import Union
import pandas as pd
import os


class PerformanceTester:
    """ The object is needed to assess how fast certain operation is processed """

    init_time: datetime.datetime
    finish_time: datetime.datetime
    is_critical_file: bool
    processing_times: list[str]
    func_name = ''
    folder_path = uc.FilePaths.values_folder_path.value
    path = folder_path + '/system_performance_report_1.csv'

    def __init__(self, critical_file=True):
        self.init_time = datetime.datetime.now()
        self.finish_time = self.init_time
        self.is_critical_file = critical_file
        self.processing_times = []
        self.func_name = ''

    def start(self) -> None:
        self.init_time = datetime.datetime.now()

    def end(self) -> None:
        self.finish_time = datetime.datetime.now()
        self.processing_times.append(self.get_time_diff())  # remember all the speeds

    def get_time_diff(self) -> str:
        time_diff: datetime.timedelta = self.finish_time - self.init_time
        seconds: float = time_diff.total_seconds()
        return DataAnalyst.convert_to_specific_format(seconds)

    @staticmethod
    def get_this_timestamp() -> str:
        return datetime.datetime.now().strftime(uc.Measurements.time_format.value + ":%f")[:-3]

    def show_time_summary(self, notes=None, function_name=None, critical=False) -> None:
        """ Show the summary of timing the functions
        If the function critical for while loop, then the text will be highlighted in red
        """
        content = f"Processing time: {self.get_time_diff()}\n"
        if function_name:
            content += f"Function name: {function_name}\n"
            self.update_func_name(new_name=function_name)
        if notes:
            content += f"Additional Notes: {notes}\n"
        if critical or self.is_critical_file:
            print(content, file=sys.stderr)
            return None
        print(content)

    def update_func_name(self, new_name: str):
        self.func_name = new_name

    def show_all_data(self, data_lim: Union[None, int]):
        ms = [int(processing_time.split(':')[-2] + processing_time.split(':')[-1]) for processing_time in
              self.processing_times]
        if data_lim:
            ms = ms[:data_lim]
        mean_processing_time = np.mean(ms)
        std_processing_time = np.std(ms)
        print(f"Mean time diff: {mean_processing_time} ms")
        print(f"Std time diff: {std_processing_time} ms")
        self.show_graph(values=ms, mean=mean_processing_time)

    def show_graph(self, values: list[int], mean=None):
        mean_vals = [mean for _ in range(len(values))]
        plt.plot(values, label='Time Diff')
        plt.plot(mean_vals, label='Mean')
        plt.legend()
        plt.ylabel('Milliseconds')
        plt.xlabel('Indexes')
        plt.title(f'Performance of {self.func_name}')
        plt.show()

    def save_report(self):
        if self.is_report_exists(self.path):
            report = pd.read_csv(self.path, index_col=False)
        else:
            report = pd.DataFrame()
        report[self.func_name] = pd.Series(data=self.processing_times)
        report.to_csv(self.path, index=False)

    @staticmethod
    def is_report_exists(path: str) -> bool:
        return os.path.exists(path)

    def show_all_results(self) -> None:
        # Get the previous report
        report = pd.read_csv(self.path)
        titles: list[str] = report.columns
        subplots_num = len(titles)
        fig, axes = plt.subplots(subplots_num)
        for i, title in enumerate(titles):
            y: list[str] = report[title].to_list()
            y_ms: list[int] = [int(time.split(':')[-2] + time.split(':')[-1]) if type(time) == str else 0 for time in y]
            if subplots_num > 1:
                subplot: Axes = axes[i-1]
            else:
                subplot = axes
            subplot.plot(y_ms, label='Performance')
            subplot.set_title(title)
            # get mean
            mean_val = np.mean(y_ms)
            y_mean = [mean_val for _ in range(len(y_ms))]
            subplot.plot(y_mean, label='Mean')
            subplot.set_ylabel('Time (ms)')
            subplot.set_xlabel('Num of Calls')
            subplot.legend()
        plt.show()
