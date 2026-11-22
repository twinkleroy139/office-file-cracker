<?php
// backend/router.php
$uriPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

if ($uriPath === '/' || $uriPath === '/index.php') {
    require __DIR__ . '/multi_format_bootstrap.php';
    return true;
}

$docRoot = realpath(__DIR__ . '/..');
$candidate = realpath($docRoot . $uriPath);
if ($candidate && strpos($candidate, $docRoot) === 0 && is_file($candidate)) {
    return false;
}

require __DIR__ . '/multi_format_bootstrap.php';
return true;