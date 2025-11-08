#!/usr/bin/env python3
"""
Process Images to Desktop
Standalone script that processes images and creates gallery pages on your desktop
"""

import os
import sys
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed!")
    print("Please run: pip install Pillow")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DesktopGalleryProcessor:
    """Processes images and creates gallery on desktop"""

    def __init__(self):
        # Find desktop path (cross-platform)
        self.desktop_path = self.get_desktop_path()
        self.output_folder = os.path.join(self.desktop_path, "REALIAIGRILS NEW PAGES")

        # Processing settings
        self.max_width = 1920
        self.max_height = 1080
        self.thumbnail_size = (400, 400)
        self.quality = 85
        self.items_per_page = 20

        # Track processed files
        self.processed_hashes = set()
        self.media_items = []

    def get_desktop_path(self):
        """Get desktop path for current OS"""
        home = str(Path.home())

        # Try common desktop locations
        possible_paths = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "desktop"),
            os.path.join(home, "OneDrive", "Desktop"),
            os.path.expanduser("~/Desktop")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Fallback to home directory
        logger.warning("Could not find Desktop, using home directory")
        return home

    def setup_output_folder(self):
        """Create output folder structure"""
        folders = [
            self.output_folder,
            os.path.join(self.output_folder, "images"),
            os.path.join(self.output_folder, "thumbnails"),
            os.path.join(self.output_folder, "pages")
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)

        logger.info(f"✓ Created output folder: {self.output_folder}")

    def get_file_hash(self, filepath):
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {filepath}: {e}")
            return None

    def process_image(self, input_path, output_name):
        """Process a single image"""
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                # Get original size
                original_size = img.size

                # Resize if too large
                if img.width > self.max_width or img.height > self.max_height:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)

                # Save optimized image
                output_path = os.path.join(self.output_folder, "images", output_name)
                img.save(output_path, 'JPEG', quality=self.quality, optimize=True)

                # Create thumbnail
                img_copy = img.copy()
                img_copy.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                thumbnail_path = os.path.join(self.output_folder, "thumbnails", output_name)
                img_copy.save(thumbnail_path, 'JPEG', quality=self.quality)

                return {
                    'filename': output_name,
                    'image_path': f"../images/{output_name}",
                    'thumb_path': f"../thumbnails/{output_name}",
                    'original_size': original_size,
                    'processed_size': img.size
                }

        except Exception as e:
            logger.error(f"Error processing {input_path}: {e}")
            return None

    def find_images(self, source_folder):
        """Find all images in source folder"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        images = []

        for root, dirs, files in os.walk(source_folder):
            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext in image_extensions:
                    images.append(os.path.join(root, filename))

        return images

    def process_all_images(self, source_folder):
        """Process all images from source folder"""
        logger.info(f"Scanning for images in: {source_folder}")

        images = self.find_images(source_folder)

        if not images:
            logger.error("No images found in source folder!")
            return

        logger.info(f"Found {len(images)} image(s). Processing...")

        processed_count = 0
        duplicate_count = 0

        for i, image_path in enumerate(images, 1):
            # Check for duplicates
            file_hash = self.get_file_hash(image_path)
            if file_hash in self.processed_hashes:
                logger.info(f"[{i}/{len(images)}] DUPLICATE: {Path(image_path).name}")
                duplicate_count += 1
                continue

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = Path(image_path).stem
            output_name = f"{timestamp}_{i:04d}_{original_name}.jpg"

            # Process image
            logger.info(f"[{i}/{len(images)}] Processing: {Path(image_path).name}")
            result = self.process_image(image_path, output_name)

            if result:
                self.media_items.append({
                    'filename': output_name,
                    'image_path': result['image_path'],
                    'thumb_path': result['thumb_path'],
                    'original_name': Path(image_path).name,
                    'timestamp': timestamp
                })
                self.processed_hashes.add(file_hash)
                processed_count += 1

        logger.info(f"\n✓ Processing complete!")
        logger.info(f"  Processed: {processed_count}")
        logger.info(f"  Duplicates skipped: {duplicate_count}")
        logger.info(f"  Total unique images: {len(self.media_items)}")

    def generate_gallery_page(self, page_num, items, total_pages):
        """Generate a single gallery page"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RealAIGirls Gallery - Page {page_num}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 20px;
            font-size: 3em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .stats {{
            color: white;
            text-align: center;
            margin-bottom: 40px;
            font-size: 1.2em;
        }}

        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .gallery-item {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
        }}

        .gallery-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }}

        .gallery-item img {{
            width: 100%;
            height: 300px;
            object-fit: cover;
            display: block;
        }}

        .item-info {{
            padding: 15px;
            background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
        }}

        .item-info p {{
            color: #495057;
            font-size: 0.9em;
            margin: 5px 0;
        }}

        .pagination {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 40px 0;
            flex-wrap: wrap;
        }}

        .pagination a,
        .pagination span {{
            padding: 10px 20px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
        }}

        .pagination a:hover {{
            background: #667eea;
            color: white;
            transform: scale(1.05);
        }}

        .pagination .current {{
            background: #667eea;
            color: white;
        }}

        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}

        .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}

        .close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }}

        .close:hover {{
            color: #bbb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RealAIGirls Gallery</h1>
        <div class="stats">
            Page {page_num} of {total_pages} • {len(self.media_items)} Total Images
        </div>

        <div class="gallery">
"""

        # Add gallery items
        for item in items:
            html += f"""
            <div class="gallery-item" onclick="openModal('{item['image_path']}')">
                <img src="{item['thumb_path']}" alt="{item['original_name']}">
                <div class="item-info">
                    <p><strong>{item['filename']}</strong></p>
                    <p>Original: {item['original_name']}</p>
                </div>
            </div>
"""

        html += """
        </div>

        <div class="pagination">
"""

        # Add pagination
        if page_num > 1:
            html += f'            <a href="page-{page_num - 1}.html">← Previous</a>\n'

        # Page numbers
        for i in range(1, total_pages + 1):
            if i == page_num:
                html += f'            <span class="current">{i}</span>\n'
            else:
                html += f'            <a href="page-{i}.html">{i}</a>\n'

        if page_num < total_pages:
            html += f'            <a href="page-{page_num + 1}.html">Next →</a>\n'

        html += """
        </div>
    </div>

    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
        function openModal(imageSrc) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = imageSrc;
        }

        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""
        return html

    def generate_all_pages(self):
        """Generate all gallery pages"""
        if not self.media_items:
            logger.error("No images to generate pages from!")
            return

        logger.info("Generating gallery pages...")

        total_pages = max(1, (len(self.media_items) + self.items_per_page - 1) // self.items_per_page)
        pages_dir = os.path.join(self.output_folder, "pages")

        # Generate each page
        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            page_items = self.media_items[start_idx:end_idx]

            html = self.generate_gallery_page(page_num, page_items, total_pages)

            page_file = os.path.join(pages_dir, f"page-{page_num}.html")
            with open(page_file, 'w') as f:
                f.write(html)

            logger.info(f"  ✓ Created page-{page_num}.html ({len(page_items)} images)")

        # Create index.html that redirects to page 1
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=page-1.html">
    <title>RealAIGirls Gallery</title>
</head>
<body>
    <p>Redirecting to gallery...</p>
</body>
</html>
"""
        with open(os.path.join(pages_dir, "index.html"), 'w') as f:
            f.write(index_html)

        logger.info(f"✓ Generated {total_pages} gallery page(s)")

    def create_readme(self):
        """Create README file in output folder"""
        readme = f"""RealAIGirls Gallery Pages
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CONTENTS:
- images/      - {len(self.media_items)} optimized images (max {self.max_width}x{self.max_height})
- thumbnails/  - {len(self.media_items)} thumbnails ({self.thumbnail_size[0]}x{self.thumbnail_size[1]})
- pages/       - Gallery HTML pages

TO VIEW:
Open pages/index.html in your web browser

TO UPLOAD TO WEBSITE:
1. Upload the entire 'images' folder to your website
2. Upload the entire 'thumbnails' folder to your website
3. Upload the entire 'pages' folder to your website
4. Visit yoursite.com/pages/ to see the gallery

SETTINGS USED:
- Max image size: {self.max_width}x{self.max_height}
- JPEG quality: {self.quality}%
- Items per page: {self.items_per_page}
- Total images: {len(self.media_items)}
"""
        readme_file = os.path.join(self.output_folder, "README.txt")
        with open(readme_file, 'w') as f:
            f.write(readme)


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         REALAIGIRLS GALLERY GENERATOR                     ║
║         Process images and create gallery pages           ║
╚═══════════════════════════════════════════════════════════╝
""")

    processor = DesktopGalleryProcessor()

    print(f"Output folder: {processor.output_folder}\n")

    # Get source folder from user
    print("Where are your images located?")
    print("Enter the full path to the folder containing your images:")
    print("(or drag and drop the folder here)\n")

    source_folder = input("Image folder path: ").strip().strip('"').strip("'")

    if not os.path.exists(source_folder):
        print(f"\n❌ ERROR: Folder not found: {source_folder}")
        print("Please check the path and try again.")
        sys.exit(1)

    if not os.path.isdir(source_folder):
        print(f"\n❌ ERROR: Not a folder: {source_folder}")
        sys.exit(1)

    print("\n" + "="*60)

    # Setup and process
    processor.setup_output_folder()
    processor.process_all_images(source_folder)
    processor.generate_all_pages()
    processor.create_readme()

    print("\n" + "="*60)
    print("✓ ALL DONE!")
    print("="*60)
    print(f"\nYour gallery has been created at:")
    print(f"  {processor.output_folder}")
    print(f"\nTo view your gallery:")
    print(f"  Open: {os.path.join(processor.output_folder, 'pages', 'index.html')}")
    print(f"\nTo upload to your website:")
    print(f"  1. Upload 'images' folder")
    print(f"  2. Upload 'thumbnails' folder")
    print(f"  3. Upload 'pages' folder")
    print(f"  4. Visit yoursite.com/pages/")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
