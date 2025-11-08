#!/usr/bin/env python3
"""
Smart Image Finder & Organizer
Finds all images on your computer, detects duplicates, helps you select which to process
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import logging

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed!")
    print("Please run: pip install Pillow")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageFinder:
    """Finds and organizes images across your computer"""

    def __init__(self):
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        self.skip_folders = {
            'Windows', 'Program Files', 'Program Files (x86)',
            'AppData', 'ProgramData', 'System32',
            '.git', 'node_modules', '__pycache__',
            'Library', 'Applications'
        }

        self.found_images = []
        self.duplicates = {}  # hash -> list of files
        self.selected_images = set()

    def should_skip_folder(self, folder_path):
        """Check if folder should be skipped"""
        folder_name = os.path.basename(folder_path)

        # Skip system folders
        if folder_name in self.skip_folders:
            return True

        # Skip hidden folders
        if folder_name.startswith('.'):
            return True

        return False

    def get_common_image_locations(self):
        """Get common locations where users store images"""
        home = str(Path.home())

        locations = [
            os.path.join(home, "Pictures"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "OneDrive", "Pictures"),
            os.path.join(home, "Google Drive"),
            os.path.join(home, "Dropbox"),
        ]

        # Only return locations that exist
        return [loc for loc in locations if os.path.exists(loc)]

    def calculate_hash(self, filepath):
        """Calculate file hash"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {filepath}: {e}")
            return None

    def get_image_info(self, filepath):
        """Get image information"""
        try:
            with Image.open(filepath) as img:
                return {
                    'path': filepath,
                    'filename': os.path.basename(filepath),
                    'size': os.path.getsize(filepath),
                    'dimensions': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'modified': os.path.getmtime(filepath)
                }
        except Exception as e:
            logger.debug(f"Could not read image info for {filepath}: {e}")
            return None

    def scan_folders(self, folders):
        """Scan folders for images"""
        print("\n" + "="*60)
        print("SCANNING FOR IMAGES...")
        print("="*60)

        all_images = {}  # hash -> image info

        for folder in folders:
            print(f"\nScanning: {folder}")

            try:
                for root, dirs, files in os.walk(folder):
                    # Remove folders to skip from dirs list
                    dirs[:] = [d for d in dirs if not self.should_skip_folder(os.path.join(root, d))]

                    for filename in files:
                        ext = Path(filename).suffix.lower()
                        if ext in self.image_extensions:
                            filepath = os.path.join(root, filename)

                            # Calculate hash
                            file_hash = self.calculate_hash(filepath)
                            if not file_hash:
                                continue

                            # Get image info
                            info = self.get_image_info(filepath)
                            if not info:
                                continue

                            info['hash'] = file_hash

                            # Track duplicates
                            if file_hash in all_images:
                                # Duplicate found
                                if file_hash not in self.duplicates:
                                    self.duplicates[file_hash] = [all_images[file_hash]]
                                self.duplicates[file_hash].append(info)
                            else:
                                all_images[file_hash] = info

                            # Progress indicator
                            if len(all_images) % 100 == 0:
                                print(f"  Found {len(all_images)} unique images...", end='\r')

            except Exception as e:
                logger.error(f"Error scanning {folder}: {e}")

        self.found_images = list(all_images.values())

        print(f"\n\n✓ Scan complete!")
        print(f"  Unique images found: {len(self.found_images)}")
        print(f"  Duplicate sets found: {len(self.duplicates)}")

        return self.found_images

    def show_duplicates_report(self):
        """Show report of duplicates"""
        if not self.duplicates:
            print("\n✓ No duplicates found!")
            return

        print("\n" + "="*60)
        print("DUPLICATE IMAGES FOUND")
        print("="*60)

        total_duplicates = sum(len(dupes) for dupes in self.duplicates.values())
        total_wasted_space = 0

        for i, (file_hash, dupes) in enumerate(list(self.duplicates.items())[:10], 1):
            print(f"\nDuplicate Set #{i}:")
            print(f"  Size: {dupes[0]['size']:,} bytes")
            print(f"  Dimensions: {dupes[0]['dimensions']}")
            print(f"  Copies: {len(dupes)}")
            print(f"  Locations:")
            for dupe in dupes:
                print(f"    • {dupe['path']}")

            wasted = dupes[0]['size'] * (len(dupes) - 1)
            total_wasted_space += wasted

        if len(self.duplicates) > 10:
            print(f"\n... and {len(self.duplicates) - 10} more duplicate sets")

        print(f"\n💾 Total wasted space from duplicates: {total_wasted_space / (1024*1024):.1f} MB")

    def filter_by_dimensions(self, min_width=512, min_height=512):
        """Filter images by minimum dimensions"""
        filtered = [
            img for img in self.found_images
            if img['dimensions'][0] >= min_width and img['dimensions'][1] >= min_height
        ]

        print(f"\nFiltered to images at least {min_width}x{min_height}:")
        print(f"  Before: {len(self.found_images)}")
        print(f"  After: {len(filtered)}")
        print(f"  Removed: {len(self.found_images) - len(filtered)} (too small)")

        return filtered

    def save_catalog(self, filename="image_catalog.json"):
        """Save catalog of found images"""
        catalog = {
            'scan_date': datetime.now().isoformat(),
            'total_images': len(self.found_images),
            'total_duplicates': len(self.duplicates),
            'images': self.found_images,
            'duplicates': {
                hash_val: dupes for hash_val, dupes in self.duplicates.items()
            }
        }

        desktop = self.get_desktop_path()
        catalog_file = os.path.join(desktop, filename)

        with open(catalog_file, 'w') as f:
            json.dump(catalog, f, indent=2)

        print(f"\n✓ Saved catalog to: {catalog_file}")
        return catalog_file

    def get_desktop_path(self):
        """Get desktop path"""
        home = str(Path.home())
        possible_paths = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "desktop"),
            os.path.join(home, "OneDrive", "Desktop"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return home

    def create_selection_html(self, images, output_file="select_images.html"):
        """Create HTML file for selecting images"""
        desktop = self.get_desktop_path()
        html_file = os.path.join(desktop, output_file)

        # Limit to first 500 for performance
        images_to_show = images[:500]

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Select Images to Process</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f0f0f0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
        }
        h1 {
            color: #333;
        }
        .controls {
            margin: 20px 0;
            padding: 15px;
            background: #e9ecef;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #5568d3;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .image-item {
            border: 3px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s;
        }
        .image-item:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .image-item.selected {
            border-color: #28a745;
            box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
        }
        .image-item img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        .image-info {
            padding: 8px;
            font-size: 11px;
            background: #f8f9fa;
        }
        .selected-count {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 25px;
            border-radius: 50px;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .info-box {
            background: #d1ecf1;
            border-left: 4px solid #0c5460;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Select Images to Process</h1>

        <div class="info-box">
            <strong>Instructions:</strong>
            <ol>
                <li>Click images to select/deselect them</li>
                <li>Use buttons below to select all, clear, or filter</li>
                <li>Copy the selected file paths (shown at bottom)</li>
                <li>Save them to a text file</li>
                <li>Use that file with the processor</li>
            </ol>
        </div>

        <div class="controls">
            <button onclick="selectAll()">Select All</button>
            <button onclick="clearAll()">Clear All</button>
            <button onclick="selectLarge()">Only Large Images (1000x1000+)</button>
            <button onclick="copySelected()">Copy Selected Paths</button>
            <span style="margin-left: 20px;">
                Showing: <strong id="showing-count">0</strong> images
            </span>
        </div>

        <div class="gallery" id="gallery">
        </div>

        <div class="selected-count" id="selected-count">
            Selected: 0
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
            <h3>Selected Image Paths:</h3>
            <textarea id="selected-paths" style="width: 100%; height: 200px; font-family: monospace; font-size: 12px;"></textarea>
            <button onclick="copySelected()">Copy to Clipboard</button>
            <button onclick="downloadList()">Download as Text File</button>
        </div>
    </div>

    <script>
        const images = """ + json.dumps(images_to_show) + """;
        let selected = new Set();

        function renderGallery() {
            const gallery = document.getElementById('gallery');
            gallery.innerHTML = '';

            images.forEach((img, index) => {
                const div = document.createElement('div');
                div.className = 'image-item';
                div.onclick = () => toggleSelect(index);

                // Try to create image preview (file:// protocol may not work in all browsers)
                const imgPath = img.path.replace(/\\/g, '/');

                div.innerHTML = `
                    <div style="width: 100%; height: 200px; background: #eee; display: flex; align-items: center; justify-content: center;">
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 40px;">🖼️</div>
                            <div style="font-size: 11px; margin-top: 5px;">${img.dimensions[0]} x ${img.dimensions[1]}</div>
                        </div>
                    </div>
                    <div class="image-info">
                        <div><strong>${img.filename}</strong></div>
                        <div>${(img.size / 1024).toFixed(1)} KB</div>
                        <div>${img.dimensions[0]} x ${img.dimensions[1]}</div>
                    </div>
                `;

                gallery.appendChild(div);
            });

            document.getElementById('showing-count').textContent = images.length;
            updateSelectedCount();
        }

        function toggleSelect(index) {
            if (selected.has(index)) {
                selected.delete(index);
            } else {
                selected.add(index);
            }
            updateSelected();
        }

        function updateSelected() {
            const items = document.querySelectorAll('.image-item');
            items.forEach((item, index) => {
                if (selected.has(index)) {
                    item.classList.add('selected');
                } else {
                    item.classList.remove('selected');
                }
            });
            updateSelectedCount();
        }

        function updateSelectedCount() {
            document.getElementById('selected-count').textContent = `Selected: ${selected.size}`;

            const paths = Array.from(selected).map(i => images[i].path).join('\\n');
            document.getElementById('selected-paths').value = paths;
        }

        function selectAll() {
            selected = new Set(images.map((_, i) => i));
            updateSelected();
        }

        function clearAll() {
            selected.clear();
            updateSelected();
        }

        function selectLarge() {
            selected.clear();
            images.forEach((img, i) => {
                if (img.dimensions[0] >= 1000 && img.dimensions[1] >= 1000) {
                    selected.add(i);
                }
            });
            updateSelected();
        }

        function copySelected() {
            const textarea = document.getElementById('selected-paths');
            textarea.select();
            document.execCommand('copy');
            alert(`Copied ${selected.size} file paths to clipboard!`);
        }

        function downloadList() {
            const paths = document.getElementById('selected-paths').value;
            const blob = new Blob([paths], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'selected_images.txt';
            a.click();
        }

        renderGallery();
    </script>
</body>
</html>
"""

        with open(html_file, 'w') as f:
            f.write(html)

        print(f"\n✓ Created selection page: {html_file}")
        print(f"\nOpen this file in your browser to select which images to process!")

        return html_file


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         SMART IMAGE FINDER & ORGANIZER                    ║
║         Find all your images and organize them            ║
╚═══════════════════════════════════════════════════════════╝
""")

    finder = ImageFinder()

    print("\nThis tool will help you:")
    print("  1. Find ALL images on your computer")
    print("  2. Detect duplicates")
    print("  3. Help you select which ones to process")
    print("  4. Create a catalog for future use")

    print("\n" + "="*60)
    print("STEP 1: Choose what to scan")
    print("="*60)

    print("\nOptions:")
    print("  1. Scan common locations (Pictures, Downloads, Desktop, Documents)")
    print("  2. Scan specific folders (you choose)")
    print("  3. Scan entire drive (WARNING: Very slow!)")

    choice = input("\nEnter choice (1-3): ").strip()

    folders_to_scan = []

    if choice == '1':
        folders_to_scan = finder.get_common_image_locations()
        print("\nWill scan:")
        for folder in folders_to_scan:
            print(f"  • {folder}")

    elif choice == '2':
        print("\nEnter folder paths (one per line, empty line to finish):")
        while True:
            folder = input("Folder: ").strip().strip('"').strip("'")
            if not folder:
                break
            if os.path.exists(folder):
                folders_to_scan.append(folder)
            else:
                print(f"  ⚠️  Folder not found: {folder}")

    elif choice == '3':
        home = str(Path.home())
        drive_root = Path(home).drive or '/'
        folders_to_scan = [drive_root]
        print(f"\n⚠️  WARNING: This will scan your entire {drive_root} drive!")
        print("This could take a very long time.")
        confirm = input("Are you sure? (yes/no): ").lower()
        if confirm != 'yes':
            print("Cancelled.")
            return

    else:
        print("Invalid choice.")
        return

    if not folders_to_scan:
        print("No folders to scan!")
        return

    # Scan for images
    images = finder.scan_folders(folders_to_scan)

    if not images:
        print("\nNo images found!")
        return

    # Show duplicates
    finder.show_duplicates_report()

    # Filter options
    print("\n" + "="*60)
    print("STEP 2: Filter images")
    print("="*60)

    print("\nOptions:")
    print("  1. Keep all images")
    print("  2. Only large images (1000x1000+)")
    print("  3. Only medium+ images (512x512+)")
    print("  4. Custom minimum size")

    filter_choice = input("\nEnter choice (1-4): ").strip()

    if filter_choice == '2':
        images = finder.filter_by_dimensions(1000, 1000)
    elif filter_choice == '3':
        images = finder.filter_by_dimensions(512, 512)
    elif filter_choice == '4':
        min_width = int(input("Minimum width: "))
        min_height = int(input("Minimum height: "))
        images = finder.filter_by_dimensions(min_width, min_height)

    # Save catalog
    print("\n" + "="*60)
    print("STEP 3: Save results")
    print("="*60)

    catalog_file = finder.save_catalog()

    # Create selection page
    print("\nCreating interactive selection page...")
    selection_file = finder.create_selection_html(images)

    print("\n" + "="*60)
    print("✓ COMPLETE!")
    print("="*60)

    print(f"\nFiles created on your desktop:")
    print(f"  1. {catalog_file}")
    print(f"  2. {selection_file}")

    print(f"\nNEXT STEPS:")
    print(f"  1. Open {selection_file} in your browser")
    print(f"  2. Select which images you want to process")
    print(f"  3. Copy the selected paths or download the list")
    print(f"  4. Use those paths with the gallery creator")

    print(f"\nSummary:")
    print(f"  • Total unique images: {len(images)}")
    print(f"  • Duplicate sets: {len(finder.duplicates)}")
    print(f"  • Ready to process!")


if __name__ == "__main__":
    main()
