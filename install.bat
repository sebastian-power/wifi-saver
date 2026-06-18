@echo off
echo Setting up Wi-Fi Watcher virtual environment...

:: Create venv in the same folder as this script
python -m venv "%~dp0venv"

echo Installing dependencies into venv...
"%~dp0venv\Scripts\pip.exe" install -r requirements.txt

echo.
echo Done! Use start_saver.bat to launch.
pause
