<?php
// backend/multi_format_bootstrap.php
ob_start();
require __DIR__ . '/../index.php';
$html = ob_get_clean();

$scriptTag = '<script src="assets/js/multi_format_ui.js"></script>';
if (stripos($html, 'multi_format_ui.js') === false) {
    if (stripos($html, '</body>') !== false) {
        $html = str_ireplace('</body>', $scriptTag . "\n</body>", $html);
    } else {
        $html .= "\n" . $scriptTag;
    }
}

header('Content-Type: text/html; charset=UTF-8');
echo $html;