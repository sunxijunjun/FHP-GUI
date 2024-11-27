import random
import tkinter as tk
from tkinter import ttk, colorchooser  # 导入 colorchooser

import serial
from sound_controller import SoundControllerApp
from light_controller import LightControllerApp
from serial_manager import SerialManager
import tkinter as tk
from tkinter import ttk, messagebox
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
import dynamic_labelling
from dynamic_labelling import flex_median_g
from log_integration import save_integrated_csv
from logger import Logger
from reminder22 import TimerApp
from flex_collect import PostureDataCollection
from performance_tester import PerformanceTester
import numpy as np
import os
import pandas as pd
import sys
import time
from tensorflow.keras.models import load_model
from database_manager import ReportWriter, SessionInstance
import re
import math
from port_detection import GetPortName
import markdown2
from tkinterweb import HtmlFrame
from sound_player import play_sound_in_thread


class App(ThemedTk):
    def __init__(self, title: str, fullscreen=False, test=False):
        super().__init__()
        self.theme = uc.main_theme
        self.set_theme(theme_name="adapta")

        # 在 set_theme 之后，重新配置样式
        self.apply_custom_style()

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
        self.serial_manager = SerialManager(port=GetPortName())

        # 创建各个框架和UI元素
        self.sensor_values = dict()
        self.sensor_raw_values = dict()
        self.sensor_time = list()
        self.latest_facial_values = None
        self.alarm_texts = list()
        self.elapsed_time = list()
        self.alarm_num = 0
        self.alarm_duration = 0
        self.last_alarm_time = None
        self.last_sensor_time = None
        self.button_num = 0
        self.menu_button_num = 0
        self.is_stopped = False
        self.is_paused = False
        self.user_data = None
        self.info_panel_wnum = 0
        self.prev_alarm_pos = 0
        self.error_message = False
        self.device_exception_count = {"Sensor": list(), "Camera": list()}
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
        self.settings_popup = None
        self.countdown_time = 0

        self.info_panel = ttk.Frame(self.body_frame)
        self.info_panel.grid(row=self.body_row, column=0, padx=10, pady=5)

        self.alarm_num_label = None
        self.alarm_text_label = None
        self.notification_frame = None
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

        self.alarm_timestamp = None
        self.alarm_consist_time = 0

        self.lastest_prediction = None

        # 初始化主UI
        self.create_major_frames()
        self.add_header_elements(title=uc.ElementNames.app_title.value)
        self.graph = self.create_graph()
        self.create_control_frame()

        # 初始化自定义框架和其他组件
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
        self.current_user_id = None
        self.current_user_features = None
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(base_path, 'data', 'users', 'logins.csv')
        self.sensor_values = {"Sensor 2": [], "Sensor 4": []}
        self.sensor_raw_values = {"Sensor 2": [], "Sensor 4": []}
        self.alarm_text_file_path = self.get_alarm_logger_path()
        self.feedback_collector = None

        # 添加设置按钮
        self.add_setting_button()
        self.add_guide_button()
        self.add_generate_report_button()

        self.calibration_window = None

        # 需要用户登录后才能进行数据采集
        if not test:
            self.after(500, func=self.show_sign_in_popup)

    def add_generate_report_button(self):
        self.add_menu_button("Generate Report", self.show_generate_report_window)

    def show_generate_report_window(self):
        self.save_graph()
        
        report_window = tk.Toplevel(self)
        report_window.title("Generate Report")
        report_window.geometry("375x900")  # 调整窗口大小
        ###.md文件的内容移动到这里　TODO
        # 生成报告内容
        report_content = self.db_manager.report_writer.get_header() + self.db_manager.report_writer.get_stats()

        # Convert markdown to HTML
        report_content = "\n".join(line.strip() for line in report_content.splitlines())
        html_content = markdown2.markdown(report_content, extras=["tables", "fenced-code-blocks"])
        html_content = html_content.replace('<h1>', '<h1 style="font-size: 175%; text-align: center;">')
        html_content = html_content.replace('<img ', '<img style="width: 350px; height: auto;" ')
        html_content = html_content.replace('<th>', '<th style="padding: 8px; text-align: left;">')
        html_content = html_content.replace('<td>', '<td style="padding: 8px; text-align: left">')
        print(html_content)

        frame = HtmlFrame(report_window)
        frame.load_html(html_content)
        frame.pack(fill="both", expand=True)

        # 保存报告功能
        def save_report():
            self.db_manager.report_writer.save_report()

        save_button = tk.Button(report_window, text="Save Report", command=save_report)
        save_button.pack(pady=10)



    def add_guide_button(self):
        self.add_menu_button("User Guide", self.show_user_guide_window)

    def show_user_guide_window(self):
        guide_window = tk.Toplevel(self)
        guide_window.title("User Guide")
        guide_window.geometry("450x400")  # 调整窗口大小

        # Create a canvas
        canvas = tk.Canvas(guide_window)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Reuse Previous Code:
        # guide_window = NotesEntryFrame()

        # Add a scrollbar to the canvas
        scrollbar = ttk.Scrollbar(guide_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create another frame inside the canvas
        inner_frame = tk.Frame(canvas, width = 330)

        # Add that frame to a window in the canvas
        canvas.create_window((0, 0), window=inner_frame, anchor="center")



        # 多语言文本字典
        guide_texts = {
            "English": (
                "Welcome to the Beta Prototype.\n\n"
                "This device will detect poor posture while you are using the computer, primarily slouching shoulders and forward head posture.\n\n"
                "For optimal accuracy, please follow the calibration steps below:\n\n"
                "1. Adjust the height of your chair and screen so that the top edge of the screen is level with or slightly below your eyes.\n\n"
                "2. Secure the device at the center of the top edge of your monitor.\n\n"
                "3. At this point, you should see your face appear in the center of the camera view, surrounded by a small green box.\n\n"
                "4. Please register a personal account and accurately fill in your height, weight, and other information.\n\n"
                "5. Enable 'Notify Bad Posture After X Seconds' in the settings and input the desired time interval in seconds in the text box.\n\n"
                "6. When notified of bad posture, please click 'True/False' as this will help the program make more accurate and personalized alerts.\n\n"
                "7. If the device fails to correctly detect bad posture, click the calibration button and follow the prompts to complete the calibration procedure. The system will check sensor status and analyze possible causes of errors.\n\n"
                "8. The preparation is complete. Fantastic!\n\n"

            ),
            "中文": (
                "欢迎使用Beta原型机。\n\n"
                "此设备将检测您在使用计算机时的不良姿势，主要是圆肩驼背和颈前伸的姿态。\n\n"
                "为了达到最佳准确性，请按照以下校准步骤操作：\n\n"
                "1.调整椅子和屏幕的高度，使屏幕上边缘的高度应该平齐于或略低于您的眼睛。\n\n"
                "2.将设备固定在显示器上边缘的中央。\n\n"
                "3.这时您应该看到您的脸出现在相机视图的中心，并且周围有一个小的绿色框。\n\n"
                "4.请注册个人账户，并且如实填写身高体重等信息。\n\n"
                "5.请在设置中打开Notify Bad Posture After X Seconds，并在方框中填入您希望被通知的时间间隔，单位是秒。\n\n"
                "6.当收到警报时，请点击True/False，这会帮助程序更加准确且个性化的发出警报。\n\n"
                "7.当设备无法正确检出不良姿态时，请点击校准按钮，并按照提示完成校准程序。系统会检测传感器状态，并且分析可能的错误原因。\n\n"
                "8.准备工作已经完成，太棒了！\n\n"
            ),

            "粤语": (
                "歡迎使用Beta原型機。\n\n"
                "此裝置會偵測你使用電腦時嘅不良姿勢，主要係圓肩、駝背同埋頸前伸嘅姿態。\n\n"
                "為咗達到最佳準確性，請按照以下校準步驟操作：\n\n"
                "1. 調整椅子同顯示屏嘅高度，顯示屏嘅上邊緣應該同你眼睛平齊，或者稍低過眼睛。\n\n"
                "2. 將裝置固定喺顯示器上邊緣嘅中間位置。\n\n"
                "3. 呢個時候你應該見到你嘅面出現喺相機視圖嘅中間，並且周圍有一個細細嘅綠色框。\n\n"
                "4. 請註冊個人帳戶，並且如實填寫你嘅身高、體重等資料。\n\n"
                "5. 請喺設定中打開'X秒後通知不良姿勢'，並喺文本框中輸入你希望嘅通知時間間隔（秒）。\n\n"
                "6. 當收到警報時，請點擊'True/False'，咁樣可以幫助程序更加準確同個性化發出警報。\n\n"
                "7. 當裝置無法準確偵測不良姿勢時，請點擊校準按鈕，並按照提示完成校準程序。系統會檢測傳感器狀態，分析可能嘅錯誤原因。\n\n"
                "8. 準備工作完成，太棒啦！\n\n"

            ),

            "Deutsch": (
                "Willkommen beim Beta-Prototyp.\n\n"
                "Dieses Gerät wird schlechte Körperhaltungen erkennen, insbesondere Rundrücken und vorgestreckten Kopf.\n\n"
                "Für optimale Genauigkeit folgen Sie bitte den folgenden Kalibrierschritten:\n\n"
                "1. Passen Sie die Höhe Ihres Stuhls und Monitors so an, dass die obere Kante des Bildschirms auf Augenhöhe oder leicht darunter ist.\n\n"
                "2. Befestigen Sie das Gerät in der Mitte der oberen Kante Ihres Monitors.\n\n"
                "3. Zu diesem Zeitpunkt sollten Sie Ihr Gesicht in der Mitte der Kameraansicht sehen, umgeben von einem kleinen grünen Rahmen.\n\n"
                "4. Bitte registrieren Sie ein persönliches Konto und geben Sie Ihre Körpergröße, Ihr Gewicht und andere Informationen korrekt an.\n\n"
                "5. Aktivieren Sie 'Benachrichtigung bei schlechter Haltung nach X Sekunden' in den Einstellungen und geben Sie das gewünschte Zeitintervall (in Sekunden) in das Textfeld ein.\n\n"
                "6. Wenn Sie benachrichtigt werden, klicken Sie bitte auf 'Wahr/Falsch', um dem Programm zu helfen, genauere und personalisierte Warnungen auszugeben.\n\n"
                "7. Falls das Gerät schlechte Haltung nicht korrekt erkennt, klicken Sie auf die Kalibrierungsschaltfläche und folgen Sie den Anweisungen zur Durchführung des Kalibrierungsverfahrens. Das System überprüft den Sensorstatus und analysiert mögliche Fehlerursachen.\n\n"
                "8. Die Vorbereitungen sind abgeschlossen. Großartig!\n\n"

            )

        }

        # 默认显示的语言是英语
        guide_label = tk.Label(inner_frame, text=guide_texts["English"], font=("Arial", 10), justify="left",
                               wraplength=300)
        guide_label.pack(pady=(20,10), fill=tk.X)

        # 选择语言的下拉菜单
        def update_language(event):
            selected_language = language_combobox.get()
            guide_label.config(text=guide_texts[selected_language])

        language_frame = tk.Frame(inner_frame)
        language_frame.pack(fill=tk.X, pady=10)

        language_combobox = ttk.Combobox(language_frame, values=["English", "中文", "粤语","Deutsch"])
        language_combobox.current(0)  # 默认选择英语
        language_combobox.bind("<<ComboboxSelected>>", update_language)
        language_combobox.pack(pady=10)

        # 关闭按钮
        close_button = ttk.Button(inner_frame, text="Close", command=guide_window.destroy)
        close_button.pack(pady=10)

        # Update the scrollregion after adding all widgets
        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


    # 在App类中添加设置按钮
    def add_setting_button(self):
        self.add_menu_button("Settings", self.show_settings_window)

    # 显示设置窗口的方法
    def show_settings_window(self):
        if self.settings_popup is not None:
            return
        self.pause()
        self.settings_popup = tk.Toplevel(self)
        self.settings_popup.title("Settings")
        self.settings_popup.geometry("400x350")
        self.settings_popup.attributes('-topmost', True)

        enable_sound = tk.BooleanVar(value=self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_sound.value][1].get())
        enable_light = tk.BooleanVar(value=self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_light.value][1].get())
        notification_bad_posture = tk.BooleanVar(value=self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.notification_bad_posture.value][1].get())

        # 设置列和行的布局
        self.settings_popup.columnconfigure([0, 1, 2], weight=1, uniform="columns")  # Adjusting 3 columns
        self.settings_popup.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7], weight=1)  # Adjusting row heights
        # Create three LabelFrames to organize the GUI
        sensor_labelframe = ttk.LabelFrame(self.settings_popup, text="Sensor")
        sensor_labelframe.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        monitor_labelframe = ttk.LabelFrame(self.settings_popup, text="Monitor")
        monitor_labelframe.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        user_labelframe = ttk.LabelFrame(self.settings_popup, text="User")
        user_labelframe.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # 声音控制
        sound_check = ttk.Checkbutton(sensor_labelframe,
                                      variable=enable_sound, # 直接使用原始的 enable_sound_var
                                      command=lambda: self.toggle_feature("sound"))
        sound_check.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        sound_label = ttk.Label(sensor_labelframe, text="Enable Sound")
        sound_label.grid(row=0, column=1, pady=5, padx=5, sticky="w")
        
        # 灯光控制
        light_check = ttk.Checkbutton(sensor_labelframe,
                                      variable=enable_light,  # 直接使用原始的 enable_light_var
                                      command=lambda: self.toggle_feature("light"))
        light_check.grid(row=1, column=0, pady=5, padx=5, sticky="w")
        light_label = ttk.Label(sensor_labelframe, text="Enable Light")
        light_label.grid(row=1, column=1, pady=5, padx=5, sticky="w")
        
        # Check button for 'Notify Bad Posture After' setting
        error_notify_check = ttk.Checkbutton(sensor_labelframe,
                                             variable=notification_bad_posture)
        error_notify_check.grid(row=2, column=0, pady=5, padx=5, sticky="w")
        # 错误通知控制
        error_notify_label = ttk.Label(sensor_labelframe, text="Notify Bad Posture After X Seconds")
        error_notify_label.grid(row=2, column=1, pady=5, padx=5, sticky="w")
        # Input box (entry field) for 'Notify Bad Posture After' time window
        notify_time_entry = ttk.Entry(sensor_labelframe, width=5)
        notify_time_entry.grid(row=2, column=2, pady=5, padx=5, sticky="w")
        notify_time_entry.insert(0, self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.notification_bad_posture.value][2].get())

        # 创建 Save 按钮
        def save_settings():
            self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_sound.value][1].set(enable_sound.get())
            self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.enable_light.value][1].set(enable_light.get())
            # Retrieve the current tuple for 'Notify Bad Posture After' setting
            current_tuple = self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.notification_bad_posture.value]
            current_tuple[2].delete(0, tk.END)
            current_tuple[2].insert(0, notify_time_entry.get())
            self.check_boxes_frame.check_boxes[uc.CheckBoxesKeys.notification_bad_posture.value] = \
                (current_tuple[0], notification_bad_posture, current_tuple[2])
            close_settings()

        def close_settings():
            self.resume()
            self.close_settings_popup()
       
        self.settings_popup.protocol("WM_DELETE_WINDOW", close_settings)
        
        # Create a frame to hold the buttons
        buttons_frame = ttk.Frame(sensor_labelframe)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=5, padx=5)

        # Create Save button
        save_button = ttk.Button(buttons_frame, text="Save", command=save_settings)
        save_button.pack(side=tk.LEFT, padx=5)

        # Create Close button
        close_button = ttk.Button(buttons_frame, text="Close", command=close_settings)
        close_button.pack(side=tk.LEFT, padx=5)

        # # 保存监控数据
        # save_all_data_button = ttk.Button(monitor_labelframe, text="Save All Data", command=self.save_last_data)
        # save_all_data_button.grid(row=0, column=0, pady=5, padx=5, sticky="w")

        self.time_interval_frame = TimeIntervalSelectorFrame(monitor_labelframe, row=1, col=0, txt="Pause For (MM:SS):", func=self.pause_for)

        # 编辑个人资料照片按钮
        edit_profile_photo_button = ttk.Button(user_labelframe, text="Edit Profile Photo", command=self.show_edit_photo_popup)
        edit_profile_photo_button.grid(row=0, column=0, pady=5, padx=5, sticky="w")

        #颜色控制
        choose_color_button = ttk.Button(user_labelframe, text="Choose Theme Color", command=self.show_color_chooser)
        choose_color_button.grid(row=0, column=1, pady=5, padx=5, sticky="w")

    def apply_custom_style(self):
        style = ttkbt.Style('flatly')
        style.configure('TFrame', background='#E8F4F8')
        style.configure('TLabel', background='#E8F4F8', foreground='#2ECC71')
        style.configure('TButton', background='#D1F2EB', foreground='#2ECC71')
        #style.configure('TFrame', background='#E8F4F8', foreground='#2ECC71')

    def show_color_chooser(self):
        color_code = colorchooser.askcolor(title="Choose color")[1]  # 直接使用 colorchooser
        if color_code:
            self.apply_theme_color(color_code)

    def apply_theme_color(self, color_code):
        # 使用 ttk.Style 来改变背景颜色，而不是使用 configure(bg=...)
        style = ttk.Style()
        style.configure("TFrame", background=color_code)  # 设置所有 Frame 的背景颜色
        style.configure("TLabel", background=color_code)  # 设置所有 Label 的背景颜色

        # 手动设置其它需要改变的组件
        self.check_boxes_frame.configure(style="TFrame")

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
            self.lastest_prediction = self.data_analyst.detect_anomaly_test(data=self.sensor_values)
        else:
            update_delay = 500 # 500ms delay for sensor values to update
            def make_prediction():
                last_update_time = datetime.datetime.now() - datetime.timedelta(milliseconds = update_delay)
                sensor_data = {sensor: self.sensor_values[sensor][-1] for sensor in ["Sensor 2", "Sensor 4"]}
                facial_data = self.latest_facial_values
                if not self.check_sensor_conditions(
                    self.sensor_raw_values["Sensor 2"],
                    self.sensor_raw_values["Sensor 4"]
                ):
                    return
                if not self.check_facial_conditions(last_update_time):
                    return
                if self.latest_facial_values is None or \
                    self.latest_facial_values["local_timestamp"] < last_update_time.timestamp() or \
                    self.data_analyst.timestamp_to_datetime(self.sensor_time[-1][0]) < last_update_time:
                    # print("No new data to make prediction.")
                    return                
                data = sensor_data | facial_data
                data.pop("local_timestamp")
                self.lastest_prediction =  self.data_analyst.detect_anomaly(data=data)
            if not self.error_message:
                self.after(update_delay, make_prediction)

        if self.logger.last_timestamp != "":
            self.logger.update_prediction(timestamp=self.logger.last_timestamp, prediction=self.lastest_prediction)
        print("Prediction: ", self.lastest_prediction)
        if self.lastest_prediction == 0:
            anomaly_detected = True
            anomaly_graph_position = len(self.sensor_values['Sensor 2']) - 1

        for collection in self.graph.ax.collections:
            if isinstance(collection, matplotlib.collections.PolyCollection):
                collection.remove()
        if anomaly_detected:
            self.show_alarm(pos=anomaly_graph_position)
            print("Alarm raised.")
        else:
            self.last_alarm_time = None
            self.db_manager.session.alarm_times.append("|")

    def validate_sens_values(self, sens_2: int, sens_4: int, values: dict) -> tuple[int, int]:
        notes = str()
        
        if np.isnan(sens_2) or np.isnan(sens_4):
            return sens_2, sens_4
        
        def validate_sensor(sensor_value, sensor_name):
            nonlocal notes
            if sensor_value > self.dist_max:
                if len(values[sensor_name]) > 1:
                    sensor_value = values[sensor_name][-1]
                    notes += f"{sensor_name} val replaced by previous valid val "
                else:
                    sensor_value = self.dist_max
                    notes += f"{sensor_name} val replaced by max valid val "
            return sensor_value

        sens_2 = validate_sensor(sens_2, "Sensor 2")
        sens_4 = validate_sensor(sens_4, "Sensor 4")
        self.logger.update_notes(timestamp=self.logger.last_timestamp, notes=notes)
          
        return sens_2, sens_4

    def check_conditions(self, conditions: dict, condition_type: str) -> bool:
        if condition_type == "Sensor":
            val_replacing_limit = uc.Measurements.sensor_val_replacing_limit.value
        elif condition_type == "Camera":
            val_replacing_limit = uc.Measurements.camera_val_replacing_limit.value
        else:
            val_replacing_limit = uc.Measurements.default_val_replacing_limit.value

        if len(self.device_exception_count[condition_type]) < len(conditions):
            self.device_exception_count[condition_type] = [0] * len(conditions)
        
        conditions_passed = True

        for condition in conditions.values():
            conditions_passed = conditions_passed and condition["pass_condition"]
            if condition["pass_condition"]:
                self.device_exception_count[condition_type][condition["condition_id"]] = 0
            else:
                self.device_exception_count[condition_type][condition["condition_id"]] += 1
                if self.device_exception_count[condition_type][condition["condition_id"]] >= val_replacing_limit:
                    play_sound_in_thread()
                    self.error_message = True
                    self.device_exception_count[condition_type][condition["condition_id"]] = 0
                    messagebox.showwarning("Warning", condition["error_msg"])
                    self.error_message = False
                break
        
        return conditions_passed
    
    def check_sensor_conditions(self, sens_2: int, sens_4: int) -> bool:
        conditions = {
            "Sensor value valid": {
                "condition_id": 0,
                "pass_condition": sens_2 <= self.dist_max and sens_4 <= self.dist_max,
                "error_msg": "Sensor cannot detect distance to participant!\nPlease adjust the posture or sensor!"
            },
            "Sensor difference valid": {
                "condition_id": 1,
                "pass_condition": sens_2 - sens_4 < 60,
                "error_msg": "Sensor values differ unexpectedly!\nPlease adjust the posture or sensor!"
            },
            "Appropriate distance": {
                "condition_id": 2,
                "pass_condition": sens_2 >= self.dist_min and sens_4 >= self.dist_min,
                "error_msg": "You are too close to the screen!\nKeep an appropriate distance to protect your eyesight."
            }
        }
        
        return self.check_conditions(conditions, condition_type="Sensor")
    
    def check_facial_conditions(self, last_datetime: datetime.datetime) -> bool:
        conditions = {
            "Facial data exists": {
                "condition_id": 0,
                "pass_condition": self.latest_facial_values is not None and \
                    self.latest_facial_values["local_timestamp"] >= last_datetime.timestamp(),
                "error_msg": "Facial data not detected!\nPlease adjust the camera."
            }
        }

        return self.check_conditions(conditions, condition_type="Camera")

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

    def update_sensor_values(self, sens_2: int, sens_4: int, timestamp: int, local_time: str) -> None:
        if pd.isna(sens_2) or pd.isna(sens_4):
            return None
        values = self.sensor_values
        values["Sensor 2"].append(sens_2)
        values["Sensor 4"].append(sens_4)
        self.last_sensor_time = timestamp
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

    def update_facial_values(self, facial_data: dict, timestamp: int, local_timestamp: str) -> None:
        face_features = ['bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
                'left_eye_x', 'left_eye_y', 'right_eye_x', 'right_eye_y',
                'nose_x', 'nose_y',
                'mouth_left_x', 'mouth_left_y', 'mouth_right_x', 'mouth_right_y']
        
        if facial_data is None or any([np.isnan(facial_data[feature]) for feature in face_features]):
            return None
        
        facial_data['local_timestamp'] = local_timestamp
        self.latest_facial_values = facial_data
        # print("facial data added: ", facial_data, " at ", local_timestamp, "latest:", self.latest_facial_values)

    def show_notify_log_success(self, subject: str) -> None:
        if self.log_notification_frame:
            try:
                self.log_notification_frame.destroy()
            except Exception as e:
                print(f"Error destroying log_notification_frame: {e}")
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
        
        if self.last_sensor_time is not None:
            if self.last_alarm_time is None:
                interval = 0
            else:
                interval = self.last_sensor_time - self.last_alarm_time # in milliseconds
            self.alarm_duration += interval
            self.last_alarm_time = self.last_sensor_time
        alarm_duration_text = str(datetime.timedelta(seconds=math.ceil(int(self.alarm_duration) / 1000)))
        self.alarm_num_label.config(text=alarm_duration_text)
        self.graph.draw_vert_span(x=pos)
        self.prev_alarm_pos = pos
        self.add_alarm_text()
        this_time = datetime.datetime.now().strftime(uc.Measurements.time_format.value)
        self.db_manager.session.alarm_times.append(this_time)
        # Show alarm notification
        interval /= 1000 # convert to seconds
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
        self.sound_controller.send_command(self.sound_controller.get_sound_command())
        self.light_controller.send_command(self.light_controller.get_light_command())

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
        # size: int = self.current_user_features[1]
        increment: float = uc.Measurements.threshold_increment.value
        self.data_analyst.update_threshold(increment=increment, db_manager=self.db_manager)
        self.logger.update_model_threshold(value=self.data_analyst.get_threshold(),
                                           timestamp=self.logger.last_timestamp)
        self.reset_false_response_limit()
        print(f"New threshold {self.data_analyst.get_threshold()} for shoulder size {self.data_analyst.user_features['size']} has been set")

    def reset_false_response_limit(self):
        self.false_responses_limit = uc.Measurements.false_responses_limit.value

    def is_bad_posture_notification_required(self, interval: float) -> bool:
        key = uc.CheckBoxesKeys.notification_bad_posture.value
        required_time: float = float(self.check_boxes_frame.get_input_value(key))
        current_timestamp = datetime.datetime.now().strftime(uc.Measurements.time_format.value)
        current_datetime = self.data_analyst.timestamp_to_datetime(current_timestamp)
        if not self.check_boxes_frame.is_true(access_key=key) or required_time == 0:
            return False
        if self.alarm_timestamp is None:            
            self.alarm_timestamp = self.data_analyst.timestamp_to_datetime(current_timestamp)
            return False
        threshold = 0.8 # Generate notification if alarm consists more than 80% of the time
        alarm_fulfilled = False
        if (current_datetime - self.alarm_timestamp).total_seconds() < required_time:
            self.alarm_consist_time += interval
        else:
            alarm_fulfilled = self.alarm_consist_time / required_time >= threshold
            self.alarm_consist_time = 0
            self.alarm_timestamp = None
        return (alarm_fulfilled and not self.notification_frame)

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

    def add_alarm_text(self) -> None:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alarm_text = f"Prediction {self.alarm_num} made at {current_time}\n"
        self.alarm_text_label.config(text=alarm_text)
        self.alarm_num += 1
        self.alarm_texts.append(alarm_text)

    def create_control_frame(self) -> None:
        frame = ttk.Frame(self.body_frame, width=250, height=200)
        frame.grid(row=self.body_row, column=2, padx=10, pady=5)
        frame.grid_propagate(False)  # Disable grid propagation to keep the buttons in place
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
        label = ttk.Label(labelframe, text=txt, font=("Helvetica", 20)) #左侧警报数量
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

        # Prompt the new user to register
        new_user_frame = ttk.Frame(pop_up)
        new_user_frame.grid(row=4, column=0, columnspan=2, pady=10)
        new_user_label = ttk.Label(new_user_frame, text="New User?")
        new_user_label.grid(row=0, column=0, padx=5)
        register_button = ttk.Button(new_user_frame, text="Register", command=self.show_register_popup)
        register_button.grid(row=0, column=1, padx=5)

        def close_popup():
            self.resume()
            pop_up.close()
            self.sign_in_popup = None

        pop_up.add_button(txt="Log in", func=self.sign_in)
        pop_up.add_button(txt="Cancel", func=close_popup)       

        self.sign_in_popup = pop_up

    def show_register_popup(self):
        self.pause()
        if self.sign_in_popup is not None:
            self.sign_in_popup.close()
            self.sign_in_popup = None
        pop_up = UserRegistrationWindow(self, title=uc.ElementNames.registration_popup_title.value)
        pop_up.add_button(txt="Submit", func=self.register_user, row=9)
        pop_up.add_button(txt="Cancel", func=pop_up.close, row=9)
        self.registration_popup = pop_up

    def show_edit_photo_popup(self):
        self.pause()
        popup = FileUploadWindow(self, "File Upload")
        popup.attributes('-topmost', True)
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
            self.db_manager.modify_user_info(field="Photo Path", new_value=file_path)
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

    def sign_in(self, pop_up=None):
        pop_up: UserDetailsWindow = self.sign_in_popup if pop_up is None else pop_up
        user_details: UserDetails = pop_up.get_entered_details()
        if not self.db_manager.is_valid_sign_in(details=user_details):
            pop_up.show_message_frame(subject="Error",
                                      details="Entered details do not match the details in the database")
            return
        pop_up.show_message_frame(subject="Success",
                                  details=f"Welcome back, {self.db_manager.session.user_details.get_full_name()}")
        self.set_user_photo()
        self.sign_in_popup = None

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
                'Weight': self.db_manager.session.user_details.weight,
                "User ID": self.db_manager.session.user_id,
                "Threshold": self.db_manager.session.user_details.threshold
            }
            self.current_user_features = self.process_user_info(user_info)
            self.data_analyst.set_user_features(self.current_user_features)
            # size = self.current_user_features[1]
            # increment: float = uc.Measurements.threshold_increment.value
            # self.data_analyst.update_threshold(increment)
            self.logger.update_model_threshold(value=self.data_analyst.get_threshold(),
                                               timestamp=self.logger.last_timestamp)
        else:
            print(f"File not found at path: {self.csv_path}")

        # Change button config
        sign_in_button: ttk.Button = self.control_buttons[uc.ElementNames.sign_in_button_txt.value]
        sign_in_button.configure(text=uc.ElementNames.sign_out_button_txt.value, command=self.sign_out)
        # Add button
        # edit_button_txt = uc.ElementNames.edit_photo_button_txt.value
        # self.add_menu_button(text=edit_button_txt, func=self.show_edit_photo_popup)
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
            self.sign_in(popup)
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

    def calibration(self):
        if self.calibration_window is not None and self.calibration_window.winfo_exists():
            self.calibration_window.lift()
            return
        self.calibration_window = PostureDataCollection(
            serial_manager=self.serial_manager,
            db_manager=self.db_manager
        )
        self.calibration_window.protocol("WM_DELETE_WINDOW", self.on_calibration_close)
        dynamic_labelling.use_flex_median()
        flex_median_g = dynamic_labelling.flex_median_g
        print(f"flex_median_g = {flex_median_g}")

    def on_calibration_close(self):
        self.calibration_window.destroy()
        self.calibration_window = None

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
            threshold = user_info['Threshold'] if user_info['Threshold'] else np.nan

            height = float(user_info['Height'])
            weight = float(user_info['Weight'])

            user_id = user_info['User ID']

            flexibility = flex_median_g

            features = np.array([age, size, weight, height, user_id, flexibility, threshold], dtype=float)
            # print(f"Processed user features: {features}")
            return features
        except Exception as e:
            print(f"Error processing user info: {e}")
            return None

    def close_settings_popup(self):
        """ Close the settings frame """
        if self.settings_popup is not None:
            self.settings_popup.destroy()
            self.settings_popup = None

    def lock_main_page(self):
        """ Lock the main page to avoid unexpected user operations """
        for frame in [self.header_frame, self.body_frame, self.footer_frame]:
            for widget in frame.winfo_children():
                if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Checkbutton, ttk.Radiobutton)):
                    widget.state(['disabled'])
        self.withdraw()

    def unlock_main_page(self):
        """ Unlock the main page """
        for frame in [self.header_frame, self.body_frame, self.footer_frame]:
            for widget in frame.winfo_children():
                if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Checkbutton, ttk.Radiobutton)):
                    widget.state(['!disabled'])
        self.deiconify()

    def show_countdown_popup(self, countdown_time: int):
        """ Show a pop-up with a countdown """
        self.close_settings_popup()
        self.lock_main_page()

        self.countdown_popup = tk.Toplevel(self)
        self.countdown_popup.title("Monitoring Paused")
        self.countdown_popup.geometry("300x200")

        self.countdown_title = tk.Label(self.countdown_popup, text="Pausing...", font=("Helvetica", 18))
        self.countdown_title.pack(pady=20)

        self.countdown_label = tk.Label(self.countdown_popup, text=f"{datetime.timedelta(seconds = self.countdown_time)}", font=("Helvetica", 32, "bold"))
        self.countdown_label.pack(pady=20)

        self.continue_button = tk.Button(self.countdown_popup, text="Continue", command=self.break_countdown)
        self.continue_button.pack(side="bottom", pady=10, anchor="s")

        self.countdown_time = countdown_time
        self.update_countdown()

    def update_countdown(self):
        """ Update the countdown timer """
        if self.countdown_time > 0:
            self.countdown_label.config(text=f"{datetime.timedelta(seconds = self.countdown_time)}")
            self.countdown_time -= 1
            self.after(1000, self.update_countdown)
        else:
            self.countdown_popup.destroy()
            self.continue_after_countdown()

    def break_countdown(self):
        """ Break the countdown and continue the app """
        self.countdown_time = 0
        self.countdown_popup.destroy()
        self.continue_after_countdown()

    def continue_after_countdown(self):
        """ Continue after the countdown """
        self.unlock_main_page()
        self.resume()

    def pause_for(self):
        """ The function set pause for certain amount of time in seconds """
        self.show_countdown_popup(int(self.time_interval_frame.get_interval()))

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
