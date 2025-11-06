# Quick Start Guide - 5 Minutes Setup

Get your image duplicate detector running on GoDaddy in 5 minutes!

## Step 1: Upload Files (1 minute)

1. Download all files from `image-duplicate-detector` folder
2. Log into **GoDaddy cPanel**
3. Go to **File Manager**
4. Navigate to `public_html`
5. Upload all files to a new folder (e.g., `image-detector`)

## Step 2: Create Database (2 minutes)

1. In cPanel, click **MySQL® Databases**
2. Create database:
   - Name: `realaigirls_images`
   - Click "Create Database"
3. Create user:
   - Username: `img_admin` (or your choice)
   - Password: (generate strong password)
   - Click "Create User"
4. Link them:
   - Select user + database
   - Grant ALL PRIVILEGES
   - Click "Add"

**Write down**: Database name, username, password

## Step 3: Configure (1 minute)

1. Open `config.php` in File Manager
2. Update these 4 lines:

```php
define('DB_NAME', 'realaigirls_images');     // Your database name
define('DB_USER', 'img_admin');              // Your database user
define('DB_PASS', 'YOUR_PASSWORD_HERE');     // Your database password
define('ADMIN_PASSWORD', 'YOUR_ADMIN_PASS'); // Pick admin password
```

3. Save file

## Step 4: Install (30 seconds)

1. Visit: `https://realaigirls.com/image-detector/install.php`
2. Click **Install Database**
3. See success message!

## Step 5: Use It! (30 seconds)

**Upload page:**
```
https://realaigirls.com/image-detector/upload.php
```

**Admin panel:**
```
https://realaigirls.com/image-detector/admin.php
```

Login with the password you set in config.php

## Done! 🎉

Now try uploading the same image twice - it will detect the duplicate!

---

## What It Does

- ✅ Detects duplicate images automatically
- ✅ Works even if image is renamed or slightly modified
- ✅ Beautiful drag-and-drop interface
- ✅ Shows similarity percentage
- ✅ Admin panel to manage all images

## Customization

Want to change how strict it is?

In `config.php`:
```php
define('SIMILARITY_THRESHOLD', 5); // Change 5 to:
// 0 = only exact duplicates
// 5 = recommended (default)
// 10 = very lenient
```

## Need Help?

See `README.md` for full documentation and troubleshooting.

---

**That's it! You're ready to prevent duplicate uploads on REALAIGIRLS.COM** 🚀
