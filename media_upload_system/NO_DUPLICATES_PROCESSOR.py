#!/usr/bin/env python3
"""
NO DUPLICATES PROCESSOR
Processes images with 100% duplicate prevention
Checks against live website database
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image


class NoDuplicatesProcessor:
    """Process images with duplicate checking against live website"""

    def __init__(self, database_file='existing_images_database.json'):
        self.database_file = database_file
        self.existing_hashes = set()
        self.load_existing_database()

        # Output settings
        self.desktop_path = self.get_desktop_path()
        self.output_folder = os.path.join(self.desktop_path, "REALIAIGRILS NEW PAGES")

        # Processing settings
        self.max_width = 1920
        self.max_height = 1080
        self.thumbnail_size = (400, 400)
        self.quality = 85

        # Statistics
        self.stats = {
            'total_found': 0,
            'duplicates_skipped': 0,
            'processed': 0,
            'failed': 0
        }

    def get_desktop_path(self):
        """Get desktop path cross-platform"""
        if os.name == 'nt':  # Windows
            return os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        else:  # Mac/Linux
            return os.path.join(os.path.expanduser('~'), 'Desktop')

    def load_existing_database(self):
        """Load existing images database"""
        if os.path.exists(self.database_file):
            print(f"✓ Loading existing images database: {self.database_file}")
            with open(self.database_file, 'r') as f:
                data = json.load(f)
                # Extract all hashes
                for hash_value in data.get('existing_hashes', {}).keys():
                    self.existing_hashes.add(hash_value)
            print(f"  → {len(self.existing_hashes)} existing images loaded")
        else:
            print("⚠️  No database found!")
            print(f"   Expected: {self.database_file}")
            print()
            print("IMPORTANT: You should scan your website first!")
            print("Run: python scan_live_website.py")
            print()
            response = input("Continue without duplicate checking? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)

    def calculate_hash(self, filepath):
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def is_duplicate(self, filepath):
        """Check if image is a duplicate"""
        file_hash = self.calculate_hash(filepath)
        return file_hash in self.existing_hashes

    def process_image(self, input_path, output_images_dir, output_thumbs_dir):
        """Process a single image"""
        try:
            # Check for duplicate FIRST
            if self.is_duplicate(input_path):
                self.stats['duplicates_skipped'] += 1
                return None

            # Open and process image
            img = Image.open(input_path)

            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_name = f"{timestamp}_{base_name}.jpg"

            # Resize if needed
            img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)

            # Save optimized image
            output_path = os.path.join(output_images_dir, output_name)
            img.convert('RGB').save(output_path, 'JPEG', quality=self.quality, optimize=True)

            # Create thumbnail
            thumb = Image.open(input_path)
            thumb.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            thumb_path = os.path.join(output_thumbs_dir, output_name)
            thumb.convert('RGB').save(thumb_path, 'JPEG', quality=self.quality)

            self.stats['processed'] += 1

            return {
                'filename': output_name,
                'original': os.path.basename(input_path),
                'size': os.path.getsize(output_path),
                'dimensions': img.size
            }

        except Exception as e:
            print(f"   ✗ Error processing {os.path.basename(input_path)}: {e}")
            self.stats['failed'] += 1
            return None

    def find_images(self, directory):
        """Find all images in directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        images = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    images.append(os.path.join(root, file))

        return images

    def create_gallery_html(self, media_items, output_dir):
        """Create gallery HTML page"""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RealAIGirls.com Gallery</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            color: white;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            color: rgba(255,255,255,0.9);
            font-size: 1.2em;
            margin-bottom: 40px;
        }
        .stats {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .gallery-item {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
        }
        .gallery-item:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }
        .gallery-item img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            display: block;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
        }
        .modal-content {
            position: relative;
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            top: 50%;
            transform: translateY(-50%);
        }
        .close {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }
        .close:hover { color: #ff6b6b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 RealAIGirls.com</h1>
        <div class="subtitle">AI Generated Gallery - 100% Duplicate Free</div>
        <div class="stats">📸 ''' + str(len(media_items)) + ''' New Images Ready for Upload</div>
        <div class="gallery">
'''

        for item in media_items:
            html += f'''            <div class="gallery-item" onclick="openModal('../images/{item["filename"]}')">
                <img src="../thumbnails/{item["filename"]}" alt="AI Generated Image">
            </div>
'''

        html += '''        </div>
    </div>
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>
    <script>
        function openModal(src) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = src;
        }
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>'''

        # Save HTML
        html_path = os.path.join(output_dir, 'index.html')
        with open(html_path, 'w') as f:
            f.write(html)

        return html_path

    def process_folder(self, input_folder):
        """Process all images in folder"""
        print("\n" + "="*60)
        print("  NO DUPLICATES PROCESSOR")
        print("="*60)
        print()

        # Create output directories
        images_dir = os.path.join(self.output_folder, 'images')
        thumbs_dir = os.path.join(self.output_folder, 'thumbnails')
        pages_dir = os.path.join(self.output_folder, 'pages')

        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(thumbs_dir, exist_ok=True)
        os.makedirs(pages_dir, exist_ok=True)

        # Find all images
        print(f"🔍 Scanning: {input_folder}")
        images = self.find_images(input_folder)
        self.stats['total_found'] = len(images)
        print(f"   Found {len(images)} images")
        print()

        # Process each image
        print("⚙️  Processing images...")
        print()

        media_items = []

        for i, img_path in enumerate(images, 1):
            print(f"[{i}/{len(images)}] {os.path.basename(img_path)[:50]}...", end=' ')

            result = self.process_image(img_path, images_dir, thumbs_dir)

            if result:
                media_items.append(result)
                print("✓ Processed")
            elif result is None and self.stats['duplicates_skipped'] > (len(media_items) - 1):
                print("⊗ DUPLICATE - Skipped")
            else:
                print("✗ Failed")

        # Create gallery
        if media_items:
            print()
            print("🎨 Creating gallery page...")
            html_path = self.create_gallery_html(media_items, pages_dir)
            print(f"   ✓ Created: {html_path}")

        # Print summary
        self.print_summary()

        return self.output_folder

    def print_summary(self):
        """Print processing summary"""
        print()
        print("="*60)
        print("  PROCESSING COMPLETE")
        print("="*60)
        print(f"Total images found:    {self.stats['total_found']}")
        print(f"Duplicates skipped:    {self.stats['duplicates_skipped']} ⊗")
        print(f"Successfully processed: {self.stats['processed']} ✓")
        print(f"Failed:                {self.stats['failed']} ✗")
        print("="*60)
        print()
        print(f"✅ Output saved to: {self.output_folder}")
        print()
        print("📁 Folder structure:")
        print("   ├── images/       (optimized images)")
        print("   ├── thumbnails/   (preview thumbnails)")
        print("   └── pages/        (gallery HTML)")
        print()
        print("🚀 Ready to upload to realaigirls.com!")
        print()


def main():
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  NO DUPLICATES PROCESSOR - 100% DUPLICATE FREE            ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    # Initialize processor
    processor = NoDuplicatesProcessor()

    # Get input folder
    print("Enter folder path containing images:")
    input_folder = input("> ").strip().strip('"').strip("'")

    if not os.path.exists(input_folder):
        print(f"❌ Error: Folder not found: {input_folder}")
        sys.exit(1)

    # Process
    output = processor.process_folder(input_folder)

    print(f"Done! Check: {output}")
    print()


if __name__ == "__main__":
    main()
