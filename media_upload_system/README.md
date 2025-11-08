# Automated Media Upload System

A simple drag-and-drop system that automatically processes images and videos and uploads them to your website with beautiful gallery pages.

## Features

- **Drag & Drop**: Just drop images/videos into a folder and they're automatically processed
- **Image Optimization**: Automatically resizes and compresses images for web
- **Thumbnail Generation**: Creates thumbnails for faster page loading
- **Gallery Pages**: Auto-generates beautiful responsive gallery pages
- **Git Integration**: Automatically commits and pushes to GitHub
- **Duplicate Detection**: Prevents uploading the same file twice
- **Configurable**: Customize sizes, quality, and behavior via JSON config
- **Support Multiple Formats**: JPG, PNG, GIF, WebP, MP4, WebM, MOV, AVI

## Quick Start

### 1. Install Dependencies

```bash
cd media_upload_system
pip install -r requirements.txt
```

### 2. IMPORTANT: Scan for Existing Media (First Time Only)

**CRITICAL STEP to prevent duplicates!**

Before uploading any files, scan your website to build a database of existing media:

```bash
python scan_existing_media.py
```

This will:
- Scan your entire website for existing images and videos
- Build a hash database of all media files
- Prevent uploading duplicates that already exist on your site

**You only need to run this once**, or whenever you manually add files to your website outside of this system.

### 3. Run the System

```bash
python auto_uploader.py
```

### 4. Upload Media

Simply drag and drop images or videos into the `media_upload_system/upload_here/` folder!

The system will automatically:
- **Check for duplicates** (against ALL existing media on your site)
- Optimize and resize images
- Generate thumbnails
- Create gallery HTML pages
- Commit changes to Git
- Push to GitHub

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. Drop files into upload_here/ folder                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. System detects new files                            │
│     - Calculates hash to prevent duplicates             │
│     - Checks file format (image/video)                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. Process images                                      │
│     - Resize to max dimensions (1920x1080)              │
│     - Compress with 85% quality                         │
│     - Generate thumbnail (400x400)                      │
│     - Save to media/ folder                             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  4. Generate gallery pages                              │
│     - Add to media index                                │
│     - Generate HTML pages (20 items per page)           │
│     - Save to pages/ folder                             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  5. Commit and push to GitHub                           │
│     - git add .                                         │
│     - git commit -m "Auto-upload: Add N new files"      │
│     - git push                                          │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
media_upload_system/
├── auto_uploader.py          # Main script
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── upload_here/               # DROP YOUR FILES HERE
├── processed/                 # Moved original files
├── media_index.json           # Database of all media
├── processed_files.json       # Hash list to prevent duplicates
└── upload.log                 # Activity log

media/                         # Generated media files (on website)
├── thumbnails/                # Generated thumbnails
└── [timestamped files]        # Optimized images/videos

pages/                         # Generated HTML pages (on website)
├── index.html                 # Redirects to gallery-1.html
├── gallery-1.html             # First page of gallery
├── gallery-2.html             # Second page, etc.
└── ...
```

## Configuration

Edit `config.json` to customize the system:

```json
{
  "WATCH_DIR": "media_upload_system/upload_here",
  "OUTPUT_DIR": "media",
  "PAGES_DIR": "pages",

  "MAX_IMAGE_WIDTH": 1920,      // Max width for images
  "MAX_IMAGE_HEIGHT": 1080,      // Max height for images
  "THUMBNAIL_SIZE": [400, 400],  // Thumbnail dimensions
  "IMAGE_QUALITY": 85,           // JPEG quality (0-100)

  "AUTO_COMMIT": true,           // Auto-commit to git
  "AUTO_PUSH": true,             // Auto-push to GitHub

  "ITEMS_PER_PAGE": 20,          // Gallery items per page
  "GALLERY_TITLE": "Media Gallery"
}
```

## Supported File Formats

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### Videos
- MP4 (.mp4)
- WebM (.webm)
- MOV (.mov)
- AVI (.avi)

## Usage Examples

### Basic Usage

```bash
# Start the system
python auto_uploader.py

# In another terminal or file explorer:
# Copy files to upload_here/
cp ~/Downloads/photo.jpg media_upload_system/upload_here/
cp ~/Downloads/video.mp4 media_upload_system/upload_here/

# Watch the logs to see processing happen automatically!
```

### Batch Upload

```bash
# Copy multiple files at once
cp ~/Downloads/*.jpg media_upload_system/upload_here/
cp ~/Downloads/*.mp4 media_upload_system/upload_here/
```

### Processing Existing Files

If you already have files in `upload_here/` when you start the system, they'll be processed automatically on startup.

## Viewing Your Gallery

After files are processed and pushed to GitHub, your gallery will be available at:

```
https://yourdomain.com/pages/
https://yourdomain.com/pages/gallery-1.html
```

The gallery features:
- Responsive grid layout
- Click to view full-size images
- Video playback controls
- Pagination for multiple pages
- Beautiful gradient design

## Troubleshooting

### Files aren't being processed

1. Check that the system is running: `python auto_uploader.py`
2. Check the log file: `tail -f media_upload_system/upload.log`
3. Verify file format is supported
4. Make sure files aren't locked by another program

### Git push fails

1. Check you're on the correct branch: `git branch`
2. Verify git credentials are configured
3. Check network connection
4. Try manual push: `git push -u origin your-branch`

### Image quality is too low/high

Edit `config.json` and change `IMAGE_QUALITY` (0-100):
- 85 = good balance (default)
- 95 = higher quality, larger files
- 75 = lower quality, smaller files

### Want to change max image size

Edit `config.json`:
```json
{
  "MAX_IMAGE_WIDTH": 2560,  // 4K width
  "MAX_IMAGE_HEIGHT": 1440
}
```

## Advanced Features

### Enhanced Duplicate Detection

The system has **two-layer duplicate protection**:

#### Layer 1: Existing Website Media
- On first run, use `scan_existing_media.py` to scan your entire website
- Builds a hash database of **all existing images and videos**
- Before uploading any new file, checks if it already exists **anywhere on your site**
- **Prevents duplicates even if the file has a different name or is in a different folder**

#### Layer 2: Newly Uploaded Files
- Tracks all files uploaded through this system
- Prevents uploading the same file multiple times

**How it works:**
- Calculates MD5 hash of each file's binary content
- Two files with identical content will have the same hash, even with different filenames
- Example: `photo.jpg` and `image_copy_renamed.jpg` with identical pixels will be detected as duplicates

**To rescan your website** (if you manually add files outside this system):
```bash
python scan_existing_media.py
```

### Auto-generated Filenames

Files are automatically renamed with timestamps to prevent conflicts:
```
photo.jpg → 20231108_143052_photo.jpg
```

### Pagination

Gallery pages are automatically paginated. Change items per page in `config.json`:
```json
{
  "ITEMS_PER_PAGE": 30  // Show 30 items per page
}
```

### Manual Processing

You can also process files manually without the watcher:

```python
from auto_uploader import Config, MediaProcessor, GalleryGenerator

config = Config()
processor = MediaProcessor(config)
gallery = GalleryGenerator(config)

# Process a specific file
result = processor.process_file('path/to/image.jpg')
if result:
    gallery.add_media_item(result)
    gallery.generate_all_pages()
```

## Stopping the System

Press `Ctrl+C` in the terminal where the system is running.

## Tips

1. **Keep it running**: Run the system in a terminal or as a background service
2. **Backup originals**: Original files are moved to `processed/` folder
3. **Check logs**: Monitor `upload.log` for detailed activity
4. **Test first**: Try with a few files before bulk uploading
5. **Customize CSS**: Edit the gallery HTML template in `auto_uploader.py`

## Customizing Gallery Design

The gallery HTML is generated in the `GalleryGenerator.generate_gallery_page()` method. You can customize:

- Colors and gradients
- Grid layout (columns, gaps)
- Image sizes
- Hover effects
- Modal lightbox behavior

Edit the CSS in the `<style>` section of the generated HTML template.

## Running as a Service (Optional)

To keep the system running 24/7:

### Linux/Mac (systemd)

Create `/etc/systemd/system/media-uploader.service`:
```ini
[Unit]
Description=Automated Media Upload System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/sportsbettingprime
ExecStart=/usr/bin/python3 media_upload_system/auto_uploader.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable media-uploader
sudo systemctl start media-uploader
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (At startup)
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\auto_uploader.py`
7. Start in: `C:\path\to\sportsbettingprime`

## License

Free to use and modify for your needs!

## Support

For issues or questions, check the logs:
```bash
tail -f media_upload_system/upload.log
```

Happy uploading! 🚀
