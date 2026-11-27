# 🔐 OfficeCracker
### Document & Archive Password Recovery Suite

<div align="center">

**A Full-Stack Platform for Authorized Password Recovery of Protected Documents and Archives.**

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![PHP](https://img.shields.io/badge/PHP-Backend-777BB4.svg)](https://www.php.net/)
[![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-F7DF1E.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Firebase](https://img.shields.io/badge/Firebase-Integration-FFCA28.svg)](https://firebase.google.com/)
[![Deployment](https://img.shields.io/badge/Hosting-Render-black.svg)](https://render.com/)
[![License](https://img.shields.io/badge/Usage-Authorized%20Recovery-success.svg)](#responsible-use-policy)

**Repository:** [github.com/twinkleroy139/office-file-cracker](https://github.com/twinkleroy139/office-file-cracker)

LIVE Site: https://office-file-cracker.onrender.com/

</div>

---

## 📖 Overview

**OfficeCracker** is a full-stack document and archive password recovery platform designed to help users restore access to password-protected files they own or are explicitly authorized to recover.

The platform supports Microsoft Office documents (`.docx`, `.xlsx`) and multiple archive/document formats (`.zip`, `.pdf`, `.7z`).

Unlike basic password-testing scripts, OfficeCracker combines an interactive browser dashboard, a PHP orchestration layer, and multi-threaded Python recovery engines into a unified workflow.

Its clue-driven candidate generation engine allows users to build targeted password patterns from known words, numbers, symbols, and character variations. A synchronized frontend estimator provides candidate-volume warnings and approximate execution-time estimates before processing begins.

The platform also includes live job telemetry, cancellation, supported checkpoint resume functionality, hash export, Firebase job-history synchronization, and resource-management safeguards for constrained cloud environments.

### ✨ Core Features

| Feature | Description |
|---|---|
| **Clue Pattern Builder** | Generates targeted candidate patterns using user-provided words, numbers, symbols, and case variations |
| **Live Candidate Estimator** | Estimates candidate volume and execution time before starting a job |
| **Office Recovery Engine** | Supports authorized recovery workflows for `.docx` and `.xlsx` using `msoffcrypto` |
| **Multi-Format Engine** | Supports `.zip`, `.pdf`, and `.7z` through dedicated extraction and verification workflows |
| **Multi-Threaded Execution** | Uses Python worker threads for candidate verification |
| **Optional Hashcat Integration** | Detects Hashcat availability and provides a Python fallback when compatible GPU/OpenCL execution is unavailable |
| **Live Job Monitoring** | Displays progress, elapsed time, throughput, engine information, and runtime logs |
| **Job Cancellation** | Supports clean cancellation through a per-job `cancel.flag` mechanism |
| **Checkpoint Resume** | Supports resuming eligible interrupted dictionary-based jobs |
| **Hash Export** | Exports extracted hashes for authorized external or local recovery workflows |
| **Firebase Synchronization** | Optionally synchronizes job outcomes and recovery history |
| **Resource Protection** | Applies candidate limits, configurable timeouts, and automatic stale-job cleanup |

---

## 🧩 Clue Pattern Builder

One of OfficeCracker's main components is its synchronized frontend/backend password candidate generation system.

Instead of immediately relying on large dictionaries, users can provide relevant clues and configure how candidate variations are generated.

### 1. Attachment Positions

Choose where additional characters should appear:

- **Suffix:** `word + extra`
- **Prefix:** `extra + word`
- **Both:** `extra + word + extra`

### 2. Number Attachment Modes

| Mode | Description |
|---|---|
| Smart / Likely Only | Uses selected common numbers and years, including 2026, 2025, 2024, 2023, 2020, 123, 1234, 12345, 007, 12, 01, 07, and 99 |
| Short Exact Range | Expands selected numeric ranges across 2-, 3-, and capped 4-digit patterns |
| Disabled | Skips number attachments |

The exact-range generator applies a maximum of 2,500 values per configured range.

### 3. Symbol Attachments

Supports common symbols and custom characters.

Examples of built-in symbols:

```text
@  $  #  !  _  -
```

Custom symbols can also be supplied through comma-separated input.

### 4. Pattern Depth

| Depth | Description |
|---|---|
| Single | Word combined with either a number or a symbol |
| Combined | Word combined with number and symbol permutations |
| Deep | Multi-symbol and nested combinations |

### 5. Case Variants

The generator supports:

- `lowercase`
- `Capitalized`
- `UPPERCASE`
- `aLtErNaTiNg`

### 6. Candidate Estimation & Safety Warnings

The frontend implementation in `assets/js/clue_pattern_builder.js` mirrors the backend logic in `engine/clue_pattern_engine.py`.

This keeps candidate estimates aligned with the actual generation rules.

| Candidate Volume | UI Behavior |
|---|---|
| Below 2,000 | Normal estimation |
| 2,000+ | Yellow warning |
| 50,000+ | Red high-volume warning and explicit confirmation |
| 100,000 | Default maximum candidate-generation cap |

The estimator uses approximate throughput assumptions of:

- Office Python execution: 2 keys/s
- Multi-format execution: 150 keys/s

Actual execution speed depends on file encryption, hardware, worker configuration, and the recovery engine.

---

## 📂 Supported File Formats

OfficeCracker provides two dedicated recovery workflows.

### Microsoft Office Documents

<badge color="success">Supported workflow</badge>

<grid columns={2}>
  <grid-item>
    **DOCX**

    <text color="secondary" size="xs">Microsoft Word documents</text>
  </grid-item>
  <grid-item>
    **XLSX**

    <text color="secondary" size="xs">Microsoft Excel workbooks</text>
  </grid-item>
</grid>

The Office recovery engine uses:

- `msoffcrypto`
- Python `concurrent.futures`
- Multi-threaded candidate verification
- Optional Hashcat availability detection

When Hashcat cannot access compatible GPU/OpenCL resources, the application reports the fallback condition rather than silently failing.

### Multi-Format Archives & PDFs

<badge color="success">Dedicated recovery pipeline</badge>

| Format | File Type |
|---|---|
| ZIP | Compressed archive |
| PDF | Portable Document Format |
| 7Z | 7-Zip archive |

The multi-format engine uses:

- Target format and metadata inspection.
- Hash or payload extraction where supported.
- Isolated per-job workspaces.
- Clue-based candidate verification.
- Dictionary-based fallback.
- Optional Hashcat integration.

---

## 🏗️ System Architecture

OfficeCracker follows a layered architecture that separates browser interaction, PHP job orchestration, Python recovery processing, and optional cloud synchronization.

```text
                  USER BROWSER
                       │
                       ▼
              OfficeCracker Dashboard
                HTML / CSS / JS
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   Office Recovery UI         Multi-Format UI
   DOCX / XLSX                ZIP / PDF / 7Z
          │                         │
          └────────────┬────────────┘
                       ▼
                 PHP Backend
              Job Dispatch Layer
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    cracker.py             multi_format_cracker.py
    Master Controller       Archive/PDF Pipeline
          │                         │
          └────────────┬────────────┘
                       ▼
              Clue Pattern Engine
             Candidate Generation
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    Python Workers              Hashcat
    Multi-threaded               Optional
          │                         │
          └────────────┬────────────┘
                       ▼
                 Job Telemetry
              job_status.json
                cancel.flag
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
             Frontend Dashboard
              Live Job Updates
                       │
                       ▼
              Firebase Sync
               Optional Cloud
```

### 🔄 End-to-End Execution Workflow

1. **File Upload:** The user uploads an authorized target document or archive through the browser dashboard.
2. **Clue Configuration:** The user enters relevant clues and configures number, symbol, position, depth, and case variations.
3. **Candidate Estimation:** The frontend estimates candidate count and execution time, displaying warnings for high-volume configurations.
4. **Job Initialization:** The PHP backend creates an isolated workspace under `logs/jobs/` and `uploads/jobs/`.
5. **Engine Dispatch:** The appropriate Python controller starts the Office or multi-format recovery pipeline.
6. **Clue-Based Processing:** The engine generates and tests candidates, subject to the configured candidate cap.
7. **Fallback Processing:** If the clue-based stage does not recover the password, the configured dictionary/Hashcat fallback is used where supported.
8. **Live Monitoring:** Job status, progress, throughput, elapsed time, and logs are updated for the frontend.
9. **Completion & Synchronization:** Final outcomes are recorded locally and optionally synchronized with Firebase.

---

## ⚙️ Job Management & Monitoring

OfficeCracker includes a job-control system designed to make longer recovery tasks easier to monitor.

### Real-Time Telemetry

The browser dashboard polls:

```text
backend/status.php
```

The default polling interval is one second.

The status endpoint reads per-job information from:

```text
logs/jobs/<job_id>/job_status.json
```

The dashboard displays:

- Progress percentage.
- Elapsed execution time.
- Candidate verification speed (`keys/s`).
- Average processing time (`ms/key`).
- Active engine information.
- Live terminal output.
- Completion, timeout, and error states.

### Clean Cancellation

The stop mechanism uses:

```text
logs/jobs/<job_id>/cancel.flag
```

When a user requests cancellation:

1. The PHP endpoint creates the cancellation flag.
2. Python workers periodically check `is_cancelled()`.
3. Eligible processing loops stop.
4. The job status is updated to reflect the stop request.

### Checkpoint Resume

The application supports resuming eligible interrupted dictionary-based jobs through:

```text
backend/resume.php
```

Resume availability depends on the job's saved state and available checkpoint information.

### Hash Export

Extracted hashes can be exported through:

```text
backend/export_hash.php
```

This supports separate, authorized local recovery workflows.

---

## 🧠 Resource Management & Reliability

OfficeCracker is designed with resource-constrained cloud environments in mind.

Free-tier containers can have limited CPU, memory, disk capacity, and execution time. The application therefore includes several safeguards.

### 1. Candidate Generation Limit

The default candidate-generation limit is:

```text
100,000 candidates
```

The limit is enforced by:

```text
engine/clue_pattern_engine.py
```

Both recovery pipelines record warnings when a candidate set reaches the configured cap.

### 2. Execution Timeouts

| Configuration | Default | Purpose |
|---|---:|---|
| `SUBPROCESS_TIMEOUT_SEC` | 600 seconds | Limits subprocess execution in the master controller |
| `MULTI_FORMAT_MAX_SEC` | 480 seconds | Limits total multi-format processing time |

The master controller uses subprocess timeout handling and can return exit code `124` when its configured timeout is exceeded.

The multi-format engine tracks elapsed time and records a structured timeout state when its execution budget is reached.

### 3. Automated Stale Job Cleanup

The cleanup module:

```text
engine/job_cleanup.py
```

Prunes old job directories under:

```text
logs/jobs/
uploads/jobs/
```

Default cleanup configuration:

| Setting | Default |
|---|---:|
| Maximum job age | 86,400 seconds (24 hours) |
| Retained recent jobs | 10 |

Cleanup is invoked by the recovery controllers.

> **Storage note:** These cleanup rules manage temporary local job data. They do not replace persistent storage, backups, or a separate retention policy for Firebase records.

---

## 🛠️ Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | HTML5, CSS3 | Dashboard layout and styling |
| Frontend Logic | Vanilla JavaScript | Candidate builder, job submission, polling, and controls |
| Backend | PHP | Request handling, job initialization, and process orchestration |
| Recovery Engine | Python 3 | Candidate generation and verification |
| Office Processing | `msoffcrypto` | Microsoft Office password verification |
| Concurrency | `concurrent.futures` | Multi-threaded execution |
| Optional Recovery Tool | Hashcat | External recovery engine integration |
| Cloud Hosting | Render | Web application hosting |
| Cloud Synchronization | Firebase | Optional job history and outcome synchronization |

---

## 📁 Project Structure

```text
OfficeCracker/
│
├── index.php
│
├── assets/
│   ├── css/
│   │   ├── style.css
│   │   ├── cyber-aura.css
│   │   └── clue_pattern_builder.css
│   │
│   └── js/
│       ├── script.js
│       ├── clue_pattern_builder.js
│       └── multi_format_ui.js
│
├── backend/
│   ├── process.php
│   ├── process_archive_pdf.php
│   ├── status.php
│   ├── stop.php
│   ├── resume.php
│   ├── export_hash.php
│   └── history.php
│
├── engine/
│   ├── cracker.py
│   ├── clue_pattern_engine.py
│   ├── custom_cracker.py
│   ├── multi_format_cracker.py
│   ├── archive_pdf_extractor.py
│   ├── job_cleanup.py
│   └── firebase_sync.py
│
├── logs/
│   └── jobs/
│
└── uploads/
    └── jobs/
```

### Important Modules

| File | Responsibility |
|---|---|
| `index.php` | Main dashboard and recovery interface |
| `clue_pattern_builder.js` | Interactive clue builder and candidate estimator |
| `multi_format_ui.js` | Multi-format workflow and progress interface |
| `script.js` | Job submission, polling, stop/resume, and history |
| `process.php` | Dispatches Office recovery jobs |
| `process_archive_pdf.php` | Dispatches multi-format recovery jobs |
| `status.php` | Provides live job status |
| `cracker.py` | Master controller and subprocess timeout handling |
| `clue_pattern_engine.py` | Candidate generation and safety cap |
| `custom_cracker.py` | Office document recovery engine |
| `multi_format_cracker.py` | Archive/PDF recovery pipeline |
| `archive_pdf_extractor.py` | Format detection and hash/payload extraction |
| `job_cleanup.py` | Stale job directory cleanup |
| `firebase_sync.py` | Optional Firebase synchronization |

---

## 🚀 Local Development Setup

### Prerequisites

Install the following software:

- PHP with the extensions required by your application.
- Python 3.
- Git.
- A local PHP development environment such as XAMPP or another PHP-capable server.
- Required Python packages for Office and archive/PDF processing.
- Optional Hashcat installation for compatible environments.
- Firebase project credentials if cloud synchronization is enabled.

### 1. Clone the Repository

```bash
git clone https://github.com/twinkleroy139/office-file-cracker.git

cd office-file-cracker
```

### 2. Configure Python

Create a virtual environment:

```bash
python -m venv .venv
```

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install the Python dependencies using the project's dependency manifest, if provided.

At minimum, the Office engine requires the `msoffcrypto` dependency. The multi-format engine also requires the archive and PDF libraries used by `archive_pdf_extractor.py`.

### 3. Configure PHP

Make sure your PHP server can execute the backend endpoints and launch the required Python processes.

Verify that:

- PHP can execute the configured Python interpreter.
- Python dependencies are installed in the environment used by PHP.
- The process execution configuration is correct.
- Required PHP extensions are available.

### 4. Configure Writable Directories

The PHP and Python processes need appropriate read/write permissions for:

```text
logs/
uploads/
```

The job system uses these directories for temporary files, runtime logs, extracted data, and job status.

### 5. Configure Environment Variables

The main runtime controls include:

```env
SUBPROCESS_TIMEOUT_SEC=600
MULTI_FORMAT_MAX_SEC=480
```

For optional Firebase synchronization, configure the Firebase environment variables expected by:

```text
engine/firebase_sync.py
```

Use the exact credential format supported by your implementation.

### 6. Start the Application

Start your PHP development server using XAMPP, Apache, or the configured local PHP server.

Open the application using the local server URL.

---

## ☁️ Deployment on Render

OfficeCracker can be hosted on Render when the deployment environment supports the PHP backend and Python subprocess execution required by the application.

### Deployment Checklist

1. Push the project to GitHub.
2. Create a compatible Render service.
3. Configure the PHP runtime or Docker environment.
4. Install the required Python dependencies.
5. Configure the PHP and Python execution paths.
6. Set the application environment variables.
7. Ensure `logs/` and `uploads/` are writable.
8. Configure Firebase credentials if cloud synchronization is enabled.
9. Verify that subprocess execution and timeout handling work correctly.

**Important deployment considerations:**

- A standard Python-only Render start command will not automatically serve a PHP application.
- Your deployment must explicitly configure both PHP and Python.
- Render's local filesystem may be ephemeral, so job files and uploaded documents should not be assumed to persist across restarts or deployments.
- Free-tier execution limits may interrupt long-running jobs.
- Hashcat GPU/OpenCL functionality depends on the available compute environment.

### Live Service

<text>Repository:</text>

[OfficeCracker on GitHub](https://github.com/twinkleroy139/office-file-cracker)

<text>Render deployment:</text>

Configure your active service URL here once deployment is available:

```text
https://<your-service-name>.onrender.com
```

---

## 🔥 Firebase Integration

OfficeCracker supports optional cloud synchronization through:

```text
engine/firebase_sync.py
```

When Firebase credentials and appropriate security rules are configured, the application can synchronize job outcomes and recovery metrics.

Supported job outcomes described by the project include:

- Completed.
- Cracked.
- Exhausted.
- Timed out.
- Error.

Firebase integration is optional. The local job-processing workflow uses the project's local job directories and status files.

**Security recommendations:**

- Never commit Firebase service-account credentials.
- Store credentials in protected environment variables or secret files.
- Restrict Firebase database access through security rules.
- Do not expose privileged credentials to frontend JavaScript.
- Avoid storing sensitive uploaded document contents in cloud history records.

---

## ⚠️ Known Limitations

OfficeCracker is designed for authorized recovery workflows, but its performance and compatibility depend on several factors.

### 1. Encryption Complexity

Recovery time depends on password complexity, encryption method, candidate quality, and available computing resources.

A targeted clue-based search does not guarantee password recovery.

### 2. Cloud Compute Limitations

Free-tier cloud environments may not provide:

- GPU acceleration.
- Compatible OpenCL devices.
- Unlimited CPU time.
- Persistent local storage.
- Long-running subprocess execution.

### 3. Hashcat Compatibility

Hashcat is optional. If the required GPU/OpenCL environment is unavailable, the application may fall back to its Python verification engine where supported.

### 4. Execution Timeouts

Long-running jobs can be stopped by application-level timeout limits or hosting-platform restrictions.

### 5. File Format Compatibility

Actual recovery support depends on the file's encryption format and the capabilities of the relevant extraction and verification libraries.

### 6. Candidate Generation Limits

The default 100,000-candidate cap helps protect constrained environments but can limit coverage for more complex password patterns.

---

## 🔐 Security & Responsible Use

OfficeCracker is intended exclusively for legitimate password recovery and authorized security auditing.

### Responsible Use Policy

- Only upload files you own or have explicit permission to recover.
- Do not use the application to access third-party documents without authorization.
- Protect uploaded documents, extracted data, hashes, and job logs.
- Restrict access to job-control and history endpoints.
- Remove temporary files according to an appropriate retention policy.
- Keep Firebase credentials and other secrets outside public repositories.

### Data Protection

Uploaded files and extracted artifacts may contain sensitive information. Deployments should use authenticated access, secure transport, appropriate filesystem permissions, and suitable retention controls.

---

## 🗺️ Future Improvements

Potential engineering improvements for future releases:

- [ ] Improved persistent job storage.
- [ ] Stronger user authentication and per-user job isolation.
- [ ] More comprehensive job queue management.
- [ ] Enhanced recovery engine diagnostics.
- [ ] Improved checkpoint and resume reliability.
- [ ] Configurable worker concurrency.
- [ ] Better resource monitoring and automatic job scheduling.
- [ ] More detailed Firebase job analytics.
- [ ] Automated testing across supported encryption formats.
- [ ] Improved deployment support for PHP + Python environments.

---

## 📜 License & Disclaimer

OfficeCracker is provided for educational, development, and authorized document-access restoration purposes.

Users are responsible for ensuring they have the legal right and explicit authorization to recover passwords from the files they process.

Do not use this software for unauthorized access, data theft, privacy violations, or circumvention of third-party access controls.

---

## 👨‍💻 Author

**Twinkle Roy**

- GitHub: [@twinkleroy139](https://github.com/twinkleroy139)
- Portfolio: [my-portfolio-6d703.web.app](https://my-portfolio-6d703.web.app)

---

<div align="center">

**🔐 OfficeCracker — Recover access. Monitor every job. Stay in control.**

<sub>Built with PHP, Python, JavaScript, and Firebase.</sub>

</div>