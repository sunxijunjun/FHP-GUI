@echo off

cd gui
echo Launching application...
python main.py
if %errorlevel% neq 0 (
  echo Failed to launch application.
  python --version > nul 2>&1
  if errorlevel 1 (
    echo Python is not installed or not configured properly.
    echo Please download and install the latest version of Python from:
    echo https://www.python.org/downloads/
    echo Ensure that you select the option to "Add Python to PATH" during installation.
    pause
    exit /b 1
  ) else (    
    echo Checking for missing packages...
    cd ..
    pip install -r requirements.txt
    if errorlevel 1 (
      echo Failed to install packages. Please ensure you have the necessary permissions and try again.
    ) else (
      echo Packages installed successfully. Launching application...
      cd gui
      python main.py 
    )
  )
)

echo Application closed.
pause