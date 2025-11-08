#!/usr/bin/env python3
"""
Process Selected Images
Processes a list of image paths (from the finder tool) and creates gallery
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List
import logging

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed!")
    print("Please run: pip install Pillow")
    sys.exit(1)

# Import the desktop processor
sys.path.insert(0, os.path.dirname(__file__))
from process_to_desktop import DesktopGalleryProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def load_image_list(file_path):
    """Load list of image paths from text file"""
    images = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and os.path.exists(line):
                images.append(line)
    return images


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         PROCESS SELECTED IMAGES                           ║
║         Create gallery from your selected images          ║
╚═══════════════════════════════════════════════════════════╝
""")

    print("\nThis tool processes images from a list of file paths.")
    print("(Use the find_and_organize.py tool first to create the list)\n")

    print("How do you want to provide the image list?")
    print("  1. From a text file (one path per line)")
    print("  2. Paste paths directly")
    print("  3. Load from image catalog (image_catalog.json)")

    choice = input("\nEnter choice (1-3): ").strip()

    image_paths = []

    if choice == '1':
        file_path = input("\nEnter path to text file: ").strip().strip('"').strip("'")
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
        image_paths = load_image_list(file_path)

    elif choice == '2':
        print("\nPaste image paths (one per line, empty line to finish):")
        while True:
            line = input().strip()
            if not line:
                break
            if os.path.exists(line):
                image_paths.append(line)
            else:
                print(f"  ⚠️  File not found: {line}")

    elif choice == '3':
        # Load from catalog
        desktop = str(Path.home() / "Desktop")
        catalog_file = os.path.join(desktop, "image_catalog.json")

        if not os.path.exists(catalog_file):
            catalog_file = input("Enter path to image_catalog.json: ").strip().strip('"').strip("'")

        if not os.path.exists(catalog_file):
            print(f"Error: Catalog not found: {catalog_file}")
            return

        with open(catalog_file, 'r') as f:
            catalog = json.load(f)

        print(f"\nCatalog contains {len(catalog['images'])} images")
        print("\nOptions:")
        print("  1. Process all images")
        print("  2. Process only images 1000x1000+")
        print("  3. Process only images 512x512+")

        filter_choice = input("\nEnter choice (1-3): ").strip()

        if filter_choice == '1':
            image_paths = [img['path'] for img in catalog['images']]
        elif filter_choice == '2':
            image_paths = [
                img['path'] for img in catalog['images']
                if img['dimensions'][0] >= 1000 and img['dimensions'][1] >= 1000
            ]
        elif filter_choice == '3':
            image_paths = [
                img['path'] for img in catalog['images']
                if img['dimensions'][0] >= 512 and img['dimensions'][1] >= 512
            ]

    else:
        print("Invalid choice.")
        return

    if not image_paths:
        print("\nNo images to process!")
        return

    print(f"\n✓ Loaded {len(image_paths)} image(s)")

    # Create temporary source folder structure
    print("\nCreating temporary folder structure...")
    temp_folder = os.path.join(Path.home(), ".temp_image_processing")
    os.makedirs(temp_folder, exist_ok=True)

    # Copy or symlink images to temp folder
    print("Preparing images...")
    for i, img_path in enumerate(image_paths):
        # Create symlink or copy
        dest = os.path.join(temp_folder, f"{i:04d}_{os.path.basename(img_path)}")
        try:
            if os.name == 'nt':  # Windows
                import shutil
                shutil.copy2(img_path, dest)
            else:  # Unix/Mac
                if os.path.exists(dest):
                    os.remove(dest)
                os.symlink(img_path, dest)
        except Exception as e:
            logger.error(f"Error preparing {img_path}: {e}")

    # Process using the desktop processor
    print("\n" + "="*60)
    processor = DesktopGalleryProcessor()
    processor.setup_output_folder()
    processor.process_all_images(temp_folder)
    processor.generate_all_pages()
    processor.create_readme()

    # Cleanup temp folder
    print("\nCleaning up...")
    try:
        import shutil
        shutil.rmtree(temp_folder)
    except:
        pass

    print("\n" + "="*60)
    print("✓ ALL DONE!")
    print("="*60)

    print(f"\nYour gallery has been created at:")
    print(f"  {processor.output_folder}")

    print(f"\nTo view your gallery:")
    print(f"  Open: {os.path.join(processor.output_folder, 'pages', 'index.html')}")

    print(f"\nTo upload to realaigirls.com:")
    print(f"  1. Upload 'images' folder → /public_html/images/")
    print(f"  2. Upload 'thumbnails' folder → /public_html/thumbnails/")
    print(f"  3. Upload 'pages' folder → /public_html/pages/")


if __name__ == "__main__":
    main()
