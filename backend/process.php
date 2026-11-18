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
        if (!move_uploaded_file($_FILES["locked_file"]["tmp_name"], $locked_file_target)) {
            $err_msg = "Failed to move uploaded locked file.";
            log_system_error("process.php", $err_msg);
            echo json_encode(['status' => 'error', 'output' => $err_msg]);
            exit;
        }
    } else {
        $err_msg = "Locked file upload failed or missing.";
        log_system_error("process.php", $err_msg);
        echo json_encode(['status' => 'error', 'output' => $err_msg]);
        exit;
    }

    // Priority 1: Custom wordlist file upload
    if (isset($_FILES['wordlist_file']) && $_FILES['wordlist_file']['error'] == 0) {
        $wordlist_name = basename($_FILES["wordlist_file"]["name"]);
        $wordlist_target = $wordlist_dir . $wordlist_name;
        if (move_uploaded_file($_FILES["wordlist_file"]["tmp_name"], $wordlist_target)) {
            $wordlist_path = realpath($wordlist_target);
        }
    } 
    // Priority 2: Pre-installed server dropdown wordlist
    elseif (isset($_POST['wordlist_select']) && trim($_POST['wordlist_select']) !== "") {
        $selected_wordlist = trim($_POST['wordlist_select']);
        $wordlist_target = $wordlist_dir . basename($selected_wordlist);
        if (file_exists($wordlist_target)) {
            $wordlist_path = realpath($wordlist_target);
            $wordlist_name = $selected_wordlist;
        }
    }

    $custom_clues = isset($_POST['custom_clues']) ? trim($_POST['custom_clues']) : "";
    
    // Initialize status file
    $initial_status = json_encode([
        'status' => 'running',
        'progress' => 5,
        'output' => '[INIT] Background job spawned. Launching high-speed cracker engine...'
    ]);
    file_put_contents($logs_dir . "job_status.json", $initial_status);

    $is_windows = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
    $python_exe = $is_windows ? "python" : "python3";
    
    $real_doc = realpath($locked_file_target);
    $real_wordlist = $wordlist_path ? realpath($wordlist_path) : "";

    // Build absolute path to engine
    $engine_path = realpath("../engine/cracker.py");
    if (!$engine_path) {
        // Fallback relative path construction if realpath fails
        $engine_path = __DIR__ . "/../engine/cracker.py";
    }

    $escaped_engine = escapeshellarg($engine_path);
    $escaped_doc = escapeshellarg($real_doc);
    $escaped_wordlist = escapeshellarg($real_wordlist);
    $escaped_clues = escapeshellarg($custom_clues);

    $stdout_log = realpath("../logs") ? "../logs/cracker_stdout.log" : __DIR__ . "/../logs/cracker_stdout.log";

    if ($is_windows) {
        $cmd = "start /B $python_exe $escaped_engine $escaped_doc $escaped_wordlist $escaped_clues > " . escapeshellarg($stdout_log) . " 2>&1";
        pclose(popen($cmd, "r"));
    } else {
        // Linux / Render execution: pipe stderr to stdout log so we can read it if it crashes
        $cmd = "nohup $python_exe $escaped_engine $escaped_doc $escaped_wordlist $escaped_clues > " . escapeshellarg($stdout_log) . " 2>&1 &";
        exec($cmd);
    }

    echo json_encode([
        'status' => 'started',
        'file' => $locked_file_name,
        'wordlist' => $wordlist_name
    ]);
}
?>