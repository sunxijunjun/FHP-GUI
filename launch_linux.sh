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
    echo "Please install Python 3 using your distribution's package manager."
    echo "For example, on Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install python3"
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