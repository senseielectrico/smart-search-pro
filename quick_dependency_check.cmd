@echo off
REM Quick dependency check - simplified version
REM This is a faster alternative to install_dependencies.bat if you just want to verify

setlocal enabledelayedexpansion

echo.
echo ======================================
echo Smart Search - Quick Dependency Check
echo ======================================
echo.

python check_dependencies.py

pause
