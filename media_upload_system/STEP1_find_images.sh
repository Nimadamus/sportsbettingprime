#!/bin/bash

# STEP 1: Find and Organize All Your Images

echo "==============================================================="
echo "         STEP 1: FIND AND ORGANIZE YOUR IMAGES"
echo "==============================================================="
echo ""
echo "This will scan your computer for images and help you select"
echo "which ones to process."
echo ""
read -p "Press Enter to continue..."

python3 media_upload_system/find_and_organize.py
