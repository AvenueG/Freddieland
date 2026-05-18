@echo off
REM Double-click this file on Windows to run the Gamified Task System

echo Ensuring dependencies are installed...
python -m pip install -r requirements.txt -q

echo Starting Gamified Task System...
python -m streamlit run gamified_task_app.py
pause
