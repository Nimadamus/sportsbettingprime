<?php
/**
 * Image Upload Form with Duplicate Detection
 */

require_once 'config.php';
require_once 'ImageDuplicateDetector.php';

$message = '';
$messageType = '';
$duplicateInfo = null;

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['image'])) {
    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    $result = $detector->saveImage($_FILES['image'], ALLOW_DUPLICATES);

    if ($result['success']) {
        $message = 'Image uploaded successfully! File: ' . htmlspecialchars($result['filename']);
        $messageType = 'success';
    } else {
        $message = 'Error: ' . htmlspecialchars($result['error']);
        $messageType = 'error';

        if (isset($result['duplicate'])) {
            $duplicateInfo = $result['duplicate'];
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Upload - Duplicate Detection</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
            max-width: 600px;
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

        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }

        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }

        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
            transform: scale(1.02);
        }

        .upload-icon {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 15px;
        }

        .upload-text {
            color: #333;
            font-size: 16px;
            margin-bottom: 5px;
        }

        .upload-subtext {
            color: #666;
            font-size: 12px;
        }

        input[type="file"] {
            display: none;
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

        .message {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .duplicate-info {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 20px;
            margin-top: 15px;
        }

        .duplicate-info h3 {
            color: #856404;
            margin-bottom: 10px;
            font-size: 16px;
        }

        .duplicate-details {
            color: #856404;
            font-size: 14px;
            line-height: 1.6;
        }

        .duplicate-details strong {
            display: inline-block;
            width: 120px;
        }

        .preview {
            margin-top: 20px;
            text-align: center;
        }

        .preview img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .preview-label {
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }

        .admin-link {
            text-align: center;
            margin-top: 20px;
        }

        .admin-link a {
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }

        .admin-link a:hover {
            text-decoration: underline;
        }

        .file-info {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .file-info p {
            color: #333;
            font-size: 14px;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Image Upload</h1>
        <p class="subtitle">Upload images with automatic duplicate detection</p>

        <?php if ($message): ?>
            <div class="message <?php echo $messageType; ?>">
                <?php echo $message; ?>
            </div>
        <?php endif; ?>

        <?php if ($duplicateInfo): ?>
            <div class="duplicate-info">
                <h3>⚠️ Duplicate Image Detected</h3>
                <div class="duplicate-details">
                    <p><strong>Original File:</strong> <?php echo htmlspecialchars($duplicateInfo['filename']); ?></p>
                    <p><strong>Upload Date:</strong> <?php echo htmlspecialchars($duplicateInfo['upload_date']); ?></p>
                    <p><strong>Similarity:</strong> <?php echo round($duplicateInfo['similarity'], 1); ?>%</p>
                    <p><strong>Distance:</strong> <?php echo $duplicateInfo['hamming_distance']; ?> bits difference</p>
                </div>
            </div>
        <?php endif; ?>

        <form method="POST" enctype="multipart/form-data" id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📤</div>
                <div class="upload-text">Click to upload or drag and drop</div>
                <div class="upload-subtext">PNG, JPG, GIF, WebP up to <?php echo formatFileSize(MAX_FILE_SIZE); ?></div>
                <input type="file" name="image" id="imageInput" accept="image/*" required>
            </div>

            <div class="file-info" id="fileInfo">
                <p><strong>Selected file:</strong> <span id="fileName"></span></p>
                <p><strong>Size:</strong> <span id="fileSize"></span></p>
            </div>

            <div class="preview" id="preview" style="display: none;">
                <img id="previewImage" src="" alt="Preview">
                <p class="preview-label">Preview</p>
            </div>

            <button type="submit" class="btn" id="submitBtn">Upload Image</button>
        </form>

        <div class="admin-link">
            <a href="admin.php">Admin Panel →</a>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const imageInput = document.getElementById('imageInput');
        const uploadForm = document.getElementById('uploadForm');
        const preview = document.getElementById('preview');
        const previewImage = document.getElementById('previewImage');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const submitBtn = document.getElementById('submitBtn');

        // Click to upload
        uploadArea.addEventListener('click', () => {
            imageInput.click();
        });

        // File selection
        imageInput.addEventListener('change', function() {
            handleFile(this.files[0]);
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                imageInput.files = files;
                handleFile(files[0]);
            }
        });

        function handleFile(file) {
            if (!file) return;

            // Show file info
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            fileInfo.classList.add('show');

            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        // Form submission
        uploadForm.addEventListener('submit', function() {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading...';
        });
    </script>
</body>
</html>
