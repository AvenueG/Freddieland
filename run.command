#!/bin/bash
# Double-click this file on Mac to run the Gamified Task System

# Navigate to the directory containing this script
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python3 to run this application."
    exit 1
fi

# Ensure requirements are installed (silently)
echo "Ensuring dependencies are installed..."
python3 -m pip install -r requirements.txt -q

# Run the Streamlit application
echo "Starting Gamified Task System..."
python3 -m streamlit run gamified_task_app.py
