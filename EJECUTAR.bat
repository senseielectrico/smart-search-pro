@echo off
cd /d "%~dp0"
echo Iniciando Smart Search...
start "" pythonw main.py
echo Aplicacion lanzada. Esta ventana se cerrara.
timeout /t 2 >nul
