@echo off
REM Covers Contest Scraper - Windows Batch File
REM Double-click this file to run!

echo ==========================================
echo  COVERS CONSENSUS SCRAPER
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found!
echo.
echo Installing/checking dependencies...
pip install --quiet requests beautifulsoup4 lxml

echo.
echo Running scraper...
echo ==========================================
echo.

python quick_covers_scraper.py

echo.
echo ==========================================
echo Done!
echo ==========================================
echo.
echo Data saved to: covers_data.json
echo.
echo Next: Visit https://contests.covers.com/survivor
echo       to see what they're picking!
echo.
pause
