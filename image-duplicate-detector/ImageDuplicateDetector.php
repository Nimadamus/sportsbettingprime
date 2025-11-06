<?php
/**
 * Image Duplicate Detector
 * Detects duplicate images using perceptual hashing
 * Works on GoDaddy shared hosting with PHP + GD library
 */

class ImageDuplicateDetector {
    private $db;
    private $uploadDir;
    private $hashSize = 8; // Size of the hash (8x8 = 64 bits)

    /**
     * Constructor
     * @param PDO $db Database connection
     * @param string $uploadDir Directory where images are stored
     */
    public function __construct($db, $uploadDir) {
        $this->db = $db;
        $this->uploadDir = rtrim($uploadDir, '/') . '/';

        // Create upload directory if it doesn't exist
        if (!file_exists($this->uploadDir)) {
            mkdir($this->uploadDir, 0755, true);
        }
    }

    /**
     * Generate perceptual hash for an image
     * @param string $imagePath Path to the image file
     * @return string 64-character hex hash
     */
    public function generateHash($imagePath) {
        // Load image
        $img = $this->loadImage($imagePath);
        if (!$img) {
            throw new Exception("Failed to load image: $imagePath");
        }

        // Resize to hash size
        $resized = imagecreatetruecolor($this->hashSize, $this->hashSize);
        imagecopyresampled($resized, $img, 0, 0, 0, 0,
            $this->hashSize, $this->hashSize,
            imagesx($img), imagesy($img));

        // Convert to grayscale and get pixel values
        $pixels = [];
        for ($y = 0; $y < $this->hashSize; $y++) {
            for ($x = 0; $x < $this->hashSize; $x++) {
                $rgb = imagecolorat($resized, $x, $y);
                $r = ($rgb >> 16) & 0xFF;
                $g = ($rgb >> 8) & 0xFF;
                $b = $rgb & 0xFF;
                $gray = ($r + $g + $b) / 3;
                $pixels[] = $gray;
            }
        }

        // Calculate average
        $average = array_sum($pixels) / count($pixels);

        // Generate hash based on average
        $hash = '';
        foreach ($pixels as $pixel) {
            $hash .= ($pixel > $average) ? '1' : '0';
        }

        // Convert binary to hex
        $hexHash = '';
        for ($i = 0; $i < strlen($hash); $i += 4) {
            $hexHash .= dechex(bindec(substr($hash, $i, 4)));
        }

        imagedestroy($img);
        imagedestroy($resized);

        return $hexHash;
    }

    /**
     * Calculate Hamming distance between two hashes
     * @param string $hash1 First hash
     * @param string $hash2 Second hash
     * @return int Number of different bits
     */
    public function hammingDistance($hash1, $hash2) {
        if (strlen($hash1) !== strlen($hash2)) {
            throw new Exception("Hashes must be the same length");
        }

        $distance = 0;
        for ($i = 0; $i < strlen($hash1); $i++) {
            $val1 = hexdec($hash1[$i]);
            $val2 = hexdec($hash2[$i]);
            $xor = $val1 ^ $val2;

            // Count set bits
            while ($xor) {
                $distance++;
                $xor &= $xor - 1;
            }
        }

        return $distance;
    }

    /**
     * Check if image is a duplicate
     * @param string $imagePath Path to the image to check
     * @param int $threshold Maximum hamming distance (0-10 recommended)
     * @return array|null Returns duplicate info or null if no duplicate found
     */
    public function findDuplicate($imagePath, $threshold = 5) {
        $hash = $this->generateHash($imagePath);

        // Query all existing hashes
        $stmt = $this->db->prepare("SELECT id, filename, file_path, phash, upload_date FROM images");
        $stmt->execute();

        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $distance = $this->hammingDistance($hash, $row['phash']);

            if ($distance <= $threshold) {
                return [
                    'duplicate' => true,
                    'id' => $row['id'],
                    'filename' => $row['filename'],
                    'file_path' => $row['file_path'],
                    'upload_date' => $row['upload_date'],
                    'similarity' => 100 - ($distance * 100 / 64),
                    'hamming_distance' => $distance
                ];
            }
        }

        return null;
    }

    /**
     * Save image and record in database
     * @param array $file $_FILES array element
     * @param bool $allowDuplicates Whether to allow duplicate uploads
     * @return array Result with success status and info
     */
    public function saveImage($file, $allowDuplicates = false) {
        // Validate upload
        if ($file['error'] !== UPLOAD_ERR_OK) {
            return ['success' => false, 'error' => 'Upload error: ' . $file['error']];
        }

        // Validate image type
        $allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mimeType = finfo_file($finfo, $file['tmp_name']);
        finfo_close($finfo);

        if (!in_array($mimeType, $allowedTypes)) {
            return ['success' => false, 'error' => 'Invalid image type. Only JPEG, PNG, GIF, and WebP allowed.'];
        }

        // Check for duplicates
        if (!$allowDuplicates) {
            $duplicate = $this->findDuplicate($file['tmp_name']);
            if ($duplicate) {
                return [
                    'success' => false,
                    'error' => 'Duplicate image detected',
                    'duplicate' => $duplicate
                ];
            }
        }

        // Generate unique filename
        $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
        $filename = uniqid('img_', true) . '.' . $extension;
        $filepath = $this->uploadDir . $filename;

        // Move uploaded file
        if (!move_uploaded_file($file['tmp_name'], $filepath)) {
            return ['success' => false, 'error' => 'Failed to save image'];
        }

        // Generate hash and save to database
        try {
            $hash = $this->generateHash($filepath);
            $filesize = filesize($filepath);

            $stmt = $this->db->prepare("
                INSERT INTO images (filename, file_path, phash, mime_type, file_size, upload_date)
                VALUES (:filename, :file_path, :phash, :mime_type, :file_size, NOW())
            ");

            $stmt->execute([
                ':filename' => $file['name'],
                ':file_path' => $filename,
                ':phash' => $hash,
                ':mime_type' => $mimeType,
                ':file_size' => $filesize
            ]);

            return [
                'success' => true,
                'id' => $this->db->lastInsertId(),
                'filename' => $filename,
                'original_name' => $file['name'],
                'hash' => $hash
            ];

        } catch (Exception $e) {
            // Clean up file if database insert fails
            unlink($filepath);
            return ['success' => false, 'error' => 'Database error: ' . $e->getMessage()];
        }
    }

    /**
     * Get all images from database
     * @param int $limit Number of images to retrieve
     * @param int $offset Offset for pagination
     * @return array List of images
     */
    public function getAllImages($limit = 50, $offset = 0) {
        $stmt = $this->db->prepare("
            SELECT id, filename, file_path, mime_type, file_size, upload_date
            FROM images
            ORDER BY upload_date DESC
            LIMIT :limit OFFSET :offset
        ");
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /**
     * Delete an image
     * @param int $id Image ID
     * @return bool Success status
     */
    public function deleteImage($id) {
        // Get image info
        $stmt = $this->db->prepare("SELECT file_path FROM images WHERE id = :id");
        $stmt->execute([':id' => $id]);
        $image = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$image) {
            return false;
        }

        // Delete file
        $filepath = $this->uploadDir . $image['file_path'];
        if (file_exists($filepath)) {
            unlink($filepath);
        }

        // Delete from database
        $stmt = $this->db->prepare("DELETE FROM images WHERE id = :id");
        return $stmt->execute([':id' => $id]);
    }

    /**
     * Load image from file
     * @param string $path Path to image
     * @return resource|false GD image resource
     */
    private function loadImage($path) {
        $info = getimagesize($path);
        if (!$info) {
            return false;
        }

        switch ($info['mime']) {
            case 'image/jpeg':
                return imagecreatefromjpeg($path);
            case 'image/png':
                return imagecreatefrompng($path);
            case 'image/gif':
                return imagecreatefromgif($path);
            case 'image/webp':
                return imagecreatefromwebp($path);
            default:
                return false;
        }
    }

    /**
     * Initialize database table
     */
    public function createTable() {
        $sql = "
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                phash VARCHAR(64) NOT NULL,
                mime_type VARCHAR(50) NOT NULL,
                file_size INT NOT NULL,
                upload_date DATETIME NOT NULL,
                INDEX idx_phash (phash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ";

        return $this->db->exec($sql);
    }
}
