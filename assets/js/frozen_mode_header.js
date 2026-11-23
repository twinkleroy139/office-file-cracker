(function () {
    function initFrozenHeaderAndModes() {
        // Remove duplicate deck if present from earlier script
        const legacyDeck = document.getElementById('cyber-multi-format-deck');
        if (legacyDeck) {
            legacyDeck.remove();
        }
        const legacyHud = document.getElementById('cyber-aura-hud');
        if (legacyHud) {
            legacyHud.remove();
        }

        if (!document.getElementById('frozen-top-header')) {
            const header = document.createElement('header');
            header.id = 'frozen-top-header';
            header.innerHTML = `
                <div class="frozen-header-inner">
                    <div class="frozen-brand">
                        <span class="frozen-aura-dot"></span>
                        <span>AURA-BREACH // MULTI-CORE SUITE</span>
                    </div>
                    <div class="frozen-mode-switch">
                        <button type="button" id="mode-btn-office" class="frozen-mode-btn active-office">
                            📄 Office (DOCX / XLSX / Sheets)
                        </button>
                        <button type="button" id="mode-btn-multi" class="frozen-mode-btn">
                            ⚡ ZIP / PDF / 7z Engine
                        </button>
                    </div>
                </div>
            `;
            document.body.insertBefore(header, document.body.firstChild);
        }

        const dashboardView = document.getElementById('dashboard-view');
        const recoveryForm = document.getElementById('recovery-form');
        if (!dashboardView || !recoveryForm) return;

        let multiPanel = document.getElementById('multi-format-workspace');
        if (!multiPanel) {
            multiPanel = document.createElement('div');
            multiPanel.id = 'multi-format-workspace';
            recoveryForm.insertAdjacentElement('afterend', multiPanel);
        }

        multiPanel.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px; border-bottom:1px dashed rgba(232,121,249,0.4); padding-bottom:8px;">
                <strong style="color:#f0abfc; font-size:14px; letter-spacing:1.2px;">[ ZIP / PDF / 7Z MULTI-FORMAT CRACKER ]</strong>
                <span style="font-size:11px; color:#38bdf8;">● ISOLATED ENGINE: READY</span>
            </div>

            <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; font-size:11px; color:#c084fc; padding:8px 10px; margin-bottom:14px; border:1px solid rgba(232,121,249,0.3); border-radius:4px; background:rgba(15, 23, 42, 0.7);">
                <span><strong>Pipeline:</strong> Clue Mangling (Recommended First) &rarr; Dictionary Filter &rarr; Archive/PDF Engine</span>
                <span><strong>Formats:</strong> .ZIP, .PDF, .7Z</span>
            </div>

            <form id="multi-format-form" enctype="multipart/form-data">
                <div class="form-group">
                    <label style="color:#7dd3fc;">1. Select Locked Archive or PDF (.zip, .pdf, .7z):</label>
                    <input type="file" name="locked_file" id="mf_locked_file" accept=".zip,.pdf,.7z" required style="background:#030712; color:#f0abfc; border-color:rgba(232,121,249,0.45);">
                    <div class="note" style="color:#94a3b8;">Supported formats: ZIP archives (.zip), encrypted PDFs (.pdf), and 7z archives (.7z).</div>
                </div>

                <div class="form-group" style="border: 1px solid rgba(232,121,249,0.45); padding: 12px; border-radius: 4px; background: rgba(18, 10, 36, 0.75);">
                    <label style="color:#f0abfc;">2. Custom Clues / Keywords (Recommended First Step):</label>
                    <textarea name="custom_clues" id="mf_custom_clues" placeholder="Type words or numbers separated by commas, e.g., jitu, project, 2026, admin" style="background:#030712; color:#38bdf8; border-color:rgba(56,189,248,0.45);"></textarea>
                    <div class="note" style="color:#e879f9; font-size:11px; margin-top:6px;">
                        <strong>Tip:</strong> Providing 2-3 clues (name, year, pet, leet variants etc) can cut cracking time compared to a full dictionary scan.
                    </div>
                    <div class="note" style="color:#94a3b8; font-size:11px; margin-top:4px;">Clues are mangled and tested first; wordlist scanning below acts as the fallback if clues don't work.</div>
                </div>

                <div class="form-group">
                    <label style="color:#7dd3fc;">3a. Fallback Pre-Installed Server Wordlist (If Clues Don't Work):</label>
                    <select name="wordlist_select" id="mf_wordlist_select" style="width:100%; padding:10px; background:#030712; color:#00ffaa; border:1px solid rgba(56,189,248,0.45); border-radius:4px; font-family:monospace;">
                        <option value="">-- None (Skip server wordlist) --</option>
                        <option value="10k-most-common.txt" selected>10k Most Common Passwords (Recommended Fallback)</option>
                        <option value="20k.txt">20k Expanded Passwords</option>
                    </select>
                    <div class="note" style="color:#94a3b8; font-size:11px; margin-top:4px;">Used only if custom clues do not match (or select None to test clues only).</div>
                </div>

                <div class="form-group">
                    <label style="color:#7dd3fc;">3b. OR Upload Custom Password Bank Text File (.txt) (Fallback Option):</label>
                    <input type="file" name="wordlist_file" id="mf_wordlist_file" accept=".txt" style="background:#030712; color:#7dd3fc; border-color:rgba(56,189,248,0.45);">
                    <div class="note" style="color:#94a3b8; font-size:11px; margin-top:4px;">Custom upload overrides the fallback dropdown selection.</div>
                </div>

                <div class="form-group" style="border: 1px solid rgba(56,189,248,0.35); padding: 12px; border-radius: 4px; background: rgba(6, 13, 28, 0.85);">
                    <label style="color:#7dd3fc;">3a / 3b Fallback Dictionary Filtering Setup (Smarter Defaults):</label>

                    <div style="margin-top: 8px;">
                        <label style="font-weight: normal; font-size: 12px; color:#cbd5e1;">
                            <input type="checkbox" name="filter_dedup_trim" id="mf_filter_dedup_trim" value="1" checked>
                            Deduplicate &amp; trim
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 110px;">
                            <label style="font-weight: normal; font-size: 12px; color:#cbd5e1;">Min Length:</label>
                            <input type="number" name="filter_min_len" id="mf_filter_min_len" min="1" max="64" value="4" placeholder="e.g. 4" style="width: 100%; padding: 6px; background: #030712; color: #00ffaa; border: 1px solid rgba(56,189,248,0.45); border-radius: 4px; font-family: monospace; box-sizing: border-box;">
                        </div>
                        <div style="flex: 1; min-width: 110px;">
                            <label style="font-weight: normal; font-size: 12px; color:#cbd5e1;">Max Length:</label>
                            <input type="number" name="filter_max_len" id="mf_filter_max_len" min="1" max="64" value="16" placeholder="e.g. 16" style="width: 100%; padding: 6px; background: #030712; color: #00ffaa; border: 1px solid rgba(56,189,248,0.45); border-radius: 4px; font-family: monospace; box-sizing: border-box;">
                        </div>
                        <div style="flex: 1.4; min-width: 140px;">
                            <label style="font-weight: normal; font-size: 12px; color:#cbd5e1;">Pre-filter by character rules:</label>
                            <select name="filter_char_rule" id="mf_filter_char_rule" style="width: 100%; padding: 6px; background: #030712; color: #00ffaa; border: 1px solid rgba(56,189,248,0.45); border-radius: 4px; font-family: monospace;">
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
                        <label style="font-weight: normal; font-size: 12px; color:#cbd5e1;">Order by likelihood:</label>
                        <select name="filter_order" id="mf_filter_order" style="width: 100%; padding: 6px; background: #030712; color: #00ffaa; border: 1px solid rgba(56,189,248,0.45); border-radius: 4px; font-family: monospace;">
                            <option value="default">Default Dictionary Order</option>
                            <option value="short_first">Shorter Passwords First</option>
                            <option value="common_patterns" selected>Common Word+Number Patterns First (Recommended)</option>
                        </select>
                    </div>
                    <div class="note" style="color:#94a3b8; font-size:11px; margin-top:6px;">Tighter defaults trim unlikely candidates early; clear or change any field before starting if needed.</div>
                </div>

                <button type="submit" id="mf-start-btn" style="background:#3b0764; color:#f5d0fe; border-color:#e879f9;">
                    START ZIP / PDF / 7Z RECOVERY PROCESS
                </button>
            </form>
            <div id="mf-feedback" style="margin-top:10px; font-size:12px; color:#7dd3fc;"></div>
        `;

        const btnOffice = document.getElementById('mode-btn-office');
        const btnMulti = document.getElementById('mode-btn-multi');

        function activateOfficeMode() {
            recoveryForm.style.display = 'block';
            multiPanel.style.display = 'none';
            btnOffice.classList.add('active-office');
            btnMulti.classList.remove('active-multi');
        }

        function activateMultiMode() {
            recoveryForm.style.display = 'none';
            multiPanel.style.display = 'block';
            btnMulti.classList.add('active-multi');
            btnOffice.classList.remove('active-office');
        }

        btnOffice.addEventListener('click', activateOfficeMode);
        btnMulti.addEventListener('click', activateMultiMode);

        // Start in Office mode cleanly
        activateOfficeMode();

        document.getElementById('multi-format-form').addEventListener('submit', function (e) {
            e.preventDefault();
            const fileInput = document.getElementById('mf_locked_file');
            const wlFileInput = document.getElementById('mf_wordlist_file');
            const wlSelect = document.getElementById('mf_wordlist_select');
            const dedupCb = document.getElementById('mf_filter_dedup_trim');
            const fb = document.getElementById('mf-feedback');

            if (!fileInput.files.length) {
                fb.style.color = '#f87171';
                fb.textContent = '[-] Please choose a .zip, .pdf, or .7z file.';
                return;
            }

            const chosenFile = fileInput.files[0].name;
            let chosenWl = 'None';
            if (wlFileInput && wlFileInput.files.length > 0) {
                chosenWl = wlFileInput.files[0].name;
            } else if (wlSelect && wlSelect.value) {
                chosenWl = wlSelect.value;
            }

            const fd = new FormData(this);
            fd.set('filter_dedup_trim', (dedupCb && dedupCb.checked) ? '1' : '0');

            fb.style.color = '#38bdf8';
            fb.textContent = '[*] Submitting multi-format job to backend...';

            fetch('backend/process_archive_pdf.php', {
                method: 'POST',
                body: fd
            })
            .then(async res => {
                const raw = await res.text();
                return JSON.parse(raw);
            })
            .then(data => {
                if (data.status === 'started') {
                    const progressView = document.getElementById('progress-view');
                    if (document.getElementById('lbl-file')) document.getElementById('lbl-file').innerText = chosenFile;
                    if (document.getElementById('lbl-wordlist')) document.getElementById('lbl-wordlist').innerText = chosenWl;
                    if (document.getElementById('lbl-status')) document.getElementById('lbl-status').innerText = `RUNNING ${data.format} ENGINE...`;
                    if (dashboardView) dashboardView.style.display = 'none';
                    if (progressView) progressView.style.display = 'block';

                    const bar = document.getElementById('dynamic-bar');
                    const pctVal = document.getElementById('percent-val');
                    const termBox = document.getElementById('terminal-output');
                    const backBtn = document.getElementById('back-dashboard-btn');

                    const poll = setInterval(() => {
                        fetch(`backend/status.php?job_id=${encodeURIComponent(data.job_id)}`)
                            .then(r => r.json())
                            .then(st => {
                                if (bar) bar.style.width = `${st.progress || 15}%`;
                                if (pctVal) pctVal.innerText = `${st.progress || 15}% ${st.engine || data.format}`;
                                if (termBox) {
                                    termBox.innerHTML = `<pre style="color:#00ffaa; margin:0; white-space:pre-wrap;">${st.output || ''}</pre>`;
                                    termBox.scrollTop = termBox.scrollHeight;
                                }
                                if (st.status === 'finished' || st.status === 'error') {
                                    clearInterval(poll);
                                    if (bar) bar.style.width = '100%';
                                    if (pctVal) pctVal.innerText = '100% Completed';
                                    if (document.getElementById('lbl-status')) document.getElementById('lbl-status').innerText = `${data.format} SCAN FINISHED`;
                                    if (backBtn) backBtn.style.display = 'block';
                                }
                            })
                            .catch(() => {});
                    }, 1000);
                } else {
                    fb.style.color = '#f87171';
                    fb.textContent = `[-] ${data.output || 'Failed to start job.'}`;
                }
            })
            .catch(err => {
                fb.style.color = '#f87171';
                fb.textContent = `[-] Error: ${err.message || err}`;
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFrozenHeaderAndModes);
    } else {
        initFrozenHeaderAndModes();
    }
})();