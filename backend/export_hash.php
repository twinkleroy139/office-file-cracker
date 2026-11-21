<?php
// backend/export_hash.php
require_once 'error_logger.php';

$raw_job_id = isset($_GET['job_id']) ? trim((string)$_GET['job_id']) : '';
$safe_job_id = preg_replace('/[^a-zA-Z0-9_-]/', '', $raw_job_id);

if ($safe_job_id === '') {
    http_response_code(400);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Missing or invalid job_id.";
    exit;
}

$job_log_dir = realpath(__DIR__ . "/../logs/jobs/" . $safe_job_id);
$job_upload_dir = realpath(__DIR__ . "/../uploads/jobs/" . $safe_job_id);

if ($job_log_dir === false || !is_dir($job_log_dir)) {
    http_response_code(404);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Job logs directory not found for job_id: " . $safe_job_id;
    exit;
}

$cached_hash_file = $job_log_dir . DIRECTORY_SEPARATOR . "office_target.hash";
$exported_hash_file = $job_log_dir . DIRECTORY_SEPARATOR . "exported_gpu.hash";

$hash_str = "";
$hc_mode = "";

// 1. Reuse existing hash file if already extracted by Hashcat engine
if (file_exists($cached_hash_file) && filesize($cached_hash_file) > 0) {
    $hash_str = trim((string)file_get_contents($cached_hash_file));
    if (strpos($hash_str, '*2013*') !== false) {
        $hc_mode = "9600";
    } elseif (strpos($hash_str, '*2010*') !== false) {
        $hc_mode = "9500";
    } elseif (strpos($hash_str, '*2007*') !== false) {
        $hc_mode = "9400";
    }
}

// 2. Otherwise extract on demand from the uploaded file for this job
if ($hash_str === "") {
    if ($job_upload_dir === false || !is_dir($job_upload_dir)) {
        http_response_code(404);
        header('Content-Type: text/plain; charset=utf-8');
        echo "Uploaded document not found for this job.";
        exit;
    }

    $uploaded_files = array_values(array_filter(scandir($job_upload_dir), function ($item) use ($job_upload_dir) {
        if ($item === '.' || $item === '..') {
            return false;
        }
        $full = $job_upload_dir . DIRECTORY_SEPARATOR . $item;
        if (!is_file($full)) {
            return false;
        }
        $ext = strtolower(pathinfo($item, PATHINFO_EXTENSION));
        return in_array($ext, ['docx', 'xlsx', 'doc', 'xls'], true);
    }));

    if (empty($uploaded_files)) {
        http_response_code(404);
        header('Content-Type: text/plain; charset=utf-8');
        echo "No supported Office document found in job uploads.";
        exit;
    }

    $locked_file = $job_upload_dir . DIRECTORY_SEPARATOR . $uploaded_files[0];
    $is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
    $python_exe = $is_windows ? "python" : "python3";
    $extractor_script = realpath(__DIR__ . "/../engine/hash_extractor.py");

    $cmd = escapeshellarg($python_exe) . " "
        . escapeshellarg($extractor_script) . " "
        . escapeshellarg($locked_file) . " "
        . escapeshellarg($exported_hash_file) . " 2>&1";

    $raw_output = (string)shell_exec($cmd);

    if (file_exists($exported_hash_file) && filesize($exported_hash_file) > 0) {
        $hash_str = trim((string)file_get_contents($exported_hash_file));
    }

    foreach (preg_split('/\r?\n/', $raw_output) as $line) {
        if (preg_match('/^MODE=(\d+)$/', trim($line), $m)) {
            $hc_mode = $m[1];
        } elseif ($hash_str === "" && preg_match('/^HASH=(.+)$/', trim($line), $h)) {
            $hash_str = trim($h[1]);
        }
    }

    if ($hash_str === "") {
        log_system_error("export_hash.php", "Hash export failed for {$safe_job_id}: {$raw_output}");
        http_response_code(422);
        header('Content-Type: text/plain; charset=utf-8');
        echo "Could not extract a valid Hashcat hash from this file.\n" . $raw_output;
        exit;
    }
}

$mode_suffix = $hc_mode !== "" ? "_m" . $hc_mode : "";
$download_name = $safe_job_id . $mode_suffix . ".hash";

header('Content-Type: text/plain; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $download_name . '"');
header('Content-Length: ' . strlen($hash_str . "\n"));
header('Cache-Control: no-store, no-cache, must-revalidate');
echo $hash_str . "\n";
exit;