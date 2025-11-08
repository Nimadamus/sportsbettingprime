# Deploying to GoDaddy-Hosted Website (realaigirls.com)

This guide explains how to use the automated media upload system with your GoDaddy-hosted website.

## Overview

Since this system was built in a GitHub repository but your actual website (realaigirls.com) is hosted on GoDaddy, you have two deployment options:

## Option 1: Local System with FTP Upload (Recommended for Simplicity)

Run the system on your computer and automatically upload to GoDaddy via FTP.

### Setup Steps

#### 1. Download Your Current Website from GoDaddy

First, you need to download your existing website files to scan for duplicates:

```bash
# Install lftp (FTP client)
# Mac:
brew install lftp

# Linux:
sudo apt-get install lftp

# Download your website
mkdir ~/realaigirls-website
cd ~/realaigirls-website
lftp ftp.yourdomain.com -u your-username
# Enter password when prompted
> mirror /public_html ./
> quit
```

Or use FileZilla (GUI FTP client):
1. Download FileZilla: https://filezilla-project.org/
2. Connect to your GoDaddy FTP
3. Download all files from `/public_html/` to a local folder

#### 2. Copy the Media Upload System

Copy the `media_upload_system/` folder to your local website directory:

```bash
cp -r /path/to/sportsbettingprime/media_upload_system ~/realaigirls-website/
```

#### 3. Scan for Existing Media

**CRITICAL STEP to prevent duplicates:**

```bash
cd ~/realaigirls-website
python media_upload_system/scan_existing_media.py
```

This will scan your entire website and build a hash database of all existing images and videos.

#### 4. Install FTP Upload Capability

Install additional dependencies:

```bash
pip install ftplib pathlib
```

#### 5. Configure FTP Settings

Edit `media_upload_system/config.json` and add your GoDaddy FTP credentials:

```json
{
  "WATCH_DIR": "media_upload_system/upload_here",
  "OUTPUT_DIR": "media",
  "PAGES_DIR": "pages",

  "FTP_ENABLED": true,
  "FTP_HOST": "ftp.realaigirls.com",
  "FTP_USERNAME": "your-ftp-username@realaigirls.com",
  "FTP_PASSWORD": "your-ftp-password",
  "FTP_REMOTE_PATH": "/public_html",

  "MAX_IMAGE_WIDTH": 1920,
  "MAX_IMAGE_HEIGHT": 1080,
  "IMAGE_QUALITY": 85,
  "ITEMS_PER_PAGE": 20,
  "GALLERY_TITLE": "RealAIGirls Gallery",

  "AUTO_COMMIT": false,
  "AUTO_PUSH": false
}
```

**IMPORTANT:** Keep this file secure! Don't commit it to Git with your password.

#### 6. Update the Auto-Uploader to Support FTP

I'll create an FTP module for you. See `ftp_uploader.py` (created separately).

#### 7. Run the System

```bash
cd ~/realaigirls-website
python media_upload_system/auto_uploader.py
```

Now when you drop files into `media_upload_system/upload_here/`, they will:
1. Be checked for duplicates against your entire website
2. Get optimized and processed
3. Automatically upload to GoDaddy via FTP
4. Generate gallery pages and upload them too

---

## Option 2: GitHub + Manual FTP (Simpler Setup)

If you don't want to run the system locally all the time:

### Workflow

1. **On your computer:**
   - Copy the `media_upload_system/` folder to a separate directory
   - Drop images into `upload_here/`
   - Run `python auto_uploader.py`
   - This generates optimized files and gallery pages locally

2. **Upload to GoDaddy:**
   - Use FileZilla or any FTP client
   - Upload the `media/` folder to your GoDaddy `/public_html/media/`
   - Upload the `pages/` folder to your GoDaddy `/public_html/pages/`

### Steps

```bash
# 1. Download your GoDaddy website (first time only)
mkdir ~/realaigirls-local
# Use FileZilla to download everything

# 2. Copy the media system
cp -r /path/to/sportsbettingprime/media_upload_system ~/realaigirls-local/

# 3. Scan existing media (first time only)
cd ~/realaigirls-local
python media_upload_system/scan_existing_media.py

# 4. Process new media
# Drop images into media_upload_system/upload_here/
python media_upload_system/auto_uploader.py

# 5. Upload to GoDaddy via FileZilla
# Upload the generated media/ and pages/ folders
```

---

## Option 3: VPS/Cloud Server (Fully Automated 24/7)

For a completely hands-off solution, run this on a cloud server.

### Best Options:
- **DigitalOcean Droplet**: $6/month
- **AWS Lightsail**: $5/month
- **Linode**: $5/month

### Setup:

1. Create a small Linux VPS
2. Install Python and dependencies
3. Clone this repository
4. Download your GoDaddy website to the VPS
5. Run the system 24/7 as a service
6. Set up FTP auto-upload to GoDaddy

**Benefits:**
- Runs 24/7 without your computer
- Can trigger uploads via API or scheduled jobs
- Can even generate AI images automatically and upload them

---

## Finding Your GoDaddy FTP Credentials

### Method 1: GoDaddy Dashboard

1. Log into GoDaddy: https://www.godaddy.com/
2. Go to **My Products**
3. Find your **Web Hosting** for realaigirls.com
4. Click **Manage**
5. Go to **Settings** → **FTP/SFTP**
6. Your FTP hostname will be like: `ftp.realaigirls.com`
7. Username is usually your GoDaddy email or custom username
8. Password: Reset if needed

### Method 2: cPanel (if you have it)

1. Log into cPanel from GoDaddy
2. Find **FTP Accounts**
3. Create a new FTP account or use the main one
4. Note the server, username, and password

### Common GoDaddy FTP Settings:
- **Host:** `ftp.yourdomain.com` or provided by GoDaddy
- **Port:** 21 (FTP) or 22 (SFTP - more secure)
- **Username:** Usually `username@yourdomain.com`
- **Remote Path:** `/public_html/` or `/html/`

---

## Security Best Practices

### Don't Commit FTP Credentials to Git!

Add this to your `.gitignore`:

```
# FTP credentials
media_upload_system/config.json
media_upload_system/ftp_credentials.json
```

### Store Credentials Separately

Create `media_upload_system/ftp_credentials.json`:

```json
{
  "FTP_HOST": "ftp.realaigirls.com",
  "FTP_USERNAME": "your-username",
  "FTP_PASSWORD": "your-password",
  "FTP_REMOTE_PATH": "/public_html"
}
```

Then update the auto-uploader to load from this file.

---

## Testing the System

### Test 1: Duplicate Detection

1. Download an image from your website
2. Try to upload it again through the system
3. It should be rejected as a duplicate

### Test 2: New Upload

1. Drop a new image into `upload_here/`
2. Check the logs: `tail -f media_upload_system/upload.log`
3. Verify it gets optimized and uploaded
4. Check your website to see the new image

### Test 3: Gallery Pages

1. Upload several images
2. Check that `pages/gallery-1.html` was created
3. Visit `https://realaigirls.com/pages/gallery-1.html`
4. Verify the gallery displays correctly

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────┐
│  YOU: Drop images into upload_here/                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  SYSTEM: Scans file and calculates hash            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  CHECK: Is this file already on realaigirls.com?   │
│  - Checks against hash database                    │
│  - If duplicate: SKIP and alert you                │
│  - If new: Continue processing                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  PROCESS: Optimize image                           │
│  - Resize to max 1920x1080                         │
│  - Compress to 85% quality                         │
│  - Generate 400x400 thumbnail                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  GENERATE: Update gallery pages                    │
│  - Add to media index                              │
│  - Regenerate all gallery HTML pages               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  UPLOAD: Send to GoDaddy via FTP                   │
│  - Upload optimized image                          │
│  - Upload thumbnail                                │
│  - Upload updated gallery pages                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  DONE: Image now live on realaigirls.com!          │
└─────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Cannot connect to FTP"

1. Check your FTP credentials are correct
2. Try connecting with FileZilla manually first
3. Check if your GoDaddy hosting has FTP enabled
4. Verify firewall isn't blocking FTP (port 21)

### "Duplicate not detected"

1. Make sure you ran `scan_existing_media.py` first
2. Check `existing_media_hashes.json` exists and has data
3. Rescan: `python scan_existing_media.py`

### "Files uploading but not visible on website"

1. Check the remote path is correct (`/public_html/` or `/html/`)
2. Verify file permissions on GoDaddy (should be 644 for files, 755 for directories)
3. Check GoDaddy file manager to confirm files are there

---

## Next Steps

1. Choose which deployment option works best for you
2. Set up FTP credentials
3. Download your existing website
4. Scan for duplicates
5. Start uploading!

Need help? Check the logs in `media_upload_system/upload.log`
