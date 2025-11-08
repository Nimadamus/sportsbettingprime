#!/usr/bin/env python3
"""
FTP Uploader Module
Automatically uploads files to GoDaddy or any FTP server
"""

import os
import json
import logging
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FTPUploader:
    """Handles FTP uploads to web host"""

    def __init__(self, config_file: str = "media_upload_system/config.json"):
        self.ftp = None
        self.host = None
        self.username = None
        self.password = None
        self.remote_path = "/public_html"
        self.use_tls = False

        self.load_config(config_file)

    def load_config(self, config_file: str):
        """Load FTP configuration"""
        # Try main config file
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                self.host = config.get('FTP_HOST')
                self.username = config.get('FTP_USERNAME')
                self.password = config.get('FTP_PASSWORD')
                self.remote_path = config.get('FTP_REMOTE_PATH', '/public_html')
                self.use_tls = config.get('FTP_USE_TLS', False)

                if self.host and self.username and self.password:
                    logger.info(f"Loaded FTP config: {self.username}@{self.host}")
                else:
                    logger.warning("FTP credentials not configured in config.json")
            except Exception as e:
                logger.error(f"Error loading FTP config: {e}")

        # Try separate credentials file (more secure)
        cred_file = "media_upload_system/ftp_credentials.json"
        if os.path.exists(cred_file):
            try:
                with open(cred_file, 'r') as f:
                    creds = json.load(f)

                self.host = creds.get('FTP_HOST', self.host)
                self.username = creds.get('FTP_USERNAME', self.username)
                self.password = creds.get('FTP_PASSWORD', self.password)
                self.remote_path = creds.get('FTP_REMOTE_PATH', self.remote_path)
                self.use_tls = creds.get('FTP_USE_TLS', self.use_tls)

                logger.info(f"Loaded FTP credentials from {cred_file}")
            except Exception as e:
                logger.error(f"Error loading FTP credentials: {e}")

    def connect(self) -> bool:
        """Connect to FTP server"""
        if not all([self.host, self.username, self.password]):
            logger.error("FTP credentials not configured!")
            return False

        try:
            # Use TLS if enabled (more secure)
            if self.use_tls:
                self.ftp = FTP_TLS(self.host)
                self.ftp.login(self.username, self.password)
                self.ftp.prot_p()  # Enable encryption
                logger.info("Connected to FTP with TLS encryption")
            else:
                self.ftp = FTP(self.host)
                self.ftp.login(self.username, self.password)
                logger.info("Connected to FTP")

            # Change to remote directory
            if self.remote_path:
                self.ftp.cwd(self.remote_path)
                logger.info(f"Changed to remote directory: {self.remote_path}")

            return True

        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from FTP server"""
        if self.ftp:
            try:
                self.ftp.quit()
                logger.info("Disconnected from FTP")
            except:
                pass

    def ensure_remote_directory(self, remote_dir: str):
        """Create remote directory if it doesn't exist"""
        if not self.ftp:
            return False

        try:
            # Try to change to the directory
            self.ftp.cwd(remote_dir)
            # If successful, go back
            self.ftp.cwd(self.remote_path)
        except:
            # Directory doesn't exist, create it
            try:
                # Create parent directories if needed
                parts = remote_dir.strip('/').split('/')
                current = self.remote_path

                for part in parts:
                    if not part:
                        continue

                    current = f"{current}/{part}"

                    try:
                        self.ftp.cwd(current)
                    except:
                        # Doesn't exist, create it
                        self.ftp.mkd(current)
                        logger.info(f"Created remote directory: {current}")

                # Return to base directory
                self.ftp.cwd(self.remote_path)

            except Exception as e:
                logger.error(f"Error creating remote directory {remote_dir}: {e}")
                return False

        return True

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a single file to FTP server

        Args:
            local_path: Path to local file
            remote_path: Path on remote server (relative to FTP_REMOTE_PATH)

        Returns:
            True if successful, False otherwise
        """
        if not self.ftp:
            if not self.connect():
                return False

        try:
            # Ensure remote directory exists
            remote_dir = str(Path(remote_path).parent)
            if remote_dir and remote_dir != '.':
                self.ensure_remote_directory(remote_dir)

            # Change to the target directory
            if remote_dir and remote_dir != '.':
                self.ftp.cwd(f"{self.remote_path}/{remote_dir}")

            # Upload file
            filename = Path(remote_path).name

            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {filename}', f)

            logger.info(f"✓ Uploaded: {local_path} → {remote_path}")

            # Return to base directory
            self.ftp.cwd(self.remote_path)

            return True

        except Exception as e:
            logger.error(f"Error uploading {local_path}: {e}")
            return False

    def upload_directory(self, local_dir: str, remote_dir: str = "") -> List[str]:
        """
        Upload entire directory to FTP server

        Args:
            local_dir: Path to local directory
            remote_dir: Path on remote server (relative to FTP_REMOTE_PATH)

        Returns:
            List of successfully uploaded files
        """
        if not self.ftp:
            if not self.connect():
                return []

        uploaded_files = []

        try:
            for root, dirs, files in os.walk(local_dir):
                # Calculate relative path
                rel_path = os.path.relpath(root, local_dir)

                if rel_path == '.':
                    remote_subdir = remote_dir
                else:
                    remote_subdir = f"{remote_dir}/{rel_path}".strip('/')

                # Upload files in this directory
                for filename in files:
                    local_file = os.path.join(root, filename)
                    remote_file = f"{remote_subdir}/{filename}".strip('/')

                    if self.upload_file(local_file, remote_file):
                        uploaded_files.append(remote_file)

            logger.info(f"Uploaded {len(uploaded_files)} files from {local_dir}")

        except Exception as e:
            logger.error(f"Error uploading directory {local_dir}: {e}")

        return uploaded_files

    def test_connection(self) -> bool:
        """Test FTP connection"""
        print("Testing FTP connection...")
        print(f"Host: {self.host}")
        print(f"Username: {self.username}")
        print(f"Remote path: {self.remote_path}")
        print(f"TLS: {self.use_tls}")
        print()

        if self.connect():
            print("✓ Connection successful!")

            # List files
            try:
                print("\nFiles in remote directory:")
                files = self.ftp.nlst()
                for i, f in enumerate(files[:10], 1):
                    print(f"  {i}. {f}")

                if len(files) > 10:
                    print(f"  ... and {len(files) - 10} more")

            except Exception as e:
                print(f"Could not list files: {e}")

            self.disconnect()
            return True
        else:
            print("✗ Connection failed!")
            return False


def main():
    """Test the FTP uploader"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║              FTP UPLOADER TEST                            ║
╚═══════════════════════════════════════════════════════════╝
""")

    uploader = FTPUploader()

    if not uploader.host:
        print("FTP not configured!")
        print("\nTo configure FTP:")
        print("1. Edit media_upload_system/config.json")
        print("2. Add FTP credentials:")
        print("""
{
  "FTP_HOST": "ftp.yourdomain.com",
  "FTP_USERNAME": "username@yourdomain.com",
  "FTP_PASSWORD": "your-password",
  "FTP_REMOTE_PATH": "/public_html",
  "FTP_USE_TLS": false
}
""")
        return

    uploader.test_connection()


if __name__ == "__main__":
    main()
