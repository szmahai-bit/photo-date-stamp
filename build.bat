@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  Photo Date Stamp - Build single-file EXE
echo ========================================
echo.

echo [0/2] Generate app icon ...
python make_icon.py
if errorlevel 1 (
  echo [ERROR] Icon generation failed. Make sure Pillow is installed:
  echo          pip install -r requirements-dev.txt
  pause
  exit /b 1
)

echo [1/2] Building with PyInstaller ...
python -m PyInstaller build.spec --noconfirm --clean
if errorlevel 1 (
  echo [ERROR] Build failed. Make sure pyinstaller is installed:
  echo          pip install -r requirements-dev.txt
  pause
  exit /b 1
)

echo.
echo [DONE] Output EXE is in the dist\ folder.
pause
