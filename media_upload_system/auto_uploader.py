#!/usr/bin/env python3
"""
Automated Media Upload System
Watches a folder for new images/videos, processes them, and uploads to website
"""

import os
import sys
import time
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import logging

try:
    from PIL import Image
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: Required dependencies not installed!")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Try to import FTP uploader (optional)
try:
    from ftp_uploader import FTPUploader
    FTP_AVAILABLE = True
except ImportError:
    FTP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("FTP uploader not available. Install ftplib for FTP support.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_upload_system/upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration for the media upload system"""

    # Directories
    WATCH_DIR = "media_upload_system/upload_here"
    PROCESSED_DIR = "media_upload_system/processed"
    OUTPUT_DIR = "media"  # Where files go on the website
    PAGES_DIR = "pages"   # Where HTML pages are generated

    # Image processing settings
    MAX_IMAGE_WIDTH = 1920
    MAX_IMAGE_HEIGHT = 1080
    THUMBNAIL_SIZE = (400, 400)
    IMAGE_QUALITY = 85
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.webm', '.mov', '.avi'}

    # Git settings
    AUTO_COMMIT = True
    AUTO_PUSH = True
    COMMIT_MESSAGE_TEMPLATE = "Auto-upload: Add {} new media file(s)"

    # FTP settings (for GoDaddy or other hosting)
    FTP_ENABLED = False
    FTP_HOST = None
    FTP_USERNAME = None
    FTP_PASSWORD = None
    FTP_REMOTE_PATH = "/public_html"
    FTP_USE_TLS = False

    # Gallery settings
    ITEMS_PER_PAGE = 20
    GALLERY_TITLE = "Media Gallery"

    @classmethod
    def load_from_file(cls, config_file: str = "media_upload_system/config.json"):
        """Load configuration from JSON file if it exists"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    for key, value in config_data.items():
                        if hasattr(cls, key):
                            setattr(cls, key, value)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")


class MediaProcessor:
    """Handles image and video processing"""

    def __init__(self, config: Config):
        self.config = config
        self.processed_files: Set[str] = set()
        self.existing_media_hashes: Dict[str, str] = {}  # hash -> filepath on website
        self.load_processed_files()
        self.load_existing_media_hashes()

    def load_processed_files(self):
        """Load list of already processed files"""
        processed_log = "media_upload_system/processed_files.json"
        if os.path.exists(processed_log):
            try:
                with open(processed_log, 'r') as f:
                    self.processed_files = set(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load processed files log: {e}")

    def load_existing_media_hashes(self):
        """Load hash database of existing media on website"""
        existing_hashes_file = "media_upload_system/existing_media_hashes.json"
        if os.path.exists(existing_hashes_file):
            try:
                with open(existing_hashes_file, 'r') as f:
                    self.existing_media_hashes = json.load(f)
                logger.info(f"Loaded existing media hashes: {len(self.existing_media_hashes)} files")
            except Exception as e:
                logger.warning(f"Could not load existing media hashes: {e}")
        else:
            logger.warning("No existing media hash database found. Run scan_existing_media.py first!")
            logger.warning("Without this, duplicate detection will only work for newly uploaded files.")

    def save_processed_files(self):
        """Save list of processed files"""
        processed_log = "media_upload_system/processed_files.json"
        try:
            with open(processed_log, 'w') as f:
                json.dump(list(self.processed_files), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed files log: {e}")

    def get_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of file to detect duplicates"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {filepath}: {e}")
            return ""

    def is_image(self, filepath: str) -> bool:
        """Check if file is a supported image"""
        ext = Path(filepath).suffix.lower()
        return ext in self.config.SUPPORTED_IMAGE_FORMATS

    def is_video(self, filepath: str) -> bool:
        """Check if file is a supported video"""
        ext = Path(filepath).suffix.lower()
        return ext in self.config.SUPPORTED_VIDEO_FORMATS

    def optimize_image(self, input_path: str, output_path: str) -> bool:
        """Optimize and resize image"""
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                # Resize if too large
                if img.width > self.config.MAX_IMAGE_WIDTH or img.height > self.config.MAX_IMAGE_HEIGHT:
                    img.thumbnail((self.config.MAX_IMAGE_WIDTH, self.config.MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)

                # Save optimized image
                img.save(output_path, 'JPEG', quality=self.config.IMAGE_QUALITY, optimize=True)
                logger.info(f"Optimized image: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Error optimizing image {input_path}: {e}")
            return False

    def create_thumbnail(self, input_path: str, output_path: str) -> bool:
        """Create thumbnail for image or video"""
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                img.thumbnail(self.config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=self.config.IMAGE_QUALITY)
                logger.info(f"Created thumbnail: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Error creating thumbnail for {input_path}: {e}")
            return False

    def process_file(self, filepath: str) -> Dict[str, any]:
        """Process a single media file"""
        file_hash = self.get_file_hash(filepath)

        # Check if already processed
        if file_hash in self.processed_files:
            logger.info(f"File already processed (duplicate): {filepath}")
            return None

        # Check if file already exists on website (CRITICAL DUPLICATE CHECK)
        if file_hash in self.existing_media_hashes:
            existing_file = self.existing_media_hashes[file_hash]
            logger.warning(f"⚠️  DUPLICATE DETECTED! File already exists on website:")
            logger.warning(f"   New file: {filepath}")
            logger.warning(f"   Existing: {existing_file}")
            logger.warning(f"   Skipping upload to prevent duplicate.")
            # Move to processed folder to avoid reprocessing
            try:
                processed_path = f"{self.config.PROCESSED_DIR}/{Path(filepath).name}"
                shutil.move(filepath, processed_path)
                self.processed_files.add(file_hash)
            except Exception as e:
                logger.error(f"Error moving duplicate file: {e}")
            return None

        filename = Path(filepath).name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directories
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(f"{self.config.OUTPUT_DIR}/thumbnails", exist_ok=True)

        result = {
            'original_name': filename,
            'timestamp': timestamp,
            'file_hash': file_hash,
            'type': None,
            'path': None,
            'thumbnail_path': None
        }

        if self.is_image(filepath):
            # Process image
            ext = Path(filepath).suffix.lower()
            new_filename = f"{timestamp}_{filename}"
            output_path = f"{self.config.OUTPUT_DIR}/{new_filename}"
            thumbnail_path = f"{self.config.OUTPUT_DIR}/thumbnails/{timestamp}_{Path(filename).stem}.jpg"

            # Optimize and save
            if self.optimize_image(filepath, output_path):
                self.create_thumbnail(output_path, thumbnail_path)
                result['type'] = 'image'
                result['path'] = output_path
                result['thumbnail_path'] = thumbnail_path

                # Move original to processed folder
                processed_path = f"{self.config.PROCESSED_DIR}/{filename}"
                shutil.move(filepath, processed_path)
                self.processed_files.add(file_hash)

                logger.info(f"Successfully processed image: {filename}")
                return result

        elif self.is_video(filepath):
            # Process video (copy to output directory)
            new_filename = f"{timestamp}_{filename}"
            output_path = f"{self.config.OUTPUT_DIR}/{new_filename}"

            shutil.copy2(filepath, output_path)
            result['type'] = 'video'
            result['path'] = output_path

            # Move original to processed folder
            processed_path = f"{self.config.PROCESSED_DIR}/{filename}"
            shutil.move(filepath, processed_path)
            self.processed_files.add(file_hash)

            logger.info(f"Successfully processed video: {filename}")
            return result

        else:
            logger.warning(f"Unsupported file format: {filepath}")
            return None

        return None


class GalleryGenerator:
    """Generates HTML gallery pages"""

    def __init__(self, config: Config):
        self.config = config
        self.media_index_file = "media_upload_system/media_index.json"
        self.media_items: List[Dict] = []
        self.load_media_index()

    def load_media_index(self):
        """Load existing media index"""
        if os.path.exists(self.media_index_file):
            try:
                with open(self.media_index_file, 'r') as f:
                    self.media_items = json.load(f)
                logger.info(f"Loaded {len(self.media_items)} media items from index")
            except Exception as e:
                logger.warning(f"Could not load media index: {e}")

    def save_media_index(self):
        """Save media index"""
        try:
            with open(self.media_index_file, 'w') as f:
                json.dump(self.media_items, f, indent=2)
            logger.info(f"Saved media index with {len(self.media_items)} items")
        except Exception as e:
            logger.error(f"Could not save media index: {e}")

    def add_media_item(self, item: Dict):
        """Add media item to index"""
        if item:
            self.media_items.insert(0, item)  # Add to beginning (newest first)
            self.save_media_index()

    def generate_gallery_page(self, page_num: int = 1) -> str:
        """Generate a gallery HTML page"""
        start_idx = (page_num - 1) * self.config.ITEMS_PER_PAGE
        end_idx = start_idx + self.config.ITEMS_PER_PAGE
        page_items = self.media_items[start_idx:end_idx]

        total_pages = (len(self.media_items) + self.config.ITEMS_PER_PAGE - 1) // self.config.ITEMS_PER_PAGE

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.GALLERY_TITLE} - Page {page_num}</title>
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
            margin-bottom: 40px;
            font-size: 3em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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

        .gallery-item video {{
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
        }}

        .pagination {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 40px 0;
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
        }}

        .close:hover {{
            color: #bbb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.config.GALLERY_TITLE}</h1>

        <div class="gallery">
"""

        # Add gallery items
        for item in page_items:
            if item['type'] == 'image':
                thumbnail = item.get('thumbnail_path', item['path'])
                html += f"""
            <div class="gallery-item" onclick="openModal('{item['path']}')">
                <img src="{thumbnail}" alt="{item['original_name']}">
                <div class="item-info">
                    <p>{item['original_name']}</p>
                </div>
            </div>
"""
            elif item['type'] == 'video':
                html += f"""
            <div class="gallery-item">
                <video controls>
                    <source src="{item['path']}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <div class="item-info">
                    <p>{item['original_name']}</p>
                </div>
            </div>
"""

        html += """
        </div>

        <div class="pagination">
"""

        # Add pagination
        if page_num > 1:
            html += f'            <a href="gallery-{page_num - 1}.html">← Previous</a>\n'

        for i in range(1, total_pages + 1):
            if i == page_num:
                html += f'            <span class="current">{i}</span>\n'
            else:
                html += f'            <a href="gallery-{i}.html">{i}</a>\n'

        if page_num < total_pages:
            html += f'            <a href="gallery-{page_num + 1}.html">Next →</a>\n'

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
        os.makedirs(self.config.PAGES_DIR, exist_ok=True)

        total_pages = max(1, (len(self.media_items) + self.config.ITEMS_PER_PAGE - 1) // self.config.ITEMS_PER_PAGE)

        for page_num in range(1, total_pages + 1):
            html = self.generate_gallery_page(page_num)
            output_file = f"{self.config.PAGES_DIR}/gallery-{page_num}.html"

            with open(output_file, 'w') as f:
                f.write(html)

            logger.info(f"Generated gallery page: {output_file}")

        # Create index.html pointing to first page
        if total_pages > 0:
            index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=gallery-1.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to gallery...</p>
</body>
</html>
"""
            with open(f"{self.config.PAGES_DIR}/index.html", 'w') as f:
                f.write(index_html)


class DeploymentManager:
    """Handles deployment (Git or FTP)"""

    def __init__(self, config: Config):
        self.config = config
        self.ftp_uploader = None

        # Initialize FTP if enabled
        if config.FTP_ENABLED and FTP_AVAILABLE:
            try:
                self.ftp_uploader = FTPUploader()
                logger.info("FTP uploader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FTP uploader: {e}")

    def deploy(self, message: str, files_to_upload: List[str] = None) -> bool:
        """
        Deploy changes via Git or FTP

        Args:
            message: Commit message or deployment description
            files_to_upload: List of files to upload (for FTP mode)
        """
        if self.config.FTP_ENABLED and self.ftp_uploader:
            return self._ftp_deploy(files_to_upload)
        elif self.config.AUTO_COMMIT:
            return self._git_deploy(message)
        else:
            logger.info("No deployment method enabled")
            return True

    def _git_deploy(self, message: str) -> bool:
        """Deploy via Git commit and push"""
        try:
            # Add all changes
            os.system('git add .')

            # Commit
            commit_cmd = f'git commit -m "{message}"'
            result = os.system(commit_cmd)

            if result == 0:
                logger.info(f"Committed changes: {message}")

                if self.config.AUTO_PUSH:
                    # Push
                    branch = os.popen('git branch --show-current').read().strip()
                    push_cmd = f'git push -u origin {branch}'
                    push_result = os.system(push_cmd)

                    if push_result == 0:
                        logger.info(f"Pushed changes to {branch}")
                        return True
                    else:
                        logger.error("Failed to push changes")
                        return False
                return True
            else:
                logger.info("No changes to commit")
                return True

        except Exception as e:
            logger.error(f"Git operation failed: {e}")
            return False

    def _ftp_deploy(self, files_to_upload: List[str]) -> bool:
        """Deploy via FTP upload"""
        if not self.ftp_uploader:
            logger.error("FTP uploader not initialized")
            return False

        try:
            # Connect to FTP
            if not self.ftp_uploader.connect():
                return False

            success_count = 0

            # Upload each file
            for local_file in files_to_upload:
                if os.path.exists(local_file):
                    # Calculate remote path (relative to current directory)
                    remote_file = local_file

                    if self.ftp_uploader.upload_file(local_file, remote_file):
                        success_count += 1

            # Disconnect
            self.ftp_uploader.disconnect()

            logger.info(f"✓ Uploaded {success_count}/{len(files_to_upload)} files via FTP")

            return success_count > 0

        except Exception as e:
            logger.error(f"FTP deployment failed: {e}")
            return False


# Keep GitManager for backward compatibility
class GitManager(DeploymentManager):
    """Backward compatible Git manager"""

    @staticmethod
    def commit_and_push(message: str):
        """Legacy method for backward compatibility"""
        config = Config()
        manager = DeploymentManager(config)
        return manager._git_deploy(message)


class MediaWatcher(FileSystemEventHandler):
    """Watches directory for new files"""

    def __init__(self, processor: MediaProcessor, gallery: GalleryGenerator, config: Config):
        self.processor = processor
        self.gallery = gallery
        self.config = config
        self.processing = False
        self.deployment_manager = DeploymentManager(config)

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        filepath = event.src_path

        # Wait a moment to ensure file is fully written
        time.sleep(1)

        # Check if file still exists and is accessible
        if not os.path.exists(filepath):
            return

        logger.info(f"New file detected: {filepath}")
        self.process_new_file(filepath)

    def process_new_file(self, filepath: str):
        """Process a new file"""
        if self.processing:
            logger.info("Already processing, queuing file...")
            return

        self.processing = True

        try:
            # Process the file
            result = self.processor.process_file(filepath)

            if result:
                # Add to gallery
                self.gallery.add_media_item(result)

                # Regenerate gallery pages
                self.gallery.generate_all_pages()

                # Save processed files log
                self.processor.save_processed_files()

                # Deploy changes (Git or FTP)
                if self.config.AUTO_COMMIT or self.config.FTP_ENABLED:
                    commit_message = self.config.COMMIT_MESSAGE_TEMPLATE.format(1)

                    # Collect files to upload (for FTP mode)
                    files_to_upload = []
                    if result.get('path'):
                        files_to_upload.append(result['path'])
                    if result.get('thumbnail_path'):
                        files_to_upload.append(result['thumbnail_path'])

                    # Add all gallery pages
                    if os.path.exists(self.config.PAGES_DIR):
                        for page_file in os.listdir(self.config.PAGES_DIR):
                            if page_file.endswith('.html'):
                                files_to_upload.append(f"{self.config.PAGES_DIR}/{page_file}")

                    # Deploy
                    self.deployment_manager.deploy(commit_message, files_to_upload)

                logger.info("✓ File processed successfully!")

        except Exception as e:
            logger.error(f"Error processing file: {e}")

        finally:
            self.processing = False


def main():
    """Main function"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         AUTOMATED MEDIA UPLOAD SYSTEM                     ║
║         Drop images/videos and watch them upload!         ║
╚═══════════════════════════════════════════════════════════╝
""")

    # Load configuration
    config = Config()
    config.load_from_file()

    # Create necessary directories
    os.makedirs(config.WATCH_DIR, exist_ok=True)
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)

    # Initialize components
    processor = MediaProcessor(config)
    gallery = GalleryGenerator(config)

    # Process any existing files in watch directory
    logger.info(f"Checking for existing files in {config.WATCH_DIR}...")
    for filename in os.listdir(config.WATCH_DIR):
        filepath = os.path.join(config.WATCH_DIR, filename)
        if os.path.isfile(filepath):
            logger.info(f"Processing existing file: {filename}")
            result = processor.process_file(filepath)
            if result:
                gallery.add_media_item(result)

    # Generate initial gallery pages
    gallery.generate_all_pages()
    processor.save_processed_files()

    # Set up file watcher
    event_handler = MediaWatcher(processor, gallery, config)
    observer = Observer()
    observer.schedule(event_handler, config.WATCH_DIR, recursive=False)
    observer.start()

    logger.info(f"✓ Watching directory: {config.WATCH_DIR}")
    logger.info("Drop images or videos into this folder to auto-upload!")
    logger.info("Press Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopping media upload system...")

    observer.join()


if __name__ == "__main__":
    main()
