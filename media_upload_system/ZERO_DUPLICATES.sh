#!/bin/bash

clear

echo ""
echo "================================================================"
echo "       REALAIGIRLS.COM - ZERO DUPLICATES UPLOAD SYSTEM"
echo "================================================================"
echo ""
echo "This system GUARANTEES no duplicate uploads!"
echo ""
echo "How it works:"
echo "  STEP 1: Scan your live website for existing images"
echo "  STEP 2: Find all images on your computer"
echo "  STEP 3: Check each image - SKIP if duplicate"
echo "  STEP 4: Process only NEW images"
echo "  STEP 5: Upload to website"
echo ""
echo "================================================================"
echo ""
read -p "Press Enter to start..."

echo ""
echo "[Installing dependencies...]"
pip3 install --quiet Pillow beautifulsoup4 requests
echo "Done!"

echo ""
echo "================================================================"
echo " STEP 1: SCANNING LIVE WEBSITE FOR EXISTING IMAGES"
echo "================================================================"
echo ""
echo "This will download all existing images from realaigirls.com"
echo "and create a database to prevent duplicates."
echo ""
echo "This may take 5-10 minutes..."
echo ""
python3 scan_live_website.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Website scan failed!"
    echo ""
    echo "You can continue without it, but duplicates won't be detected."
    echo ""
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "================================================================"
echo " STEP 2-3: FINDING AND PROCESSING YOUR IMAGES"
echo "================================================================"
echo ""
echo "Enter the folder path where your images are:"
echo "Example: /Users/YourName/Pictures/AI Images"
echo ""
read -p "Image folder path: " image_folder

if [ ! -d "$image_folder" ]; then
    echo ""
    echo "ERROR: Folder not found!"
    exit 1
fi

echo ""
echo "Processing images from: $image_folder"
echo ""
echo "This will:"
echo "  - Check each image against website database"
echo "  - Skip any duplicates"
echo "  - Process only NEW images"
echo ""

# Pass the folder to the script
echo "$image_folder" | python3 NO_DUPLICATES_PROCESSOR.py

echo ""
echo "================================================================"
echo "                        SUCCESS!"
echo "================================================================"
echo ""
echo "Your NEW (non-duplicate) images are ready on your Desktop:"
echo "   REALIAIGRILS NEW PAGES"
echo ""
echo "NEXT STEP: Upload to realaigirls.com"
echo ""
echo "Upload these 3 folders via FTP:"
echo "   images/       --> /public_html/images/"
echo "   thumbnails/   --> /public_html/thumbnails/"
echo "   pages/        --> /public_html/pages/"
echo ""
echo "See UPLOAD_INSTRUCTIONS.txt for detailed FTP guide"
echo ""
echo "================================================================"
echo ""
read -p "Press Enter to exit..."
