@echo off
echo ============================================
echo  REALAIGIRLS.COM - Image Organizer
echo ============================================
echo.
echo This will help you organize and upload images!
echo.
echo STEP 1: Find all your images
echo STEP 2: Select which ones to upload
echo STEP 3: Create gallery pages ready for upload
echo.
echo Press any key to start...
pause > nul

echo.
echo Installing dependencies...
pip install Pillow watchdog

echo.
echo ============================================
echo  STEP 1: FINDING ALL YOUR IMAGES
echo ============================================
echo.
echo This will scan your computer for images.
echo It may take 5-10 minutes depending on how many you have.
echo.
python find_and_organize.py

echo.
echo ============================================
echo  STEP 2: SELECT IMAGES
echo ============================================
echo.
echo Opening the selection page...
echo Select which images you want to upload to realaigirls.com
echo Then download the selection as a text file.
echo.
start select_images.html
echo.
echo When you're done selecting, press any key to continue...
pause > nul

echo.
echo ============================================
echo  STEP 3: PROCESS SELECTED IMAGES
echo ============================================
echo.
python process_selected_images.py

echo.
echo ============================================
echo  ALL DONE!
echo ============================================
echo.
echo Your gallery is ready on your Desktop:
echo    REALIAIGRILS NEW PAGES
echo.
echo Upload these folders to realaigirls.com via FTP:
echo    - images/
echo    - thumbnails/
echo    - pages/
echo.
echo Press any key to exit...
pause > nul
