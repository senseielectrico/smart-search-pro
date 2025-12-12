@echo off
REM =========================================================================
REM Smart Search - Automated Installation Script
REM =========================================================================
REM
REM This script automates the complete installation of Smart Search.
REM
REM It will:
REM  1. Check Python installation
REM  2. Install required packages
REM  3. Run pywin32 post-install
REM  4. Verify installation
REM  5. Create shortcuts (optional)
REM
REM Usage:
REM    install.bat
REM
REM =========================================================================

setlocal enabledelayedexpansion

cls
echo.
echo =========================================================================
echo Smart Search - Installation
echo =========================================================================
echo.

REM Get directory where this script is located
set SCRIPT_DIR=%~dp0

REM =========================================================================
REM Check Python
REM =========================================================================
echo [1/5] Checking Python installation...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo.
    echo Please ensure Python 3.8+ is installed and added to PATH:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   Python version: %PYTHON_VERSION%
echo.

REM =========================================================================
REM Install Dependencies
REM =========================================================================
echo [2/5] Installing dependencies...
echo.

echo   Installing PyQt6...
pip install PyQt6>=6.6.0 --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyQt6
    pause
    exit /b 1
)

echo   Installing pywin32...
pip install pywin32 --quiet
if errorlevel 1 (
    echo ERROR: Failed to install pywin32
    pause
    exit /b 1
)

echo   Installing comtypes...
pip install comtypes --quiet
if errorlevel 1 (
    echo ERROR: Failed to install comtypes
    pause
    exit /b 1
)

echo   Installation complete.
echo.

REM =========================================================================
REM Post-Install pywin32
REM =========================================================================
echo [3/5] Configuring pywin32...
echo.
echo   Running pywin32 post-install script...

python -m pip install --upgrade pywin32 --quiet
if errorlevel 1 (
    echo WARNING: pywin32 upgrade had issues, continuing...
)

REM Try to run post-install
python "%PYTHON_PATH%\Scripts\pywin32_postinstall.py" -install >nul 2>&1
if errorlevel 1 (
    REM Alternative: try using Python -m
    python -c "import sys; import pywin32_postinstall; pywin32_postinstall.install(['-install'])" >nul 2>&1
)

echo   pywin32 configuration complete.
echo.

REM =========================================================================
REM Verify Installation
REM =========================================================================
echo [4/5] Verifying installation...
echo.

python "%SCRIPT_DIR%verify_setup.py"

if errorlevel 1 (
    echo.
    echo Installation verification FAILED
    echo.
    echo Please check the output above and resolve any missing dependencies.
    echo.
    pause
    exit /b 1
)

echo.

REM =========================================================================
REM Create Desktop Shortcut (Optional)
REM =========================================================================
echo [5/5] Creating shortcuts...
echo.

REM Ask user if they want shortcuts
set /p CREATE_SHORTCUTS=Do you want to create desktop shortcuts? (Y/N):
if /i "%CREATE_SHORTCUTS%"=="Y" (
    echo.
    echo Creating desktop shortcut...

    REM Create shortcut using VBScript
    set SHORTCUT_PATH=%USERPROFILE%\Desktop\Smart Search.lnk
    set TARGET=%SCRIPT_DIR%start.bat

    (
        echo Set oWS = WScript.CreateObject("WScript.Shell"^)
        echo sLinkFile = "%SHORTCUT_PATH%"
        echo Set oLink = oWS.CreateShortcut(sLinkFile^)
        echo oLink.TargetPath = "%TARGET%"
        echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
        echo oLink.Description = "Smart Search - Advanced File Search"
        echo oLink.IconLocation = "%SCRIPT_DIR%smart_search.pyw"
        echo oLink.Save
    ) > "%TEMP%\create_shortcut.vbs"

    cscript.exe "%TEMP%\create_shortcut.vbs"
    del "%TEMP%\create_shortcut.vbs"

    echo   Desktop shortcut created!
    echo.
)

REM =========================================================================
REM Summary
REM =========================================================================
echo =========================================================================
echo Installation Complete!
echo =========================================================================
echo.
echo Smart Search is ready to use. You can launch it in several ways:
echo.
echo   1. Double-click: smart_search.pyw
echo   2. Run batch script: start.bat
echo   3. Console mode: start.bat --console
echo.
echo For more information, see: PRODUCTION_GUIDE.md
echo.
echo Press any key to continue...
pause >nul

endlocal
exit /b 0
