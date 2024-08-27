import os.path
from enum import Enum


main_theme = 'yaru'


class FrameColors(Enum):
    graph = "black"
    control = "black"
    header = "red"
    body = "white"
    footer = "green"


class ElementNames(Enum):
    app_title = "Posture Analysis Dashboard"

    graph_title = "Sensor Values"
    graph_y = "Distance (mm)"
    graph_x = "Number of Data"
    sensor_names = ["Sensor 2", "Sensor 4"]

    alarm_num_label = "Number of Alarms"
    processing_time_label = "Processing Time"
    data_notes_label = "Data Notes"

    pause_button_txt = "Pause Graph"
    resume_button_txt = "Resume Graph"
    close_button_txt = "Close APP"
    save_data_button_txt = "Save All Data"
    sign_in_button_txt = "Sign in"
    sign_out_button_txt = "Sign out"
    register_button_txt = "Register"
    edit_photo_button_txt = "Edit Photo"
    save_selected_button_txt = "Add Notes"

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
                             "Weight"]

    shoulder_options = ["XL", "L", "M", "S", "XS"]
    shoulder_category_txt = "Shoulder Size"

    gender_options = ["Male", "Female", "Prefer not to say"]
    gender_category_txt = "Gender"


class Measurements(Enum):
    window_size = "1600x900"
    graph_size = (9, 3)
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
    val_replacing_limit = 10  # threshold when the notification should popup
    false_responses_limit = 3  # specify after how many responses the model threshold should be changed
    threshold_increment = 10.0  # specify how the threshold should be incremented

    widgets_padding = 100
    time_offset = 10*1000  # in ms


class Fonts(Enum):
    info_panel_font = ("Helvetica", 48)
    button_font = None
    title_font = None


class FilePaths(Enum):
    """ Notes:
    Absolute path for user photos are preferred
    """
    project_root = os.path.dirname(os.path.abspath(__file__))

    """ Specific file paths """
    user_photo_icon = project_root + '/data/img/user_photo.jpeg'
    user_login_db_path = project_root + "/data/users/logins.csv"
    flex_collect_csv_path = project_root + '/data/dynamic_data_collected/posture_data_20240713145850.csv'
    model_path = project_root + '/model_all.h5'

    """ Folder paths """
    values_folder_path = project_root + "/data/values"
    graph_folder_path = project_root + "/data/img/graphs"
    reports_folder_path = project_root + "/data/reports"
    logs_folder_path = project_root + "/data/logs"


class CheckBoxesKeys(Enum):
    notification_bad_posture = "notify_bad_posture"
    enable_sound = "enable_sound"
    rand_bad_posture_command = "bad_posture_command"


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
