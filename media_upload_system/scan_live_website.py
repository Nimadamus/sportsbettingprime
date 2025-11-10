#!/usr/bin/env python3
"""
Website Duplicate Scanner for RealAIGirls.com
Downloads and scans ALL existing images on your live website to prevent duplicates
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
import urllib.parse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    os.system("pip install beautifulsoup4 requests")
    from bs4 import BeautifulSoup


class WebsiteDuplicateScanner:
    """Scans live website for existing images to prevent duplicates"""

    def __init__(self, website_url="https://realaigirls.com"):
        self.website_url = website_url
        self.existing_hashes = {}  # hash -> url
        self.scan_results = {
            'total_images': 0,
            'scanned': 0,
            'failed': 0,
            'scan_date': datetime.now().isoformat()
        }

    def calculate_hash(self, image_data):
        """Calculate MD5 hash of image data"""
        hash_md5 = hashlib.md5()
        hash_md5.update(image_data)
        return hash_md5.hexdigest()

    def find_all_image_urls(self):
        """Find all image URLs on the website"""
        print("🔍 Scanning website for image URLs...")
        image_urls = set()

        # Common paths where images might be
        paths_to_scan = [
            '/pages/',
            '/images/',
            '/media/',
            '/gallery/',
            '/'
        ]

        for path in paths_to_scan:
            try:
                url = f"{self.website_url}{path}"
                print(f"   Checking: {url}")
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Find all img tags
                    for img in soup.find_all('img'):
                        src = img.get('src')
                        if src:
                            # Convert relative to absolute URLs
                            if src.startswith('/'):
                                full_url = f"{self.website_url}{src}"
                            elif src.startswith('http'):
                                full_url = src
                            else:
                                full_url = f"{self.website_url}/{path}/{src}"

                            # Only process image files
                            if any(full_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                image_urls.add(full_url)

                    # Also check for links to gallery pages
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if 'gallery' in href.lower() or 'page' in href.lower():
                            try:
                                if href.startswith('/'):
                                    page_url = f"{self.website_url}{href}"
                                else:
                                    page_url = href

                                page_response = requests.get(page_url, timeout=10)
                                if page_response.status_code == 200:
                                    page_soup = BeautifulSoup(page_response.content, 'html.parser')
                                    for img in page_soup.find_all('img'):
                                        src = img.get('src')
                                        if src and any(src.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                            if src.startswith('/'):
                                                image_urls.add(f"{self.website_url}{src}")
                                            elif src.startswith('http'):
                                                image_urls.add(src)
                            except:
                                pass

            except Exception as e:
                print(f"   ⚠️  Error scanning {path}: {e}")

        print(f"\n✓ Found {len(image_urls)} unique image URLs on website")
        return list(image_urls)

    def scan_image(self, image_url):
        """Download and hash a single image"""
        try:
            response = requests.get(image_url, timeout=15, stream=True)
            if response.status_code == 200:
                image_data = response.content
                image_hash = self.calculate_hash(image_data)

                self.existing_hashes[image_hash] = {
                    'url': image_url,
                    'size': len(image_data)
                }
                self.scan_results['scanned'] += 1
                return True
        except Exception as e:
            self.scan_results['failed'] += 1
            return False

    def scan_website(self):
        """Scan entire website for existing images"""
        print("\n" + "="*60)
        print("  SCANNING REALAIGIRLS.COM FOR EXISTING IMAGES")
        print("="*60)
        print()
        print("This will download and hash all existing images")
        print("to prevent uploading duplicates.")
        print()

        # Find all image URLs
        image_urls = self.find_all_image_urls()

        if not image_urls:
            print("\n⚠️  No images found on website.")
            print("This might mean:")
            print("  • Website is empty (first upload)")
            print("  • Images are in a different location")
            print("  • Website structure is different than expected")
            print()
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)

        self.scan_results['total_images'] = len(image_urls)

        # Scan each image
        print(f"\n📥 Downloading and hashing {len(image_urls)} images...")
        print("This may take a few minutes...")
        print()

        for i, url in enumerate(image_urls, 1):
            print(f"[{i}/{len(image_urls)}] {url.split('/')[-1][:50]}...", end=' ')
            if self.scan_image(url):
                print("✓")
            else:
                print("✗ Failed")

        return self.existing_hashes

    def save_database(self, filepath='existing_images_database.json'):
        """Save hash database to file"""
        data = {
            'scan_results': self.scan_results,
            'existing_hashes': self.existing_hashes
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n💾 Saved database: {filepath}")
        return filepath

    def print_summary(self):
        """Print scan summary"""
        print("\n" + "="*60)
        print("  SCAN COMPLETE")
        print("="*60)
        print(f"Total images found:  {self.scan_results['total_images']}")
        print(f"Successfully hashed: {self.scan_results['scanned']}")
        print(f"Failed:              {self.scan_results['failed']}")
        print(f"Unique hashes:       {len(self.existing_hashes)}")
        print("="*60)
        print()
        print("✅ Duplicate protection is now active!")
        print("   Any image matching these hashes will be skipped.")
        print()


def main():
    """Main function"""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   REALAIGIRLS.COM - DUPLICATE PREVENTION SCANNER          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    # Get website URL
    website = input("Website URL [https://realaigirls.com]: ").strip()
    if not website:
        website = "https://realaigirls.com"

    # Create scanner
    scanner = WebsiteDuplicateScanner(website)

    # Scan website
    scanner.scan_website()

    # Save database
    db_path = scanner.save_database()

    # Print summary
    scanner.print_summary()

    print(f"Database saved to: {db_path}")
    print()
    print("Next steps:")
    print("  1. Run the main upload script (RUN_ME.bat or RUN_ME.sh)")
    print("  2. It will automatically check against this database")
    print("  3. Only NEW images will be uploaded")
    print()


if __name__ == "__main__":
    main()
