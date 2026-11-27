<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document Password Recovery Suite</title>
    <link rel="stylesheet" href="assets/css/styles.css">
    <link rel="stylesheet" href="assets/css/frozen_cyber_aura.css">
    <link rel="stylesheet" href="assets/css/clue_pattern_builder.css">
</head>
<body>
<div class="container">
    <div id="dashboard-view">
        <div class="cyber-top-bar">
            <div>
                <h2 class="cyber-main-title">Document Password Recovery Suite</h2>
                <div class="cyber-subtitle">clue mangling &rarr; dictionary filter &rarr; decrypt engine</div>
            </div>
            <span class="cyber-ready-pill">&#9679; ready</span>
        </div>

        <div class="cyber-telemetry-strip">
            <span><strong>Pipeline:</strong> Clue Mangling (Recommended First) &rarr; Dictionary Filter &rarr; Decrypt Engine</span>
            <span><strong>Status:</strong> Successfully Working</span>
            <span><strong>Queue:</strong> Idle &amp; Ready</span>
        </div>

        <form id="recovery-form" enctype="multipart/form-data">
            <div class="form-group cyber-step-card">
                <label class="cyber-step-heading">1 &middot; Locked Document (.docx, .xlsx)</label>
                <div class="note cyber-step-desc">Supported encrypted Office formats: Word (.docx) and Excel (.xlsx).</div>
                <div class="cyber-dropzone">
                    <input type="file" name="locked_file" id="locked_file" required>
                    <div class="note">Choose target file &bull; Agile &amp; legacy Office encryption</div>
                </div>
            </div>

            <div class="form-group cyber-step-card cyber-step-highlight">
                <label class="cyber-step-heading">2 &middot; Custom Clues / Keywords (Recommended First Step)</label>
                <div class="note cyber-step-desc">
                    <strong>Tip:</strong> 2&ndash;3 clues (name, year, pet, leet variants etc.) can cut cracking time by 10&ndash;100&times; vs. a full dictionary pass. Clues are mangled and tested first; fallback dictionary runs only if clues don't match.
                </div>
                <textarea name="custom_clues" id="custom_clues" placeholder="Type words or numbers separated by commas, e.g., jitu, project, 2026, admin"></textarea>
            </div>

            <div class="form-group cyber-step-card">
                <label class="cyber-step-heading">3 &middot; Fallback Dictionary &amp; Filtering Setup</label>
                <div class="note cyber-step-desc">Used only if custom clues do not match (or select None to test clues only). Custom upload overrides the dropdown selection.</div>

                <div class="cyber-grid-2">
                    <div>
                        <label for="wordlist_select">3a. Fallback Pre-Installed Server Wordlist</label>
                        <select name="wordlist_select" id="wordlist_select" class="cyber-select-field">
                            <option value="">-- None (Skip server wordlist) --</option>
                            <option value="10k-most-common.txt" selected>10k Most Common Passwords (Recommended Fallback)</option>
                            <option value="20k.txt">20k Expanded Passwords</option>
                        </select>
                    </div>

                    <div>
                        <label for="wordlist_file">3b. OR Upload Custom Wordlist (.txt)</label>
                        <input type="file" name="wordlist_file" id="wordlist_file">
                    </div>
                </div>

                <div class="cyber-subpanel">
                    <label class="cyber-subpanel-title">Dictionary Filtering Setup (Smarter Defaults)</label>

                    <div class="cyber-filter-check-row">
                        <label class="cyber-inline-label">
                            <input type="checkbox" name="filter_dedup_trim" id="filter_dedup_trim" value="1" checked>
                            Deduplicate &amp; trim
                        </label>
                    </div>

                    <div class="cyber-filter-row">
                        <div class="cyber-filter-col">
                            <label for="filter_min_len">Min Length:</label>
                            <input type="number" name="filter_min_len" id="filter_min_len" min="1" max="64" value="4" placeholder="e.g. 4" class="cyber-num-input">
                        </div>
                        <div class="cyber-filter-col">
                            <label for="filter_max_len">Max Length:</label>
                            <input type="number" name="filter_max_len" id="filter_max_len" min="1" max="64" value="16" placeholder="e.g. 16" class="cyber-num-input">
                        </div>
                        <div class="cyber-filter-col-wide">
                            <label for="filter_char_rule">Pre-filter by character rules:</label>
                            <select name="filter_char_rule" id="filter_char_rule" class="cyber-select-field">
                                <option value="any">All Characters</option>
                                <option value="numeric">Numbers Only (0-9)</option>
                                <option value="alpha">Letters Only (A-Z, a-z)</option>
                                <option value="alnum">Alphanumeric (Letters + Numbers)</option>
                                <option value="lower">Lowercase Only</option>
                                <option value="no_spaces" selected>No Spaces (Recommended)</option>
                            </select>
                        </div>
                    </div>

                    <div class="cyber-filter-check-row">
                        <label for="filter_order">Order by likelihood:</label>
                        <select name="filter_order" id="filter_order" class="cyber-select-field">
                            <option value="default">Default Dictionary Order</option>
                            <option value="short_first">Shorter Passwords First</option>
                            <option value="common_patterns" selected>Common Word+Number Patterns First (Recommended)</option>
                        </select>
                    </div>
                    <div class="note">Tighter defaults trim unlikely candidates early; clear or change any field before starting if needed.</div>
                </div>
            </div>

            <button type="submit" id="start-btn" class="cyber-primary-cta">START RECOVERY PROCESS</button>
        </form>

        <div id="job-history-panel" style="display: none;" class="cyber-history-panel">
            <div class="cyber-history-header">
                <strong>[&#128338;] Recent Job History (Firebase)</strong>
                <button type="button" id="refresh-history-btn" class="cyber-mini-btn">Refresh</button>
            </div>
            <div id="job-history-list">Loading job history...</div>
        </div>
    </div>

    <!-- Live Progress View -->
    <div id="progress-view" style="display: none;">
        <h2>[ FILE RECOVERY IN PROGRESS ]</h2>

        <div class="status-bar">
            <span>Locked File: <span class="status-badge" id="lbl-file">None</span></span>
            <span>Dictionary: <span class="status-badge" id="lbl-wordlist">None</span></span>
        </div>

        <div class="status-bar cyber-status-sub">
            <span>Status: <span class="status-badge" id="lbl-status">INITIALIZING SERVER DECRYPTION...</span></span>
            <span>State: <span class="status-badge" id="lbl-state">&#9679; ACTIVE</span></span>
        </div>

        <div class="cyber-timer-block">
            <div class="cyber-bolt">&#9889;</div>
            <div id="live-timer">Elapsed Time: 0s</div>
        </div>

        <div class="progress-container">
            <div id="dynamic-bar" class="progress-bar" style="width: 10%;"></div>
        </div>

        <div class="cyber-progress-meta">
            <span id="percent-val">10% Analyzing Header...</span>
            <span id="speed-indicator">Multi-threaded Core Active</span>
        </div>

        <div class="terminal-box" id="terminal-output">
            [INIT] Establishing secure bridge to cracking engine...
        </div>

        <div class="cyber-action-row">
            <button type="button" id="stop-process-btn" class="cyber-btn-stop">[&#9632;] Stop Backend Process</button>
            <a href="index.php" id="cancel-btn" onclick="return confirm('Stop backend process and return to dashboard?');" class="cyber-btn-cancel">[X] Stop &amp; Reload Dashboard</a>
            <button type="button" id="back-dashboard-btn" style="display:none;" class="cyber-btn-back">[&lt;&lt;] Return to Dashboard</button>
        </div>

        <button type="button" id="resume-process-btn" style="display:none;" class="cyber-btn-resume">[&#9654;] Resume From Checkpoint</button>

        <div class="cyber-export-wrap">
            <button type="button" id="export-hash-btn" style="display: none;" class="cyber-btn-export">[&#11015;] Export Hash for Local GPU Cracking (.hash)</button>
        </div>
    </div>
</div>

<script src="assets/js/clue_pattern_builder.js"></script>
<script src="assets/js/script.js"></script>
<script src="assets/js/frozen_mode_header.js"></script>
</body>
</html>