let activePollInterval = null;
let activeTimerInterval = null;
let currentJobId = null;

function stopAllIntervals() {
    if (activePollInterval) {
        clearInterval(activePollInterval);
        activePollInterval = null;
    }
    if (activeTimerInterval) {
        clearInterval(activeTimerInterval);
        activeTimerInterval = null;
    }
}

function showDashboardView() {
    stopAllIntervals();
    document.getElementById('progress-view').style.display = 'none';
    document.getElementById('dashboard-view').style.display = 'block';


    function loadJobHistory() {
    const listEl = document.getElementById('job-history-list');
    if (!listEl) return;

    fetch('backend/history.php')
        .then(res => res.json())
        .then(data => {
            const jobs = Array.isArray(data.jobs) ? data.jobs : [];
            if (jobs.length === 0) {
                listEl.innerHTML = `<div style="color: #00b347;">No persistent jobs recorded yet (check Firebase DB rules / env config if locked).</div>`;
                return;
            }
            listEl.innerHTML = jobs.map(j => {
                const id = j.job_id || 'unknown';
                const file = j.file_name || 'Unknown file';
                const wl = j.wordlist_name || 'None';
                const st = (j.status || 'unknown').toUpperCase();
                const lineIdx = Number(j.last_line_index || 0).toLocaleString();
                const pwdBadge = j.cracked_password
                    ? ` | <span style="color: #38bdf8;">Password: <strong>${j.cracked_password}</strong></span>`
                    : '';
                const outcomeBadge = j.outcome
                    ? ` | <span>${j.outcome}</span>`
                    : '';
                return `<div style="border-top: 1px solid #00ff6622; padding: 8px 0; display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <div>
                        <div><strong style="color: #00ff66;">${file}</strong> <span style="font-size: 11px; color: #00b347;">(${wl})</span></div>
                        <div style="font-size: 11px; color: #00b347;">ID: ${id} | Status: <strong>${st}</strong>${pwdBadge}${outcomeBadge} | Line: #${lineIdx}</div>
                    </div>
                </div>`;
            }).join('');
        })
        .catch(() => {
            listEl.innerHTML = `<div style="color: #ffaa33;">Unable to load Firebase job history right now.</div>`;
        });
}

document.getElementById('refresh-history-btn')?.addEventListener('click', loadJobHistory);
loadJobHistory();


}

function sendStopRequest(jobId) {
    return fetch('backend/stop.php', {
        method: 'POST',
        headers: jobId ? { 'Content-Type': 'application/json' } : {},
        body: jobId ? JSON.stringify({ job_id: jobId }) : null
    });
}

function startPollingJob(jobId) {
    stopAllIntervals();

    let seconds = 0;
    const bar = document.getElementById('dynamic-bar');
    const percentVal = document.getElementById('percent-val');
    const terminalBox = document.getElementById('terminal-output');
    const lblStatus = document.getElementById('lbl-status');
    const lblState = document.getElementById('lbl-state');
    const liveTimerEl = document.getElementById('live-timer');
    const speedIndicatorEl = document.getElementById('speed-indicator');
    const stopBtn = document.getElementById('stop-process-btn');
    const cancelLink = document.getElementById('cancel-btn');
    const backBtn = document.getElementById('back-dashboard-btn');
    const resumeBtn = document.getElementById('resume-process-btn');

    if (resumeBtn) resumeBtn.style.display = 'none';
    if (lblState) lblState.innerText = '• ACTIVE';
    liveTimerEl.innerText = 'Elapsed Time: 0s';

    activeTimerInterval = setInterval(() => {
        seconds++;
        liveTimerEl.innerText = `Elapsed Time: ${seconds}s`;
    }, 1000);

    const statusUrl = jobId
        ? `backend/status.php?job_id=${encodeURIComponent(jobId)}`
        : 'backend/status.php';

    activePollInterval = setInterval(() => {
        fetch(statusUrl)
        .then(async res => {
            const rawStatus = await res.text();
            return JSON.parse(rawStatus);
        })
        .then(statusData => {
            const outText = statusData.output || '';
            bar.style.width = statusData.progress + '%';
            percentVal.innerText = `${statusData.progress}% Scanning...`;
            terminalBox.innerHTML = `<pre style="color: #00ff66; margin:0; white-space: pre-wrap;">${outText}</pre>`;
            terminalBox.scrollTop = terminalBox.scrollHeight;

            const elapsedMatch = outText.match(/Elapsed:\s*([\d.]+)s/) || outText.match(/Time:\s*([\d.]+)s/);
            if (elapsedMatch && elapsedMatch[1]) {
                const backendSec = Math.floor(parseFloat(elapsedMatch[1]));
                if (!Number.isNaN(backendSec) && backendSec >= seconds) {
                    seconds = backendSec;
                    liveTimerEl.innerText = `Elapsed Time: ${seconds}s`;
                }
            }

            const engineMatch = outText.match(/\[ENGINE\]\s*Active:\s*([^\n]+)/);
            const activeEngine = statusData.engine || (engineMatch && engineMatch[1] ? engineMatch[1].trim() : '');
            const rateMatch = outText.match(/\(([\d.]+\s*keys\/s\s*\|\s*[\d.]+\s*ms\/key)\)/);

            if (speedIndicatorEl) {
                if (activeEngine && rateMatch && rateMatch[1]) {
                    speedIndicatorEl.innerText = `${activeEngine} | ${rateMatch[1]}`;
                } else if (activeEngine) {
                    speedIndicatorEl.innerText = activeEngine;
                } else if (rateMatch && rateMatch[1]) {
                    speedIndicatorEl.innerText = rateMatch[1];
                }
            }

            if (statusData.status === 'finished' || statusData.status === 'error') {
                stopAllIntervals();
                bar.style.width = '100%';
                percentVal.innerText = '100% Completed';
                const isIncomplete = statusData.status === 'error' || outText.includes('[INCOMPLETE]') || statusData.resumable === true;
                lblStatus.innerText = statusData.status === 'finished' && !isIncomplete
                    ? 'RECOVERY OPERATION FINISHED'
                    : 'INCOMPLETE / INTERRUPTED SCAN';
                if (lblState) lblState.innerText = '• COMPLETED';
                stopBtn.style.display = 'none';
                cancelLink.style.display = 'none';
                backBtn.style.display = 'block';
                if (resumeBtn && jobId && (statusData.resumable === true || outText.includes('[INCOMPLETE]'))) {
                    resumeBtn.style.display = 'block';
                    resumeBtn.disabled = false;
                    resumeBtn.innerText = '[▶] Resume From Checkpoint';
                }
            }
        })
        .catch(err => {
            console.log("Polling error:", err);
        });
    }, 1000);
}

document.getElementById('back-dashboard-btn').addEventListener('click', function() {
    showDashboardView();
});

document.getElementById('resume-process-btn').addEventListener('click', function() {
    if (!currentJobId) {
        alert('No job ID available to resume.');
        return;
    }
    const resumeBtn = this;
    const stopBtn = document.getElementById('stop-process-btn');
    const cancelLink = document.getElementById('cancel-btn');
    const backBtn = document.getElementById('back-dashboard-btn');
    const lblStatus = document.getElementById('lbl-status');

    resumeBtn.disabled = true;
    resumeBtn.innerText = 'RESUMING FROM CHECKPOINT...';
    lblStatus.innerText = 'RESUMING INTERRUPTED SCAN...';
    stopBtn.style.display = 'block';
    stopBtn.disabled = false;
    stopBtn.innerText = '[■] Stop Backend Process';
    cancelLink.style.display = 'block';
    backBtn.style.display = 'none';

    fetch('backend/resume.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: currentJobId })
    })
    .then(async res => {
        const txt = await res.text();
        return JSON.parse(txt);
    })
    .then(data => {
        if (data.status === 'resumed') {
            startPollingJob(currentJobId);
        } else {
            resumeBtn.style.display = 'block';
            resumeBtn.disabled = false;
            resumeBtn.innerText = '[▶] Resume From Checkpoint';
            backBtn.style.display = 'block';
            document.getElementById('terminal-output').innerHTML = `<span style="color: #ff3333;">[-] ${data.output || 'Unable to resume job.'}</span>`;
        }
    })
    .catch(err => {
        resumeBtn.style.display = 'block';
        resumeBtn.disabled = false;
        resumeBtn.innerText = '[▶] Resume From Checkpoint';
        backBtn.style.display = 'block';
        document.getElementById('terminal-output').innerHTML = `<span style="color: #ff3333;">[-] Resume request failed: ${err.message || err}</span>`;
    });
});

document.getElementById('stop-process-btn').addEventListener('click', function() {
    if (!confirm('Stop the running backend recovery process now?')) {
        return;
    }

    const stopBtn = document.getElementById('stop-process-btn');
    const cancelLink = document.getElementById('cancel-btn');
    const backBtn = document.getElementById('back-dashboard-btn');
    const resumeBtn = document.getElementById('resume-process-btn');
    const lblStatus = document.getElementById('lbl-status');
    const lblState = document.getElementById('lbl-state');
    const terminalBox = document.getElementById('terminal-output');

    stopAllIntervals();
    stopBtn.disabled = true;
    stopBtn.innerText = 'STOPPING BACKEND...';

    sendStopRequest(currentJobId)
        .then(res => res.json())
        .then(data => {
            lblStatus.innerText = 'PROCESS STOPPED BY USER';
            if (lblState) lblState.innerText = '• STOPPED';
            terminalBox.innerHTML = `<pre style="color: #ffaa33; margin:0; white-space: pre-wrap;">[STOPPED] ${data.output || 'Backend recovery process stopped.'}\n[INFO] Working Process is now stopped. Click [▶] Resume From Checkpoint or [<<] Return to Dashboard.</pre>`;
            stopBtn.style.display = 'none';
            cancelLink.style.display = 'none';
            backBtn.style.display = 'block';
            if (resumeBtn && currentJobId && data.resumable) {
                resumeBtn.style.display = 'block';
                resumeBtn.disabled = false;
                resumeBtn.innerText = '[▶] Resume From Checkpoint';
            }
        })
        .catch(() => {
            lblStatus.innerText = 'STOP SIGNAL SENT';
            if (lblState) lblState.innerText = '• STOPPED';
            terminalBox.innerHTML = `<pre style="color: #ffaa33; margin:0; white-space: pre-wrap;">[STOPPED] Stop request sent to backend.</pre>`;
            stopBtn.style.display = 'none';
            cancelLink.style.display = 'none';
            backBtn.style.display = 'block';
        });
});

document.getElementById('cancel-btn').addEventListener('click', function(e) {
    e.preventDefault();
    if (!confirm('Stop backend process and return to dashboard?')) {
        return;
    }
    stopAllIntervals();
    sendStopRequest(currentJobId)
        .finally(() => {
            window.location.href = 'index.php';
        });
});

document.getElementById('export-hash-btn').addEventListener('click', function() {
    if (!currentJobId) {
        alert('No active job ID available yet for hash export.');
        return;
    }
    const exportUrl = `backend/export_hash.php?job_id=${encodeURIComponent(currentJobId)}`;
    window.open(exportUrl, '_blank');
});

document.getElementById('recovery-form').addEventListener('submit', function(e) {
    e.preventDefault();
    stopAllIntervals();
    currentJobId = null;

    let fileInput = document.getElementById('locked_file');
    let wordlistFileInput = document.getElementById('wordlist_file');
    let wordlistSelect = document.getElementById('wordlist_select');

    document.getElementById('lbl-file').innerText = fileInput.files.length > 0 ? fileInput.files[0].name : "None";

    let chosenWordlist = "None";
    if (wordlistFileInput && wordlistFileInput.files.length > 0) {
        chosenWordlist = wordlistFileInput.files[0].name;
    } else if (wordlistSelect && wordlistSelect.value) {
        chosenWordlist = wordlistSelect.value;
    }
    document.getElementById('lbl-wordlist').innerText = chosenWordlist;

    document.getElementById('stop-process-btn').style.display = 'block';
    document.getElementById('stop-process-btn').disabled = false;
    document.getElementById('stop-process-btn').innerText = '[■] Stop Backend Process';
    document.getElementById('cancel-btn').style.display = 'block';
    document.getElementById('back-dashboard-btn').style.display = 'none';
    const resumeBtn = document.getElementById('resume-process-btn');
    if (resumeBtn) resumeBtn.style.display = 'none';

    const exportHashBtn = document.getElementById('export-hash-btn');
    if (exportHashBtn) {
        exportHashBtn.style.display = 'none';
        exportHashBtn.disabled = false;
        exportHashBtn.innerText = '[⬇] Export Hash for Local GPU Cracking (.hash)';
    }

    const lblState = document.getElementById('lbl-state');
    if (lblState) lblState.innerText = '• ACTIVE';

    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('progress-view').style.display = 'block';

    let bar = document.getElementById('dynamic-bar');
    let percentVal = document.getElementById('percent-val');
    let terminalBox = document.getElementById('terminal-output');
    let lblStatus = document.getElementById('lbl-status');
    document.getElementById('live-timer').innerText = 'Elapsed Time: 0s';

    let formData = new FormData(this);
    let dedupCheckbox = document.getElementById('filter_dedup_trim');
    formData.set('filter_dedup_trim', (dedupCheckbox && dedupCheckbox.checked) ? '1' : '0');

    fetch('backend/process.php', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        const rawText = await response.text();
        try {
            return JSON.parse(rawText);
        } catch (parseErr) {
            throw new Error(`Invalid server response (${response.status}): not fully complete dic pass and try again`);
        }
    })
    .then(data => {
        if (data.status === 'started') {
            currentJobId = data.job_id || null;
            if (currentJobId && exportHashBtn) {
                exportHashBtn.style.display = 'block';
            }
            lblStatus.innerText = 'EXECUTING BACKGROUND CRACKING PIPELINE...';
            startPollingJob(currentJobId);
        } else {
            stopAllIntervals();
            lblStatus.innerText = 'INITIALIZATION FAILED';
            terminalBox.innerHTML = `<span style="color: #ff3333;">[-] not fully complete dic pass and try again<br>${data.output}</span>`;
            document.getElementById('stop-process-btn').style.display = 'none';
            document.getElementById('cancel-btn').style.display = 'none';
            document.getElementById('back-dashboard-btn').style.display = 'block';
        }
    })
    .catch(error => {
        stopAllIntervals();
        lblStatus.innerText = 'INCOMPLETE / ERROR';
        terminalBox.innerHTML = `<span style="color: #ff3333;">[-] not fully complete dic pass and try again<br>${error.message || error}</span>`;
        bar.style.width = '100%';
        percentVal.innerText = '100% Completed';
        document.getElementById('stop-process-btn').style.display = 'none';
        document.getElementById('cancel-btn').style.display = 'none';
        document.getElementById('back-dashboard-btn').style.display = 'block';
    });
});