import random

import serial
from sound_controller import SoundControllerApp
from light_controller import LightControllerApp
from serial_manager import SerialManager
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkbt
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from tkinter import filedialog
from ttkthemes import ThemedTk
from typing import Callable, Union
import matplotlib.collections
import datetime
import ui_config as uc
from database_manager import DatabaseManager, UserDetails
from data_analyst import DataAnalyst
from custom_widgets import (Clock,
                            TkCustomImage,
                            UserDetailsWindow,
                            FileUploadWindow,
                            UserRegistrationWindow,
                            NotesEntryFrame,
                            GraphScrollBar,
                            TimeIntervalSelectorFrame,
                            CheckBoxesFrame,
                            NotificationIncorrectPosture,
                            NotificationSuccessSave,
                            ErrorNotification,
                            # RandomSideQuestNotification,
                            # XRangeSelectorFrame,
                            FeedbackCollector,
                            Graph)
from dynamic_labelling import flex_median_g
from log_integration import save_integrated_csv
from logger import Logger
from reminder22 import TimerApp
from performance_tester import PerformanceTester
import numpy as np
import os
import pandas as pd
import sys
import time
from tensorflow.keras.models import load_model


class App(ThemedTk):
    def __init__(self, title: str, fullscreen=False, test=False):
        super().__init__()
        self.theme = uc.main_theme
        self.set_theme(theme_name="adapta")
        self.configure(background=uc.FrameColors.body.value)
        self.is_test_mode = test
        self.p_tester = PerformanceTester(critical_file=True)
        self.title(title)
        self.attributes("-fullscreen", fullscreen)
        self.geometry(uc.Measurements.window_size.value)

        # 创建一个 ttk.Style 实例
        style = ttkbt.Style('flatly')

        # 配置颜色样式之 白底荧光绿
        style.configure('TFrame', background='#E8F4F8')
        style.configure('TLabel', background='#E8F4F8', foreground='#2ECC71')
        style.configure('TButton', background='#D1F2EB', foreground='#2ECC71')

        # 配置颜色样式之 浅蓝活力橙
        # style.configure('TFrame', background='#E3F2FD')
        # style.configure('TLabel', background='#BBDEFB', foreground='#FF5722')
        # style.configure('TButton', background='#90CAF9', foreground='#FF5722')
        # 配置颜色样式之 粉红色
        # style.configure('TFrame', background='#FDFDFD')
        # style.configure('TLabel', background='#F5F5F5', foreground='#FF1744')
        # style.configure('TButton', background='#FFEBEE', foreground='#FF1744')

        # 初始化串口管理器
        self.serial_manager = SerialManager()

        # 创建各个框架和UI元素
        self.sensor_values = dict()
        self.sensor_time = list()
        self.alarm_texts = list()
        self.elapsed_time = list()
        self.alarm_num = 0
        self.button_num = 0
        self.menu_button_num = 0
        self.is_stopped = False
        self.is_paused = False
        self.user_data = None
        self.info_panel_wnum = 0
        self.prev_alarm_pos = 0
        self.val_replacing_num = 0
        self.false_responses_limit = uc.Measurements.false_responses_limit.value
        self.x_range = uc.Measurements.graph_x_limit.value
        self.dist_max = uc.Measurements.distance_max.value
        self.dist_min = uc.Measurements.distance_min.value
        self.bpc_popup_times = []

        self.header_row = 0
        self.header_frame = ttk.Frame(self)
        self.body_row = 1
        self.body_frame = ttk.Frame(self)
        self.footer_row = 2
        self.footer_frame = ttk.Frame(self)
        self.db_manager = DatabaseManager()
        self.logger = Logger(session_id=self.db_manager.session.id, test=test)
        self.data_analyst = DataAnalyst()

        self.info_panel = ttk.Frame(self.body_frame)
        self.info_panel.grid(row=self.body_row, column=0, padx=10, pady=5)

        self.alarm_num_label = None
        self.alarm_text_label = None
        self.notification_frame = None
        self.error_notify_frame = None
        self.log_notification_frame = None

        self.graph_scroll_bar = None
        self.scroll_bar_frame = None

        self.note_frame = None
        self.control_frame = None

        self.user_photo = None
        self.user_name = None

        self.sign_in_popup = None
        self.registration_popup = None
        self.edit_photo_popup = None

        self.rand_quest_notification = None
        self.control_buttons = dict()

        # 初始化主UI
        self.create_major_frames()
        self.add_header_elements(title=uc.ElementNames.app_title.value)
        self.graph = self.create_graph()
        self.create_control_frame()

        # 初始化自定义框架和其他组件
        self.time_interval_frame = TimeIntervalSelectorFrame(self.control_frame,
                                                             row=0,
                                                             col=1,
                                                             txt="Pause For (MM:SS):",
                                                             func=self.pause_for)
        self.check_boxes_frame = CheckBoxesFrame(self.control_frame,
                                                 row=1,
                                                 col=1)

        # 使用CheckBoxesFrame中的enable_sound_var
        enable_sound_var = self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_sound.value][1]
        # 初始化 SoundControllerApp
        self.sound_controller = SoundControllerApp(enable_sound_var=enable_sound_var,
                                                   serial_manager=self.serial_manager)

        # 使用 CheckBoxesFrame 中的 enable_light_var
        enable_light_var = self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_light.value][1]
        # 初始化 LightControllerApp
        self.light_controller = LightControllerApp(light_control_var=enable_light_var,
                                                   serial_manager=self.serial_manager)

        self.model = load_model(uc.FilePaths.model_path.value)
        self.current_user_id = None
        self.current_user_features = None
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_path, 'data', 'users', 'logins.csv')
        self.sensor_values = {"Sensor 2": [], "Sensor 4": []}
        self.alarm_text_file_path = self.get_alarm_logger_path()
        self.feedback_collector = None

        # 添加设置按钮
        self.add_setting_button()
        self.add_guide_button()

        # 需要用户登录后才能进行数据采集
        if not test:
            self.after(500, func=self.show_sign_in_popup)

    def add_guide_button(self):
        self.add_menu_button("User Guide", self.show_user_guide_window)

    def show_user_guide_window(self):
        guide_window = tk.Toplevel(self)
        guide_window.title("User Guide")
        guide_window.geometry("350x500")  # 调整窗口大小

        # 多语言文本字典
        guide_texts = {
            "English": (
                "Welcome to the Beta Prototype. \n\n"
                "This device will help detect poor posture while you are using a computer.\n\n"
                "To achieve optimal accuracy, please follow "
                "the calibration steps below:\n\n"
                "1. Please take a seat.\n\n"
                "2. Adjust the height of your chair and screen so that the top edge of the screen "
                "is at or slightly below your eye level.\n\n"
                "3. Position the device in the center of your screen. \n\n"
                "You should see your face appear "
                "in the center of the camera view with a small green frame around it."
            ),
            "中文": (
                "欢迎使用Beta原型。\n\n"
                "此设备将帮助您在使用计算机时检测不良姿势。\n\n"
                "为了达到最佳准确性，请按照以下校准步骤操作：\n\n"
                "1. 请坐下。\n\n"
                "2. 调整椅子和屏幕的高度，使屏幕的上边缘位于或略低于您的眼睛水平。\n\n"
                "3. 将设备放置在屏幕的中心。\n\n"
                "您应该看到您的脸出现在相机视图的中心，并且周围有一个小的绿色框。"
            ),
            "粤语": (
                "歡迎使用Beta原型。\n\n"
                "此設備將幫助您在使用計算機時檢測不良姿勢。\n\n"
                "為了達到最佳準確性，請按照以下校準步驟操作：\n\n"
                "1. 請坐下。\n\n"
                "2. 調整椅子和屏幕的高度，使屏幕的上邊緣位於或略低於您的眼睛水平。\n\n"
                "3. 將設備放置在屏幕的中心。\n\n"
                "您應該看到您的臉出現在相機視圖的中心，並且周圍有一個小的綠色框。"
            )
        }

        # 默认显示的语言是英语
        guide_label = tk.Label(guide_window, text=guide_texts["English"], font=("Arial", 12), justify="left",
                               wraplength=300)
        guide_label.pack(pady=20)

        # 选择语言的下拉菜单
        def update_language(event):
            selected_language = language_combobox.get()
            guide_label.config(text=guide_texts[selected_language])

        language_combobox = ttk.Combobox(guide_window, values=["English", "中文", "粤语"])
        language_combobox.current(0)  # 默认选择英语
        language_combobox.bind("<<ComboboxSelected>>", update_language)
        language_combobox.pack(pady=10)

        # 关闭按钮
        close_button = ttk.Button(guide_window, text="Close", command=guide_window.destroy)
        close_button.pack(pady=10)


    # 在App类中添加设置按钮
    def add_setting_button(self):
        self.add_menu_button("Settings", self.show_settings_window)

    # 显示设置窗口的方法
    def show_settings_window(self):
        self.pause()
        settings_popup = tk.Toplevel(self)
        settings_popup.title("Settings")
        settings_popup.geometry("300x300")

        # 设置布局
        settings_popup.columnconfigure(0, weight=1)
        settings_popup.rowconfigure([0, 1, 2, 3, 4], weight=1)  # 小窗口行数

        # 声音控制
        sound_label = ttk.Label(settings_popup, text="Enable Sound")
        sound_label.grid(row=0, column=0, pady=(20, 5), padx=1, sticky="w")
        # 直接使用原始的 enable_sound_var
        sound_check = ttk.Checkbutton(settings_popup,
                                      variable=self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_sound.value][
                                          1],
                                      command=lambda: self.toggle_feature("sound"))
        sound_check.grid(row=0, column=1, pady=5, padx=1, sticky="w")

        # 灯光控制
        light_label = ttk.Label(settings_popup, text="Enable Light")
        light_label.grid(row=2, column=0, pady=(20, 5), padx=1, sticky="w")
        # 直接使用原始的 enable_light_var
        light_check = ttk.Checkbutton(settings_popup,
                                      variable=self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_light.value][
                                          1],
                                      command=lambda: self.toggle_feature("light"))
        light_check.grid(row=2, column=1, pady=5, padx=1, sticky="w")


        # 错误通知控制
        error_notify_label = ttk.Label(settings_popup, text="Notify Bad Posture After")
        error_notify_label.grid(row=3, column=0, pady=(20, 5), padx=1, sticky="w")

        error_notify_input = self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.notification_bad_posture.value][2]
        if error_notify_input:
            error_notify_input.grid(row=3, column=1, pady=5, padx=1, sticky="w")

        # 创建 Save 按钮
        save_button = ttk.Button(settings_popup, text="Save", command=lambda: None)
        save_button.grid(row=4, column=0, pady=5, padx=(10, 5), sticky="n")

        # 创建 Close 按钮
        close_button = ttk.Button(settings_popup, text="Close", command=settings_popup.destroy)
        close_button.grid(row=4, column=1, pady=5, padx=(5, 10), sticky="n")

        self.resume()

    def toggle_feature(self, feature_type):
        if feature_type == "sound":
            if self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_sound.value][1].get():
                print("Sound enabled")
            else:
                print("Sound disabled")
        elif feature_type == "light":
            if self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_light.value][1].get():
                print("Light enabled")
            else:
                print("Light disabled")

    def forget_feedback_collector(self):
        if self.feedback_collector:
            self.feedback_collector.destroy()
            self.feedback_collector = None
        notification_frame = NotificationSuccessSave(self.footer_frame, subject="Feedback Saved!")
        notification_frame.show(x=0, y=4, callback=notification_frame.destroy)
        self.resume()

    def create_major_frames(self):
        self.header_frame.pack(fill='both', expand=False)
        self.body_frame.pack(fill='both', expand=True)
        self.footer_frame.pack(fill='both', expand=True)
        # Set styles
        self.header_frame.config(height=uc.Measurements.header_h.value)
        self.body_frame.config(height=uc.Measurements.body_h.value)
        self.footer_frame.config(height=uc.Measurements.footer_h.value)

    def add_header_elements(self, title: str):
        self.create_header_title(title)
        self.create_default_user_icon()

    def create_header_title(self, title: str):
        # Create header components
        title_label = ttk.Label(self.header_frame, text=title, font=("Helvetica", 24))
        title_label.grid(row=self.header_row, column=0, padx=10, pady=10)

    def create_default_user_icon(self):
        image_path: str = uc.FilePaths.user_photo_icon.value
        photo_w: int = uc.Measurements.photo_w.value
        photo_h: int = uc.Measurements.photo_h.value
        user_photo = TkCustomImage(file_path=image_path,
                                   w=photo_w,
                                   h=photo_h)
        img_label: ttk.Label = user_photo.attach_image(master=self.header_frame,
                                                       row=self.body_row,
                                                       col=0)
        img_label.configure(image=user_photo.tk_image)
        img_label.image = user_photo.tk_image
        self.user_photo = img_label

    def add_user_name_label(self, name: str, master: ttk.Frame, row: int, col: int):
        label = ttk.Label(master, text=name)
        label.grid(row=row, column=col, padx=5, pady=5)
        self.user_name = label

    def run_app(self) -> None:
        self.mainloop()

    def scrollbar_update(self, lr: int, ur: int):
        for i, sensor_name in enumerate(self.sensor_values.keys()):
            x, y = self.data_analyst.get_axes_values(self.sensor_values,
                                                     self.elapsed_time,
                                                     sensor=sensor_name,
                                                     upper_limit=ur,
                                                     lower_limit=lr)
            self.graph.ax.plot(x, y, label=sensor_name)
            self.graph.ax.set_xlim(x[0], x[-1])
            self.graph.lines[i].set_data(list(range(len(y))), y)

    def default_update(self, lr: Union[None, int], ur: Union[None, int]):
        # Local flags
        anomaly_detected = False
        anomaly_graph_position = None
        for i, sensor_name in enumerate(self.sensor_values.keys()):
            x, y = self.data_analyst.get_axes_values(self.sensor_values,
                                                     self.elapsed_time,
                                                     sensor_name,
                                                     upper_limit=ur,
                                                     lower_limit=lr)
            self.graph.ax.plot(x, y, label=sensor_name)
            self.graph.lines[i].set_data(list(range(len(y))), y)
            if x[0] != x[-1]:
                self.graph.ax.set_xlim(x[0], x[-1])

        if self.is_test_mode:
            prediction = self.data_analyst.detect_anomaly_test(data=self.sensor_values)
        else:
            prediction = self.data_analyst.detect_anomaly(data=self.sensor_values,
                                                          user_features=self.current_user_features,
                                                          model=self.model)
        if self.logger.last_timestamp != "":
            self.logger.update_prediction(timestamp=self.logger.last_timestamp, prediction=prediction)
        print("Prediction: ", prediction)
        if prediction == 0:
            anomaly_detected = True
            anomaly_graph_position = len(self.sensor_values['Sensor 2']) - 1

        for collection in self.graph.ax.collections:
            if isinstance(collection, matplotlib.collections.PolyCollection):
                collection.remove()
        if anomaly_detected:
            self.show_alarm(pos=anomaly_graph_position)
            print("Alarm raised.")
        else:
            self.db_manager.session.alarm_times.append("|")

    def update_graph(self, event=None, lower_range=None, upper_range=None):
        # Prepare the graph
        self.graph.ax.clear()
        self.graph.ax.set_ylim(self.dist_min, self.dist_max)

        # Plot new values
        if upper_range is None:
            upper_range = self.x_range
        if lower_range is not None and upper_range is not None:
            self.scrollbar_update(lr=lower_range, ur=upper_range)
            self.graph.redraw_vert_spans(visible_range=None)
        else:
            self.default_update(lr=lower_range, ur=upper_range)
            self.graph.redraw_vert_spans(visible_range=self.x_range)
        # Add annotations
        self.graph.ax.legend()
        self.graph.canvas.draw()

    def validate_sens_values(self, sens_2: int, sens_4: int, values: dict) -> tuple[int, int]:
        notes = ""
        is_valid = True
        if np.isnan(sens_2) or np.isnan(sens_4):
            return sens_2, sens_4
        if sens_2 > self.dist_max:
            is_valid = False
            self.val_replacing_num += 1
            if len(values["Sensor 2"]) > 1:
                sens_2 = values["Sensor 2"][-1]  # get the last
                notes += "Sensor 2 val replaced by previous valid val "
            else:
                sens_2 = self.dist_max
                notes += "Sensor 2 val replaced by max valid val "
        if sens_4 > self.dist_max:
            is_valid = False
            self.val_replacing_num += 1
            if len(values["Sensor 4"]) > 1:
                sens_4 = values["Sensor 4"][-1]
                notes += "Sensor 4 val replaced by previous valid val "
            else:
                sens_4 = self.dist_max
                notes += "Sensor 4 val replaced by max valid val "
        if is_valid:
            self.val_replacing_num = 0  # reset
            self.remove_error_notification()
        self.logger.update_notes(timestamp=self.logger.last_timestamp, notes=notes)
        if not self.error_notify_frame \
                and not is_valid \
                and self.val_replacing_num >= uc.Measurements.val_replacing_limit.value:
            self.error_notify_frame = ErrorNotification(self.footer_frame,
                                                        error_message="Sensor cannot detect distance to participant!\n"
                                                                      "Please adjust the posture or sensor!")
            self.error_notify_frame.show(x=uc.Positions.vals_validation.value[0],
                                         y=uc.Positions.vals_validation.value[1],
                                         callback=None)  # keep the notification
        return sens_2, sens_4

    def update_sensor_values(self, sens_2: int, sens_4: int, local_time: str) -> None:
        if pd.isna(sens_2) or pd.isna(sens_4):
            return None
        values = self.sensor_values
        values["Sensor 2"].append(sens_2)
        values["Sensor 4"].append(sens_4)
        self.sensor_values = values
        self.sensor_time.append((local_time, self.db_manager.session.user_id))
        self.elapsed_time.append(self.p_tester.get_this_timestamp().split(' ')[-1])
        self.p_tester.start()
        self.update_graph()
        self.p_tester.end()
        self.p_tester.show_time_summary(function_name=f"update_graph() with updated redrawing function",
                                        notes="Line 327 at app_ui.py", critical=True)
        # rand_moment = random.randint(self.bpc_lr,
        #                              self.bpc_hr)
        # if self.is_bad_posture_command_allowed(next_time_call=rand_moment):
        #     self.bpc_popup_times.append(rand_moment)
        #     self.bpc_lr = rand_moment
        #     self.after(rand_moment, self.show_rand_quest)
        #     self.bad_posture_comm_limit -= 1
        #     print("Next time call: ", rand_moment)
        #     print(f"Random Side Quest will be displayed after {rand_moment / 1000} seconds.\n"
        #           f"Number of side quests left: {self.bad_posture_comm_limit}")

    def show_notify_log_success(self, subject: str) -> None:
        if self.log_notification_frame:
            if not self.log_notification_frame:
                return None
            self.log_notification_frame.destroy()
            self.log_notification_frame = None
        self.log_notification_frame = NotificationSuccessSave(self.footer_frame, subject=subject)
        # reduce size of the notification frame
        self.log_notification_frame.content.config(height=2)
        self.log_notification_frame.show(x=uc.Positions.log_success.value[0],
                                         y=uc.Positions.log_success.value[1],
                                         callback=self.remove_log_notification)

    def forget_side_quest(self):
        self.rand_quest_notification = None

    def show_alarm(self, pos: int) -> None:
        if not self.alarm_num_label or not self.graph.ax or pos == self.prev_alarm_pos:
            return None
        self.alarm_num += 1
        self.alarm_num_label.config(text=str(self.alarm_num))
        self.graph.draw_vert_span(x=pos)
        self.prev_alarm_pos = pos
        self.add_alarm_text()
        this_time = datetime.datetime.now().strftime(uc.Measurements.time_format.value)
        self.db_manager.session.alarm_times.append(this_time)
        # Show alarm notification
        interval = self.data_analyst.get_time_interval(self.db_manager.session.alarm_times)
        self.db_manager.session.update_total_alarm_time(interval)
        if not self.is_bad_posture_notification_required(interval):
            return None
        self.notification_frame = NotificationIncorrectPosture(self.footer_frame,
                                                               interval=interval)
        self.notification_frame.show(x=uc.Positions.incorrect_posture.value[0],
                                     y=uc.Positions.incorrect_posture.value[1],
                                     callback=self.remove_notification)
        self.graph.canvas.draw()
        self.db_manager.session.alarm_times.append('|')
        self.logger.update_alarm_notification_status(interval=int(interval))
        if not (self.feedback_collector is None):
            self.feedback_collector.destroy()  # update the feedback collector
            self.feedback_collector = None
        self.pause()  # give time for the participant to response
        self.feedback_collector = FeedbackCollector(self.footer_frame, logger=self.logger,
                                                    closing_callback=self.forget_feedback_collector,
                                                    response_callback=self.update_model_thresholds)
        self.feedback_collector.show(x=uc.Positions.feedback.value[0],
                                     y=uc.Positions.feedback.value[1],
                                     timestamp=self.logger.last_timestamp,
                                     local_time=self.logger.get_last_local_time(),
                                     x_position=pos)

    def update_model_thresholds(self, response: bool) -> None:
        if response is True:
            self.reset_false_response_limit()
            return None
        self.false_responses_limit -= 1
        if self.false_responses_limit != 0:
            return None

        if self.current_user_features is None:
            print("No user features are available", file=sys.stderr)
            return None
        size: int = self.current_user_features[1]
        increment: float = uc.Measurements.threshold_increment.value
        self.data_analyst.update_threshold(shoulder_size=size,
                                           increment=increment)
        self.logger.update_model_threshold(value=self.data_analyst.get_threshold(size),
                                           timestamp=self.logger.last_timestamp)
        self.reset_false_response_limit()
        print(f"New threshold for shoulder size {size} has been set")
        print(self.data_analyst.thresholds)

    def reset_false_response_limit(self):
        self.false_responses_limit = uc.Measurements.false_responses_limit.value

    def is_bad_posture_notification_required(self, interval: float) -> bool:
        key = uc.CheckBoxesKeys.notification_bad_posture.value
        required_time: float = float(self.check_boxes_frame.get_input_value(key))
        return ((self.check_boxes_frame.is_true(access_key=key) and interval >= required_time)
                and not self.notification_frame)

    # def is_bad_posture_command_allowed(self, next_time_call: int) -> bool:
    #     key = uc.CheckBoxesKeys.rand_bad_posture_command.value
    #     # Analyze if the next popup will not override the existing one
    #     user_allowed = self.check_boxes_frame.is_true(access_key=key)
    #     enough_quotes = self.bad_posture_comm_limit > 0
    #     no_quest_given = self.rand_quest_notification is None
    #     not_overlapping = True
    #     if len(self.bpc_popup_times) > 0:
    #         required_time_call = self.bpc_popup_times[-1] + uc.Measurements.rand_quest_duration.value[1]*1000 + uc.Measurements.time_offset.value
    #         not_overlapping = next_time_call > required_time_call
    #     if not_overlapping is False and len(self.bpc_popup_times) >= 2:
    #         # Get the first two elements
    #         first_two = self.bpc_popup_times[:2]
    #
    #         # Delete the first two elements from the list
    #         del self.bpc_popup_times[:2]
    #         # Set new boundaries for random moment
    #         self.bpc_lr = first_two[0]
    #         self.bpc_hr = first_two[1]
    #     return user_allowed and enough_quotes and no_quest_given and not_overlapping

    def remove_notification(self) -> None:
        if not self.notification_frame:
            return None
        self.notification_frame.destroy()
        self.notification_frame = None

    def remove_log_notification(self) -> None:
        if not self.log_notification_frame:
            return None
        self.log_notification_frame.destroy()
        self.notification_frame = None

    def remove_error_notification(self) -> None:
        if not self.error_notify_frame:
            return None
        self.error_notify_frame.destroy()
        self.error_notify_frame = None

    def add_alarm_text(self) -> None:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alarm_text = f"Alarm {self.alarm_num} at {current_time}\n"
        self.alarm_text_label.config(text=alarm_text)
        self.alarm_num += 1
        self.alarm_texts.append(alarm_text)

    def create_control_frame(self) -> None:
        frame = ttk.Frame(self.body_frame)
        frame.grid(row=self.body_row, column=2, padx=10, pady=5)
        self.control_frame = frame  # save the frame

    def create_graph(self) -> Graph:
        # Refactored graph
        graph = Graph(self.body_frame, row=self.body_row, col=1, values=self.sensor_values, times=self.elapsed_time)
        alarm_frame = ttk.LabelFrame(graph.frame, text="Alarm Time")
        alarm_frame.pack(side=tk.BOTTOM, fill="x", pady=10)
        self.alarm_text_label = ttk.Label(alarm_frame, text="", font=("Helvetica", 12))
        self.alarm_text_label.pack(side=tk.LEFT, padx=10)
        return graph

    # def save_selected_data_notes(self) -> None:
    #     data_dict = self.get_selected_values()
    #     print("SELECTED DATA: ", file=sys.stderr)
    #     print(data_dict)
    #     if data_dict is None:
    #         return None
    #     max_length = len(data_dict[uc.ElementNames.sensor_names.value[0]])
    #     # Add Notes to all values
    #     notes: str = self.note_frame.get_notes()
    #     data_dict["Notes"] = [notes for _ in range(max_length)]
    #
    #     # Ensure all lists in data_dict are of the same length by padding with NaN
    #     for key in data_dict:
    #         while len(data_dict[key]) < max_length:
    #             data_dict[key].append(np.nan)
    #
    #     result_df = pd.DataFrame(data_dict)
    #     self.db_manager.session.update_marked_data(data=result_df)
    #     self.remove_note_frame()
    #     self.remove_graph_scrollbar()
    #     if self.notification_frame:
    #         self.remove_notification()
    #     self.notification_frame = NotificationSuccessSave(self.footer_frame, subject="New Notes")
    #     self.notification_frame.show(x=0, y=0, callback=self.remove_notification)
    #     self.resume()

    # def get_selected_values(self) -> Union[None, dict[str, list[Union[str, int, float]]]]:
    #     """ Get the values selected by the user in the format:
    #     {Sensor 1: [x1, x2, x3],
    #     Sensor N: [x1, x2, x3],
    #     Time: [str, str, str]
    #     }
    #
    #     Notes:
    #         Each time is positioned respectively to the position of sensor data
    #         Time has a format mentioned in the UI Config file
    #     """
    #     start, end = self.graph.selected_span
    #     # Round indexes
    #     start, end = round(start), round(end)
    #     print(f"Selected span: {start} to {end} (both limits inclusive)")
    #     data_dict = {'Time': []}
    #     if self.graph.selected_span is None or start == end:
    #         print("No data selected", file=sys.stderr)
    #         if self.error_notify_frame:
    #             self.remove_error_notification()
    #         # Add new notification
    #         self.error_notify_frame = ErrorNotification(self.footer_frame,
    #                                                     error_message="Sensor data are not selected. "
    #                                                                   "Please select range of values on graph and"
    #                                                                   "try again")
    #         self.error_notify_frame.show(x=uc.Positions.vals_validation.value[0],
    #                                      y=uc.Positions.vals_validation.value[1],
    #                                      callback=self.remove_error_notification)
    #         return None
    #     # Find the values between selected index window [start, end]
    #     sensor_names = uc.ElementNames.sensor_names.value
    #     data_dict[sensor_names[0]] = self.data_analyst.get_axes_values(sensor_values=self.sensor_values,
    #                                                                    sensor_timestamps=self.elapsed_time,
    #                                                                    sensor=sensor_names[0],
    #                                                                    upper_limit=end+1,
    #                                                                    lower_limit=start)[1]
    #     data_dict[sensor_names[1]] = self.data_analyst.get_axes_values(sensor_values=self.sensor_values,
    #                                                                    sensor_timestamps=self.elapsed_time,
    #                                                                    sensor=sensor_names[1],
    #                                                                    upper_limit=end+1,
    #                                                                    lower_limit=start)[1]
    #     # Get time by the indexes of selected values
    #     timestamps = []
    #     sensor_name = sensor_names[0]
    #     selected_values = data_dict[sensor_name]
    #     stored_values = self.sensor_values[sensor_name]
    #     for v in selected_values:
    #         if v in stored_values and len(stored_values) == len(self.sensor_time):
    #             index = stored_values.index(v)
    #             timestamp = self.sensor_time[index][0]  # find timestamp respectively to its position in the list
    #             timestamps.append(timestamp)
    #         else:
    #             print(len(stored_values) == len(self.sensor_time))
    #     data_dict["Time"] = timestamps
    #     return data_dict

    def create_alarms_label(self, txt_frame: str, txt: str) -> None:
        labelframe = ttk.LabelFrame(self.info_panel, text=txt_frame)
        labelframe.grid(row=self.info_panel_wnum, column=0, padx=10, pady=5)
        label = ttk.Label(labelframe, text=txt, font=("Helvetica", 48))
        label.pack()
        self.alarm_num_label = label
        self.info_panel_wnum += 1

    def create_clock_label(self, txt_frame: str) -> None:
        labelframe = ttk.LabelFrame(self.info_panel, text=txt_frame)
        labelframe.grid(row=self.info_panel_wnum, column=0, padx=10, pady=5)
        clock = Clock(labelframe)
        clock.pack(fill="both", expand=True)
        self.info_panel_wnum += 1

    def add_control_button(self, text: str, func: Callable) -> None:
        button = ttk.Button(self.control_frame, text=text, command=func)
        button.place(y=self.button_num*60, x=0, height=uc.Measurements.button_height.value)
        self.button_num += 1
        # Remember the button
        self.control_buttons[text] = button

    def add_menu_button(self, text: str, func: Callable):
        # Add sign in button
        sign_in_button = ttk.Button(self.header_frame, text=text, command=func)
        sign_in_button.grid(row=self.body_row, column=self.menu_button_num + 1, padx=0, pady=10)
        self.menu_button_num += 1
        self.control_buttons[text] = sign_in_button

    """ Sensor Comm Control """

    def pause_comm(self) -> None:
        self.is_paused = True

    def resume_comm(self) -> None:
        self.is_paused = False

    """ Pop up functions """

    def show_sign_in_popup(self):
        self.pause()
        pop_up = UserDetailsWindow(self, title=uc.ElementNames.sign_in_popup_title.value)
        pop_up.add_button(txt="Log in", func=self.sign_in)
        pop_up.add_button(txt="Cancel", func=pop_up.close)
        self.sign_in_popup = pop_up

    def show_register_popup(self):
        self.pause()
        pop_up = UserRegistrationWindow(self, title=uc.ElementNames.registration_popup_title.value)
        pop_up.add_button(txt="Submit", func=self.register_user)
        pop_up.add_button(txt="Cancel", func=pop_up.close)
        self.registration_popup = pop_up

    def show_edit_photo_popup(self):
        self.pause()
        popup = FileUploadWindow(self, "File Upload")
        popup.add_button(txt="Select File", func=self.select_file)
        popup.add_button(txt="Upload", func=self.submit_new_user_photo)
        popup.add_button(txt="Cancel", func=popup.close)
        self.edit_photo_popup = popup

    def show_notes_entry(self):
        self.pause()
        if self.note_frame is not None:
            return None
        title = uc.ElementNames.data_notes_label.value
        self.note_frame = NotesEntryFrame(self.body_frame, title=title)
        self.note_frame.add_button(text="Save", func=self.save_selected_data_notes)
        self.note_frame.grid(row=2, column=1, padx=10, pady=10)

    """ Control functions """

    def set_user_photo(self, path=None):
        photo_label: ttk.Label = self.user_photo
        # The order of procedure should not be changed
        if path is None:
            path: str = self.db_manager.get_user_photo_path()
        if path == "":
            path: str = uc.FilePaths.user_photo_icon.value
        width: int = uc.Measurements.photo_w.value
        height: int = uc.Measurements.photo_h.value
        img = TkCustomImage(path, w=width, h=height)
        photo_label.configure(image=img.tk_image)
        photo_label.image = img.tk_image

    def submit_new_user_photo(self):
        popup: FileUploadWindow = self.edit_photo_popup
        file_path = popup.get_file_path()
        if file_path:
            self.set_user_photo(path=file_path)
            self.db_manager.save_new_photo_path(new_path=file_path)
            popup.show_message_frame("File Uploaded", f"The file '{file_path}' has been uploaded.")
            popup.disable_submission_button()
        else:
            popup.show_message_frame("Error", "Please select a file to upload.")

    def select_file(self):
        popup: FileUploadWindow = self.edit_photo_popup
        file_path = filedialog.askopenfilename()
        popup.file_path_entry.delete(0, tk.END)
        popup.file_path_entry.insert(0, file_path)

    def do_nothing(self):
        pass

    def save_last_data(self):
        self.save_graph()
        save_paths: dict[str, str] = self.db_manager.save_data()
        self.logger.log_buffer()  # save the remaining values in the buffer
        notify_content = (f"Report saved in {save_paths['report_path']}\n"
                          f"Graph saved in {save_paths['graph_path']}\n")
        if self.notification_frame:
            self.remove_notification()
        self.notification_frame = NotificationSuccessSave(self.footer_frame,
                                                          subject="Data Saved!",
                                                          details=notify_content)
        self.notification_frame.show(x=0, y=0, callback=self.remove_notification)
        self.logger.save_alarm_texts(path=self.alarm_text_file_path,
                                     texts=self.alarm_texts)
        self.db_manager.session.save_notes(folder_path=self.logger.folder_path)
        save_integrated_csv(self.logger.folder_path, self.logger.session_id)
        if self.is_test_mode:
            self.p_tester.save_report()

    def save_all_log(self):
        self.logger.log_all_data()

    def sign_in(self):
        pop_up: UserDetailsWindow = self.sign_in_popup
        user_details: UserDetails = pop_up.get_entered_details()
        if not self.db_manager.is_valid_sign_in(details=user_details):
            pop_up.show_message_frame(subject="Error",
                                      details="Entered details do not match the details in the database")
            return
        pop_up.show_message_frame(subject="Success",
                                  details=f"Welcome back, {self.db_manager.session.user_details.get_full_name()}")
        self.set_user_photo()

        print(f"Checking if file exists at path: {self.csv_path}")
        if os.path.exists(self.csv_path):
            print(f"File found at path: {self.csv_path}")
            self.user_data = self.load_user_data(self.csv_path)
            print(f"User data loaded: {self.user_data.head()}")

            print(f"User details: {self.db_manager.session.user_details.__dict__}")

            user_info = {
                'Age': self.db_manager.session.user_details.age,
                'Shoulder Size': self.db_manager.session.user_details.shoulder_size,
                'Height': self.db_manager.session.user_details.height,
                'Weight': self.db_manager.session.user_details.weight
            }
            self.current_user_features = self.process_user_info(user_info)
            size = self.current_user_features[1]
            increment: float = uc.Measurements.threshold_increment.value
            self.data_analyst.update_threshold(shoulder_size=size,
                                               increment=increment)
            self.logger.update_model_threshold(value=self.data_analyst.get_threshold(size),
                                               timestamp=self.logger.last_timestamp)
        else:
            print(f"File not found at path: {self.csv_path}")

        # Change button config
        sign_in_button: ttk.Button = self.control_buttons[uc.ElementNames.sign_in_button_txt.value]
        sign_in_button.configure(text=uc.ElementNames.sign_out_button_txt.value, command=self.sign_out)
        # Add button
        edit_button_txt = uc.ElementNames.edit_photo_button_txt.value
        self.add_menu_button(text=edit_button_txt, func=self.show_edit_photo_popup)
        self.add_user_name_label(name=self.db_manager.session.user_details.get_full_name(),
                                 row=self.footer_row,
                                 col=0,
                                 master=self.header_frame)
        self.resume()

    def sign_out(self):
        # Forget session
        self.db_manager.session.reset()
        self.set_user_photo()

        self.current_user_features = None

        # Change button config
        sign_in_button: ttk.Button = self.control_buttons[uc.ElementNames.sign_in_button_txt.value]
        sign_in_button.configure(text=uc.ElementNames.sign_in_button_txt.value, command=self.show_sign_in_popup)
        # Remove the button with name:
        button_txt: str = uc.ElementNames.edit_photo_button_txt.value
        self.control_buttons[button_txt].destroy()
        self.user_name.destroy()

    def register_user(self):
        popup: UserRegistrationWindow = self.registration_popup
        user_details: UserDetails = popup.get_entered_details()
        saved: bool = self.db_manager.save_user(user_details)
        if saved:
            popup.show_message_frame(subject="Success",
                                     details="Your personal details has been saved!\n"
                                             "Please try to sign in to your account.",
                                     row=popup.message_location[0],
                                     col=popup.message_location[1])
            self.resume()
        else:
            popup.show_message_frame(subject="Error",
                                     details="User with similar personal details already exists!\n"
                                             "Please try to sign in.",
                                     row=popup.message_location[0],
                                     col=popup.message_location[1])

    def start_20_timer(self):
        timer_root = ttkbt.Toplevel()       #creat a new top level for 20-20-20 reminder
        timer_app = TimerApp(timer_root)
        timer_root.mainloop()

    def pause(self):
        self.pause_comm()
        self.graph.pause()
        button = self.control_buttons[uc.ElementNames.pause_button_txt.value]
        resume_txt: str = uc.ElementNames.resume_button_txt.value
        button.config(text=resume_txt, command=self.resume)
        # Add scroll bar for the Graph
        if self.scroll_bar_frame:
            self.remove_graph_scrollbar()
        self.scroll_bar_frame = tk.Frame(self.body_frame)
        self.scroll_bar_frame.grid(row=3, column=1, pady=10, padx=10, sticky=tk.NSEW)
        options: list[int] = [sen[0] for sen in self.sensor_time]
        self.graph_scroll_bar = GraphScrollBar(parent=self.scroll_bar_frame,
                                               options=options,
                                               figure_func=self.update_graph)

    def remove_graph_scrollbar(self) -> None:
        if self.scroll_bar_frame:
            self.scroll_bar_frame.destroy()
            self.graph_scroll_bar.destroy()
            self.graph_scroll_bar = None
            self.scroll_bar_frame = None

    def remove_note_frame(self):
        if self.note_frame:
            self.note_frame.destroy()
            self.note_frame = None

    def resume(self):
        self.resume_comm()
        self.graph.resume()
        stop_txt: str = uc.ElementNames.pause_button_txt.value
        button = self.control_buttons[stop_txt]
        button.config(text=stop_txt, command=self.pause)
        self.remove_note_frame()
        self.remove_graph_scrollbar()

    def save_graph(self):
        file_path = self.db_manager.session.get_graph_save_path(ask_path=False)
        self.graph.figure.savefig(file_path)
        print(f"Graph saved to {file_path}")

    @staticmethod
    def load_user_data(filepath: str) -> Union[pd.DataFrame, None]:
        try:
            data = pd.read_csv(filepath)
            print(f"CSV data loaded successfully from {filepath}")
            print(data.head())
            return data
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return None

    @staticmethod
    def process_user_info(user_info) -> np.array:
        try:
            birth_date = datetime.datetime.strptime(user_info['Age'], '%d-%m-%Y')
            age = int((datetime.datetime.now() - birth_date).days / 365.25)

            shoulder_size_map = {'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'XL': 4}
            size = shoulder_size_map.get(user_info['Shoulder Size'], -1)

            height = float(user_info['Height']) / 100
            weight = float(user_info['Weight'])

            flexibility = flex_median_g

            features = np.array([age, size, weight, height, flexibility], dtype=float)
            # print(f"Processed user features: {features}")
            return features
        except Exception as e:
            print(f"Error processing user info: {e}")
            return None

    def pause_for(self):
        """ The function set pause for certain amount of time in seconds """
        self.pause()
        interval = self.time_interval_frame.get_interval()
        time.sleep(interval)  # seconds
        self.resume()

    def update_x_range(self, new_range: int):
        self.x_range = new_range
        self.update_graph()

    # def show_rand_quest(self):
    #     if self.rand_quest_notification is not None:
    #         # do not overlap pop up notifications
    #         return None
    #     self.rand_quest_notification = RandomSideQuestNotification(self.footer_frame,
    #                                                                self.logger.update_side_quest_status,
    #                                                                self.forget_side_quest)
    #     self.rand_quest_notification.show(x=uc.Positions.random_quest.value[0],
    #                                       y=uc.Positions.random_quest.value[1],
    #                                       callback=None)
    #     self.logger.update_side_quest_status('appeared')
    #     print("Bad Posture Command Activated!")

    @staticmethod
    def get_alarm_logger_path() -> str:
        file_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        alarm_text_file_name = f'/data/alarmrepo_dir/alarm_texts_{file_time}.txt'
        return uc.FilePaths.project_root.value + alarm_text_file_name

    def get_meta_data(self) -> dict:
        # Get the initial window height and width
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        print(f"Initial window width: {window_width}")
        print(f"Initial window height: {window_height}")
        return {"width": window_width,
                "height": window_height}
