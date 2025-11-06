<?php
/**
 * Installation Script
 * Run this file once to set up the database
 */

require_once 'config.php';

$errors = [];
$success = [];

// Check PHP version
if (version_compare(PHP_VERSION, '7.0.0', '<')) {
    $errors[] = 'PHP 7.0 or higher is required. Current version: ' . PHP_VERSION;
}

// Check required extensions
$requiredExtensions = ['pdo', 'pdo_mysql', 'gd'];
foreach ($requiredExtensions as $ext) {
    if (!extension_loaded($ext)) {
        $errors[] = "Required PHP extension not loaded: $ext";
    }
}

// Check GD library capabilities
if (extension_loaded('gd')) {
    $gdInfo = gd_info();
    $requiredFormats = [
        'JPEG Support' => 'JPEG',
        'PNG Support' => 'PNG',
        'GIF Read Support' => 'GIF',
    ];

    foreach ($requiredFormats as $key => $format) {
        if (empty($gdInfo[$key])) {
            $errors[] = "GD library does not support $format images";
        }
    }
}

// Check config
if (DB_NAME === 'your_database_name' || DB_USER === 'your_database_user') {
    $errors[] = 'Please update database credentials in config.php';
}

if (ADMIN_PASSWORD === 'change_this_password') {
    $errors[] = 'Please change the admin password in config.php';
}

// Try database connection
$dbConnected = false;
if (empty($errors)) {
    try {
        $db = getDbConnection();
        $dbConnected = true;
        $success[] = 'Database connection successful';
    } catch (Exception $e) {
        $errors[] = 'Database connection failed: ' . $e->getMessage();
    }
}

// Create database table
if ($dbConnected && isset($_POST['install'])) {
    try {
        require_once 'ImageDuplicateDetector.php';
        $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);
        $detector->createTable();
        $success[] = 'Database table created successfully';

        // Create uploads directory
        if (!file_exists(UPLOAD_DIR)) {
            mkdir(UPLOAD_DIR, 0755, true);
            $success[] = 'Uploads directory created: ' . UPLOAD_DIR;
        } else {
            $success[] = 'Uploads directory already exists: ' . UPLOAD_DIR;
        }

        // Create .htaccess for uploads directory (security)
        $htaccessContent = "Options -Indexes\n";
        file_put_contents(UPLOAD_DIR . '/.htaccess', $htaccessContent);
        $success[] = 'Security .htaccess file created';

        $success[] = '<strong>Installation complete! You can now use the application.</strong>';
    } catch (Exception $e) {
        $errors[] = 'Installation failed: ' . $e->getMessage();
    }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Installation - Image Duplicate Detector</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 700px;
            width: 100%;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .check-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .check-item.success {
            background: #d4edda;
            color: #155724;
        }

        .check-item.error {
            background: #f8d7da;
            color: #721c24;
        }

        .check-item.warning {
            background: #fff3cd;
            color: #856404;
        }

        .icon {
            font-size: 20px;
        }

        .section {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 18px;
            color: #333;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }

        .info-box h3 {
            color: #1976D2;
            margin-bottom: 10px;
            font-size: 16px;
        }

        .info-box p {
            color: #333;
            font-size: 14px;
            line-height: 1.6;
        }

        .info-box code {
            background: #fff;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 13px;
        }

        .requirements {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        .requirements ul {
            margin-left: 20px;
            color: #333;
            line-height: 1.8;
        }

        .links {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .links a {
            flex: 1;
            padding: 12px;
            text-align: center;
            background: #f0f0f0;
            color: #667eea;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s;
        }

        .links a:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Installation Setup</h1>
        <p class="subtitle">Image Duplicate Detector for GoDaddy Hosting</p>

        <div class="section">
            <div class="section-title">System Requirements</div>
            <div class="requirements">
                <ul>
                    <li>PHP 7.0 or higher</li>
                    <li>MySQL or MariaDB database</li>
                    <li>PHP GD Library (image processing)</li>
                    <li>PDO MySQL extension</li>
                    <li>Write permissions for uploads directory</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Pre-Installation Checks</div>

            <?php if (!empty($errors)): ?>
                <?php foreach ($errors as $error): ?>
                    <div class="check-item error">
                        <span class="icon">❌</span>
                        <div><?php echo htmlspecialchars($error); ?></div>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>

            <?php if (!empty($success)): ?>
                <?php foreach ($success as $msg): ?>
                    <div class="check-item success">
                        <span class="icon">✅</span>
                        <div><?php echo $msg; ?></div>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>

            <?php if (empty($errors) && empty($success)): ?>
                <div class="check-item warning">
                    <span class="icon">⚠️</span>
                    <div>Ready to install. Please review the requirements above.</div>
                </div>
            <?php endif; ?>
        </div>

        <?php if (!empty($errors)): ?>
            <div class="info-box">
                <h3>Configuration Required</h3>
                <p>Please update <code>config.php</code> with your GoDaddy database credentials and admin password before proceeding.</p>
            </div>
        <?php endif; ?>

        <?php if ($dbConnected && !isset($_POST['install'])): ?>
            <div class="info-box">
                <h3>Ready to Install</h3>
                <p>Click the button below to create the database table and set up the uploads directory.</p>
            </div>

            <form method="POST">
                <button type="submit" name="install" class="btn">Install Database</button>
            </form>
        <?php elseif (isset($_POST['install']) && empty($errors)): ?>
            <div class="info-box">
                <h3>🎉 Installation Successful!</h3>
                <p>Your image duplicate detector is now ready to use.</p>
            </div>

            <div class="links">
                <a href="upload.php">Upload Images</a>
                <a href="admin.php">Admin Panel</a>
            </div>
        <?php else: ?>
            <button class="btn" disabled>Fix Errors Above First</button>
        <?php endif; ?>

        <div class="section" style="margin-top: 30px;">
            <div class="section-title">Next Steps</div>
            <div class="check-item" style="background: #e7f3ff;">
                <span class="icon">1️⃣</span>
                <div>Update database credentials in <code>config.php</code></div>
            </div>
            <div class="check-item" style="background: #e7f3ff;">
                <span class="icon">2️⃣</span>
                <div>Change the admin password in <code>config.php</code></div>
            </div>
            <div class="check-item" style="background: #e7f3ff;">
                <span class="icon">3️⃣</span>
                <div>Run this installer to create the database</div>
            </div>
            <div class="check-item" style="background: #e7f3ff;">
                <span class="icon">4️⃣</span>
                <div>Start uploading images via <code>upload.php</code></div>
            </div>
        </div>
    </div>
</body>
</html>
