<?php
header('Content-Type: application/json');

$raw_input = file_get_contents('php://input');
$decoded = json_decode($raw_input, true);
$raw_id = '';
if (is_array($decoded) && isset($decoded['job_id'])) {
    $raw_id = (string)$decoded['job_id'];
} elseif (isset($_POST['job_id'])) {
    $raw_id = (string)$_POST['job_id'];
} elseif (isset($_GET['job_id'])) {
    $raw_id = (string)$_GET['job_id'];
}

$safe_job_id = preg_replace('/[^a-zA-Z0-9_-]/', '', trim($raw_id));
$logs_dir = __DIR__ . "/../logs/";
$job_dir = ($safe_job_id !== '') ? ($logs_dir . "jobs/" . $safe_job_id . "/") : $logs_dir;

if (!is_dir($job_dir)) {
    mkdir($job_dir, 0777, true);
}

$cancel_flag = $job_dir . "cancel.flag";
$pid_file = $job_dir . "cracker.pid";
$status_file = $job_dir . "job_status.json";

file_put_contents($cancel_flag, (string)time());

$is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
$killed_specific_pid = false;

if (file_exists($pid_file)) {
    $pid = trim((string)file_get_contents($pid_file));
    if ($pid !== '' && ctype_digit($pid)) {
        if ($is_windows) {
            exec("taskkill /PID " . escapeshellarg($pid) . " /T /F >nul 2>&1");
        } else {
            exec("kill -TERM -" . escapeshellarg($pid) . " >/dev/null 2>&1; kill -KILL -" . escapeshellarg($pid) . " >/dev/null 2>&1; kill -TERM " . escapeshellarg($pid) . " >/dev/null 2>&1");
        }
        $killed_specific_pid = true;
    }
    @unlink($pid_file);
}

if (!$killed_specific_pid && $safe_job_id === '') {
    if (!$is_windows) {
        exec("pkill -f 'engine/(dictionary_filter|cracker|custom_cracker|wordlist_cracker|wordlist_cracker_phase1|hash_extractor|hashcat_cracker)\\.py' >/dev/null 2>&1; pkill -f 'hashcat' >/dev/null 2>&1");
    } else {
        exec("wmic process where \"CommandLine like '%dictionary_filter.py%' or CommandLine like '%cracker.py%' or CommandLine like '%wordlist_cracker.py%' or CommandLine like '%wordlist_cracker_phase1.py%' or CommandLine like '%hash_extractor.py%' or CommandLine like '%hashcat_cracker.py%' or CommandLine like '%hashcat.exe%'\" call terminate >nul 2>&1");
    }
}

$job_label = ($safe_job_id !== '') ? " [{$safe_job_id}]" : "";
$stopped_status = json_encode([
    'status' => 'finished',
    'progress' => 100,
    'job_id' => $safe_job_id,
    'output' => "[STOPPED] Backend recovery process{$job_label} terminated by user.\n[STATUS] Working Process: IDLE | Safe to return to dashboard or start a new scan."
]);
file_put_contents($status_file, $stopped_status);

echo json_encode([
    'status' => 'stopped',
    'job_id' => $safe_job_id,
    'output' => "Backend process{$job_label} stopped cleanly."
]);
?>