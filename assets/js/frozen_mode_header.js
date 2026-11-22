(function () {
    function initFrozenHeaderAndModes() {
        if (document.getElementById('frozen-top-header')) return;

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

        const dashboardView = document.getElementById('dashboard-view');
        const recoveryForm = document.getElementById('recovery-form');
        if (!dashboardView || !recoveryForm) return;

        const multiPanel = document.createElement('div');
        multiPanel.id = 'multi-format-workspace';
        multiPanel.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px; border-bottom:1px dashed rgba(232,121,249,0.4); padding-bottom:8px;">
                <strong style="color:#f0abfc; font-size:14px; letter-spacing:1.2px;">[ ZIP / PDF / 7Z MULTI-FORMAT CRACKER ]</strong>
                <span style="font-size:11px; color:#38bdf8;">ISOLATED SUB-ENGINE: ACTIVE</span>
            </div>

            <form id="multi-format-form" enctype="multipart/form-data">
                <div class="form-group">
                    <label style="color:#7dd3fc;">1. Select Locked Archive or PDF (.zip, .pdf, .7z):</label>
                    <input type="file" name="locked_file" id="mf_locked_file" accept=".zip,.pdf,.7z" required style="background:#030712; color:#f0abfc; border-color:rgba(232,121,249,0.45);">
                    <div class="note" style="color:#94a3b8;">Supports password-protected ZIP archives, encrypted PDF files, and 7z archives.</div>
                </div>

                <div class="form-group">
                    <label style="color:#7dd3fc;">2. Custom Clues / Keywords (Tested First):</label>
                    <textarea name="custom_clues" id="mf_custom_clues" placeholder="e.g., archive, secret, 2026, admin" style="background:#030712; color:#38bdf8; border-color:rgba(56,189,248,0.45);"></textarea>
                </div>

                <div class="form-group">
                    <label style="color:#7dd3fc;">3. Fallback Server Wordlist:</label>
                    <select name="wordlist_select" id="mf_wordlist_select" style="width:100%; padding:10px; background:#030712; color:#00ffaa; border:1px solid rgba(56,189,248,0.45); border-radius:4px; font-family:monospace;">
                        <option value="">-- None (Clues Only) --</option>
                        <option value="10k-most-common.txt" selected>10k Most Common Passwords</option>
                        <option value="20k.txt">20k Expanded Passwords</option>
                    </select>
                </div>

                <button type="submit" id="mf-start-btn" style="background:#3b0764; color:#f5d0fe; border-color:#e879f9;">
                    START ZIP / PDF / 7Z RECOVERY
                </button>
            </form>
            <div id="mf-feedback" style="margin-top:10px; font-size:12px; color:#7dd3fc;"></div>
        `;

        recoveryForm.insertAdjacentElement('afterend', multiPanel);

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

        document.getElementById('multi-format-form').addEventListener('submit', function (e) {
            e.preventDefault();
            const fileInput = document.getElementById('mf_locked_file');
            const fb = document.getElementById('mf-feedback');
            if (!fileInput.files.length) {
                fb.style.color = '#f87171';
                fb.textContent = '[-] Please choose a .zip, .pdf, or .7z file.';
                return;
            }

            const chosenFile = fileInput.files[0].name;
            const chosenWl = document.getElementById('mf_wordlist_select').value || 'None';
            const fd = new FormData(this);

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