document.getElementById('recovery-form').addEventListener('submit', function(e) {
    e.preventDefault();

    let fileInput = document.getElementById('locked_file');
    let wordlistFileInput = document.getElementById('wordlist_file');
    let wordlistSelect = document.getElementById('wordlist_select');
    
    document.getElementById('lbl-file').innerText = fileInput.files.length > 0 ? fileInput.files[0].name : "None";
    
    let chosenWordlist = "None";
    if (wordlistFileInput && wordlistFileInput.files.length > 0) {
        chosenWordlist = wordlistFileInput.files[0].name;
    } else if (wordlistSelect) {
        chosenWordlist = wordlistSelect.value;
    }
    document.getElementById('lbl-wordlist').innerText = chosenWordlist;

    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('progress-view').style.display = 'block';

    let seconds = 0;
    let bar = document.getElementById('dynamic-bar');
    let percentVal = document.getElementById('percent-val');
    let terminalBox = document.getElementById('terminal-output');
    let lblStatus = document.getElementById('lbl-status');

    let timerInterval = setInterval(() => {
        seconds++;
        document.getElementById('live-timer').innerText = `Elapsed Time: ${seconds}s`;
    }, 1000);

    let formData = new FormData(this);

    fetch('backend/process.php', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            lblStatus.innerText = 'EXECUTING BACKGROUND CRACKING PIPELINE...';
            
            let pollInterval = setInterval(() => {
                fetch('backend/status.php')
                .then(res => res.json())
                .then(statusData => {
                    bar.style.width = statusData.progress + '%';
                    percentVal.innerText = `${statusData.progress}% Scanning...`;
                    terminalBox.innerHTML = `<pre style="color: #00ff66; margin:0;">${statusData.output}</pre>`;
                    terminalBox.scrollTop = terminalBox.scrollHeight;

                    if (statusData.status === 'finished' || statusData.status === 'error') {
                        clearInterval(pollInterval);
                        clearInterval(timerInterval);
                        bar.style.width = '100%';
                        percentVal.innerText = '100% Completed';
                        lblStatus.innerText = statusData.status === 'finished' ? 'RECOVERY OPERATION FINISHED' : 'EXECUTION ERROR';
                        document.getElementById('cancel-btn').style.display = 'none';
                        document.getElementById('back-dashboard-btn').style.display = 'block';
                    }
                })
                .catch(err => {
                    console.log("Polling error:", err);
                });
            }, 1000);

        } else {
            clearInterval(timerInterval);
            lblStatus.innerText = 'INITIALIZATION FAILED';
            terminalBox.innerHTML = `<span style="color: #ff3333;">[-] ${data.output}</span>`;
            document.getElementById('back-dashboard-btn').style.display = 'block';
        }
    })
    .catch(error => {
        clearInterval(timerInterval);
        lblStatus.innerText = 'NETWORK ERROR';
        terminalBox.innerHTML = `<span style="color: #ff3333;">[-] Failed to connect: ${error}</span>`;
        document.getElementById('back-dashboard-btn').style.display = 'block';
    });
});