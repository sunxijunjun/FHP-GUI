# 🖥️ Posture Monitoring GUI
This project is developed by researchers and students from The Hong Kong Polytechnic University. It focuses on the development of a posture analysis patent device designed to monitor user postures while using a computer. This Graphical User Interface (GUI) allows users to interact with the prototype device, providing an intuitive interface to manage settings, monitor posture, and generate reports.
## Cloning This Repository

To clone this repository and switch to the `tested` branch, follow these steps:

1. **Open a terminal** on your local machine.
2. **Clone the repository** using the following command:
   ```bash
   git clone -b tested --single-branch https://github.com/sunxijunjun/FHP-GUI.git


## 🌟 Features
![9749fd169c8e906edd63c405f3971f6](https://github.com/user-attachments/assets/03069b5f-38cd-4e10-8e0d-93502111b161)

### 1. 📝 User Registration
During registration, users are prompted to provide personal information such as height, weight, and other relevant metrics. This data helps the algorithm to personalize posture analysis and offer more accurate recommendations for maintaining a healthy sitting posture.

![385929b9edfad9f6616cb4693801b86](https://github.com/user-attachments/assets/e5d164fd-e502-40f1-ad79-92b46a97e7f9)

### 2. 🔐 User Login
The system supports secure login for returning users, including a "Remember Me" option that allows users to log in quickly without entering their credentials each time. This feature ensures seamless access while maintaining data security.

![343d7c03e76dd1c1e34857c82737323](https://github.com/user-attachments/assets/29fe273f-89ee-4bdc-bfb0-27deec593779)

### 3. 📖 User Guide
A comprehensive user manual is provided within the GUI. It helps users set up and calibrate the device by offering step-by-step instructions. The guide includes calibration tips for sensor positioning, posture monitoring, and troubleshooting common issues to ensure accurate readings.

![869bb7b8d1d5d34ac58713c8cb94dae](https://github.com/user-attachments/assets/9be61da0-4201-49f1-b387-14d482719755)

### 4. ⚠️ Error Notifications
The application displays real-time error messages when there is a failure in detecting the user's posture or if the sensors are misaligned. These notifications help users quickly adjust the system to avoid incorrect posture measurements and ensure proper functioning of the device.

![f0ecc2f83710c17229e8ead9da0f535](https://github.com/user-attachments/assets/1c9f94d2-aea7-45b7-8831-16163760de3b)

### 5. ⚙️ Settings
The settings menu gives users control over various aspects of the device, including:

🔊 Sound and LED Control: Users can enable or disable sound alerts and LED indicators for better feedback during monitoring.

⏲️ Alert Frequency: Allows users to set the frequency of posture alerts. Users can choose from preset intervals (e.g., every 10 minutes) or customize according to their needs.

🛑 Pause Monitoring: Users can temporarily pause the posture monitoring system, useful during breaks or when the device isn't in use.

🎨 UI Theme Customization: The interface offers different themes, including light and dark modes, to provide an aesthetically pleasing and comfortable user experience.


### 6. 📊 Monitoring Report
After each session, the application generates a detailed monitoring report. This report includes:

· Total monitoring duration.

· The number of bad posture detections.

· Cumulative time spent in incorrect postures.

· These insights are valuable for users who want to track their progress and adjust their behavior to improve posture over time. 

![06f269b0a104914a6a19d07dd6ec93d](https://github.com/user-attachments/assets/43d1e602-106e-4e53-9652-25be9a32bd43)


### 7. 👁️ 20-20-20 Reminder
The GUI implements the 20-20-20 rule to reduce digital eye strain. Every 20 minutes, the system reminds users to:

· Take a 20-second break from the screen.

· Look at an object at least 20 feet away to help relax eye muscles.

This reminder helps users maintain eye health while working for extended periods in front of the computer.

![194b1c019390d3c2fab59bf8c77c2d6](https://github.com/user-attachments/assets/0e6cb714-b6c9-4d70-82b1-fce7b38cfbd1)

## 🚀 Current Status
The core framework of the application has been established and is functional.

## 🛠️ TODO:
1. Use thresholds and ML models to make predictions, a voting method is under development.
2. Rule out situations when prediction cannot be made, such as sensors miss focus or no facial key points detected.
3. Finalize GUI: Complete calinration function.  
## 👥 Contributors
The following people have contributed to the development and testing of this GUI:

Xijun SUN, Altair ISSAMETOV, Huanyu ZHANG, Qigang ZHANG, and Wenhan ZHENG.
