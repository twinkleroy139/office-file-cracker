<?php
// backend/multi_format_bootstrap.php
ob_start();
require __DIR__ . '/../index.php';
$html = ob_get_clean();

header('Content-Type: text/html; charset=UTF-8');
echo $html;