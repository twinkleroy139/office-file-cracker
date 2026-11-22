(function () {
    const STYLE_ID = 'cyber-aura-multi-format-style';
    const DECK_ID = 'cyber-multi-format-deck';

    if (document.getElementById(DECK_ID)) return;

    const styleEl = document.createElement('style');
    styleEl.id = STYLE_ID;
    styleEl.textContent = `
        @keyframes cyberPulseAura {
            0%, 100% {
                box-shadow: 0 0 14px rgba(0, 255, 170, 0.22), 0 0 28px rgba(56, 189, 248, 0.14), inset 0 0 12px rgba(217, 70, 239, 0.08);
            }
            50% {
                box-shadow: 0 0 22px rgba(56, 189, 248, 0.36), 0 0 36px rgba(217, 70, 239, 0.22), inset 0 0 16px rgba(0, 255, 170, 0.14);
            }
        }
        @keyframes cyberScanBar {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        #${DECK_ID} {
            position: relative;
            margin-top: 18px;
            padding: 16px;
            border-radius: 8px;
            background:
                radial-gradient(circle at top right, rgba(217, 70, 239, 0.14), transparent 45%),
                radial-gradient(circle at bottom left, rgba(56, 189, 248, 0.16), transparent 50%),
                linear-gradient(145deg, rgba(4, 12, 20, 0.96), rgba(9, 6, 22, 0.96));
            border: 1px solid rgba(56, 189, 248, 0.45);
            color: #e0f2fe;
            font-family: monospace;
            animation: cyberPulseAura 4.5s infinite ease-in-out;
            overflow: hidden;
        }
        #${DECK_ID}::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, #00ffaa, #38bdf8, #d946ef, #00ffaa);
            background-size: 250% 250%;
            animation: cyberScanBar 5s linear infinite;
        }
        .cyber-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin: 10px 0 14px;
        }
        .cyber-chip {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            letter-spacing: 0.06em;
            border: 1px solid rgba(56, 189, 248, 0.5);
            background: rgba(15, 23, 42, 0.85);
            color: #7dd3fc;
        }
        .cyber-chip.neon-pink {
            border-color: rgba(217, 70, 239, 0.55);
            color: #f5d0fe;
        }
        .cyber-chip.neon-mint {
            border-color: rgba(0, 255, 170, 0.55);
            color: #6ee7b7;
        }
        .cyber-grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 12px;
        }
        .cyber-field label {
            display: block;
            font-size: 11px;
            color: #7dd3fc;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .cyber-input, .cyber-select {
            width: 100%;
            box-sizing: border-box;
            padding: 9px 10px;
            border-radius: 5px;
            border: 1px solid rgba(56, 189, 248, 0.35);
            background: rgba(2, 6, 23, 0.92);
            color: #00ffaa;
            font-family: monospace;
            font-size: 12px;
        }
        .cyber-input:focus, .cyber-select:focus {
            outline: none;
            border-color: #d946ef;
            box-shadow: 0 0 10px rgba(217, 70, 239, 0.35);
        }
        .cyber-launch-btn {
            width: 100%;
            padding: 11px 14px;
            border-radius: 6px;
            border: 1px solid #00ffaa;
            background: linear-gradient(90deg, rgba(0, 255, 170, 0.16), rgba(56, 189, 248, 0.2), rgba(217, 70, 239, 0.22));
            color: #ffffff;
            font-family: monospace;
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 0.08em;
            cursor: pointer;
            text-shadow: 0 0 8px rgba(0, 255, 170, 0.65);
            transition: transform 0.15s ease, box-shadow 0.2s ease;
        }
        .cyber-launch-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.45), 0 0 24px rgba(217, 70, 239, 0.3);
        }
        #cyber-aura-hud {
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid rgba(217, 70, 239, 0.4);
            background: rgba(12, 7, 26, 0.85);
            color: #f0abfc;
            font-family: monospace;
            font-size: 11px;
            display: none;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
    `;
    document.head.appendChild(styleEl);

    function injectCyberDeck() {
        const dashboardView = document.getElementById('dashboard-view');
        if (!dashboardView || document.getElementById(DECK_ID)) return;

        const deck = document.createElement('div');
        deck.id = DECK_ID;
        deck.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <div style="font-size:14px; font-weight:bold; color:#38bdf8; text-shadow:0 0 10px rgba(56,189,248,0.55);">
                        ⚡ CYBER-DECK // MULTI-FORMAT BREACH MODULE (ZIP • PDF • 7Z)
                    </div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
                        Isolated sub-engine • Clue mangling + dictionary/hashcat verification • Live Firebase sync
                    </div>
                </div>
                <span class="cyber-chip neon-mint">● AURA LINK: ONLINE</span>
            </div>

            <div class="cyber-badge-row">
                <span class="cyber-chip">.ZIP ARCHIVES</span>
                <span class="cyber-chip neon-pink">.PDF DOCUMENTS</span>
                <span class="cyber-chip neon-mint">.7Z CONTAINERS</span>
            </div>

            <form id="cyber-multi-form" enctype="multipart/form-data">
                <div class="cyber-grid-2">
                    <div class="cyber-field">
                        <label>Target Archive / PDF (.zip, .pdf, .7z)</label>
                        <input type="file" name="locked_file" id="cyber_locked_file" accept=".zip,.pdf,.7z" class="cyber-input" required>
                    </div>
                    <div class="cyber-field">
                        <label>Fallback Server Dictionary</label>
                        <select name="wordlist_select" id="cyber_wordlist_select" class="cyber-select">
                            <option value="">-- None (Clues Only) --</option>
                            <option value="10k-most-common.txt" selected>10k Most Common Passwords</option>
                            <option value="20k.txt">20k Expanded Passwords</option>
                        </select>
                    </div>
                </div>

                <div class="cyber-field" style="margin-bottom:12px;">
                    <label>Custom Clues / Keywords (Comma-Separated)</label>
                    <input type="text" name="custom_clues" id="cyber_custom_clues" placeholder="e.g., vault, secret, 2026, root" class="cyber-input">
                </div>

                <button type="submit" id="cyber-start-btn" class="cyber-launch-btn">
                    [ ⚡ INITIATE ZIP / PDF / 7Z MULTI-FORMAT SCAN ]
                </button>
            </form>
            <div id="cyber-multi-feedback" style="margin-top:8px; font-size:11px; color:#6ee7b7;"></div>
        `;

        const historyPanel = document.getElementById('job-history-panel');
        if (historyPanel && historyPanel.parentNode === dashboardView) {
            dashboardView.insertBefore(deck, historyPanel);
        } else {
            dashboardView.appendChild(deck);
        }

        const progressView = document.getElementById('progress-view');
        if (progressView && !document.getElementById('cyber-aura-hud')) {
            const hud = document.createElement('div');
            hud.id = 'cyber-aura-hud';
            hud.innerHTML = `
                <span>AURA TELEMETRY: <strong>NEON-GRID ACTIVE</strong></span>
                <span id="cyber-hud-format">FORMAT: MULTI-ENGINE</span>
            `;
            const termBox = document.getElementById('terminal-output');
            if (termBox && termBox.parentNode === progressView) {
                termBox.insertAdjacentElement('afterend', hud);
            }
        }

        const form = document.getElementById('cyber-multi-form');
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const fileEl = document.getElementById('cyber_locked_file');
            const fbEl = document.getElementById('cyber-multi-feedback');
            if (!fileEl.files.length) {
                fbEl.style.color = '#f87171';
                fbEl.textContent = '[-] Select a .zip, .pdf, or .7z file first.';
                return;
            }

            const chosenFile = fileEl.files[0];
            const chosenWl = document.getElementById('cyber_wordlist_select').value || 'None';
            const fd = new FormData(form);

            fbEl.style.color = '#38bdf8';
            fbEl.textContent = '[*] Launching multi-format background job...';

            fetch('backend/process_archive_pdf.php', {
                method: 'POST',
                body: fd
            })
            .then(async r => {
                const txt = await r.text();
                return JSON.parse(txt);
            })
            .then(data => {
                if (data.status === 'started') {
                    fbEl.style.color = '#00ffaa';
                    fbEl.textContent = `[+] Job ${data.job_id} (${data.format}) started! Switching to live monitor...`;

                    const lblFile = document.getElementById('lbl-file');
                    const lblWl = document.getElementById('lbl-wordlist');
                    const lblStatus = document.getElementById('lbl-status');
                    const hud = document.getElementById('cyber-aura-hud');
                    const hudFmt = document.getElementById('cyber-hud-format');

                    if (lblFile) lblFile.innerText = chosenFile.name;
                    if (lblWl) lblWl.innerText = chosenWl;
                    if (lblStatus) lblStatus.innerText = `EXECUTING ${data.format} MULTI-FORMAT ENGINE...`;
                    if (hud) hud.style.display = 'flex';
                    if (hudFmt) hudFmt.innerText = `FORMAT: ${data.format} | JOB: ${data.job_id}`;

                    if (dashboardView) dashboardView.style.display = 'none';
                    if (progressView) progressView.style.display = 'block';

                    const bar = document.getElementById('dynamic-bar');
                    const pctVal = document.getElementById('percent-val');
                    const termBox = document.getElementById('terminal-output');
                    const backBtn = document.getElementById('back-dashboard-btn');

                    const poll = setInterval(() => {
                        fetch(`backend/status.php?job_id=${encodeURIComponent(data.job_id)}`)
                            .then(res => res.json())
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
                                    if (lblStatus) lblStatus.innerText = 'MULTI-FORMAT SCAN COMPLETED';
                                    if (backBtn) backBtn.style.display = 'block';
                                }
                            })
                            .catch(() => {});
                    }, 1000);
                } else {
                    fbEl.style.color = '#f87171';
                    fbEl.textContent = `[-] ${data.output || 'Failed to start multi-format job.'}`;
                }
            })
            .catch(err => {
                fbEl.style.color = '#f87171';
                fbEl.textContent = `[-] Request error: ${err.message || err}`;
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectCyberDeck);
    } else {
        injectCyberDeck();
    }
})();