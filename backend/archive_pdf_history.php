<?php
// backend/archive_pdf_history.php
require_once __DIR__ . '/firebase_history.php';

function record_multi_format_job_start(string $job_id, string $file_name, string $wordlist_name, string $format_label): bool {
    return firebase_upsert_job($job_id, [
        'file_name' => $file_name,
        'wordlist_name' => $wordlist_name,
        'format' => strtoupper($format_label),
        'status' => 'running',
        'progress' => 5,
        'resumable' => false,
        'last_line_index' => 0,
        'created_at' => time(),
    ]);
}