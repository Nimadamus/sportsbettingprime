#!/bin/bash

# Quick Gallery Creator for Desktop

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         REALAIGIRLS GALLERY GENERATOR                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3 first: https://www.python.org/downloads/"
    exit 1
fi

# Install Pillow if needed
echo "Checking dependencies..."
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "Installing Pillow..."
    pip3 install Pillow
fi

echo ""
echo "Starting gallery generator..."
echo ""

# Run the processor
python3 media_upload_system/process_to_desktop.py
