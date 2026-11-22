<?php
ob_start();
require_once __DIR__ . '/error_logger.php';
require_once __DIR__ . '/archive_pdf_history.php';

set_time_limit(0);
ini_set('max_execution_time', 0);

$upload_dir = __DIR__ . "/../uploads/";
$wordlist_dir = __DIR__ . "/../wordlists/";
$logs_dir = __DIR__ . "/../logs/";

function respond_multi_json($payload, int $code = 200) {
    http_response_code($code);
    if (ob_get_length()) {
        ob_clean();
    }
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond_multi_json(['status' => 'error', 'output' => 'POST required.'], 405);
}

$job_id = 'job_' . date('Ymd_His') . '_' . bin2hex(random_bytes(4));
$job_log_dir = $logs_dir . "jobs/" . $job_id . "/";
$job_upload_dir = $upload_dir . "jobs/" . $job_id . "/";

foreach ([$upload_dir, $wordlist_dir, $logs_dir, $logs_dir . "jobs/", $upload_dir . "jobs/", $job_log_dir, $job_upload_dir] as $dir) {
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
}

$pid_file = $job_log_dir . "cracker.pid";
$status_file = $job_log_dir . "job_status.json";

$locked_file_name = "";
$wordlist_name = "None";
$locked_file_target = "";
$wordlist_path = "";

if (isset($_FILES['locked_file']) && $_FILES['locked_file']['error'] == 0) {
    $locked_file_name = basename($_FILES["locked_file"]["name"]);
    $ext = strtolower(pathinfo($locked_file_name, PATHINFO_EXTENSION));
    if (!in_array($ext, ['zip', 'pdf', '7z'], true)) {
        respond_multi_json([
            'status' => 'error',
            'job_id' => $job_id,
            'output' => "Unsupported format '.{$ext}'. Allowed formats: .zip, .pdf, .7z."
        ], 400);
    }
    $locked_file_target = $job_upload_dir . $locked_file_name;
    if (!move_uploaded_file($_FILES["locked_file"]["tmp_name"], $locked_file_target)) {
        $err_msg = "Failed to save uploaded archive/PDF file.";
        log_system_error("process_archive_pdf.php", $err_msg);
        respond_multi_json(['status' => 'error', 'job_id' => $job_id, 'output' => $err_msg]);
    }
} else {
    $err_msg = "Archive/PDF file upload failed or missing.";
    log_system_error("process_archive_pdf.php", $err_msg);
    respond_multi_json(['status' => 'error', 'job_id' => $job_id, 'output' => $err_msg]);
}

if (isset($_FILES['wordlist_file']) && $_FILES['wordlist_file']['error'] == 0) {
    $wordlist_name = basename($_FILES["wordlist_file"]["name"]);
    $wordlist_target = $job_upload_dir . $wordlist_name;
    if (move_uploaded_file($_FILES["wordlist_file"]["tmp_name"], $wordlist_target)) {
        $wordlist_path = realpath($wordlist_target);
    }
} elseif (isset($_POST['wordlist_select']) && trim($_POST['wordlist_select']) !== "") {
    $selected_wordlist = basename(trim($_POST['wordlist_select']));
    $wordlist_target = $wordlist_dir . $selected_wordlist;
    if (file_exists($wordlist_target)) {
        $wordlist_path = realpath($wordlist_target);
        $wordlist_name = $selected_wordlist;
    }
}

$custom_clues = isset($_POST['custom_clues']) ? trim($_POST['custom_clues']) : "";
$filter_dedup_trim = (isset($_POST['filter_dedup_trim']) && $_POST['filter_dedup_trim'] === '0') ? '0' : '1';
$filter_min_len = isset($_POST['filter_min_len']) ? preg_replace('/[^0-9]/', '', $_POST['filter_min_len']) : '';
$filter_max_len = isset($_POST['filter_max_len']) ? preg_replace('/[^0-9]/', '', $_POST['filter_max_len']) : '';
$allowed_char_rules = ['any', 'numeric', 'alpha', 'alnum', 'lower', 'no_spaces'];
$filter_char_rule = (isset($_POST['filter_char_rule']) && in_array($_POST['filter_char_rule'], $allowed_char_rules, true)) ? $_POST['filter_char_rule'] : 'any';
$allowed_orders = ['default', 'short_first', 'common_patterns'];
$filter_order = (isset($_POST['filter_order']) && in_array($_POST['filter_order'], $allowed_orders, true)) ? $_POST['filter_order'] : 'default';

$fmt_ext = strtolower(pathinfo($locked_file_name, PATHINFO_EXTENSION));

$initial_status = json_encode([
    'status' => 'running',
    'progress' => 5,
    'job_id' => $job_id,
    'engine' => "MULTI-FORMAT [" . strtoupper($fmt_ext) . "]",
    'output' => "[INIT] Job [{$job_id}] initializing " . strtoupper($fmt_ext) . " cracking pipeline..."
]);
file_put_contents($status_file, $initial_status);

record_multi_format_job_start($job_id, $locked_file_name, $wordlist_name, $fmt_ext);

$is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
$python_exe = $is_windows ? "python" : "python3";

$real_doc = realpath($locked_file_target);
$real_wordlist = $wordlist_path ? realpath($wordlist_path) : "";
$filter_script = __DIR__ . "/../engine/dictionary_filter.py";
$filtered_out = $job_log_dir . "filtered_wordlist.txt";
$engine_path = __DIR__ . "/../engine/multi_format_cracker.py";
$stdout_log = $job_log_dir . "multi_format_stdout.log";

$env_prefix = "";
if (!$is_windows) {
    $env_prefix = "FILTER_DEDUP_TRIM=" . escapeshellarg($filter_dedup_trim) . " "
        . "FILTER_MIN_LEN=" . escapeshellarg($filter_min_len) . " "
        . "FILTER_MAX_LEN=" . escapeshellarg($filter_max_len) . " "
        . "FILTER_CHAR_RULE=" . escapeshellarg($filter_char_rule) . " "
        . "FILTER_ORDER=" . escapeshellarg($filter_order) . " "
        . "JOB_ID=" . escapeshellarg($job_id) . " ";
}

$escaped_filter = escapeshellarg($filter_script);
$escaped_filtered_out = escapeshellarg($filtered_out);
$escaped_engine = escapeshellarg($engine_path);
$escaped_doc = escapeshellarg($real_doc);
$escaped_wordlist = escapeshellarg($real_wordlist);
$escaped_clues = escapeshellarg($custom_clues);
$escaped_label = escapeshellarg($wordlist_name);
$escaped_job_id = escapeshellarg($job_id);

if ($is_windows) {
    $filter_cmd = "set \"FILTER_DEDUP_TRIM=$filter_dedup_trim\" && set \"FILTER_MIN_LEN=$filter_min_len\" && set \"FILTER_MAX_LEN=$filter_max_len\" && set \"FILTER_CHAR_RULE=$filter_char_rule\" && set \"FILTER_ORDER=$filter_order\" && set \"JOB_ID=$job_id\" && $python_exe $escaped_filter $escaped_wordlist $escaped_filtered_out";
    $crack_cmd = "$python_exe $escaped_engine $escaped_doc $escaped_filtered_out $escaped_clues $escaped_label $escaped_job_id";
    $cmd = "start /B cmd /C \"($filter_cmd && $crack_cmd) > " . escapeshellarg($stdout_log) . " 2>&1\"";
    pclose(popen($cmd, "r"));
} else {
    $filter_cmd = "{$env_prefix}{$python_exe} {$escaped_filter} {$escaped_wordlist} {$escaped_filtered_out}";
    $crack_cmd = "{$env_prefix}{$python_exe} {$escaped_engine} {$escaped_doc} {$escaped_filtered_out} {$escaped_clues} {$escaped_label} {$escaped_job_id}";
    $inner = "({$filter_cmd} && {$crack_cmd}) > " . escapeshellarg($stdout_log) . " 2>&1";
    $cmd = "setsid sh -c " . escapeshellarg($inner) . " < /dev/null >/dev/null 2>&1 & echo $!";
    $pid = trim((string)shell_exec($cmd));
    if ($pid !== '' && ctype_digit($pid)) {
        file_put_contents($pid_file, $pid);
    }
}

respond_multi_json([
    'status' => 'started',
    'job_id' => $job_id,
    'format' => strtoupper($fmt_ext),
    'file' => $locked_file_name,
    'wordlist' => $wordlist_name
]);