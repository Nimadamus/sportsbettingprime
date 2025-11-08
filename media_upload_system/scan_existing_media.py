#!/usr/bin/env python3
"""
Website Media Scanner
Scans the entire website directory for existing images and builds a hash database
to prevent duplicate uploads.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Set
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebsiteScanner:
    """Scans website for existing media files"""

    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.webm', '.mov', '.avi'
    }

    def __init__(self, website_root: str = "."):
        self.website_root = website_root
        self.hash_database_file = "media_upload_system/existing_media_hashes.json"
        self.hash_database: Dict[str, str] = {}  # hash -> filepath

        # Directories to exclude from scanning
        self.exclude_dirs = {
            '.git',
            'media_upload_system/processed',
            'media_upload_system/upload_here',
            '__pycache__',
            'node_modules',
            'venv',
            'env'
        }

    def calculate_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {filepath}: {e}")
            return ""

    def is_media_file(self, filepath: str) -> bool:
        """Check if file is a supported media format"""
        ext = Path(filepath).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from scanning"""
        path_parts = Path(path).parts
        for exclude in self.exclude_dirs:
            if exclude in path_parts:
                return True
        return False

    def scan_website(self) -> Dict[str, str]:
        """
        Scan entire website for media files and build hash database
        Returns: Dict mapping file hash to filepath
        """
        logger.info(f"Scanning website directory: {self.website_root}")

        media_files = []

        # Walk through all directories
        for root, dirs, files in os.walk(self.website_root):
            # Skip excluded directories
            if self.should_exclude_path(root):
                continue

            # Remove excluded directories from dirs to prevent walking into them
            dirs[:] = [d for d in dirs if not self.should_exclude_path(os.path.join(root, d))]

            for filename in files:
                filepath = os.path.join(root, filename)

                if self.is_media_file(filepath):
                    media_files.append(filepath)

        logger.info(f"Found {len(media_files)} media files. Building hash database...")

        hash_database = {}
        duplicate_count = 0

        for i, filepath in enumerate(media_files, 1):
            file_hash = self.calculate_file_hash(filepath)

            if file_hash:
                if file_hash in hash_database:
                    # Duplicate found!
                    logger.warning(f"Duplicate found: {filepath} == {hash_database[file_hash]}")
                    duplicate_count += 1
                else:
                    hash_database[file_hash] = filepath

                if i % 10 == 0:
                    logger.info(f"Processed {i}/{len(media_files)} files...")

        logger.info(f"Scan complete! Unique files: {len(hash_database)}, Duplicates found: {duplicate_count}")

        return hash_database

    def save_hash_database(self, hash_database: Dict[str, str]):
        """Save hash database to file"""
        try:
            with open(self.hash_database_file, 'w') as f:
                json.dump(hash_database, f, indent=2, sort_keys=True)
            logger.info(f"Hash database saved to {self.hash_database_file}")
        except Exception as e:
            logger.error(f"Error saving hash database: {e}")

    def load_hash_database(self) -> Dict[str, str]:
        """Load hash database from file"""
        if os.path.exists(self.hash_database_file):
            try:
                with open(self.hash_database_file, 'r') as f:
                    hash_database = json.load(f)
                logger.info(f"Loaded hash database with {len(hash_database)} entries")
                return hash_database
            except Exception as e:
                logger.error(f"Error loading hash database: {e}")
        return {}

    def run_scan_and_save(self):
        """Main method: scan website and save hash database"""
        hash_database = self.scan_website()
        self.save_hash_database(hash_database)

        print("\n" + "="*60)
        print("SCAN RESULTS")
        print("="*60)
        print(f"Total unique media files: {len(hash_database)}")
        print(f"Hash database saved to: {self.hash_database_file}")
        print("\nSample files found:")
        for i, (hash_val, filepath) in enumerate(list(hash_database.items())[:10], 1):
            print(f"  {i}. {filepath}")
            print(f"     Hash: {hash_val[:16]}...")

        if len(hash_database) > 10:
            print(f"  ... and {len(hash_database) - 10} more files")
        print("="*60)

    def check_file_is_duplicate(self, filepath: str) -> tuple[bool, str]:
        """
        Check if a file is a duplicate of any existing media
        Returns: (is_duplicate: bool, existing_filepath: str)
        """
        file_hash = self.calculate_file_hash(filepath)

        if not file_hash:
            return False, ""

        hash_database = self.load_hash_database()

        if file_hash in hash_database:
            return True, hash_database[file_hash]

        return False, ""


def main():
    """Run the scanner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║            WEBSITE MEDIA SCANNER                          ║
║     Scans for existing images to prevent duplicates       ║
╚═══════════════════════════════════════════════════════════╝
""")

    scanner = WebsiteScanner()
    scanner.run_scan_and_save()

    print("\nThis hash database will be used by the auto-uploader")
    print("to prevent duplicate uploads!")


if __name__ == "__main__":
    main()
