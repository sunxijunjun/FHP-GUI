import os.path
from enum import Enum


main_theme = 'adapta'


class FrameColors(Enum):
    graph = "#2C3E50"  # 深海蓝
    control = "#34495E"  # 午夜蓝
    header = "#2980B9"  # 贝壳蓝
    body = "#D3D3D3"  # 浅灰色
    footer = "#2ECC71"  # 翡翠绿


class ElementNames(Enum):
    app_title = "Posture Analysis Dashboard"

    graph_title = "Sensor Values"
    graph_y = "Distance (mm)"
    graph_x = "Number of Data"
    sensor_names = ["Sensor 2", "Sensor 4"]

    alarm_num_label = "Duration of Alarms" #目前是计数，需要改成计时　TODO -> DONE
    processing_time_label = "Monitoring Time"
    data_notes_label = "Data Notes"

    pause_button_txt = "Pause Graph"
    resume_button_txt = "Resume Graph"
    close_button_txt = "Close APP"
    save_data_button_txt = "Save All Data"
    start_20timer_button_txt = "20-20-20 reminder"
    calibration_button_txt = "Calibration"
    sign_in_button_txt = "Sign in"
    sign_out_button_txt = "Sign out"
    register_button_txt = "Register"
    edit_photo_button_txt = "Edit Photo"
    #save_selected_button_txt = "Add Notes"

    sign_in_error = "The user does not exists. Please try again!"

    registration_popup_title = "User Registration"
    sign_in_popup_title = "User Sign In"

    user_login_db_headers = ["First Name",
                             "Second Name",
                             "Middle Name",
                             "Password",
                             "Photo Path",
                             "Gender",
                             "Age",
                             "Shoulder Size",
                             "Height",
                             "Weight",
                             "Threshold"]

    shoulder_options = ["XL", "L", "M", "S", "XS"]
    shoulder_category_txt = "Shoulder Size"

    gender_options = ["Male", "Female", "Prefer not to say"]
    gender_category_txt = "Gender"


class Measurements(Enum):
    window_size = "1100x600"
    graph_size = (6, 3)
    graph_x_limit = 50  # show up to last X values or None for infinite number
    header_h = 200
    body_h = 500
    footer_h = 500
    button_height = 50

    photo_h = 50
    photo_w = 50

    pop_up_closing_delay = 2000  # ms
    thread_delay = 0.01  # s

    time_format = "%Y-%m-%d %H:%M:%S"  # "H:M:S.MS PM/AM, DD-MM-YYYY
    csv_time_format = "%I%M%S%d%m%y"
    graph_refresh_rate = 5

    notification_delay = 2000  # in ms

    distance_max = 850
    distance_min = 400

    rand_quest_popup = [30*1000, 1000*1000]  # should be in ms  # time window for posture commands
    rand_quest_duration = [30, 60]  # clock duration range

    num_bad_posture_commands = 10  # max total posture commands
    val_replacing_limit = 20  # threshold when the notification should popup
    sensor_val_replacing_limit = 10  # 传感器最大容忍异常次数
    camera_val_replacing_limit = 100  # 摄像头最大容忍异常次数
    default_val_replacing_limit = 20 # 默认容忍异常次数
    false_responses_limit = 1  # specify after how many responses the model threshold should be changed
    
    threshold = {
        "XS": 66,
        "S": 67,
        "M": 80,
        "L": 88,
        "XL": 95
    }
    threshold_increment = 10.0  # specify how the threshold should be incremented

    widgets_padding = 100
    time_offset = 10*1000  # in ms


class Fonts(Enum):
    info_panel_font = ("Roboto", 36, "bold")
    button_font = ("Arial", 14, "bold")
    title_font = ("Helvetica", 24, "bold")


class FilePaths(Enum):
    """ Notes:
    Absolute path for user photos are preferred
    """
    project_root = os.path.dirname(os.path.abspath(__file__))

    """ Specific file paths """
    user_photo_icon = project_root + '/data/img/user_photo.jpeg'
    user_login_db_path = project_root + "/data/users/logins.csv"
    flex_collect_csv_path = project_root + '/data/dynamic_data_collected/posture_data_20240713145850.csv'

    """ Folder paths """
    values_folder_path = project_root + "/data/values"
    graph_folder_path = project_root + "/data/img/graphs"
    piechart_folder_path = project_root + "/data/img/piecharts"
    reports_folder_path = project_root + "/data/reports"
    logs_folder_path = project_root + "/data/logs"
    model_path = project_root + '/models'


class CheckBoxesKeys(Enum):
    notification_bad_posture = "notify_bad_posture"
    enable_sound = "enable_sound"
    enable_light = "enable_light"



class Ports(Enum):
    linux_path = "/dev/tty"
    linux_sensor_1 = linux_path + "ACM0"
    linux_sensor_2 = linux_path + "AMA0"
    linux_img_sensor = linux_path + "ACM1"

    windows_serial = "COM8"

    macos_serial = "/dev/cu.usbmodem58881039021"


class Positions(Enum):
    vals_validation = [1200, 0]
    incorrect_posture = [1200, 80]
    log_success = [1200, 200]
    feedback = [10, 0]
    random_quest = [500, 0]
