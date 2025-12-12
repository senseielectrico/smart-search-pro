@echo off
REM =========================================================================
REM Smart Search - Simple Launch Script
REM =========================================================================

cd /d "%~dp0"

echo Starting Smart Search...
echo.

REM Try to run without console window using pythonw
where pythonw.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw.exe smart_search.pyw
) else (
    REM Fallback to python if pythonw is not available
    python main.py
)

exit
