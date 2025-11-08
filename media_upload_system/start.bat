@echo off
REM Quick Start Script for Automated Media Upload System (Windows)

echo ===============================================================
echo          AUTOMATED MEDIA UPLOAD SYSTEM - SETUP
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

echo Python found
echo.

REM Install dependencies
echo Checking dependencies...
pip install -r media_upload_system\requirements.txt
echo.

echo ===============================================================
echo                   SETUP COMPLETE!
echo ===============================================================
echo.
echo Starting the automated media upload system...
echo.
echo Drop your images/videos into:
echo    -^> media_upload_system\upload_here\
echo.
echo Gallery pages will be created in:
echo    -^> pages\
echo.
echo Press Ctrl+C to stop the system
echo.
echo ---------------------------------------------------------------
echo.

REM Start the system
python media_upload_system\auto_uploader.py

pause
