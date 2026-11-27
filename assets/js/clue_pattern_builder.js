(function () {
    const THRESHOLD_YELLOW = 2000;
    const THRESHOLD_RED = 50000;
    const MAX_CANDIDATES_CAP = 100000;
    const SMART_NUMBERS_COUNT = 13;

    function getClueCount(textareaEl) {
        if (!textareaEl || !textareaEl.value) return 0;
        const parts = textareaEl.value
            .split(/[\n,]+/)
            .map(s => s.trim())
            .filter(Boolean);
        return Math.max(parts.length, 0);
    }

    function readConfig(rootEl) {
        const q = sel => rootEl.querySelector(sel);
        const posEl = q('input[name="cpb_pos_radio"]:checked');
        const numEnabledEl = q('.cpb-num-enable');
        const numModeEl = q('input[name^="cpb_num_mode_"]:checked');
        const d2 = q('.cpb-d2')?.checked ? 100 : 0;
        const d3 = q('.cpb-d3')?.checked ? 1000 : 0;
        const d4 = q('.cpb-d4')?.checked ? 2500 : 0;

        const symEnabledEl = q('.cpb-sym-enable');
        const checkedSyms = Array.from(rootEl.querySelectorAll('.cpb-sym-cb:checked')).map(cb => cb.value);
        const customSymVal = (q('.cpb-sym-custom-input')?.value || '').trim();
        if (customSymVal) {
            customSymVal.split(',').map(s => s.trim()).filter(Boolean).forEach(s => {
                if (!checkedSyms.includes(s)) checkedSyms.push(s);
            });
        }

        const depthEl = q('input[name^="cpb_depth_radio_"]:checked');
        const caseLower = q('.cpb-case-lower')?.checked ? 1 : 0;
        const caseCap = q('.cpb-case-cap')?.checked ? 1 : 0;
        const caseUpper = q('.cpb-case-upper')?.checked ? 1 : 0;
        const caseAlt = q('.cpb-case-alt')?.checked ? 1 : 0;

        return {
            position: posEl ? posEl.value : 'suffix',
            numEnabled: !!(numEnabledEl && numEnabledEl.checked),
            numMode: numModeEl ? numModeEl.value : 'smart',
            exactRangeSize: d2 + d3 + d4,
            symEnabled: !!(symEnabledEl && symEnabledEl.checked),
            symbols: checkedSyms,
            depth: depthEl ? depthEl.value : 'combined',
            caseCount: Math.max(1, caseLower + caseCap + caseUpper + caseAlt),
            rawPayload: {
                position: posEl ? posEl.value : 'suffix',
                num_enabled: numEnabledEl && numEnabledEl.checked ? '1' : '0',
                num_mode: numModeEl ? numModeEl.value : 'smart',
                num_digits: [
                    q('.cpb-d2')?.checked ? '2' : '',
                    q('.cpb-d3')?.checked ? '3' : '',
                    q('.cpb-d4')?.checked ? '4' : ''
                ].filter(Boolean).join(','),
                sym_enabled: symEnabledEl && symEnabledEl.checked ? '1' : '0',
                symbols: checkedSyms.join(','),
                depth: depthEl ? depthEl.value : 'combined',
                cases: [
                    caseLower ? 'lower' : '',
                    caseCap ? 'cap' : '',
                    caseUpper ? 'upper' : '',
                    caseAlt ? 'alt' : ''
                ].filter(Boolean).join(',')
            }
        };
    }

    function estimateCandidates(clueCount, cfg, isMultiFormat) {
        const speed = isMultiFormat ? 150 : 2;
        if (clueCount <= 0) return { total: 0, speed };

        let numPool = 0;
        if (cfg.numEnabled) {
            if (cfg.numMode === 'exact') {
                numPool = cfg.exactRangeSize > 0 ? cfg.exactRangeSize : 100;
            } else if (cfg.numMode === 'smart') {
                numPool = SMART_NUMBERS_COUNT;
            }
        }

        const symPool = cfg.symEnabled ? cfg.symbols.length : 0;
        let perVariantCount = 1 + numPool + symPool;

        if (cfg.depth === 'combined') {
            perVariantCount += 4 * numPool * symPool;
        } else if (cfg.depth === 'deep') {
            const deepExtraPerPair = 2 + Math.min(3, symPool);
            perVariantCount += deepExtraPerPair * numPool * symPool;
        }

        const rawTotal = clueCount * cfg.caseCount * perVariantCount;
        const total = Math.min(MAX_CANDIDATES_CAP, rawTotal);
        return { total, speed };
    }

    function syncHiddenInputs(formEl, cfg) {
        const map = {
            cpb_position: cfg.rawPayload.position,
            cpb_num_enabled: cfg.rawPayload.num_enabled,
            cpb_num_mode: cfg.rawPayload.num_mode,
            cpb_num_digits: cfg.rawPayload.num_digits,
            cpb_sym_enabled: cfg.rawPayload.sym_enabled,
            cpb_symbols: cfg.rawPayload.symbols,
            cpb_depth: cfg.rawPayload.depth,
            cpb_cases: cfg.rawPayload.cases
        };
        Object.entries(map).forEach(([name, val]) => {
            let inp = formEl.querySelector(`input[type="hidden"][name="${name}"]`);
            if (!inp) {
                inp = document.createElement('input');
                inp.type = 'hidden';
                inp.name = name;
                formEl.appendChild(inp);
            }
            inp.value = val;
        });
    }

    function mountOnForm(formEl, clueTextareaId, submitBtnId, isMultiFormat) {
        if (!formEl || formEl.querySelector('.cpb-wrapper')) return;
        const clueTextarea = document.getElementById(clueTextareaId);
        const submitBtn = document.getElementById(submitBtnId);
        if (!clueTextarea || !submitBtn) return;

        const uid = formEl.id || (isMultiFormat ? 'mf' : 'of');
        const clueBox = clueTextarea.closest('.form-group') || clueTextarea.parentElement;

        const wrapper = document.createElement('div');
        wrapper.className = 'cpb-wrapper';
        wrapper.innerHTML = `
            <button type="button" class="cpb-toggle-btn" aria-expanded="true">
                <span>&#9662; ATTACH NUMBERS &amp; SYMBOLS TO CLUES (OPTIONAL)</span>
                <span class="cpb-toggle-state">[OPEN]</span>
            </button>
            <div class="cpb-body">
                <div class="cpb-row">
                    <span class="cpb-row-title">1. Attachment Position</span>
                    <div class="cpb-inline-group">
                        <label><input type="radio" name="cpb_pos_radio" value="suffix" checked> Suffix (word + extra)</label>
                        <label><input type="radio" name="cpb_pos_radio" value="prefix"> Prefix (extra + word)</label>
                        <label><input type="radio" name="cpb_pos_radio" value="both"> Both ends</label>
                    </div>
                </div>

                <div class="cpb-row">
                    <span class="cpb-row-title">2. Number Attachment Mode</span>
                    <div class="cpb-inline-group">
                        <label><input type="checkbox" class="cpb-num-enable" checked> Enable</label>
                    </div>
                    <div class="cpb-subbox">
                        <div class="cpb-inline-group" style="flex-direction:column; gap:5px;">
                            <label><input type="radio" name="cpb_num_mode_${uid}" value="smart" checked> Smart/Likely only — years, 123, 1234, 007, common patterns (~30-50 candidates)</label>
                            <label><input type="radio" name="cpb_num_mode_${uid}" value="exact"> Short exact range — brute-force ALL numbers in a range you set below</label>
                            <label><input type="radio" name="cpb_num_mode_${uid}" value="disabled"> Disabled — no numbers attached</label>
                        </div>
                        <div class="cpb-exact-digits cpb-subbox" style="display:none; margin-top:6px;">
                            <span class="cpb-row-title" style="font-size:10px;">Exact Range Digit Length:</span>
                            <div class="cpb-inline-group">
                                <label><input type="checkbox" class="cpb-d2" checked> 2-digit (00-99)</label>
                                <label><input type="checkbox" class="cpb-d3" checked> 3-digit (000-999)</label>
                                <label><input type="checkbox" class="cpb-d4"> 4-digit (0000-9999)</label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="cpb-row">
                    <span class="cpb-row-title">3. Symbol Attachment</span>
                    <div class="cpb-inline-group">
                        <label><input type="checkbox" class="cpb-sym-enable" checked> Enable</label>
                    </div>
                    <div class="cpb-subbox">
                        <div class="cpb-inline-group">
                            <label><input type="checkbox" class="cpb-sym-cb" value="@" checked> @</label>
                            <label><input type="checkbox" class="cpb-sym-cb" value="$" checked> $</label>
                            <label><input type="checkbox" class="cpb-sym-cb" value="#"> #</label>
                            <label><input type="checkbox" class="cpb-sym-cb" value="!"> !</label>
                            <label><input type="checkbox" class="cpb-sym-cb" value="_"> _</label>
                            <label><input type="checkbox" class="cpb-sym-cb" value="-"> -</label>
                            <label>Custom: <input type="text" class="cpb-sym-custom-input cpb-custom-sym" placeholder="e.g. *,&"></label>
                        </div>
                    </div>
                </div>

                <div class="cpb-row">
                    <span class="cpb-row-title">4. Pattern Depth (Combination Structure)</span>
                    <div class="cpb-inline-group" style="flex-direction:column; gap:5px;">
                        <label><input type="radio" name="cpb_depth_radio_${uid}" value="single"> Word only + one extra (number OR symbol, not both)</label>
                        <label><input type="radio" name="cpb_depth_radio_${uid}" value="combined" checked> Word + number + symbol combined (e.g. word@123, $word123)</label>
                        <label><input type="radio" name="cpb_depth_radio_${uid}" value="deep"> Deep combination (symbol + word + symbol + number + symbol) — slower, use if simple patterns fail</label>
                    </div>
                </div>

                <div class="cpb-row">
                    <span class="cpb-row-title">5. Case Variants</span>
                    <div class="cpb-inline-group">
                        <label><input type="checkbox" class="cpb-case-lower" checked> lowercase</label>
                        <label><input type="checkbox" class="cpb-case-cap" checked> Capitalized</label>
                        <label><input type="checkbox" class="cpb-case-upper"> UPPERCASE</label>
                        <label><input type="checkbox" class="cpb-case-alt"> aLtErNaTiNg</label>
                    </div>
                </div>

                <div class="cpb-estimate-bar est-green">
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; font-weight:bold;">
                        <span class="cpb-est-count">ESTIMATED CANDIDATES: 0</span>
                        <span class="cpb-est-time">EST. TIME: ~0s</span>
                    </div>
                    <div class="cpb-est-speed" style="margin-top:4px; opacity:0.92;">(at current engine speed: python / 2 keys-s)</div>
                </div>

                <div class="cpb-warning-box" style="display:none;">
                    <strong>&#9888; High Candidate Count (50,000+):</strong> This may take a long time on free-tier hosting. Check
                    <label style="display:inline; margin-left:4px;"><input type="checkbox" class="cpb-confirm-high"> I understand &amp; want to run</label>
                </div>
            </div>
        `;

        clueBox.insertAdjacentElement('afterend', wrapper);

        const engineBar = document.createElement('div');
        engineBar.className = isMultiFormat ? 'cpb-engine-status' : 'cpb-engine-status fallback-loud';
        if (isMultiFormat) {
            engineBar.innerHTML = `
                <span>&#9881; ENGINE: Multi-Format Python Engine (ZIP / PDF / 7z)</span>
                <strong style="color:#00ffaa;">&#9679; READY</strong>
            `;
        } else {
            engineBar.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">
                    <span>&#9888; ENGINE: Hashcat failed to start on container — using Python fallback (slower).</span>
                    <button type="button" class="cpb-err-toggle">[View error details]</button>
                </div>
                <div class="cpb-err-detail">Hashcat (-m 9500/9600) exits with code 255 when no GPU/OpenCL compute device is exposed; job automatically runs via Python Multi-Core + msoffcrypto.</div>
            `;
        }
        submitBtn.insertAdjacentElement('beforebegin', engineBar);

        const toggleBtn = wrapper.querySelector('.cpb-toggle-btn');
        const bodyEl = wrapper.querySelector('.cpb-body');
        const toggleState = wrapper.querySelector('.cpb-toggle-state');
        toggleBtn.addEventListener('click', () => {
            const isHidden = bodyEl.classList.toggle('collapsed');
            toggleBtn.setAttribute('aria-expanded', String(!isHidden));
            toggleState.textContent = isHidden ? '[CLOSED]' : '[OPEN]';
        });

        const errBtn = engineBar.querySelector('.cpb-err-toggle');
        const errBox = engineBar.querySelector('.cpb-err-detail');
        if (errBtn && errBox) {
            errBtn.addEventListener('click', () => {
                errBox.style.display = errBox.style.display === 'block' ? 'none' : 'block';
            });
        }

        const exactBox = wrapper.querySelector('.cpb-exact-digits');
        const estBar = wrapper.querySelector('.cpb-estimate-bar');
        const estCountEl = wrapper.querySelector('.cpb-est-count');
        const estTimeEl = wrapper.querySelector('.cpb-est-time');
        const estSpeedEl = wrapper.querySelector('.cpb-est-speed');
        const warnBox = wrapper.querySelector('.cpb-warning-box');
        const confirmHighCb = wrapper.querySelector('.cpb-confirm-high');

        function refreshEstimate() {
            const cfg = readConfig(wrapper);
            if (!cfg.numEnabled) {
                cfg.numMode = 'disabled';
            }
            if (exactBox) {
                exactBox.style.display = (cfg.numEnabled && cfg.numMode === 'exact') ? 'block' : 'none';
            }
            syncHiddenInputs(formEl, cfg);

            const cluesCount = getClueCount(clueTextarea);
            const { total, speed } = estimateCandidates(cluesCount, cfg, isMultiFormat);
            const estSec = total > 0 ? Math.max(1, Math.ceil(total / speed)) : 0;

            estCountEl.textContent = `ESTIMATED CANDIDATES: ${total.toLocaleString()}`;
            estTimeEl.textContent = `EST. TIME: ~${estSec}s`;
            estSpeedEl.textContent = `(at current engine speed: ${isMultiFormat ? 'multi-core' : 'python'} / ${speed} keys-s)`;

            estBar.classList.remove('est-green', 'est-yellow', 'est-red');
            if (total >= THRESHOLD_RED) {
                estBar.classList.add('est-red');
                warnBox.style.display = 'block';
            } else if (total >= THRESHOLD_YELLOW) {
                estBar.classList.add('est-yellow');
                warnBox.style.display = 'none';
                if (confirmHighCb) confirmHighCb.checked = false;
            } else {
                estBar.classList.add('est-green');
                warnBox.style.display = 'none';
                if (confirmHighCb) confirmHighCb.checked = false;
            }
        }

        wrapper.addEventListener('input', refreshEstimate);
        wrapper.addEventListener('change', refreshEstimate);
        clueTextarea.addEventListener('input', refreshEstimate);

        formEl.addEventListener('submit', function (e) {
            const cfg = readConfig(wrapper);
            syncHiddenInputs(formEl, cfg);
            const cluesCount = getClueCount(clueTextarea);
            const { total } = estimateCandidates(cluesCount, cfg, isMultiFormat);
            if (total >= THRESHOLD_RED && confirmHighCb && !confirmHighCb.checked) {
                e.preventDefault();
                e.stopImmediatePropagation();
                warnBox.style.display = 'block';
                alert('Estimated candidates exceed 50,000. Please check "I understand & want to run" before starting.');
            }
        }, true);

        refreshEstimate();
    }

    function initCluePatternBuilder() {
        mountOnForm(document.getElementById('recovery-form'), 'custom_clues', 'start-btn', false);
        mountOnForm(document.getElementById('multi-format-form'), 'mf_custom_clues', 'mf-start-btn', true);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCluePatternBuilder);
    } else {
        initCluePatternBuilder();
    }

    const observer = new MutationObserver(() => {
        initCluePatternBuilder();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
