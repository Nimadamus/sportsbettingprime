@echo off
title RealAIGirls.com - Upload System
color 0A

echo.
echo ================================================================
echo               REALAIGIRLS.COM - UPLOAD SYSTEM
echo ================================================================
echo.
echo This will find ALL your images and get them ready to upload!
echo.
echo What this does:
echo   1. Finds all images on your computer
echo   2. Removes duplicates automatically
echo   3. Creates beautiful gallery pages
echo   4. Saves to your Desktop ready for upload
echo.
echo ================================================================
echo.
pause

echo.
echo [1/3] Installing dependencies...
pip install --quiet Pillow watchdog
echo      Done!

echo.
echo [2/3] Finding all your images...
echo      This may take 5-10 minutes...
echo.
python find_and_organize.py

echo.
echo [3/3] Processing images...
echo.
python process_selected_images.py

echo.
echo ================================================================
echo                        SUCCESS!
echo ================================================================
echo.
echo Your gallery is ready on your Desktop:
echo    REALIAIGRILS NEW PAGES
echo.
echo NEXT STEP: Upload to realaigirls.com
echo.
echo Upload these 3 folders via FTP:
echo    images/       --^> /public_html/images/
echo    thumbnails/   --^> /public_html/thumbnails/
echo    pages/        --^> /public_html/pages/
echo.
echo FTP Info:
echo    Host: ftp.realaigirls.com
echo    Use your GoDaddy FTP username and password
echo.
echo ================================================================
echo.
echo Open UPLOAD_INSTRUCTIONS.txt for step-by-step FTP guide
echo.
pause
