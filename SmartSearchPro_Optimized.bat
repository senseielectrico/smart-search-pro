@echo off
REM Smart Search Pro - Optimized Launcher
REM Uses performance-optimized entry point with lazy loading and caching

title Smart Search Pro (Optimized)

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if psutil is installed (new dependency)
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependency: psutil
    pip install psutil>=5.9.0
    if errorlevel 1 (
        echo WARNING: Failed to install psutil. Performance monitoring will be limited.
        echo.
    )
)

REM Run optimized version
echo Starting Smart Search Pro (Optimized)...
echo.

python app_optimized.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)

exit /b %errorlevel%
