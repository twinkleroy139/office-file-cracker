<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document Password Recovery Suite</title>
    <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
<div class="container">
    <div id="dashboard-view">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
            <h2 style="margin: 0;">Document Password Recovery Suite</h2>
            <span style="font-size: 11px; padding: 4px 8px; border: 1px solid #00ff6666; border-radius: 4px; background: #031206; color: #00ff66;">● WORKING PROCESS: READY</span>
        </div>

        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: 11px; color: #00b347; padding: 8px 10px; margin-bottom: 14px; border: 1px solid #00ff6633; border-radius: 4px; background: #030903;">
            <span><strong>Pipeline:</strong> Clue Mangling (Recommended First) &rarr; Dictionary Filter &rarr; Decrypt Engine</span>
            <span><strong>Status:</strong> Successfully Working</span>
            <span><strong>Queue:</strong> Idle &amp; Ready</span>
        </div>

        <form id="recovery-form" enctype="multipart/form-data">
            <div class="form-group">
                <label>1. Select Locked Document (.docx, .xlsx):</label>
                <input type="file" name="locked_file" id="locked_file" required>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Supported encrypted Office formats: Word (.docx) and Excel (.xlsx).</div>
            </div>

            <div class="form-group" style="border: 1px solid #00ff6666; padding: 12px; border-radius: 4px; background: #041206;">
                <label>2. Custom Clues / Keywords (Recommended First Step):</label>
                <textarea name="custom_clues" id="custom_clues" placeholder="Type words or numbers separated by commas, e.g., jitu, project, 2026, admin"></textarea>
                <div class="note" style="color: #00ff66; font-size: 11px; margin-top: 6px;">
                    <strong>Tip:</strong> Providing 2-3 clues (name, year, pet, leet variants etc) can cut cracking time by 10-100x compared to a full dictionary scan.
                </div>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Clues are mangled and tested first; wordlist scanning below acts as the fallback if clues don't work.</div>
            </div>

            <div class="form-group">
                <label>3a. Fallback Pre-Installed Server Wordlist (If Clues Don't Work):</label>
                <select name="wordlist_select" id="wordlist_select" style="width: 100%; padding: 10px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                    <option value="">-- None (Skip server wordlist) --</option>
                    <option value="10k-most-common.txt" selected>10k Most Common Passwords (Recommended Fallback)</option>
                    <option value="20k.txt">20k Expanded Passwords</option>
                </select>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Used only if custom clues do not match (or select None to test clues only).</div>
            </div>

            <div class="form-group">
                <label>3b. OR Upload Custom Password Bank Text File (.txt) (Fallback Option):</label>
                <input type="file" name="wordlist_file" id="wordlist_file">
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Custom upload overrides the fallback dropdown selection.</div>
            </div>

            <div class="form-group" style="border: 1px solid #00ff6633; padding: 12px; border-radius: 4px; background: #030a03;">
                <label>3a / 3b Fallback Dictionary Filtering Setup (Smarter Defaults):</label>

                <div style="margin-top: 8px;">
                    <label style="font-weight: normal; font-size: 12px;">
                        <input type="checkbox" name="filter_dedup_trim" id="filter_dedup_trim" value="1" checked>
                        Deduplicate &amp; trim
                    </label>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 110px;">
                        <label style="font-weight: normal; font-size: 12px;">Min Length:</label>
                        <input type="number" name="filter_min_len" id="filter_min_len" min="1" max="64" value="4" placeholder="e.g. 4" style="width: 100%; padding: 6px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                    </div>
                    <div style="flex: 1; min-width: 110px;">
                        <label style="font-weight: normal; font-size: 12px;">Max Length:</label>
                        <input type="number" name="filter_max_len" id="filter_max_len" min="1" max="64" value="16" placeholder="e.g. 16" style="width: 100%; padding: 6px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                    </div>
                    <div style="flex: 1.4; min-width: 140px;">
                        <label style="font-weight: normal; font-size: 12px;">Pre-filter by character rules:</label>
                        <select name="filter_char_rule" id="filter_char_rule" style="width: 100%; padding: 6px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                            <option value="any">All Characters</option>
                            <option value="numeric">Numbers Only (0-9)</option>
                            <option value="alpha">Letters Only (A-Z, a-z)</option>
                            <option value="alnum">Alphanumeric (Letters + Numbers)</option>
                            <option value="lower">Lowercase Only</option>
                            <option value="no_spaces" selected>No Spaces (Recommended)</option>
                        </select>
                    </div>
                </div>

                <div style="margin-top: 8px;">
                    <label style="font-weight: normal; font-size: 12px;">Order by likelihood:</label>
                    <select name="filter_order" id="filter_order" style="width: 100%; padding: 6px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                        <option value="default">Default Dictionary Order</option>
                        <option value="short_first">Shorter Passwords First</option>
                        <option value="common_patterns" selected>Common Word+Number Patterns First (Recommended)</option>
                    </select>
                </div>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 6px;">Tighter defaults trim unlikely candidates early; clear or change any field before starting if needed.</div>
            </div>

            <button type="submit" id="start-btn">START RECOVERY PROCESS</button>
        </form>
    </div>

    <!-- Live Progress View -->
    <div id="progress-view" style="display: none;">
        <h2>[ FILE RECOVERY IN PROGRESS ]</h2>
        
        <div class="status-bar">
            <span>Locked File: <span class="status-badge" id="lbl-file">None</span></span>
            <span>Dictionary: <span class="status-badge" id="lbl-wordlist">None</span></span>
        </div>

        <div class="status-bar" style="background: #030703; border-color: #00ff6655; margin-top: 10px;">
            <span>Status: <span class="status-badge" id="lbl-status" style="color: #00ff66;">INITIALIZING SERVER DECRYPTION...</span></span>
            <span>State: <span class="status-badge" id="lbl-state" style="color: #00ff66;">• ACTIVE</span></span>
        </div>

        <div style="text-align: center; margin: 15px 0; font-size: 12px; color: #00b347;">
            <div style="font-size: 22px; margin-bottom: 3px;">⚡</div>
            <div id="live-timer">Elapsed Time: 0s</div>
        </div>

        <div class="progress-container">
            <div id="dynamic-bar" class="progress-bar" style="width: 10%;"></div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #00b347; margin-bottom: 10px;">
            <span id="percent-val">10% Analyzing Header...</span>
            <span id="speed-indicator">Multi-threaded Core Active</span>
        </div>

        <div class="terminal-box" id="terminal-output" style="height: 200px; overflow-y: auto; text-align: left; font-family: monospace; font-size: 12px; padding: 10px; background: #020d02; color: #00ff66; border: 1px solid #00ff6644;">
            [INIT] Establishing secure bridge to cracking engine...
        </div>

        <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">
            <button type="button" id="stop-process-btn" style="flex: 1; min-width: 160px; background: #3b1e00; color: #ffaa33; border: 1px solid #ffaa33; padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; font-family: monospace;">[■] Stop Backend Process</button>
            <a href="index.php" id="cancel-btn" onclick="return confirm('Stop backend process and return to dashboard?');" style="flex: 1; min-width: 160px; text-align: center; background: #330000; color: #ff3333; border: 1px solid #ff3333; padding: 10px; text-decoration: none; border-radius: 4px; font-weight: bold;">[X] Stop &amp; Reload Dashboard</a>
            <button type="button" id="back-dashboard-btn" style="display:none; flex: 1; min-width: 160px; background: #003311; color: #00ff66; border: 1px solid #00ff66; padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; font-family: monospace;">[&lt;&lt;] Return to Dashboard</button>
        </div>

        <div style="margin-top: 10px; display: flex; justify-content: flex-end;">
            <button type="button" id="export-hash-btn" style="display: none; width: 100%; background: #041b2b; color: #38bdf8; border: 1px solid #38bdf8; padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; font-family: monospace;">[⬇] Export Hash for Local GPU Cracking (.hash)</button>
        </div>

    </div>
</div>

<script src="assets/js/script.js"></script>
</body>
</html>