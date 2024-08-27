from logger import Logger
import pandas as pd


def test_0():
    # get save dataframe
    file_name = "data_20240724145543_well_tested.csv"
    path = "data/logs/" + file_name
    save_path = "data/logs/" + file_name.split('.')[0] + '_test.' + file_name.split('.')[1]
    df_orig = pd.read_csv(path)
    print(df_orig)
    df = Logger.process_bad_posture_command_col(df_orig, replace_other_notes=True)
    print(df)
    df.to_csv(save_path)
    print('Data saved to: ', save_path)


def test_1():
    # chosen_time = "2024-07-25 17:12:47"
    file_name = "data_20240726162335.csv"
    path = "data/logs/" + file_name
    save_path = "data/logs/" + file_name.split('.')[0] + '_test.' + file_name.split('.')[1]
    df_orig = pd.read_csv(path)
    print(df_orig)
    df = Logger.process_alarm_notifications(df_orig)
    print(df)
    df.to_csv(save_path)
    print('Data saved to: ', save_path)


def show_system_performance() -> None:
    from performance_tester import PerformanceTester
    perf_tester = PerformanceTester()
    perf_tester.show_all_results()


def design_test():
    from ttkthemes import ThemedTk
    from tkinter import ttk

    def greet():
        name = name_entry.get()
        if name:
            greeting_label.config(text=f"Hello, {name}!")
        else:
            greeting_label.config(text="Please enter your name.")

    selected_theme = "yaru"

    # Create the root window
    root = ThemedTk()
    root.title("Themed Tkinter App")

    # Set the theme
    root.set_theme(selected_theme)

    # Create the main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(padx=20, pady=20)

    # Create the name entry
    name_label = ttk.Label(main_frame, text="Enter your name:")
    name_label.pack(pady=10)

    name_entry = ttk.Entry(main_frame)
    name_entry.pack(pady=10)

    # Create the greet button
    greet_button = ttk.Button(main_frame, text="Greet", command=greet)
    greet_button.pack(pady=10)

    # Create the greeting label
    greeting_label = ttk.Label(main_frame, text="")
    greeting_label.pack(pady=10)

    # Run the main loop
    root.mainloop()


def test_models_threshold_postprocessing():
    path = "gui/data/logs/session_20240814130725/integrated_data_20240814130725.csv"
    df = pd.read_csv(path, index_col=False)
    df = Logger.process_models_thresholds_gaps(df)
    new_path = path.replace('integrated', 'test_all')
    df.to_csv(new_path)


def test_serial_comm():
    from serial_manager import SerialManager
    serial_m = SerialManager(port="COM6")
    line = serial_m.test_readline()
    print(line)


def test_custom_dict_update() -> None:
    import numpy as np

    def is_empty_value(value) -> bool:
        return value is np.nan or value == '' or value is None

    def get_valid_pairs(data: dict) -> dict:
        return {key: value for key, value in data.items() if not is_empty_value(value)}

    def custom_dict_update(original_data: dict, new_data: dict) -> dict:
        original_data.update(get_valid_pairs(new_data))
        return original_data

    data1 = {'timestamp': '1650004', 'local_time': '2024-08-20 15:23:04', 'sensor_2': 10, 'sensor_4': np.nan, 'bbox_x1': np.nan,
             'bbox_y1': np.nan, 'bbox_x2': np.nan, 'bbox_y2': np.nan, 'mv_1': np.nan, 'mv_2': np.nan, 'mv_3': np.nan, 'mv_4': np.nan,
             'left_eye_x': np.nan, 'left_eye_y': np.nan, 'right_eye_x': np.nan, 'right_eye_y': np.nan, 'nose_x': np.nan, 'nose_y': np.nan,
             'mouth_left_x': np.nan, 'mouth_left_y': np.nan, 'mouth_right_x': np.nan, 'mouth_right_y': np.nan, 'fhp': np.nan,
             'prediction': np.nan, 'notes': '', 'user_id': -1, 'bad_posture_command': 'no', 'alarm_notification': 'no',
             'notification_interval': np.nan, 'feedback': np.nan}
    data2 = {'timestamp': '1650004', 'local_time': '2024-08-20 15:23:04', 'sensor_2': np.nan, 'sensor_4': np.nan, 'bbox_x1': np.nan,
             'bbox_y1': np.nan, 'bbox_x2': np.nan, 'bbox_y2': np.nan, 'mv_1': 307, 'mv_2': 311, 'mv_3': 304, 'mv_4': 323,
             'left_eye_x': np.nan, 'left_eye_y': np.nan, 'right_eye_x': np.nan, 'right_eye_y': np.nan, 'nose_x': np.nan, 'nose_y': np.nan,
             'mouth_left_x': np.nan, 'mouth_left_y': np.nan, 'mouth_right_x': np.nan, 'mouth_right_y': np.nan, 'fhp': np.nan,
             'prediction': np.nan, 'notes': '', 'user_id': -1, 'bad_posture_command': 'no', 'alarm_notification': 'no',
             'notification_interval': np.nan, 'feedback': np.nan}

    result = custom_dict_update(original_data=data1, new_data=data2)
    print(result)


if __name__ == '__main__':
    test_custom_dict_update()
