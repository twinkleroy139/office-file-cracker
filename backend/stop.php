<?php
header('Content-Type: application/json');

$logs_dir = __DIR__ . "/../logs/";
if (!is_dir($logs_dir)) {
    mkdir($logs_dir, 0777, true);
}

$cancel_flag = $logs_dir . "cancel.flag";
$pid_file = $logs_dir . "cracker.pid";
$status_file = $logs_dir . "job_status.json";

file_put_contents($cancel_flag, (string)time());

$is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';

if (file_exists($pid_file)) {
    $pid = trim((string)file_get_contents($pid_file));
    if ($pid !== '' && ctype_digit($pid)) {
        if ($is_windows) {
            exec("taskkill /PID " . escapeshellarg($pid) . " /T /F >nul 2>&1");
        } else {
            exec("kill -TERM -" . escapeshellarg($pid) . " >/dev/null 2>&1; kill -KILL -" . escapeshellarg($pid) . " >/dev/null 2>&1; kill -TERM " . escapeshellarg($pid) . " >/dev/null 2>&1");
        }
    }
    @unlink($pid_file);
}

if (!$is_windows) {
    exec("pkill -f 'engine/(dictionary_filter|cracker|custom_cracker|wordlist_cracker|wordlist_cracker_phase1|hash_extractor|hashcat_cracker)\\.py' >/dev/null 2>&1; pkill -f 'hashcat' >/dev/null 2>&1");
} else {
    exec("wmic process where \"CommandLine like '%dictionary_filter.py%' or CommandLine like '%cracker.py%' or CommandLine like '%wordlist_cracker.py%' or CommandLine like '%wordlist_cracker_phase1.py%' or CommandLine like '%hash_extractor.py%' or CommandLine like '%hashcat_cracker.py%' or CommandLine like '%hashcat.exe%'\" call terminate >nul 2>&1");
}

$stopped_status = json_encode([
    'status' => 'finished',
    'progress' => 100,
    'output' => "[STOPPED] Backend recovery process terminated by user.\n[STATUS] Working Process: IDLE | Safe to return to dashboard or start a new scan."
]);
file_put_contents($status_file, $stopped_status);

echo json_encode([
    'status' => 'stopped',
    'output' => 'Backend process stopped cleanly.'
]);
?>