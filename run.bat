@echo off
chcp 65001 >nul
cd /d "%~dp0"
python photo_date_gui.py
if errorlevel 1 (
  echo.
  echo [NOTE] Python not found. Install Python 3.10+ and add it to PATH,
  echo        or edit this file to use the full path of your python.exe.
  pause
)
