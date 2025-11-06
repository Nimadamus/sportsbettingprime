<?php
/**
 * Configuration file for Image Duplicate Detector
 * IMPORTANT: Update these values for your GoDaddy setup
 */

// Database Configuration (GoDaddy MySQL)
define('DB_HOST', 'localhost'); // Usually 'localhost' on GoDaddy
define('DB_NAME', 'your_database_name'); // Your database name
define('DB_USER', 'your_database_user'); // Your database username
define('DB_PASS', 'your_database_password'); // Your database password

// Upload Directory (relative to this file)
define('UPLOAD_DIR', __DIR__ . '/uploads');

// Duplicate Detection Settings
define('SIMILARITY_THRESHOLD', 5); // 0-10: Lower = stricter (5 is recommended)
define('ALLOW_DUPLICATES', false); // Set to true to allow duplicate uploads

// Security Settings
define('ADMIN_PASSWORD', 'change_this_password'); // Change this!
define('MAX_FILE_SIZE', 10 * 1024 * 1024); // 10MB max file size

// Session settings
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

/**
 * Get database connection
 * @return PDO
 */
function getDbConnection() {
    try {
        $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];
        return new PDO($dsn, DB_USER, DB_PASS, $options);
    } catch (PDOException $e) {
        die("Database connection failed: " . $e->getMessage());
    }
}

/**
 * Check if user is authenticated
 * @return bool
 */
function isAuthenticated() {
    return isset($_SESSION['authenticated']) && $_SESSION['authenticated'] === true;
}

/**
 * Authenticate user
 * @param string $password
 * @return bool
 */
function authenticate($password) {
    if ($password === ADMIN_PASSWORD) {
        $_SESSION['authenticated'] = true;
        return true;
    }
    return false;
}

/**
 * Logout user
 */
function logout() {
    unset($_SESSION['authenticated']);
    session_destroy();
}

/**
 * Format file size
 * @param int $bytes
 * @return string
 */
function formatFileSize($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' bytes';
    }
}
