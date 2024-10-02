from datetime import datetime
from typing import Union
import numpy as np
import ui_config


class DataAnalyst:
    """ Define the computation functions relevant for the project
    Provide convenience in testing and modification of algorithms
    Note: the dict is immutable object
    """
    recent_data: dict[str, Union[int, float]]
    thresholds = {
        0: 48.5,#58.5,  # XS
        1: 49.5,#59.5,  # S
        2: 52.5,#62.5,  # M
        3: 56.5,#65.5,  # L
        4: 61.5 #91.5  # XL
    }
    default_threshold = 62.5

    def __init__(self):
        self.recent_data = {"sensor_2": np.nan, "sensor_4": np.nan}

    @staticmethod
    def detect_anomaly_test(data: dict[str, list[int]]) -> Union[None, int]:
        """ Return the index of data which represent the incorrect posture """
        sensor_2, sensor_4 = "Sensor 2", "Sensor 4"
        if (sensor_2 in data and sensor_4 in data and
                data[sensor_2] and data[sensor_4]):
            if (data[sensor_4][-1] - data[sensor_2][-1]) >= 150:
                return 1
            else:
                return 0
        return None

    def detect_anomaly(self, data: dict, user_features: np.array, model) -> Union[None, int]:
        """
        Detects anomalies in posture data.

        Args:
            data (dict): A dictionary containing sensor data.
            user_features (np.array): An array containing user features.
            model: A model for detecting anomalies (not used in this simplified example).

        Returns:
            Union[None, int]: Returns 1 if an anomaly is detected, 0 otherwise, None if data is insufficient.
        """
        # 定义传感器名称
        sensor_2, sensor_4 = "Sensor 2", "Sensor 4"

        # 检查传感器数据是否存在并且有效
        if sensor_2 in data and sensor_4 in data and data[sensor_2] and data[sensor_4]:
            print(f"recent_data: Sensor 2: {data[sensor_2][-1]}, Sensor 4: {data[sensor_4][-1]}")

            # 检查用户特征是否存在
            if user_features is None:
                print("No user features available.")
                return None

            # 计算两个传感器之间的差值
            sensor4_2_diff = data[sensor_4][-1] - data[sensor_2][-1]

            # 获取用户肩宽
            shoulder_size = user_features[1]
            threshold = self.thresholds.get(shoulder_size, self.default_threshold)

            # 比较传感器差值与阈值，判断是否存在异常
            prediction = 1 if sensor4_2_diff < threshold else 0
            print(f"sensor4_2_diff: {sensor4_2_diff}, threshold: {threshold}, prediction: {prediction}")

            return prediction

        print("Insufficient data for anomaly detection.")
        return None

    def get_time_interval(self, alarm_times: list[str]) -> float:
        """ Return time interval in format total seconds
        indicating how long the wrong posture has been detected
        """
        first, last = self.get_time_borders(alarm_times)
        first_datetime = self.timestamp_to_datetime(first)
        last_datetime = self.timestamp_to_datetime(last)
        delta = last_datetime - first_datetime
        return delta.total_seconds()

    @staticmethod
    def timestamp_to_datetime(timestamp: str) -> datetime:
        """ Timestamp is represented as "%I:%M:%S.%f %p, %d-%m-%y"
        and converted to datetime object for calculation convenience
        """
        time_format = ui_config.Measurements.time_format.value
        return datetime.strptime(timestamp, time_format)

    @staticmethod
    def get_time_borders(values: list[str]) -> tuple[str, str]:
        # get the last continuous interval among all alarm times
        values_reversed = ["|"] + values[::-1]  # get the last values
        counter = 0
        first_value = ""
        last_value = ""
        for i in range(len(values_reversed)):
            if values_reversed[i] == "|" and counter == 0:
                last_value = values_reversed[i + 1]
                counter += 1
                continue
            if values_reversed[i] == "|" and counter == 1:
                first_value = values_reversed[i - 1]
                counter += 1
                break
        return first_value, last_value

    @staticmethod
    def convert_to_specific_format(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        microseconds = round(((seconds % 1) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{microseconds:03d}"

    @staticmethod
    def get_axes_values(sensor_values: dict[str, list[int]],
                        sensor_timestamps: list[tuple[str]],
                        sensor: str,
                        upper_limit: Union[None, int],
                        lower_limit=None) -> tuple:
        """
        Retrieves the x and y values for the specified sensor, with optional upper and lower limits.

        Args:
            sensor_values (dict[str, list[int]]): consists of the sensor name and list of their values
            sensor_timestamps (list[str]): consists of the timestamps when new values were added respectively to the index of sensor values
            sensor (str): The name of the sensor.
            upper_limit (Union[None, int]): The upper limit for the number of data points to return. If `None`, all data points are returned.
            lower_limit (Union[None, int], optional): The lower limit for the number of data points to return. If `None`, the lower limit is set to 0. Defaults to `None`.

        Returns:
            Tuple[List[int], List[float]]: A tuple containing the x-axis values (list of integers) and the y-axis values (list of floats).
        """
        if not sensor_values.get(sensor):
            return [0], [0]
        x = list(range(len(sensor_values[sensor])))  # show index of the values
        # x = [':'.join(timestamp.split(':')[-2:]) for timestamp in sensor_timestamps]   # show MM:SS
        y = sensor_values[sensor]
        if upper_limit is None:
            return x, y

        if upper_limit and len(y) > upper_limit and lower_limit is None:
            x = x[-upper_limit:]
            y = y[-upper_limit:]
            return x, y

        x = x[lower_limit:upper_limit]
        y = y[lower_limit:upper_limit]
        return x, y

    def update_threshold(self, shoulder_size: int, increment: float):
        self.thresholds[shoulder_size] += increment

    def get_threshold(self, shoulder_size: int) -> float:
        return self.thresholds[shoulder_size]

    @staticmethod
    def custom_dict_update(original_data: dict, new_data: dict) -> dict:
        def is_empty_value(value) -> bool:
            return value is np.nan or value == '' or value is None

        def get_valid_pairs(data: dict) -> dict:
            return {key: value for key, value in data.items() if not is_empty_value(value)}
        original_data.update(get_valid_pairs(new_data))  # updates data inplace
        return original_data

    # def detect_anomaly(self, data: dict, user_features: np.array, model) -> Union[None, int]:
    #     values = data
    #     sensor_2, sensor_4 = "Sensor 2", "Sensor 4"
    #     if sensor_2 in data and sensor_4 in data and data[sensor_2] and data[sensor_4]:
    #         recent_data = np.array([[self.recent_data["sensor_2"], self.recent_data["sensor_4"]]])
    #         print("recent_data:", recent_data)
    #
    #         if user_features is None:
    #             print("No user features available.")
    #             return
    #
    #         print(f"User features: {user_features}")
    #
    #         sensor4_2_diff = data[sensor_4][-1] - data[sensor_2][-1]
    #         length = data[sensor_4][-1] * np.cos(np.radians(20)) - data[sensor_2][-1]
    #         ratio = length / user_features[4]  # flexibility
    #         cos_20 = np.cos(np.radians(20))
    #         sin_20 = np.sin(np.radians(20))
    #         tangent_d = (data[sensor_4][-1] * cos_20 - data[sensor_2][-1]) / (data[sensor_4][-1] * sin_20)
    #         degree = np.degrees(np.arctan(tangent_d))
    #
    #         dynamic_features = np.array(
    #             [length, degree, sensor4_2_diff, recent_data[0, 0], recent_data[0, 1], user_features[4], ratio])
    #
    #         input_data = np.hstack((user_features[:4], dynamic_features)).reshape(1, -1)
    #         print("input_data:", input_data)
    #
    #         prediction = model.predict(input_data)
    #         print("prediction:", prediction)
    #         if prediction[0][0] == 0:
    #             return len(data[sensor_2]) - 1
    #     return None
