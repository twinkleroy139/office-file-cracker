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
                            &#128196; Office (DOCX / XLSX / Sheets)
                        </button>
                        <button type="button" id="mode-btn-multi" class="frozen-mode-btn">
                            &#9889; ZIP / PDF / 7z Engine
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
            <div class="cyber-top-bar" style="border-bottom-color: rgba(232, 121, 249, 0.35);">
                <div>
                    <h2 style="color:#f0abfc; text-shadow:0 0 10px rgba(232,121,249,0.45);">[ ZIP / PDF / 7Z MULTI-FORMAT CRACKER ]</h2>
                    <div class="cyber-subtitle" style="color:#c084fc;">clue mangling &rarr; dictionary filter &rarr; archive/pdf engine</div>
                </div>
                <span class="cyber-ready-pill" style="border-color:rgba(232,121,249,0.55); background:rgba(74,14,92,0.55); color:#f5d0fe;">&#9679; ISOLATED ENGINE: READY</span>
            </div>

            <div class="cyber-telemetry-strip" style="border-color:rgba(232,121,249,0.28); color:#d8b4fe; background:rgba(12, 18, 32, 0.85);">
                <span><strong>Pipeline:</strong> Clue Mangling (Recommended First) &rarr; Dictionary Filter &rarr; Archive/PDF Engine</span>
                <span><strong>Formats:</strong> .ZIP, .PDF, .7Z</span>
            </div>

            <form id="multi-format-form" enctype="multipart/form-data">
                <div class="form-group cyber-step-card" style="border-color:rgba(56,189,248,0.28); background:rgba(8, 15, 28, 0.92);">
                    <label class="cyber-step-heading" style="color:#7dd3fc !important;">1 &middot; Locked Archive or PDF (.zip, .pdf, .7z)</label>
                    <div class="note cyber-step-desc" style="color:#94a3b8 !important;">Supported formats: ZIP archives (.zip), encrypted PDFs (.pdf), and 7z archives (.7z).</div>
                    <div class="cyber-dropzone" style="border-color:rgba(232,121,249,0.42);">
                        <input type="file" name="locked_file" id="mf_locked_file" accept=".zip,.pdf,.7z" required style="background:#030712; color:#f0abfc; border-color:rgba(232,121,249,0.45);">
                        <div class="note" style="color:#cbd5e1;">Choose target archive or PDF &bull; Isolated multi-format extractor</div>
                    </div>
                </div>

                <div class="form-group cyber-step-card cyber-step-highlight" style="border-color:rgba(232,121,249,0.45); background:linear-gradient(180deg, rgba(24, 12, 44, 0.92), rgba(10, 15, 28, 0.95));">
                    <label class="cyber-step-heading" style="color:#f0abfc !important;">2 &middot; Custom Clues / Keywords (Recommended First Step)</label>
                    <div class="note cyber-step-desc" style="color:#e9d5ff !important;">
                        <strong>Tip:</strong> Providing 2&ndash;3 clues (name, year, pet, leet variants etc.) can cut cracking time compared to a full dictionary scan. Clues are mangled and tested first; fallback dictionary runs only if clues don't match.
                    </div>
                    <textarea name="custom_clues" id="mf_custom_clues" placeholder="Type words or numbers separated by commas, e.g., jitu, project, 2026, admin" style="background:#030712; color:#38bdf8; border-color:rgba(56,189,248,0.45);"></textarea>
                </div>

                <div class="form-group cyber-step-card" style="border-color:rgba(56,189,248,0.28); background:rgba(8, 15, 28, 0.92);">
                    <label class="cyber-step-heading" style="color:#7dd3fc !important;">3 &middot; Fallback Dictionary &amp; Filtering Setup</label>
                    <div class="note cyber-step-desc" style="color:#94a3b8 !important;">Used only if custom clues do not match (or select None to test clues only). Custom upload overrides the dropdown selection.</div>

                    <div class="cyber-grid-2">
                        <div>
                            <label for="mf_wordlist_select" style="color:#7dd3fc;">3a. Fallback Pre-Installed Server Wordlist</label>
                            <select name="wordlist_select" id="mf_wordlist_select" class="cyber-select-field" style="background:#030712; color:#00ffaa; border-color:rgba(56,189,248,0.45);">
                                <option value="">-- None (Skip server wordlist) --</option>
                                <option value="10k-most-common.txt" selected>10k Most Common Passwords (Recommended Fallback)</option>
                                <option value="20k.txt">20k Expanded Passwords</option>
                            </select>
                        </div>

                        <div>
                            <label for="mf_wordlist_file" style="color:#7dd3fc;">3b. OR Upload Custom Wordlist (.txt)</label>
                            <input type="file" name="wordlist_file" id="mf_wordlist_file" accept=".txt" style="background:#030712; color:#7dd3fc; border-color:rgba(56,189,248,0.45);">
                        </div>
                    </div>

                    <div class="cyber-subpanel" style="border-color:rgba(56,189,248,0.3); background:rgba(5, 11, 24, 0.9);">
                        <label class="cyber-subpanel-title" style="color:#7dd3fc !important;">Dictionary Filtering Setup (Smarter Defaults)</label>

                        <div class="cyber-filter-check-row">
                            <label class="cyber-inline-label" style="color:#cbd5e1 !important;">
                                <input type="checkbox" name="filter_dedup_trim" id="mf_filter_dedup_trim" value="1" checked>
                                Deduplicate &amp; trim
                            </label>
                        </div>

                        <div class="cyber-filter-row">
                            <div class="cyber-filter-col">
                                <label for="mf_filter_min_len" style="color:#cbd5e1;">Min Length:</label>
                                <input type="number" name="filter_min_len" id="mf_filter_min_len" min="1" max="64" value="4" placeholder="e.g. 4" class="cyber-num-input" style="background:#030712; color:#00ffaa; border-color:rgba(56,189,248,0.45);">
                            </div>
                            <div class="cyber-filter-col">
                                <label for="mf_filter_max_len" style="color:#cbd5e1;">Max Length:</label>
                                <input type="number" name="filter_max_len" id="mf_filter_max_len" min="1" max="64" value="16" placeholder="e.g. 16" class="cyber-num-input" style="background:#030712; color:#00ffaa; border-color:rgba(56,189,248,0.45);">
                            </div>
                            <div class="cyber-filter-col-wide">
                                <label for="mf_filter_char_rule" style="color:#cbd5e1;">Pre-filter by character rules:</label>
                                <select name="filter_char_rule" id="mf_filter_char_rule" class="cyber-select-field" style="background:#030712; color:#00ffaa; border-color:rgba(56,189,248,0.45);">
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
                            <label for="mf_filter_order" style="color:#cbd5e1;">Order by likelihood:</label>
                            <select name="filter_order" id="mf_filter_order" class="cyber-select-field" style="background:#030712; color:#00ffaa; border-color:rgba(56,189,248,0.45);">
                                <option value="default">Default Dictionary Order</option>
                                <option value="short_first">Shorter Passwords First</option>
                                <option value="common_patterns" selected>Common Word+Number Patterns First (Recommended)</option>
                            </select>
                        </div>
                        <div class="note" style="color:#94a3b8;">Tighter defaults trim unlikely candidates early; clear or change any field before starting if needed.</div>
                    </div>
                </div>

                <button type="submit" id="mf-start-btn" class="cyber-primary-cta" style="background:linear-gradient(90deg, rgba(88, 28, 135, 0.88), rgba(134, 25, 143, 0.88)); color:#fdf4ff; border-color:#e879f9; box-shadow:0 0 16px rgba(232,121,249,0.28);">
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
                    if (document.getElementById('lbl-status')) document.getElementById('lbl-status').innerText = 'EXECUTING BACKGROUND CRACKING PIPELINE...';
                    if (dashboardView) dashboardView.style.display = 'none';
                    if (progressView) progressView.style.display = 'block';

                    const bar = document.getElementById('dynamic-bar');
                    const pctVal = document.getElementById('percent-val');
                    const termBox = document.getElementById('terminal-output');
                    const backBtn = document.getElementById('back-dashboard-btn');
                    const stopBtn = document.getElementById('stop-process-btn');
                    const cancelLink = document.getElementById('cancel-btn');

                    const poll = setInterval(() => {
                        fetch(`backend/status.php?job_id=${encodeURIComponent(data.job_id)}`)
                            .then(r => r.json())
                            .then(st => {
                                if (bar) bar.style.width = `${st.progress || 15}%`;
                                if (pctVal) pctVal.innerText = `${st.progress || 15}% Scanning...`;
                                if (termBox) {
                                    termBox.innerHTML = `<pre style="color:#00ff66; margin:0; white-space:pre-wrap;">${st.output || ''}</pre>`;
                                    termBox.scrollTop = termBox.scrollHeight;
                                }
                                if (st.status === 'finished' || st.status === 'error') {
                                    clearInterval(poll);
                                    if (bar) bar.style.width = '100%';
                                    if (pctVal) pctVal.innerText = '100% Completed';
                                    if (document.getElementById('lbl-status')) {
                                        document.getElementById('lbl-status').innerText = st.status === 'finished'
                                            ? 'RECOVERY OPERATION FINISHED'
                                            : 'INCOMPLETE / ERROR';
                                    }
                                    if (stopBtn) stopBtn.style.display = 'none';
                                    if (cancelLink) cancelLink.style.display = 'none';
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
