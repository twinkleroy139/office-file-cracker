<?php
require_once 'error_logger.php';

set_time_limit(0);
ini_set('max_execution_time', 0);

$upload_dir = "../uploads/";
$wordlist_dir = "../wordlists/";
$logs_dir = "../logs/";

if (!is_dir($upload_dir)) { mkdir($upload_dir, 0777, true); }
if (!is_dir($wordlist_dir)) { mkdir($wordlist_dir, 0777, true); }
if (!is_dir($logs_dir)) { mkdir($logs_dir, 0777, true); }

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $locked_file_name = "";
    $wordlist_name = "None";
    $locked_file_target = "";
    $wordlist_path = "";

    if (isset($_FILES['locked_file']) && $_FILES['locked_file']['error'] == 0) {
        $locked_file_name = basename($_FILES["locked_file"]["name"]);
        $locked_file_target = $upload_dir . $locked_file_name;
        move_uploaded_file($_FILES["locked_file"]["tmp_name"], $locked_file_target);
    } else {
        $err_msg = "Locked file upload failed or missing.";
        log_system_error("process.php", $err_msg);
        echo json_encode(['status' => 'error', 'output' => $err_msg]);
        exit;
    }

    if (isset($_FILES['wordlist_file']) && $_FILES['wordlist_file']['error'] == 0) {
        $wordlist_name = basename($_FILES["wordlist_file"]["name"]);
        $wordlist_target = $wordlist_dir . $wordlist_name;
        if (move_uploaded_file($_FILES["wordlist_file"]["tmp_name"], $wordlist_target)) {
            $wordlist_path = realpath($wordlist_target);
        }
    } elseif (isset($_POST['wordlist_select']) && trim($_POST['wordlist_select']) !== "") {
        $selected_wordlist = trim($_POST['wordlist_select']);
        $wordlist_target = $wordlist_dir . basename($selected_wordlist);
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

    // Initialize job status
    $initial_status = json_encode([
        'status' => 'running',
        'progress' => 5,
        'output' => '[INIT] Filtering dictionary and initializing cracking engine...'
    ]);
    file_put_contents($logs_dir . "job_status.json", $initial_status);

    $is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
    $python_exe = $is_windows ? "python" : "python3";

    $real_doc = realpath($locked_file_target);
    $real_wordlist = $wordlist_path ? realpath($wordlist_path) : "";
    $filter_script = __DIR__ . "/../engine/dictionary_filter.py";
    $filtered_out = __DIR__ . "/../logs/filtered_wordlist.txt";
    $engine_path = __DIR__ . "/../engine/cracker.py";
    $stdout_log = __DIR__ . "/../logs/cracker_stdout.log";

    $env_prefix = "";
    if (!$is_windows) {
        $env_prefix = "FILTER_DEDUP_TRIM=" . escapeshellarg($filter_dedup_trim) . " "
            . "FILTER_MIN_LEN=" . escapeshellarg($filter_min_len) . " "
            . "FILTER_MAX_LEN=" . escapeshellarg($filter_max_len) . " "
            . "FILTER_CHAR_RULE=" . escapeshellarg($filter_char_rule) . " "
            . "FILTER_ORDER=" . escapeshellarg($filter_order) . " ";
    }

    $escaped_filter = escapeshellarg($filter_script);
    $escaped_filtered_out = escapeshellarg($filtered_out);
    $escaped_engine = escapeshellarg($engine_path);
    $escaped_doc = escapeshellarg($real_doc);
    $escaped_wordlist = escapeshellarg($real_wordlist);
    $escaped_clues = escapeshellarg($custom_clues);

    if ($is_windows) {
        $filter_cmd = "set \"FILTER_DEDUP_TRIM=$filter_dedup_trim\" && set \"FILTER_MIN_LEN=$filter_min_len\" && set \"FILTER_MAX_LEN=$filter_max_len\" && set \"FILTER_CHAR_RULE=$filter_char_rule\" && set \"FILTER_ORDER=$filter_order\" && $python_exe $escaped_filter $escaped_wordlist $escaped_filtered_out";
        $crack_cmd = "$python_exe $escaped_engine $escaped_doc $escaped_filtered_out $escaped_clues";
        $cmd = "start /B cmd /C \"($filter_cmd && $crack_cmd) > " . escapeshellarg($stdout_log) . " 2>&1\"";
        pclose(popen($cmd, "r"));
    } else {
        $filter_cmd = "{$env_prefix}{$python_exe} {$escaped_filter} {$escaped_wordlist} {$escaped_filtered_out}";
        $crack_cmd = "{$python_exe} {$escaped_engine} {$escaped_doc} {$escaped_filtered_out} {$escaped_clues}";
        $cmd = "setsid sh -c " . escapeshellarg("({$filter_cmd} && {$crack_cmd}) > " . $stdout_log . " 2>&1") . " < /dev/null &";
        exec($cmd);
    }

    echo json_encode([
        'status' => 'started',
        'file' => $locked_file_name,
        'wordlist' => $wordlist_name
    ]);
}
?>