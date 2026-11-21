import sys
import os
import time
import io
import json
import shutil
import subprocess
import msoffcrypto
from hash_extractor import extract_office_hash

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 3:
    sys.exit(1)

file_path = sys.argv[1]
wordlist_path = sys.argv[2]
cli_label = sys.argv[3].strip() if len(sys.argv) > 3 and sys.argv[3].strip() else ""
env_label = os.environ.get("WORDLIST_LABEL", "").strip()
wordlist_label = cli_label or env_label or os.path.basename(wordlist_path)
start_time = time.time()

base_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.abspath(os.path.join(base_dir, "../logs"))
status_json_path = os.path.join(logs_dir, "job_status.json")
cancel_flag_path = os.path.join(logs_dir, "cancel.flag")
hash_file_path = os.path.join(logs_dir, "office_target.hash")
potfile_path = os.path.join(logs_dir, "hashcat.pot")
decrypted_out_path = os.path.abspath(os.path.join(base_dir, "../decrypted_output.docx"))

os.makedirs(logs_dir, exist_ok=True)


def is_cancelled() -> bool:
    return os.path.exists(cancel_flag_path)


def update_status(state: str, progress: int, output_text: str):
    if is_cancelled() and state == "running":
        return
    data = {
        "status": state,
        "progress": progress,
        "output": output_text
    }
    try:
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def format_timing(checked_count: int, elapsed_sec: float):
    if checked_count <= 0 or elapsed_sec <= 0:
        return 0.0, 0.0
    rate_per_sec = round(checked_count / elapsed_sec, 2)
    ms_per_key = round((elapsed_sec / checked_count) * 1000.0, 1)
    return rate_per_sec, ms_per_key


def decrypt_and_save(password: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        enc_file = msoffcrypto.OfficeFile(io.BytesIO(file_bytes))
        enc_file.load_key(password=password)
        with open(decrypted_out_path, "wb") as out:
            enc_file.decrypt(out)
        return True
    except Exception:
        return False


def parse_hashcat_stdout(stdout_text: str, hash_line: str):
    cracked_pwd = None
    latest_checked = 0
    latest_rate = None

    for line in stdout_text.splitlines():
        line_s = line.strip()
        if not line_s:
            continue

        if line_s.startswith("{") and line_s.endswith("}"):
            try:
                st = json.loads(line_s)
                prog = st.get("progress")
                if isinstance(prog, list) and len(prog) >= 2:
                    latest_checked = int(prog[0])
                speeds = st.get("speeds")
                if isinstance(speeds, list) and len(speeds) > 0:
                    # hashcat reports H/s per device
                    total_hs = sum(float(x) for x in speeds if isinstance(x, (int, float)))
                    if total_hs > 0:
                        latest_rate = round(total_hs, 2)
            except Exception:
                pass
            continue

        if hash_line and line_s.startswith(hash_line + ":"):
            cracked_pwd = line_s.split(":", 1)[1]
        elif ":" in line_s and not line_s.startswith("["):
            left, right = line_s.split(":", 1)
            if left.strip().startswith("$office$") or left.strip().startswith("$oldoffice$"):
                cracked_pwd = right

    return cracked_pwd, latest_checked, latest_rate


if is_cancelled():
    sys.exit(0)

hashcat_bin = shutil.which("hashcat")
if not hashcat_bin:
    elapsed = round(time.time() - start_time, 2)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] hashcat binary not found in PATH | [TIME] {elapsed}s"
    )
    sys.exit(1)

if not os.path.exists(wordlist_path) or os.path.getsize(wordlist_path) == 0:
    elapsed = round(time.time() - start_time, 2)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] Filtered wordlist empty or missing | [TIME] {elapsed}s"
    )
    sys.exit(1)

update_status("running", 10, f"[INFO] Phase 2 Hashcat initialized for [{wordlist_label}]. Extracting Office hash...")

try:
    hc_mode, hash_str = extract_office_hash(file_path)
    with open(hash_file_path, "w", encoding="utf-8") as hf:
        hf.write(hash_str + "\n")
except Exception as e:
    elapsed = round(time.time() - start_time, 2)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] Hash extraction error: {e} | [TIME] {elapsed}s"
    )
    sys.exit(1)

if is_cancelled():
    sys.exit(0)

update_status("running", 20, f"[INFO] Extracted hash (mode {hc_mode}) for [{wordlist_label}]. Launching hashcat engine...")

cmd = [
    hashcat_bin,
    "-m", str(hc_mode),
    "-a", "0",
    hash_file_path,
    wordlist_path,
    "--potfile-disable",
    "--potfile-path", potfile_path,
    "--status",
    "--status-json",
    "--status-timer", "2",
    "--quiet"
]

try:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    stdout_chunks = []
    cracked_pwd = None
    checked_est = 0
    hc_rate = None

    while True:
        if is_cancelled():
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            sys.exit(0)

        line = proc.stdout.readline() if proc.stdout else ""
        if line:
            stdout_chunks.append(line)
            s = line.strip()
            if s.startswith("{") and s.endswith("}"):
                try:
                    st = json.loads(s)
                    prog = st.get("progress")
                    if isinstance(prog, list) and len(prog) >= 2 and prog[1]:
                        checked_est = int(prog[0])
                        total_est = max(1, int(prog[1]))
                        pct = min(95, 20 + int((checked_est / total_est) * 75))
                    else:
                        pct = 50
                    speeds = st.get("speeds")
                    if isinstance(speeds, list) and len(speeds) > 0:
                        tot_hs = sum(float(x) for x in speeds if isinstance(x, (int, float)))
                        if tot_hs > 0:
                            hc_rate = round(tot_hs, 2)

                    elapsed_now = max(0.1, round(time.time() - start_time, 1))
                    rate_now = hc_rate if hc_rate is not None else round(checked_est / elapsed_now, 2)
                    ms_now = round(1000.0 / rate_now, 1) if rate_now > 0 else 0.0
                    update_status(
                        "running",
                        pct,
                        f"[STATUS] Hashcat (m{hc_mode}) scanning [{wordlist_label}]... Checked {checked_est:,} keys ({rate_now} keys/s | {ms_now} ms/key | Elapsed: {elapsed_now}s)..."
                    )
                except Exception:
                    pass
            elif s.startswith(hash_str + ":") and not cracked_pwd:
                cracked_pwd = s.split(":", 1)[1]

        if proc.poll() is not None:
            rest = proc.stdout.read() if proc.stdout else ""
            if rest:
                stdout_chunks.append(rest)
            break

    full_out = "".join(stdout_chunks)
    parsed_pwd, parsed_checked, parsed_rate = parse_hashcat_stdout(full_out, hash_str)
    if parsed_pwd:
        cracked_pwd = parsed_pwd
    if parsed_checked > checked_est:
        checked_est = parsed_checked
    if parsed_rate is not None:
        hc_rate = parsed_rate

    if is_cancelled():
        sys.exit(0)

    elapsed = max(0.01, round(time.time() - start_time, 2))
    rate, ms_per_key = format_timing(checked_est, elapsed)
    if hc_rate is not None and hc_rate > 0:
        rate = hc_rate
        ms_per_key = round(1000.0 / rate, 1)

    if cracked_pwd is not None:
        decrypt_and_save(cracked_pwd)
        success_msg = (
            f"[SUCCESS] Password Recovered: [{cracked_pwd}]\n"
            f"[DICTIONARY] {wordlist_label} (Hashcat -m {hc_mode})\n"
            f"[METRICS] Checked: {checked_est:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
        )
        update_status("finished", 100, success_msg)
        sys.exit(0)

    # Exit code 1 in hashcat typically means exhausted (no password found)
    if proc.returncode == 1:
        exhausted_msg = (
            f"[EXHAUSTED] full dic complete not matching with dic and exhausted\n"
            f"[DICTIONARY] {wordlist_label} (Hashcat -m {hc_mode})\n"
            f"[METRICS] Checked: {checked_est:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
        )
        update_status("finished", 100, exhausted_msg)
        sys.exit(1)

    incomplete_msg = (
        f"[INCOMPLETE] not fully complete dic pass and try again\n"
        f"[DICTIONARY] {wordlist_label} (Hashcat -m {hc_mode}) | [CODE] {proc.returncode}\n"
        f"[METRICS] Checked: {checked_est:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
    )
    update_status("error", 100, incomplete_msg)
    sys.exit(1)

except Exception as e:
    if is_cancelled():
        sys.exit(0)
    elapsed = round(time.time() - start_time, 2)
    rate, ms_per_key = format_timing(0, elapsed)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] {e} | [TIME] {elapsed}s"
    )
    sys.exit(1)