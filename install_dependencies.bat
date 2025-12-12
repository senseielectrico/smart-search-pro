@echo off
REM ========================================
REM Smart Search - Dependency Installer
REM ========================================
REM This script installs all required Python dependencies for Smart Search
REM Requirements: Python 3.8+ with pip

setlocal enabledelayedexpansion

echo.
echo ======================================
echo Smart Search - Installing Dependencies
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing anyway...
)
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "REQUIREMENTS_FILE=%SCRIPT_DIR%requirements.txt"

REM Check if requirements.txt exists
if not exist "!REQUIREMENTS_FILE!" (
    echo ERROR: requirements.txt not found in %SCRIPT_DIR%
    echo Please ensure requirements.txt exists in the same directory as this script
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
echo.
python -m pip install -r "!REQUIREMENTS_FILE!"

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed!
    pause
    exit /b 1
)

echo.
echo ======================================
echo Dependencies installed successfully!
echo ======================================
echo.

REM Verify installation
echo Verifying installation...
python -c "import PyQt6; print('PyQt6: OK')" 2>nul || echo PyQt6: FAILED
python -c "import pywin32; print('pywin32: OK')" 2>nul || echo pywin32: FAILED
python -c "import comtypes; print('comtypes: OK')" 2>nul || echo comtypes: FAILED
python -c "import send2trash; print('send2trash: OK')" 2>nul || echo send2trash: FAILED

echo.
echo Installation complete! You can now run Smart Search.
echo.
pause
