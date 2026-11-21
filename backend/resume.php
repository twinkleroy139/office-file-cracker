<?php
// backend/resume.php
ob_start();
require_once 'error_logger.php';

set_time_limit(0);
ini_set('max_execution_time', 0);

function respond_json($payload, $code = 200) {
    http_response_code($code);
    if (ob_get_length()) {
        ob_clean();
    }
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond_json(['status' => 'error', 'output' => 'POST required.'], 405);
}

$raw_input = file_get_contents('php://input');
$decoded = json_decode($raw_input, true);
$raw_id = '';
if (is_array($decoded) && isset($decoded['job_id'])) {
    $raw_id = (string)$decoded['job_id'];
} elseif (isset($_POST['job_id'])) {
    $raw_id = (string)$_POST['job_id'];
}

$safe_job_id = preg_replace('/[^a-zA-Z0-9_-]/', '', trim($raw_id));
if ($safe_job_id === '') {
    respond_json(['status' => 'error', 'output' => 'Missing or invalid job_id for resume.'], 400);
}

$job_log_dir = realpath(__DIR__ . "/../logs/jobs/" . $safe_job_id);
if ($job_log_dir === false || !is_dir($job_log_dir)) {
    respond_json(['status' => 'error', 'job_id' => $safe_job_id, 'output' => 'Job directory not found.'], 404);
}

$checkpoint_file = $job_log_dir . DIRECTORY_SEPARATOR . "checkpoint.json";
if (!file_exists($checkpoint_file)) {
    respond_json(['status' => 'error', 'job_id' => $safe_job_id, 'output' => 'No saved wordlist checkpoint found for this job.'], 404);
}

$checkpoint = json_decode((string)file_get_contents($checkpoint_file), true);
if (!is_array($checkpoint)) {
    respond_json(['status' => 'error', 'job_id' => $safe_job_id, 'output' => 'Checkpoint file is corrupted.'], 500);
}

$last_line = isset($checkpoint['last_line_index']) ? max(0, (int)$checkpoint['last_line_index']) : 0;
$wordlist_label = isset($checkpoint['wordlist_label']) && trim((string)$checkpoint['wordlist_label']) !== ''
    ? trim((string)$checkpoint['wordlist_label'])
    : 'Wordlist';

$locked_file = isset($checkpoint['file_path']) ? (string)$checkpoint['file_path'] : '';
if ($locked_file === '' || !file_exists($locked_file)) {
    $job_upload_dir = realpath(__DIR__ . "/../uploads/jobs/" . $safe_job_id);
    if ($job_upload_dir !== false && is_dir($job_upload_dir)) {
        foreach (scandir($job_upload_dir) as $item) {
            if ($item === '.' || $item === '..') continue;
            $full = $job_upload_dir . DIRECTORY_SEPARATOR . $item;
            if (is_file($full)) {
                $locked_file = $full;
                break;
            }
        }
    }
}

$filtered_wordlist = $job_log_dir . DIRECTORY_SEPARATOR . "filtered_wordlist.txt";
if (!file_exists($filtered_wordlist) || filesize($filtered_wordlist) === 0) {
    respond_json(['status' => 'error', 'job_id' => $safe_job_id, 'output' => 'Filtered wordlist not available to resume.'], 404);
}

if ($locked_file === '' || !file_exists($locked_file)) {
    respond_json(['status' => 'error', 'job_id' => $safe_job_id, 'output' => 'Locked document file not found to resume.'], 404);
}

$cancel_flag = $job_log_dir . DIRECTORY_SEPARATOR . "cancel.flag";
if (file_exists($cancel_flag)) {
    @unlink($cancel_flag);
}

$status_file = $job_log_dir . DIRECTORY_SEPARATOR . "job_status.json";
$pid_file = $job_log_dir . DIRECTORY_SEPARATOR . "cracker.pid";
$stdout_log = $job_log_dir . DIRECTORY_SEPARATOR . "cracker_stdout.log";
$phase1_script = realpath(__DIR__ . "/../engine/wordlist_cracker_phase1.py");

file_put_contents($status_file, json_encode([
    'status' => 'running',
    'progress' => 15,
    'job_id' => $safe_job_id,
    'resumable' => false,
    'output' => "[RESUME] Resuming job [{$safe_job_id}] from wordlist line #" . number_format($last_line) . "..."
]));


require_once 'firebase_history.php';
firebase_upsert_job($safe_job_id, [
    'status' => 'running',
    'progress' => 15,
    'resumable' => false,
    'last_line_index' => $last_line
]);



$is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
$python_exe = $is_windows ? "python" : "python3";

$escaped_script = escapeshellarg($phase1_script);
$escaped_doc = escapeshellarg($locked_file);
$escaped_wordlist = escapeshellarg($filtered_wordlist);
$escaped_label = escapeshellarg($wordlist_label);
$escaped_job_id = escapeshellarg($safe_job_id);
$escaped_resume_line = escapeshellarg((string)$last_line);

if ($is_windows) {
    $run_cmd = "set \"JOB_ID={$safe_job_id}\" && set \"WORDLIST_LABEL={$wordlist_label}\" && set \"RESUME_FROM_LINE={$last_line}\" && {$python_exe} {$escaped_script} {$escaped_doc} {$escaped_wordlist} {$escaped_label} {$escaped_job_id} {$escaped_resume_line}";
    $cmd = "start /B cmd /C \"({$run_cmd}) >> " . escapeshellarg($stdout_log) . " 2>&1\"";
    pclose(popen($cmd, "r"));
} else {
    $env_prefix = "JOB_ID=" . escapeshellarg($safe_job_id)
        . " WORDLIST_LABEL=" . escapeshellarg($wordlist_label)
        . " RESUME_FROM_LINE=" . escapeshellarg((string)$last_line) . " ";
    $inner = "({$env_prefix}{$python_exe} {$escaped_script} {$escaped_doc} {$escaped_wordlist} {$escaped_label} {$escaped_job_id} {$escaped_resume_line}) >> " . escapeshellarg($stdout_log) . " 2>&1";
    $cmd = "setsid sh -c " . escapeshellarg($inner) . " < /dev/null >/dev/null 2>&1 & echo $!";
    $pid = trim((string)shell_exec($cmd));
    if ($pid !== '' && ctype_digit($pid)) {
        file_put_contents($pid_file, $pid);
    }
}

respond_json([
    'status' => 'resumed',
    'job_id' => $safe_job_id,
    'resume_from_line' => $last_line,
    'output' => "Resuming from line " . number_format($last_line) . "."
]);
?>