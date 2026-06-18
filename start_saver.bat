@echo off
:: Launches Wi-Fi Watcher using the local venv, no console window.
:: Put a shortcut to THIS file in your Startup folder to auto-start at login.
::
:: Startup folder path:
::   shell:startup   (current user)
::
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0wifi_saver.py"
