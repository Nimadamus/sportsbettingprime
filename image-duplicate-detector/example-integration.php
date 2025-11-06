<?php
/**
 * EXAMPLE: How to integrate the duplicate detector into your existing website
 *
 * Copy the relevant code snippets into your existing upload pages
 */

// ============================================
// EXAMPLE 1: Basic Upload Form Integration
// ============================================

require_once 'config.php';
require_once 'ImageDuplicateDetector.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['photo'])) {
    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    // Try to save the image
    $result = $detector->saveImage($_FILES['photo']);

    if ($result['success']) {
        // Image uploaded successfully
        $imageUrl = 'uploads/' . $result['filename'];
        echo "Image uploaded! URL: $imageUrl";

        // You can now save this to your own database
        // e.g., INSERT INTO user_photos (user_id, image_url) VALUES (?, ?)

    } else {
        // Upload failed
        echo "Error: " . $result['error'];

        // Check if it was a duplicate
        if (isset($result['duplicate'])) {
            $dup = $result['duplicate'];
            echo "This is a duplicate of: " . $dup['filename'];
            echo "Uploaded on: " . $dup['upload_date'];
            echo "Similarity: " . round($dup['similarity'], 1) . "%";
        }
    }
}

?>

<!-- HTML Form Example -->
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="photo" accept="image/*" required>
    <button type="submit">Upload Photo</button>
</form>


<?php
// ============================================
// EXAMPLE 2: Just Check for Duplicates (Don't Save)
// ============================================

function checkIfImageIsDuplicate($filePath) {
    require_once 'config.php';
    require_once 'ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    $duplicate = $detector->findDuplicate($filePath, $threshold = 5);

    if ($duplicate) {
        return [
            'is_duplicate' => true,
            'original_file' => $duplicate['filename'],
            'similarity' => $duplicate['similarity']
        ];
    } else {
        return ['is_duplicate' => false];
    }
}

// Usage:
$check = checkIfImageIsDuplicate($_FILES['image']['tmp_name']);
if ($check['is_duplicate']) {
    echo "Sorry, this image already exists!";
} else {
    echo "Image is unique, proceed with upload";
}


// ============================================
// EXAMPLE 3: Get All Uploaded Images
// ============================================

function getAllUploadedImages($page = 1, $perPage = 20) {
    require_once 'config.php';
    require_once 'ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    $offset = ($page - 1) * $perPage;
    return $detector->getAllImages($perPage, $offset);
}

// Usage:
$images = getAllUploadedImages(1, 20);
foreach ($images as $image) {
    echo '<img src="uploads/' . $image['file_path'] . '" alt="' . $image['filename'] . '">';
}


// ============================================
// EXAMPLE 4: WordPress Integration
// ============================================

// Add this to your WordPress theme's functions.php

function prevent_duplicate_uploads($file) {
    require_once ABSPATH . 'wp-content/image-detector/config.php';
    require_once ABSPATH . 'wp-content/image-detector/ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    // Check if duplicate
    $duplicate = $detector->findDuplicate($file['tmp_name']);

    if ($duplicate) {
        $file['error'] = 'Duplicate image detected! Original: ' . $duplicate['filename'];
        return $file;
    }

    return $file;
}

// Hook into WordPress upload process
add_filter('wp_handle_upload_prefilter', 'prevent_duplicate_uploads');


// ============================================
// EXAMPLE 5: Allow Duplicates But Track Them
// ============================================

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['image'])) {
    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    // First check if it's a duplicate
    $duplicate = $detector->findDuplicate($_FILES['image']['tmp_name']);

    if ($duplicate) {
        // It's a duplicate, but we'll allow it anyway
        echo "⚠️ Warning: Similar image already exists<br>";
        echo "Original: " . $duplicate['filename'] . "<br>";
        echo "Similarity: " . round($duplicate['similarity'], 1) . "%<br>";
    }

    // Upload anyway (pass true to allow duplicates)
    $result = $detector->saveImage($_FILES['image'], $allowDuplicates = true);

    if ($result['success']) {
        echo "✅ Image uploaded: " . $result['filename'];
    }
}


// ============================================
// EXAMPLE 6: Ajax Upload with Progress
// ============================================

// PHP Handler (save as ajax-upload.php)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['image'])) {
    header('Content-Type: application/json');

    require_once 'config.php';
    require_once 'ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    $result = $detector->saveImage($_FILES['image']);

    echo json_encode($result);
    exit;
}

?>

<!-- JavaScript for Ajax Upload -->
<script>
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('image', document.getElementById('fileInput').files[0]);

    try {
        const response = await fetch('ajax-upload.php', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            alert('Image uploaded: ' + result.filename);
        } else {
            alert('Error: ' + result.error);

            if (result.duplicate) {
                alert('Duplicate of: ' + result.duplicate.filename);
            }
        }
    } catch (error) {
        alert('Upload failed: ' + error);
    }
});
</script>


<?php
// ============================================
// EXAMPLE 7: Batch Check Multiple Images
// ============================================

function checkMultipleImagesForDuplicates($imagePaths) {
    require_once 'config.php';
    require_once 'ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    $results = [];

    foreach ($imagePaths as $path) {
        $duplicate = $detector->findDuplicate($path);
        $results[] = [
            'path' => $path,
            'is_duplicate' => $duplicate !== null,
            'duplicate_info' => $duplicate
        ];
    }

    return $results;
}

// Usage:
$paths = ['/tmp/photo1.jpg', '/tmp/photo2.jpg', '/tmp/photo3.jpg'];
$results = checkMultipleImagesForDuplicates($paths);

foreach ($results as $result) {
    if ($result['is_duplicate']) {
        echo $result['path'] . " is a duplicate!<br>";
    }
}


// ============================================
// EXAMPLE 8: Custom Threshold Per Upload
// ============================================

function uploadWithCustomThreshold($file, $threshold) {
    require_once 'config.php';
    require_once 'ImageDuplicateDetector.php';

    $db = getDbConnection();
    $detector = new ImageDuplicateDetector($db, UPLOAD_DIR);

    // Check with custom threshold
    $duplicate = $detector->findDuplicate($file['tmp_name'], $threshold);

    if ($duplicate) {
        return [
            'success' => false,
            'error' => 'Duplicate detected',
            'duplicate' => $duplicate
        ];
    }

    // No duplicate, proceed with upload
    return $detector->saveImage($file, false);
}

// Usage:
// Very strict (only exact matches)
$result = uploadWithCustomThreshold($_FILES['image'], 0);

// Lenient (allow more variation)
$result = uploadWithCustomThreshold($_FILES['image'], 8);


// ============================================
// EXAMPLE 9: Get Image Statistics
// ============================================

function getImageStats() {
    require_once 'config.php';

    $db = getDbConnection();

    $stats = [];

    // Total images
    $stmt = $db->query("SELECT COUNT(*) as total FROM images");
    $stats['total_images'] = $stmt->fetch()['total'];

    // Total storage used
    $stmt = $db->query("SELECT SUM(file_size) as total_size FROM images");
    $stats['total_size'] = $stmt->fetch()['total_size'];

    // Images today
    $stmt = $db->query("SELECT COUNT(*) as today FROM images WHERE DATE(upload_date) = CURDATE()");
    $stats['uploads_today'] = $stmt->fetch()['today'];

    // Average file size
    if ($stats['total_images'] > 0) {
        $stats['average_size'] = $stats['total_size'] / $stats['total_images'];
    } else {
        $stats['average_size'] = 0;
    }

    return $stats;
}

// Usage:
$stats = getImageStats();
echo "Total Images: " . $stats['total_images'] . "<br>";
echo "Total Storage: " . formatFileSize($stats['total_size']) . "<br>";
echo "Uploads Today: " . $stats['uploads_today'] . "<br>";


// ============================================
// TIPS FOR INTEGRATION
// ============================================

/*
1. ALWAYS include config.php and ImageDuplicateDetector.php first

2. The detector works with $_FILES array from PHP uploads

3. You can adjust the similarity threshold (0-10):
   - 0 = only exact duplicates
   - 5 = recommended default
   - 10 = very lenient

4. File paths are relative to UPLOAD_DIR (set in config.php)

5. All methods return associative arrays with status info

6. The database connection is handled automatically via config.php

7. Images are stored in the uploads/ directory with unique filenames

8. You can safely integrate this with existing databases - it uses its own table

9. The system is thread-safe and works with concurrent uploads

10. For production, add error logging and validation
*/

?>
