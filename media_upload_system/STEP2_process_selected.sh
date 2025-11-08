#!/bin/bash

# STEP 2: Process Your Selected Images

echo "==============================================================="
echo "         STEP 2: PROCESS SELECTED IMAGES"
echo "==============================================================="
echo ""
echo "This will process the images you selected in Step 1 and create"
echo "beautiful gallery pages on your desktop."
echo ""
read -p "Press Enter to continue..."

python3 media_upload_system/process_selected_images.py
