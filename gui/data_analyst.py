from datetime import datetime
from typing import Union
import numpy as np
import ui_config
import torch
import pandas as pd
import os
import torch.nn as nn
import joblib  
import onnxruntime as ort

# Define input columns for each model

model1_input_columns = [ 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
                'left_eye_x', 'left_eye_y', 'right_eye_x', 'right_eye_y',
                'nose_x', 'nose_y',
                'mouth_left_x', 'mouth_left_y', 'mouth_right_x', 'mouth_right_y',
                'facew', 'faceh', 'facea','height','weight']

model2_input_columns = [
    'weight', 'height', 'sensor4_2_diff', 'Sensor 2', 'Sensor 4'
]

# Input columns for threshold method
threshold_input_columns = [
    'sensor4_2_diff','size'
]

class SimplifiedBinaryClassificationModel(nn.Module):
    def __init__(self, input_size):
        super(SimplifiedBinaryClassificationModel, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.dropout1 = nn.Dropout(0.5)

        self.fc2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.dropout2 = nn.Dropout(0.5)

        # New hidden layer
        self.fc3 = nn.Linear(64, 32)
        self.bn3 = nn.BatchNorm1d(32)
        self.dropout3 = nn.Dropout(0.5)

        self.fc4 = nn.Linear(32, 1)  # Updated final layer

    def forward(self, x):
        x = torch.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        x = torch.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        # Forward pass through the new hidden layer
        x = torch.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)

        x = self.fc4(x)  # No activation for final layer (logits)
        return x

class DataAnalyst:
    """ Define the computation functions relevant for the project
    Provide convenience in testing and modification of algorithms
    Note: the dict is immutable object
    """
    def __init__(self):
        self.recent_data = {"sensor_2": np.nan, "sensor_4": np.nan}
        self.data = dict()
        self.thresholds = {
            "XS": 66.638889,
            "S": 67.769231,
            "M": 80.333333,
            "L": 88.857143,
            "XL": 95.187500
        }

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

    def detect_anomaly(self, data: dict, user_features: np.array) -> Union[None, int]:
        """
        Detects anomalies in posture data.

        Args:
            data (dict): A dictionary containing sensor data.
            user_features (np.array): An array containing user features.
            model: Path to the model used for detecting anomalies. If None, the default model will be used.

        Returns:
            Union[None, int]: Returns 1 if an anomaly is detected, 0 otherwise, None if data is insufficient.
        """
            
        def load_pytorch_model(model_path, input_columns):
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = SimplifiedBinaryClassificationModel(input_size=len(input_columns)).to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            return model, device

        def predict_with_pytorch_model(df, model, device, input_columns, scaler, prediction_column_name):
            missing_columns = set(input_columns) - set(df.columns)
            if missing_columns:
                print(f"Warning: Missing columns for {prediction_column_name}: {missing_columns}")
                df[prediction_column_name] = np.nan
                return df

            features_df = df[input_columns]
            nan_mask = features_df.isnull().any(axis=1)
            predictions = np.full(len(df), np.nan)
            valid_indices = (~nan_mask).to_numpy().nonzero()[0]
            if len(valid_indices) > 0:
                valid_features = features_df.iloc[valid_indices].values
                valid_features_scaled = scaler.transform(valid_features)
                inputs = torch.tensor(valid_features_scaled, dtype=torch.float32).to(device)
                with torch.no_grad():
                    outputs = model(inputs).cpu().squeeze().numpy()
                    probabilities = torch.sigmoid(torch.tensor(outputs)).numpy()
                    binary_predictions = (probabilities > 0.5).astype(int) #tune!
                    predictions[valid_indices] = binary_predictions

            df[prediction_column_name] = predictions
            return df

        def predict_with_onnx_model(df, session, input_columns, scaler, prediction_column_name):
            missing_columns = set(input_columns) - set(df.columns)
            if missing_columns:
                print(f"Warning: Missing columns for {prediction_column_name}: {missing_columns}")
                df[prediction_column_name] = np.nan
                return df

            features_df = df[input_columns]
            nan_mask = features_df.isnull().any(axis=1)
            predictions = np.full(len(df), np.nan)
            valid_indices = (~nan_mask).to_numpy().nonzero()[0]
            if len(valid_indices) > 0:
                valid_features = features_df.iloc[valid_indices].values
                valid_features_scaled = scaler.transform(valid_features)
                input_name = session.get_inputs()[0].name
                inputs = {input_name: valid_features_scaled.astype(np.float32)}
                outputs = session.run(None, inputs)

                probabilities = outputs[0].squeeze()
                binary_predictions = (probabilities > 0.5).astype(int) #tune!
                predictions[valid_indices] = binary_predictions

            df[prediction_column_name] = predictions
            return df

        # Threshold method prediction
        def predict_with_threshold(df: pd.DataFrame, input_columns: list, threshold_mapping: dict, prediction_column_name):
            missing_columns = set(input_columns) - set(df.columns)
            if missing_columns:
                print(f"Warning: Missing columns for {prediction_column_name}: {missing_columns}")
                df[prediction_column_name] = np.nan
                return df

            df[prediction_column_name] = df.apply(
                lambda row: (
                    0 if row['sensor4_2_diff'] > threshold_mapping.get(row['size'], np.nan) else 1
                ) if not pd.isnull(row['sensor4_2_diff']) else np.nan,
                axis=1
            )

            return df

        if user_features is None:
            print("No user features available.")
            return None
        
        #特征工程新建的列：
        data['sensor4_2_diff'] = data['Sensor 4'] - data['Sensor 2']
        data['diff2'] = data['sensor4_2_diff'] / data['Sensor 2']
        data['diff4'] = data['sensor4_2_diff'] / data['Sensor 4']
        data['facew'] = data['bbox_x2'] - data['bbox_x1']
        data['faceh'] = data['bbox_y2'] - data['bbox_y1']
        data['facea'] = data['facew'] * data['faceh']
        data['facea2'] = data['facea'] / data['Sensor 2']
        data['facea4'] = data['facea'] / data['Sensor 4']
        data['height'] = user_features[3]
        data['weight'] = user_features[2]
        def map_size(height):
            if height < 157:
                return 'XS'
            elif 157 <= height < 162:
                return 'S'
            elif 162 <= height < 167:
                return 'M'
            elif 167 <= height < 172:
                return 'L'
            else:
                return 'XL'
        data['size'] = map_size(data['height'])
        self.data = data

        models_dir = ui_config.FilePaths.model_path.value

        # Model 1 (PyTorch)
        model1_path = os.path.join(models_dir, 'voting_model3.pth')
        model1_scaler_path = os.path.join(models_dir, 'voting_model3_scaler.joblib')
        model1_scaler = joblib.load(model1_scaler_path)
        model1, device1 = load_pytorch_model(model1_path, model1_input_columns)
        #model 1 in tuning. now still out puts a lot 0. since phase 2 data were smaller.

        # Model 2 (ONNX)
        model2_onnx_path = os.path.join(models_dir, 'voting_model2.onnx')
        model2_scaler_path = os.path.join(models_dir, 'model2scaler.pkl')
        model2_scaler = joblib.load(model2_scaler_path)
        model2_session = ort.InferenceSession(model2_onnx_path)

        df = pd.DataFrame(data, index=[0])
        df_predictions = df.copy()
        
        # Predict with model1 (PyTorch)
        df_predictions = predict_with_pytorch_model(
            df_predictions, model1, device1, model1_input_columns, model1_scaler, 'prediction_model1'
        )

        # Predict with model2 (ONNX)
        df_predictions = predict_with_onnx_model(
            df_predictions, model2_session, model2_input_columns, model2_scaler, 'prediction_model2'
        )

        # Predict with threshold method
        df_predictions = predict_with_threshold(
            df_predictions, threshold_input_columns, self.thresholds, 'prediction_threshold'
        )

        df_predictions['voting_result'] = df_predictions.apply(
            lambda row: 0 if row['prediction_threshold'] == 0
            else (0 if row['prediction_model1'] == 0 and row['prediction_model2'] == 0 else 1),
            axis=1
        )
        """
        If prediction_threshold is 0, set voting_result to 0 directly; otherwise, check if both prediction_model1 and prediction_model2 are 0. If they are, 
        set voting_result to 0; otherwise, set it to 1.
        The purpose of this design is that, under normal circumstances, incorrect posture can be determined based on the threshold. 
        However, there are some situations where the threshold value may be too small. In such cases, the threshold alone cannot make a reliable judgment, 
        so the predictions from the two models are used. If both models predict 0, the output is set to 0 to reduce the number of false alarms.
        
        The threshold is prioritized because it can be quickly adjusted based on the accuracy of alerts provided by user feedback.
        """
        print(
            f"{df_predictions[['prediction_model1','prediction_model2','prediction_threshold','voting_result']]}\nfor data:\n{df}"
        )
        return df_predictions['voting_result'].iloc[-1]

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

    def update_threshold(self, increment: float):
        try:
            self.thresholds[self.data['size']] += increment
        except KeyError:
            print("The user's size is not defined.")
            return

    def get_threshold(self) -> float:
        try:
            return self.thresholds[self.data['size']]
        except KeyError:
            print("The user's size is not defined.")

    @staticmethod
    def custom_dict_update(original_data: dict, new_data: dict) -> dict:
        def is_empty_value(value) -> bool:
            return value is np.nan or value == '' or value is None

        def get_valid_pairs(data: dict) -> dict:
            return {key: value for key, value in data.items() if not is_empty_value(value)}
        original_data.update(get_valid_pairs(new_data))  # updates data inplace
        return original_data
