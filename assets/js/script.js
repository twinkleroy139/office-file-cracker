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
}

function sendStopRequest(jobId) {
    return fetch('backend/stop.php', {
        method: 'POST',
        headers: jobId ? { 'Content-Type': 'application/json' } : {},
        body: jobId ? JSON.stringify({ job_id: jobId }) : null
    });
}

document.getElementById('back-dashboard-btn').addEventListener('click', function() {
    showDashboardView();
});

document.getElementById('stop-process-btn').addEventListener('click', function() {
    if (!confirm('Stop the running backend recovery process now?')) {
        return;
    }

    const stopBtn = document.getElementById('stop-process-btn');
    const cancelLink = document.getElementById('cancel-btn');
    const backBtn = document.getElementById('back-dashboard-btn');
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
            terminalBox.innerHTML = `<pre style="color: #ffaa33; margin:0; white-space: pre-wrap;">[STOPPED] ${data.output || 'Backend recovery process stopped.'}\n[INFO] Working Process is now stopped. Click [<<] Return to Dashboard when ready.</pre>`;
            stopBtn.style.display = 'none';
            cancelLink.style.display = 'none';
            backBtn.style.display = 'block';
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

    const lblState = document.getElementById('lbl-state');
    if (lblState) lblState.innerText = '• ACTIVE';

    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('progress-view').style.display = 'block';

    let seconds = 0;
    let bar = document.getElementById('dynamic-bar');
    let percentVal = document.getElementById('percent-val');
    let terminalBox = document.getElementById('terminal-output');
    let lblStatus = document.getElementById('lbl-status');
    let liveTimerEl = document.getElementById('live-timer');
    let speedIndicatorEl = document.getElementById('speed-indicator');

    liveTimerEl.innerText = 'Elapsed Time: 0s';
    activeTimerInterval = setInterval(() => {
        seconds++;
        liveTimerEl.innerText = `Elapsed Time: ${seconds}s`;
    }, 1000);

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
            lblStatus.innerText = 'EXECUTING BACKGROUND CRACKING PIPELINE...';
            const statusUrl = currentJobId
                ? `backend/status.php?job_id=${encodeURIComponent(currentJobId)}`
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

                    const rateMatch = outText.match(/\(([\d.]+\s*keys\/s\s*\|\s*[\d.]+\s*ms\/key)\)/);
                    if (speedIndicatorEl && rateMatch && rateMatch[1]) {
                        speedIndicatorEl.innerText = rateMatch[1];
                    }

                    if (statusData.status === 'finished' || statusData.status === 'error') {
                        stopAllIntervals();
                        bar.style.width = '100%';
                        percentVal.innerText = '100% Completed';
                        lblStatus.innerText = statusData.status === 'finished' ? 'RECOVERY OPERATION FINISHED' : 'INCOMPLETE / ERROR';
                        if (lblState) lblState.innerText = '• COMPLETED';
                        document.getElementById('stop-process-btn').style.display = 'none';
                        document.getElementById('cancel-btn').style.display = 'none';
                        document.getElementById('back-dashboard-btn').style.display = 'block';
                    }
                })
                .catch(err => {
                    console.log("Polling error:", err);
                });
            }, 1000);

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
        document.getElementById('stop-process-btn').style.display = 'none';
        document.getElementById('cancel-btn').style.display = 'none';
        document.getElementById('back-dashboard-btn').style.display = 'block';
    });
});