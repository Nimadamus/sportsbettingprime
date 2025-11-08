# Desktop Gallery Creator - Quick Start

## Process Images on Your Computer & Create Gallery Pages

This tool processes images from any folder on your computer and creates beautiful gallery pages on your desktop.

### What It Does

1. ✓ Finds all images in a folder you specify
2. ✓ Optimizes and resizes them (max 1920x1080)
3. ✓ Creates thumbnails (400x400)
4. ✓ Generates beautiful gallery HTML pages
5. ✓ Saves everything to `REALIAIGRILS NEW PAGES` on your desktop
6. ✓ Detects and skips duplicate images

### How to Use

#### Option 1: Double-Click (Easiest)

**Windows:**
1. Double-click `create_gallery.bat`
2. Enter the path to your images folder
3. Wait for processing
4. Done! Check your desktop for the new folder

**Mac/Linux:**
1. Double-click `create_gallery.sh` (or run in terminal)
2. Enter the path to your images folder
3. Wait for processing
4. Done! Check your desktop for the new folder

#### Option 2: Command Line

```bash
# Install dependency first (one time)
pip install Pillow

# Run the processor
python media_upload_system/process_to_desktop.py
```

When prompted, enter the full path to your images folder, for example:
- Windows: `C:\Users\YourName\Pictures\AI Girls`
- Mac: `/Users/YourName/Pictures/AI Girls`
- Linux: `/home/yourname/Pictures/AI Girls`

### What You Get

A folder on your desktop called `REALIAIGRILS NEW PAGES` containing:

```
REALIAIGRILS NEW PAGES/
├── images/              ← Optimized images
├── thumbnails/          ← Small preview images
├── pages/               ← Gallery HTML pages
│   ├── index.html      ← Open this to view!
│   ├── page-1.html
│   ├── page-2.html
│   └── ...
└── README.txt          ← Info about the gallery
```

### View Your Gallery

**On Your Computer:**
1. Go to your Desktop
2. Open `REALIAIGRILS NEW PAGES` folder
3. Open `pages/index.html` in your browser

**Upload to Your Website:**
1. Use FileZilla or your FTP client
2. Upload the `images` folder to your website
3. Upload the `thumbnails` folder to your website
4. Upload the `pages` folder to your website
5. Visit `yourwebsite.com/pages/` to see the live gallery!

### Features

**Automatic Duplicate Detection**
- Uses file hashing to detect identical images
- Skips duplicates even if they have different names
- Prevents wasting space and processing time

**Smart Image Processing**
- Resizes large images to max 1920x1080 (maintains aspect ratio)
- Compresses to 85% quality for fast loading
- Converts all images to JPEG format
- Creates thumbnails for faster page loading

**Beautiful Gallery Pages**
- Responsive grid layout
- Click images to view full size
- Automatic pagination (20 images per page)
- Modern gradient purple design
- Mobile-friendly

**Cross-Platform**
- Works on Windows, Mac, and Linux
- Automatically finds your desktop
- Handles all common image formats (JPG, PNG, GIF, WebP, BMP)

### Examples

**Process images from Downloads folder:**
```
Image folder path: C:\Users\John\Downloads\AI Images
```

**Process images from Pictures folder:**
```
Image folder path: /Users/jane/Pictures/Generated Art
```

**Process images from USB drive:**
```
Image folder path: D:\My Images
```

### Settings

You can edit `process_to_desktop.py` to change:

```python
self.max_width = 1920          # Maximum image width
self.max_height = 1080         # Maximum image height
self.thumbnail_size = (400, 400)  # Thumbnail size
self.quality = 85              # JPEG quality (0-100)
self.items_per_page = 20       # Images per page
```

### Troubleshooting

**"No images found"**
- Check the folder path is correct
- Make sure folder contains JPG, PNG, GIF, WebP, or BMP files
- Try using the full path (not relative path)

**"Pillow not installed"**
```bash
pip install Pillow
```

**"Can't find Desktop"**
- The script will use your home directory instead
- Look for `REALIAIGRILS NEW PAGES` in your home folder

**Images look too compressed**
- Edit `process_to_desktop.py`
- Change `self.quality = 85` to `95` for higher quality

### Tips

1. **Organize First**: Put all images you want in one folder before running
2. **Subfolders Work**: The script searches all subfolders automatically
3. **Run Multiple Times**: Each run creates a timestamp, won't overwrite
4. **Preview First**: View the gallery locally before uploading
5. **Backup Originals**: The script doesn't modify your original images

### What Gets Created

**For 100 images, you'll get:**

```
REALIAIGRILS NEW PAGES/
├── images/              ← 100 optimized images (~2-5 MB each)
├── thumbnails/          ← 100 thumbnails (~50-100 KB each)
├── pages/
│   ├── index.html
│   ├── page-1.html     ← First 20 images
│   ├── page-2.html     ← Next 20 images
│   ├── page-3.html     ← Next 20 images
│   ├── page-4.html     ← Next 20 images
│   └── page-5.html     ← Last 20 images
└── README.txt
```

### Quick Reference

| What | Where |
|------|-------|
| **Source images** | Folder you specify |
| **Output folder** | Desktop/REALIAIGRILS NEW PAGES |
| **View gallery** | pages/index.html |
| **Upload to web** | Upload all 3 folders (images, thumbnails, pages) |
| **Max image size** | 1920x1080 pixels |
| **Quality** | 85% JPEG |
| **Per page** | 20 images |

### Next Steps

1. Run the script
2. Point it to your images folder
3. Wait for processing
4. Open `pages/index.html` to preview
5. Upload to realaigirls.com when ready!

That's it! Simple and fast gallery creation.
