#!/bin/bash

cd gui
echo "Launching application..."
python3 main.py
exit_code=$?

if [ $exit_code -ne 0 ]; then
  echo "Failed to launch application."
  echo "Checking Python installation..."
  python3 --version > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "Python 3 is not installed or not configured properly."
    echo "Please download and install the latest version of Python from:"
    echo "https://www.python.org/downloads/"
    echo "Ensure that you select the option to 'Add Python to PATH' during installation."
    exit 1
  else
    echo "Python 3 is installed. Checking for missing packages..."
    cd ..
    echo "Installing packages..."
    pip3 install -r requirements.txt > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "Failed to install packages. Please ensure you have the necessary permissions and try again."
    else
      echo "Packages installed successfully. Launching application..."
      cd gui
      python3 main.py
    fi
  fi
fi

echo "Application closed."