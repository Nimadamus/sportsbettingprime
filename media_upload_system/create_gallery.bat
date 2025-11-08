@echo off
REM Quick Gallery Creator for Desktop (Windows)

echo ===============================================================
echo          REALAIGIRLS GALLERY GENERATOR
echo ===============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3 first: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install Pillow if needed
echo Checking dependencies...
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing Pillow...
    pip install Pillow
)

echo.
echo Starting gallery generator...
echo.

REM Run the processor
python media_upload_system\process_to_desktop.py

pause
