<?php
// backend/firebase_history.php

function firebase_db_url(): string {
    $env_url = getenv('FIREBASE_DB_URL');
    if ($env_url && trim($env_url) !== '') {
        return rtrim(trim($env_url), '/');
    }
    return 'https://officecracker-history-default-rtdb.firebaseio.com';
}

function firebase_auth_query(): string {
    $secret = getenv('FIREBASE_DB_SECRET');
    if ($secret && trim($secret) !== '') {
        return '?auth=' . urlencode(trim($secret));
    }
    return '';
}

function firebase_job_request(string $method, string $job_id, ?array $payload = null): array {
    $safe_id = preg_replace('/[^a-zA-Z0-9_-]/', '', $job_id);
    if ($safe_id === '') {
        return ['ok' => false, 'error' => 'Invalid job_id'];
    }

    $url = firebase_db_url() . '/jobs/' . $safe_id . '.json' . firebase_auth_query();

    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, strtoupper($method));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 6);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        if ($payload !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        }
        $raw = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err = curl_error($ch);
        curl_close($ch);

        if ($err !== '') {
            return ['ok' => false, 'error' => $err];
        }
        return ['ok' => ($code >= 200 && $code < 300), 'http_code' => $code, 'body' => $raw];
    }

    $opts = [
        'http' => [
            'method'  => strtoupper($method),
            'header'  => "Content-Type: application/json\r\n",
            'timeout' => 6,
            'ignore_errors' => true,
        ]
    ];
    if ($payload !== null) {
        $opts['http']['content'] = json_encode($payload);
    }
    $ctx = stream_context_create($opts);
    $raw = @file_get_contents($url, false, $ctx);
    return ['ok' => ($raw !== false), 'body' => $raw];
}

function firebase_list_jobs(int $limit = 15): array {
    $url = firebase_db_url() . '/jobs.json' . firebase_auth_query();
    $sep = (strpos($url, '?') !== false) ? '&' : '?';
    $url .= $sep . 'orderBy="$key"&limitToLast=' . max(1, min(50, $limit));

    $raw = false;
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 6);
        $raw = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($raw === false || $code < 200 || $code >= 300) {
            return [];
        }
    } else {
        $ctx = stream_context_create(['http' => ['timeout' => 6, 'ignore_errors' => true]]);
        $raw = @file_get_contents($url, false, $ctx);
        if ($raw === false) {
            return [];
        }
    }

    $decoded = json_decode((string)$raw, true);
    if (!is_array($decoded)) {
        return [];
    }

    $jobs = array_values(array_filter($decoded, fn($item) => is_array($item)));
    usort($jobs, fn($a, $b) => ((int)($b['updated_at'] ?? 0)) <=> ((int)($a['updated_at'] ?? 0)));
    return array_slice($jobs, 0, $limit);
}

function firebase_upsert_job(string $job_id, array $fields): bool {
    $fields['job_id'] = $job_id;
    $fields['updated_at'] = time();
    $res = firebase_job_request('PATCH', $job_id, $fields);
    return !empty($res['ok']);
}