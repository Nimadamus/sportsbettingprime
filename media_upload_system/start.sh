#!/bin/bash

# Quick Start Script for Automated Media Upload System

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         AUTOMATED MEDIA UPLOAD SYSTEM - SETUP             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3 first: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed!"
    echo "Please install pip first"
    exit 1
fi

echo "✓ pip found"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r media_upload_system/requirements.txt
    echo ""
fi

echo "✓ All dependencies installed"
echo ""

# Make the script executable
chmod +x media_upload_system/auto_uploader.py

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  SETUP COMPLETE!                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Starting the automated media upload system..."
echo ""
echo "📁 Drop your images/videos into:"
echo "   → media_upload_system/upload_here/"
echo ""
echo "🌐 Gallery pages will be created in:"
echo "   → pages/"
echo ""
echo "Press Ctrl+C to stop the system"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Start the system
python3 media_upload_system/auto_uploader.py
