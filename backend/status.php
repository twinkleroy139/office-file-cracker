<?php
// backend/status.php
header('Content-Type: application/json');

$status_file = "../logs/job_status.json";

if (file_exists($status_file)) {
    echo file_get_contents($status_file);
} else {
    echo json_encode([
        'status' => 'running',
        'progress' => 0,
        'output' => '[INIT] Initializing background job...'
    ]);
}
?>