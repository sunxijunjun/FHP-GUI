"""
This module is used to play sound files in the background.
Please save the sound files in the 'audio' folder.
To play a sound, import the 'play_sound_in_thread' function and call it with the file name.
If no file name is provided, the default sound file is 'notification.wav'.
"""

import platform
import threading
import os

# Detect the operating system
current_os = platform.system()

# Conditional import based on the operating system
if current_os == "Windows":
    import winsound
elif current_os == "Darwin":  # macOS
    import subprocess
elif current_os == "Linux":
    import subprocess
else:
    print(f"Unsupported operating system for sound playing: {current_os}")

def play_sound(file_name:str  = "notification.wav"):
        audio_file = os.path.join(os.path.dirname(__file__), "audio", file_name)
        if current_os == "Windows":
            winsound.PlaySound(audio_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif current_os == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file])
        elif current_os == "Linux":
            subprocess.run(["aplay", audio_file])
        else:
            print("Sound playback is not supported on this operating system.")

def play_sound_in_thread(file_name:str  = "notification.wav"):
    threading.Thread(target=play_sound, args=(file_name,)).start()