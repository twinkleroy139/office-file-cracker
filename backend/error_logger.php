<?php
// backend/error_logger.php
function log_system_error($module_name, $error_message) {
    $log_dir = "../logs/";
    if (!is_dir($log_dir)) { mkdir($log_dir, 0777, true); }
    
    $timestamp = date("Y-m-d H:i:s");
    $log_entry = "[$timestamp] [MODULE: $module_name] $error_message\n";
    
    file_put_contents($log_dir . "system_errors.log", $log_entry, FILE_APPEND);
    return $log_entry;
}

function get_latest_error_logs() {
    $log_file = "../logs/system_errors.log";
    if (file_exists($log_file)) {
        $lines = file($log_file);
        return implode("", array_slice($lines, -10));
    }
    return "No system errors recorded.";
}
?>