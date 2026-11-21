<?php
// backend/history.php
header('Content-Type: application/json');
require_once 'firebase_history.php';

$jobs = firebase_list_jobs(15);
echo json_encode([
    'status' => 'ok',
    'jobs' => $jobs
]);