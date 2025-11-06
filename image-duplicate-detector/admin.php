<?php
/**
 * Admin Panel - Manage uploaded images
 */

require_once 'config.php';
require_once 'ImageDuplicateDetector.php';

// Handle logout
if (isset($_GET['logout'])) {
    logout();
    header('Location: admin.php');
    exit;
}

// Handle login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['password'])) {
    if (authenticate($_POST['password'])) {
        header('Location: admin.php');
        exit;
    } else {
        $loginError = 'Invalid password';
    }
}

// Require authentication
if (!isAuthenticated()) {
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .login-container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 40px;
                max-width: 400px;
                width: 100%;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
                font-size: 24px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                color: #333;
                margin-bottom: 8px;
                font-weight: 500;
            }
            input[type="password"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: transform 0.3s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 20px;
                font-size: 14px;
            }
            .back-link {
                text-align: center;
                margin-top: 20px;
            }
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>🔒 Admin Login</h1>
            <?php if (isset($loginError)): ?>
                <div class="error"><?php echo htmlspecialchars($loginError); ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required autofocus>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
            <div class="back-link">
                <a href="upload.php">← Back to Upload</a>
            </div>
        </div>
    </body>
    </html>
    <?php
    exit;
}

// Handle image deletion
if (isset($_POST['delete_id'])) {
    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);
    $detector->deleteImage($_POST['delete_id']);
    header('Location: admin.php');
    exit;
}

// Get images
$db = getDbConnection();
$detector = new ImageDuplicateDetector($db, UPLOAD_DIR);
$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;
$perPage = 20;
$offset = ($page - 1) * $perPage;
$images = $detector->getAllImages($perPage, $offset);

// Get total count
$stmt = $db->query("SELECT COUNT(*) as total FROM images");
$totalImages = $stmt->fetch()['total'];
$totalPages = ceil($totalImages / $perPage);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Image Management</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            color: #333;
            font-size: 28px;
        }

        .stats {
            display: flex;
            gap: 30px;
        }

        .stat {
            text-align: center;
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }

        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .image-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }

        .image-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        .image-wrapper {
            width: 100%;
            height: 200px;
            overflow: hidden;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .image-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .image-info {
            padding: 15px;
        }

        .image-name {
            font-size: 14px;
            color: #333;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-weight: 600;
        }

        .image-meta {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }

        .image-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
            flex: 1;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .btn-info {
            background: #17a2b8;
            color: white;
        }

        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
        }

        .pagination a {
            padding: 10px 16px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s;
        }

        .pagination a:hover {
            background: #667eea;
            color: white;
        }

        .pagination a.active {
            background: #667eea;
            color: white;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 12px;
        }

        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }

        .empty-state-text {
            color: #666;
            font-size: 18px;
            margin-bottom: 20px;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            align-items: center;
            justify-content: center;
        }

        .modal.show {
            display: flex;
        }

        .modal-content {
            max-width: 90%;
            max-height: 90%;
        }

        .modal-content img {
            max-width: 100%;
            max-height: 90vh;
            border-radius: 8px;
        }

        .modal-close {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🖼️ Image Management</h1>
            </div>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value"><?php echo $totalImages; ?></div>
                    <div class="stat-label">Total Images</div>
                </div>
            </div>
            <div class="actions">
                <a href="upload.php" class="btn btn-primary">Upload New</a>
                <a href="?logout=1" class="btn btn-secondary">Logout</a>
            </div>
        </div>

        <?php if (empty($images)): ?>
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No images uploaded yet</div>
                <a href="upload.php" class="btn btn-primary">Upload Your First Image</a>
            </div>
        <?php else: ?>
            <div class="gallery">
                <?php foreach ($images as $image): ?>
                    <div class="image-card">
                        <div class="image-wrapper">
                            <img src="<?php echo 'uploads/' . htmlspecialchars($image['file_path']); ?>"
                                 alt="<?php echo htmlspecialchars($image['filename']); ?>"
                                 onclick="showModal('<?php echo 'uploads/' . htmlspecialchars($image['file_path']); ?>')">
                        </div>
                        <div class="image-info">
                            <div class="image-name" title="<?php echo htmlspecialchars($image['filename']); ?>">
                                <?php echo htmlspecialchars($image['filename']); ?>
                            </div>
                            <div class="image-meta">
                                <strong>Size:</strong> <?php echo formatFileSize($image['file_size']); ?>
                            </div>
                            <div class="image-meta">
                                <strong>Uploaded:</strong> <?php echo date('M j, Y', strtotime($image['upload_date'])); ?>
                            </div>
                            <div class="image-actions">
                                <a href="<?php echo 'uploads/' . htmlspecialchars($image['file_path']); ?>"
                                   target="_blank"
                                   class="btn btn-small btn-info">View</a>
                                <form method="POST" style="flex: 1;" onsubmit="return confirm('Delete this image?');">
                                    <input type="hidden" name="delete_id" value="<?php echo $image['id']; ?>">
                                    <button type="submit" class="btn btn-small btn-danger" style="width: 100%;">Delete</button>
                                </form>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>

            <?php if ($totalPages > 1): ?>
                <div class="pagination">
                    <?php if ($page > 1): ?>
                        <a href="?page=<?php echo $page - 1; ?>">← Previous</a>
                    <?php endif; ?>

                    <?php for ($i = 1; $i <= $totalPages; $i++): ?>
                        <?php if ($i === $page): ?>
                            <a href="?page=<?php echo $i; ?>" class="active"><?php echo $i; ?></a>
                        <?php elseif ($i === 1 || $i === $totalPages || abs($i - $page) <= 2): ?>
                            <a href="?page=<?php echo $i; ?>"><?php echo $i; ?></a>
                        <?php elseif (abs($i - $page) === 3): ?>
                            <span>...</span>
                        <?php endif; ?>
                    <?php endfor; ?>

                    <?php if ($page < $totalPages): ?>
                        <a href="?page=<?php echo $page + 1; ?>">Next →</a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>

    <div class="modal" id="imageModal" onclick="hideModal()">
        <span class="modal-close">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="" alt="Full size image">
        </div>
    </div>

    <script>
        function showModal(src) {
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').classList.add('show');
        }

        function hideModal() {
            document.getElementById('imageModal').classList.remove('show');
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideModal();
            }
        });
    </script>
</body>
</html>
