@echo off
REM Quick launcher for iPhone View
REM Run from Smart Search Pro directory

echo ========================================
echo iPhone View - Smart Search Pro
echo ========================================
echo.
echo Select an option:
echo.
echo 1. Run Full iPhone View Test
echo 2. Run Integration Example
echo 3. Run Widget Gallery Only
echo 4. View Documentation
echo 5. Exit
echo.

choice /c 12345 /n /m "Enter your choice (1-5): "

if errorlevel 5 goto :end
if errorlevel 4 goto :docs
if errorlevel 3 goto :widgets
if errorlevel 2 goto :integration
if errorlevel 1 goto :test

:test
echo.
echo Running iPhone View Test...
python test_iphone_view.py
goto :end

:integration
echo.
echo Running Integration Example...
python examples\iphone_view_integration.py
goto :end

:widgets
echo.
echo Running Widget Gallery...
python ui\iphone_widgets.py
goto :end

:docs
echo.
echo Opening documentation...
start IPHONE_VIEW_README.md
start IPHONE_VIEW_QUICKSTART.md
echo.
echo Documentation opened in default viewer.
pause
goto :end

:end
echo.
echo Goodbye!
