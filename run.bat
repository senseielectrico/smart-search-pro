@echo off
REM =========================================================================
REM Smart Search Launcher for Windows
REM =========================================================================
REM
REM This batch file launches the Smart Search application.
REM It uses the production executable smart_search.pyw which runs without
REM a console window.
REM
REM Usage:
REM    run.bat                  - Run the application
REM    run.bat --console        - Run with console window visible
REM
REM Requirements:
REM    - Python 3.8+
REM    - PyQt6: pip install PyQt6>=6.6.0
REM    - pywin32: pip install pywin32
REM    - comtypes: pip install comtypes
REM
REM =========================================================================

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Check if --console flag is passed
if "%1"=="--console" (
    echo Starting Smart Search (with console window)...
    python "%SCRIPT_DIR%main.py"
) else (
    echo Starting Smart Search...

    REM Use pythonw.exe if available (no console window)
    where pythonw.exe >nul 2>&1
    if !errorlevel! equ 0 (
        pythonw.exe "%SCRIPT_DIR%smart_search.pyw"
    ) else (
        REM Fallback to python.exe (may show console briefly)
        python "%SCRIPT_DIR%smart_search.pyw"
    )
)

if errorlevel 1 (
    echo.
    echo Error: Failed to start application
    echo.
    echo Please ensure all dependencies are installed:
    echo   pip install PyQt6 pywin32 comtypes
    echo.
    echo For more information, check the error log in:
    echo   %%USERPROFILE%%\.smart_search\error.log
    echo.
    pause
)

endlocal

