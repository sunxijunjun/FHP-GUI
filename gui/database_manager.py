import pandas as pd
import ui_config
import csv
import datetime
import bcrypt
from typing import Union
from tkinter import filedialog
from pathlib import Path
import re
from data_analyst import DataAnalyst
import random
import matplotlib.pyplot as plt
from pathlib import Path
import os
import re
from tkinter import filedialog, messagebox
from typing import Union
import markdown2
from xhtml2pdf import pisa
import tkinter as tk


class UserDetails:
    # Meta Data
    first_name: str
    last_name: str
    middle_name: str
    password: str
    # Other details
    weight: Union[int, None]
    height: Union[int, None]
    gender: Union[str, None]
    age: Union[int, None]
    shoulder_size: Union[str, None]
    threshold: Union[float, None]
    photo_path: str

    def __init__(self, full_name: str, new_password: str):
        self.parse_full_name(full_name)
        self.photo_path = ui_config.FilePaths.user_photo_icon.value
        self.password = self.check_password(new_password)
        self.weight = None
        self.height = None
        self.gender = None
        self.age = None
        self.shoulder_size = None

    def __repr__(self) -> str:
        representation = f"Received UserDetails:\n" \
                         f"Name:\t\t{self.get_full_name()}\n" \
                         f"Has Photo:\t\t{self.has_photo()}\n" \
                         f"Weight:\t\t{self.weight} (kg)\n" \
                         f"Height:\t\t{self.height} (cm)\n" \
                         f"Shoulder Size:\t\t{self.shoulder_size}\n" \
                         f"Gender:\t\t{self.gender}\n" \
                         f"Age:\t\t{self.age}\n"\
                         f"Threshold:\t\t{self.threshold} (mm)\n"
        return representation
    
    def check_password(self,password: str)-> None:
        if not password:
            raise ValueError("Empty password value detected!")
        else:
            return password

    def parse_full_name(self, name: str) -> None:
        if name == "Unknown":
            self.first_name = name
            self.middle_name = ""
            self.last_name = ""
            return None
        first, *middle, last = name.split()
        # convert array to a single str
        middle = ''.join(middle)
        self.first_name = first
        self.middle_name = self.reformat_mid_name(middle)
        self.last_name = last

    def get_full_name(self) -> str:
        return f"{self.first_name} " \
               f"{self.middle_name} " \
               f"{self.last_name}"

    def has_photo(self) -> bool:
        if self.photo_path == ui_config.FilePaths.user_photo_icon.value:
            return False
        return True

    def get_ordered_data(self) -> list[Union[str, int]]:
        ordered_data = [self.first_name,
                        self.last_name,
                        self.middle_name,
                        self.encrypt_password(self.password),
                        self.photo_path,
                        self.gender,
                        self.age,
                        self.shoulder_size,
                        self.height,
                        self.weight]
        return ordered_data

    def is_valid_password(self, stored_password: str) -> bool:
        stored_password: bytes = stored_password.encode('utf-8')
        this_pw: bytes = self.password.encode('utf-8')
        return bcrypt.checkpw(password=this_pw, hashed_password=stored_password)

    @staticmethod
    def encrypt_password(new_password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def reformat_mid_name(name: Union[str, None]) -> str:
        if name is None:
            return ""
        return name


class SessionInstance:
    id: str
    user_id: int
    alarm_times: list[str]  # the variable stores sequences of alarms timestamps separated by "|"
    marked_data: pd.DataFrame  # list of the of values being commented during observations
    total_alarm_time: float
    user_details: UserDetails
    session_start_time: datetime.datetime
    graph_file_path: str

    def __init__(self):
        self.id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')  # generate unique id
        self.user_id = -1
        self.user_details = self.get_default_details()
        self.alarm_times = ["|"]
        self.session_start_time = datetime.datetime.now()
        self.graph_file_path = self.get_graph_save_path()
        self.total_alarm_time = 0.0
        self.log_file_path = ""
        self.marked_data = pd.DataFrame()

    def update(self, user_id: int, details: UserDetails):
        """ Remember user details when signed in """
        self.user_id = user_id
        self.user_details = details
        self.graph_file_path = self.get_graph_save_path()

    def get_total_alarm_time(self) -> str:
        return DataAnalyst.convert_to_specific_format(self.total_alarm_time)

    def update_total_alarm_time(self, interval: float) -> None:
        self.total_alarm_time += interval

    def get_session_elapsed_time(self) -> str:
        this_time = datetime.datetime.now()
        elapsed_time: datetime.timedelta = this_time - self.session_start_time
        # Convert the elapsed_time to the desired format
        total_seconds = elapsed_time.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        elapsed_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return elapsed_time_str

    def get_total_alarm_num(self) -> int:
        return len(self.alarm_times)

    def get_graph_save_path(self, type = "graph", ask_path = False) -> str:
        if ask_path:
            path = filedialog.asksaveasfilename(filetypes=[("Image Files", ["*.png", "*.jpeg"])])
            if ".png" not in path:
                path += ".png"
            elif ".jpeg" not in path:
                path += ".jpeg"
            return path
        today = datetime.datetime.now()
        file_name = f"{type}_{today.strftime('%Y%m%d%H%M%S')}_{str(self.user_id)}.png"
        base_path = os.path.dirname(os.path.abspath(__file__))
        if type == "graph":
            path = os.path.join(base_path, ui_config.FilePaths.graph_folder_path.value, file_name)
        elif type == "piechart":
            path = os.path.join(base_path, ui_config.FilePaths.piechart_folder_path.value, file_name)
        return os.path.normpath(path)

    def update_marked_data(self, data: pd.DataFrame):
        self.marked_data = pd.concat([self.marked_data, data], ignore_index=True)

    def reset(self):
        """ Reset is used when the user signs out """
        self.user_id = -1
        self.user_details = self.get_default_details()

    def save_notes(self, folder_path):
        """ Save all the notes during the session into a separate file """
        file_name = f"/notes_{self.id}_all.csv"
        path = folder_path + file_name
        self.marked_data.to_csv(path)
        print(f"All User Notes saved at: {path}")

    @staticmethod
    def get_default_details() -> UserDetails:
        return UserDetails(full_name="Unknown", new_password='Default')

    @staticmethod
    def convert_time_format(time_list: list[str]) -> list[str]:
        """
        Convert a list of time strings in the format "%I:%M:%S.%f %p, %d-%m-%y"
        to the format "%I%M%S%d%m%y".

        Args:
            time_list (list): A list of time strings in the format "%I:%M:%S.%f %p, %d-%m-%y".

        Returns:
            list: A list of time strings in the format "%I%M%S%d%m%y".
        """
        converted_times = []
        for time_str in time_list:
            try:
                this_format = ui_config.Measurements.time_format.value
                time_obj = datetime.datetime.strptime(time_str, this_format)
                new_format = ui_config.Measurements.csv_time_format.value
                converted_time_str = time_obj.strftime(new_format)
                converted_times.append(converted_time_str)
            except ValueError:
                print(f"Error converting time string: {time_str}")
                converted_times.append(time_str)
        return converted_times


import matplotlib.pyplot as plt
from pathlib import Path
import os
import re
from tkinter import filedialog
from typing import Union

class ReportWriter:
    path: Union[None, Path]
    session: SessionInstance

    def __init__(self, session: SessionInstance):
        self.session = session
        self.path = None
        # 创建 report pie plot 文件夹
        self.pie_chart_dir = Path(ui_config.FilePaths.piechart_folder_path.value)
        self.pie_chart_dir.mkdir(exist_ok=True)

    def convert_path_to_url(self, path):
        """ Convert a local file path to a URL path """
        path = os.path.abspath(path)
        path = os.path.normpath(path)
        path = path.replace(os.sep, "/")
        path = "file:///" + path.lstrip("/")
        return path

    def get_stats(self) -> str:
        # 获取数据
        elapsed_time_str = self.session.get_session_elapsed_time()  # 假设返回的是 'HH:MM:SS' 格式的字符串

        # 将 'HH:MM:SS' 格式转换为秒数
        elapsed_time = self.convert_time_to_seconds(elapsed_time_str)
        alarm_total_time = self.session.total_alarm_time

        # 计算非警报时间
        non_alarm_time = elapsed_time - alarm_total_time

        # 生成饼图数据
        labels = ['Alarm Duration', 'Monitoring Duration']
        sizes = [alarm_total_time, non_alarm_time]
        colors = ['#ff9999', '#66b3ff']

        # 生成饼图
        plt.figure(figsize=(5, 5))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title("Alarm Time vs Elapsed Time")

        # 保存饼图为图片文件
        pie_chart_path = self.session.get_graph_save_path(type = "piechart")
        plt.savefig(pie_chart_path)
        plt.close()

        # 生成统计文本
        content = f"""## User Details:\n
        | Name | {self.session.user_details.get_full_name()} |
        | --- | --- |
        | Alarm Total Time | {alarm_total_time} seconds |
        | Number of Alarms | {self.session.get_total_alarm_num()} |
        | Elapsed Time | {elapsed_time} seconds |\n
        """

        # 将饼图加入内容
        self.latest_stats = content + f"![Pie Chart]({pie_chart_path})\n"

        # Convert the pie chart path to a URL path
        pie_chart_path = self.convert_path_to_url(pie_chart_path)
        content += f"![Pie Chart]({pie_chart_path})\n"

        return content

    def convert_time_to_seconds(self, time_str: str) -> float:
        """将 'HH:MM:SS' 格式的时间字符串转换为秒数"""
        print(f"Converting time: {time_str}")  # 调试信息
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except ValueError:
            print(f"Invalid time format: {time_str}")
            return 0.0  # 如果格式不正确，返回0或其他默认值

    def get_header(self) -> str:
        content = f"""# User Report\n
        The report represents the basic information over the usage of the app\n
        """

        return content

    def save_report(self, path=None):
        """ The function collect all the data from the app
        and save in the format of .md or .txt
        If the param path is None, the user may have an opportunity to select the destination
        """
        content = self.latest_header + self.latest_stats
        save_path = self.get_path(path)
        save_result = False
        
        try:
            if save_path.suffix.lower() == '.pdf':
                report_content = "\n".join(line.strip() for line in content.splitlines())
                html_content = markdown2.markdown(report_content, extras=["tables", "fenced-code-blocks"])
                html_content = html_content.replace('<h1>', '<h1 style="font-size: 175%; text-align: center;">')
                html_content = html_content.replace('<img ', '<img style="width: 350px; height: auto;" ')
                html_content = html_content.replace('<th>', '<th style="padding: 8px; text-align: left;">')
                html_content = html_content.replace('<td>', '<td style="padding: 8px; text-align: left">')
                # Convert HTML to PDF
                with open(save_path, "wb") as pdf_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
                
                save_result = not pisa_status.err
            else:
                content = re.sub(r'\n\s+', '\n', content)
                with open(save_path, "w", encoding="utf-8") as file:
                    file.write(content)
                save_result = True
        finally:
            if save_result:
                tk.messagebox.showinfo("Report Saved", f"Report saved at: {save_path}")
            else:
                tk.messagebox.showerror("Report Save Error", f"Failing to save the report. Please try again.")
        

    def get_path(self, path: Union[None, str]) -> Path:
        if path is not None:
            self.path = Path(path)
            return self.path
        new_path = filedialog.asksaveasfilename(filetypes=[("PDF Files", ".pdf")])        
        self.path = Path(new_path)
        if not self.path.suffix:
            self.path = self.path.with_suffix(".pdf")
        return self.path



class DatabaseManager:
    """
    Storage and reading the data in csv format
    using pandas
    """
    users_login_path: str
    values_folder: str
    session: SessionInstance
    report_writer: ReportWriter

    def __init__(self):
        self.users_login_path = ui_config.FilePaths.user_login_db_path.value
        self.values_folder = ui_config.FilePaths.values_folder_path.value
        """ Store other object instances """
        self.session = SessionInstance()
        self.report_writer = ReportWriter(session=self.session)

    def get_user_db(self) -> pd.DataFrame:
        """ The method checks for the existence of the file
        and creates an empty file with proper column names
        if no file exists
        """
        try:
            return pd.read_csv(self.users_login_path)
        except:
            users_login_db_headers: list[str] = ui_config.ElementNames.user_login_db_headers.value
            with open(self.users_login_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(users_login_db_headers)
            print("Empty user login csv file has been created")
            return pd.read_csv(self.users_login_path)

    def find_user_in_db(self, details: UserDetails) -> pd.DataFrame:
        df = self.get_user_db()
        df = df.fillna("")
        if df.shape[0] == 0:
            return df  # return an empty df
        df_condition = (df["First Name"] == details.first_name) \
                        & (df["Second Name"] == details.last_name) \
                        & (df["Middle Name"] == details.middle_name)
        df = df[df_condition]
        print(df)
        return df  # return sorted df

    def is_valid_sign_in(self, details: UserDetails) -> bool:
        """ The function determines whether entered details are correct and add them into one session instance """
        df_user = self.find_user_in_db(details)
        if df_user.shape[0] == 0 or not details.is_valid_password(df_user["Password"].iloc[0]):
            return False
        # Get other details
        details.photo_path = df_user["Photo Path"].iloc[0]
        details.gender = df_user["Gender"].iloc[0]
        details.age = df_user["Age"].iloc[0]
        details.shoulder_size = df_user["Shoulder Size"].iloc[0]
        details.height = df_user["Height"].iloc[0]
        details.weight = df_user["Weight"].iloc[0]
        details.threshold = df_user["Threshold"].iloc[0]
        print("==== User below has signed in ====")
        print(details)
        self.session.update(df_user.index[0],
                            details)
        return True

    def save_user(self, details: UserDetails) -> bool:
        """ The function returns bool to determine completion of the process
        True if the data has been successfully added
        False if the data is already stored in the db
        """
        data_entity = details.get_ordered_data()
        if self.find_user_in_db(details).shape[0] > 0:
            return False  # details already exists

        with open(self.users_login_path, "a", newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(data_entity)
        return True  # details have been saved

    def save_data(self) -> dict[str, str]:
        """
        The function saves:
            1. Report
            2. Logs
            3. Graph
        Returns:
            1. Report path file
            2. Logger path file
            3. Graph path file
        as a tuple
        """
        today = datetime.datetime.now()
        file_name = f"/report_{today.strftime('%Y%m%d%H%M%S')}.md"
        report_path = ui_config.FilePaths.reports_folder_path.value + file_name
        self.report_writer.save_report(path=report_path)
        paths = {"report_path": report_path,
                 "graph_path": self.session.graph_file_path}
        return paths

    def get_user_photo_path(self, relative_path=False) -> str:
        if not relative_path:
            details: UserDetails = self.session.user_details
            if details is None:
                return ""
            return details.photo_path

    def modify_user_info(self, field: str, new_value: str):
        user_id: int = self.session.user_id
        df: pd.DataFrame = self.get_user_db()
        # df[field] = df[field].astype(str)
        df.loc[user_id, field] = new_value
        df.to_csv(self.users_login_path, index=False)

    @staticmethod
    def hide_columns(data: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        # Create a new DataFrame with the selected columns hidden
        hidden_df = data.copy()
        hidden_df = hidden_df.drop(cols, axis=1)
        return hidden_df
