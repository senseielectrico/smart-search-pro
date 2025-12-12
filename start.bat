@echo off
REM =========================================================================
REM Smart Search - Production Start Script
REM =========================================================================
REM
REM This is the main entry point for Smart Search application.
REM
REM Features:
REM  - Automatically detects and uses pythonw.exe (no console window)
REM  - Optional dependency verification
REM  - Error logging to ~/.smart_search/error.log
REM  - Console window support with --console flag
REM
REM Usage:
REM    start.bat                   - Run normally (no console)
REM    start.bat --check           - Verify dependencies first
REM    start.bat --console         - Run with console window visible
REM
REM Requirements:
REM    Python 3.8+ with:
REM    - PyQt6>=6.6.0
REM    - pywin32 (with post-install script run)
REM    - comtypes
REM
REM =========================================================================

setlocal enabledelayedexpansion

REM Get directory where this script is located
set SCRIPT_DIR=%~dp0

REM Parse arguments
set CHECK_DEPS=0
set CONSOLE_MODE=0

for %%A in (%*) do (
    if "%%A"=="--check" set CHECK_DEPS=1
    if "%%A"=="--console" set CONSOLE_MODE=1
)

REM =========================================================================
REM Dependency Check (Optional)
REM =========================================================================
if %CHECK_DEPS% equ 1 (
    echo.
    echo Verifying dependencies...
    echo.
    python "%SCRIPT_DIR%verify_setup.py"

    if errorlevel 1 (
        echo.
        echo Dependencies check failed. Please install required packages:
        echo   pip install PyQt6 pywin32 comtypes
        echo.
        pause
        exit /b 1
    )
    echo.
)

REM =========================================================================
REM Launch Application
REM =========================================================================
if %CONSOLE_MODE% equ 1 (
    REM Run with console window (for debugging)
    echo Smart Search - Console Mode
    echo ============================
    python "%SCRIPT_DIR%main.py"
) else (
    REM Run without console window (production)

    REM Try to use pythonw.exe first (Windows-only, no console)
    where pythonw.exe >nul 2>&1

    if !errorlevel! equ 0 (
        REM Found pythonw.exe - run without console
        start "" pythonw.exe "%SCRIPT_DIR%smart_search.pyw"
    ) else (
        REM Fallback to python.exe (may show console briefly)
        REM This is less ideal but works on all setups
        python "%SCRIPT_DIR%smart_search.pyw"
    )
)

REM =========================================================================
REM Error Handling
REM =========================================================================
if errorlevel 1 (
    REM Only show error message if not in console mode
    if %CONSOLE_MODE% equ 0 (
        echo.
        echo Smart Search - Error
        echo =====================
        echo.
        echo Failed to start application.
        echo.
        echo Possible causes:
        echo   1. Missing dependencies
        echo   2. Python not in PATH
        echo   3. Module import errors
        echo.
        echo Solutions:
        echo   1. Install dependencies: pip install PyQt6 pywin32 comtypes
        echo   2. Run with --console flag for detailed error messages
        echo   3. Check error log: %%USERPROFILE%%\.smart_search\error.log
        echo.
        pause
    )
    exit /b 1
)

endlocal
exit /b 0
