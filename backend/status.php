<?php
// backend/status.php
header('Content-Type: application/json');

$raw_job_id = isset($_GET['job_id']) ? trim((string)$_GET['job_id']) : '';
$safe_job_id = preg_replace('/[^a-zA-Z0-9_-]/', '', $raw_job_id);

if ($safe_job_id !== '') {
    $status_file = __DIR__ . "/../logs/jobs/" . $safe_job_id . "/job_status.json";
} else {
    $status_file = __DIR__ . "/../logs/job_status.json";
}

if (file_exists($status_file)) {
    echo file_get_contents($status_file);
} else {
    echo json_encode([
        'status' => 'running',
        'progress' => 0,
        'job_id' => $safe_job_id,
        'output' => '[INIT] Initializing background job...'
    ]);
}
?>