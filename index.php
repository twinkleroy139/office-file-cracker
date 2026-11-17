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
        <h2>Document Password Recovery Suite</h2>
        <form id="recovery-form" enctype="multipart/form-data">
            <div class="form-group">
                <label>1. Select Locked Document (.docx, .xlsx):</label>
                <input type="file" name="locked_file" id="locked_file" required>
            </div>

            <div class="form-group">
                <label>2. Select Pre-Installed Server Wordlist:</label>
                <select name="wordlist_select" id="wordlist_select" style="width: 100%; padding: 10px; background: #030703; color: #00ff66; border: 1px solid #00ff6644; border-radius: 4px; font-family: monospace;">
                    <option value="10k-most-common.txt">10k Most Common Passwords (Recommended & Fast)</option>
                    <option value="20k.txt">20k Expanded Passwords</option>
                </select>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Optimized server-side dictionaries (Bypasses upload limits).</div>
            </div>

            <div class="form-group">
                <label>3. Custom Clues / Keywords (Optional):</label>
                <textarea name="custom_clues" id="custom_clues" placeholder="Type words or numbers separated by commas, e.g., jitu, project, 2026, admin"></textarea>
                <div class="note" style="color: #00b347; font-size: 11px; margin-top: 4px;">Words will be mixed and tested dynamically before the wordlist file.</div>
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
            <span>State: <span class="status-badge" style="color: #00ff66;">• ACTIVE</span></span>
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

        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <a href="index.php" id="back-dashboard-btn" style="display:none; flex: 1; text-align: center; background: #003311; color: #00ff66; border: 1px solid #00ff66; padding: 10px; text-decoration: none; border-radius: 4px; font-weight: bold;">[<<] Return to Dashboard</a>
            <a href="index.php" id="cancel-btn" onclick="return confirm('Abort current password recovery operation?');" style="flex: 1; text-align: center; background: #330000; color: #ff3333; border: 1px solid #ff3333; padding: 10px; text-decoration: none; border-radius: 4px; font-weight: bold;">[X] Stop / Cancel Progress</a>
        </div>
    </div>
</div>

<script src="assets/js/script.js"></script>
</body>
</html>