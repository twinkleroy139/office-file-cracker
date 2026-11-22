import sys
import os
import time
import json
import shutil
import subprocess
import concurrent.futures

from archive_pdf_extractor import extract_multi_format_target, verify_password_for_format

try:
    from firebase_sync import sync_job_result
except Exception:
    def sync_job_result(*args, **kwargs):
        return False

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 2:
    sys.exit(1)

file_path = sys.argv[1]
wordlist_path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].strip() else ""
custom_clues = sys.argv[3] if len(sys.argv) > 3 else ""
wordlist_label = sys.argv[4].strip() if len(sys.argv) > 4 and sys.argv[4].strip() else (os.path.basename(wordlist_path) if wordlist_path else "Clues Only")
job_id = sys.argv[5].strip() if len(sys.argv) > 5 and sys.argv[5].strip() else os.environ.get("JOB_ID", "").strip()

start_time = time.time()
base_dir = os.path.dirname(os.path.abspath(__file__))
root_logs_dir = os.path.abspath(os.path.join(base_dir, "../logs"))
logs_dir = os.path.join(root_logs_dir, "jobs", job_id) if job_id else root_logs_dir
extracted_dir = os.path.join(logs_dir, "extracted_payload")

status_json_path = os.path.join(logs_dir, "job_status.json")
cancel_flag_path = os.path.join(logs_dir, "cancel.flag")
hash_file_path = os.path.join(logs_dir, "multi_target.hash")

os.makedirs(logs_dir, exist_ok=True)


def is_cancelled() -> bool:
    return os.path.exists(cancel_flag_path)


def update_status(state: str, progress: int, output_text: str, engine_label: str = "MULTI-FORMAT (ZIP/PDF/7z)"):
    if is_cancelled() and state == "running":
        return
    data = {
        "status": state,
        "progress": int(progress),
        "job_id": job_id,
        "engine": engine_label,
        "output": output_text,
    }
    try:
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def build_clue_candidates(raw_clues: str) -> list[str]:
    base_clues = [c.strip() for c in raw_clues.split(",") if c.strip()]
    if not base_clues:
        return []
    candidates = set()
    suffixes = ["2026", "2025", "2024", "2023", "2020", "123", "1234", "12345", "!", "@", "#", "01", "07"]
    for word in base_clues:
        candidates.add(word)
        candidates.add(word.lower())
        candidates.add(word.upper())
        candidates.add(word.capitalize())
        candidates.add(word[::-1])
        for sfx in suffixes:
            candidates.add(word + sfx)
            candidates.add(word.capitalize() + sfx)
            candidates.add(word.upper() + sfx)
            candidates.add(sfx + word)
        leet = word.lower().replace("a", "@").replace("e", "3").replace("i", "1").replace("o", "0").replace("s", "$")
        candidates.add(leet)
        for sfx in suffixes:
            candidates.add(leet + sfx)
    return list(candidates)


def run_hashcat_if_applicable(hc_mode: int, hash_line: str, wl_path: str, engine_tag: str):
    hashcat_bin = shutil.which("hashcat")
    if not hashcat_bin or not hash_line or not wl_path or not os.path.exists(wl_path):
        return None, 0

    try:
        with open(hash_file_path, "w", encoding="utf-8") as hf:
            hf.write(hash_line.strip() + "\n")
    except Exception:
        return None, 0

    pot_path = os.path.join(logs_dir, "multi_hashcat.pot")
    cmd = [
        hashcat_bin,
        "-m", str(hc_mode),
        "-a", "0",
        hash_file_path,
        wl_path,
        "--potfile-disable",
        "--potfile-path", pot_path,
        "--quiet",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        for ln in (proc.stdout or "").splitlines():
            s = ln.strip()
            if s.startswith(hash_line.strip() + ":"):
                return s.split(":", 1)[1], 1
        return None, proc.returncode
    except Exception:
        return None, -1


if is_cancelled():
    sys.exit(0)

try:
    meta = extract_multi_format_target(file_path)
except Exception as e:
    elapsed = round(time.time() - start_time, 2)
    err_msg = f"[ENGINE] Active: MULTI-FORMAT\n[-] FORMAT / HEADER ERROR\n[FILE] {os.path.basename(file_path)}\n{e}\n[TIME] {elapsed}s"
    update_status("error", 100, err_msg, "MULTI-FORMAT")
    sync_job_result(
        job_id=job_id,
        status="error",
        progress=100,
        outcome=f"Format error: {e}",
        engine="MULTI-FORMAT",
        resumable=False,
    )
    sys.exit(1)

fmt = meta["format"].upper()
hc_mode = meta["hashcat_mode"]
hash_line = meta["hash_line"]
engine_tag = f"MULTI-FORMAT [{fmt}]"

update_status(
    "running",
    12,
    f"[ENGINE] Active: {engine_tag}\n[INFO] Detected {fmt} target ({meta['info']}). Preparing attack pipeline...",
    engine_tag,
)


def try_candidate_list(candidates: list[str], phase_label: str, start_pct: int, end_pct: int):
    if not candidates:
        return None, 0

    total = len(candidates)
    checked = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(verify_password_for_format, file_path, meta["format"], pwd, extracted_dir): pwd for pwd in candidates}
        for fut in concurrent.futures.as_completed(futures):
            if is_cancelled():
                return None, checked
            checked += 1
            matched = fut.result()
            if matched:
                return matched, checked

            if checked % 25 == 0 or checked == total:
                elapsed_now = max(0.1, round(time.time() - start_time, 1))
                rate_now = round(checked / elapsed_now, 2)
                pct = min(end_pct, start_pct + int((checked / max(1, total)) * (end_pct - start_pct)))
                update_status(
                    "running",
                    pct,
                    f"[ENGINE] Active: {engine_tag}\n[STATUS] {phase_label} on [{os.path.basename(file_path)}]... Checked {checked:,}/{total:,} keys ({rate_now} keys/s | Elapsed: {elapsed_now}s)",
                    engine_tag,
                )
    return None, checked


total_checked = 0
cracked_pwd = None
outcome_text = "No Match Found"

# 1. Custom clues first
clue_list = build_clue_candidates(custom_clues)
if clue_list:
    update_status(
        "running",
        20,
        f"[ENGINE] Active: {engine_tag}\n[INFO] Testing {len(clue_list):,} mangled clue permutations...",
        engine_tag,
    )
    cracked_pwd, c_checked = try_candidate_list(clue_list, "Clue Mangling", 20, 45)
    total_checked += c_checked
    if cracked_pwd:
        outcome_text = f"{fmt} Smart Clue Match Found"

# 2. Wordlist / Hashcat / Python verification
if not cracked_pwd and not is_cancelled() and wordlist_path and os.path.exists(wordlist_path) and os.path.getsize(wordlist_path) > 0:
    if hc_mode and hash_line:
        update_status(
            "running",
            48,
            f"[ENGINE] Active: {engine_tag}\n[INFO] Attempting Hashcat (-m {hc_mode}) with [{wordlist_label}]...",
            engine_tag,
        )
        hc_pwd, hc_rc = run_hashcat_if_applicable(hc_mode, hash_line, wordlist_path, engine_tag)
        if hc_pwd is not None:
            cracked_pwd = hc_pwd
            outcome_text = f"{fmt} Password Recovered (Hashcat -m {hc_mode})"

    if not cracked_pwd and not is_cancelled():
        wl_candidates = []
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wf:
            for line in wf:
                word = line.strip()
                if word:
                    wl_candidates.append(word)
                    if len(wl_candidates) >= 25000:
                        break
        cracked_pwd, w_checked = try_candidate_list(wl_candidates, f"Dictionary [{wordlist_label}]", 50, 95)
        total_checked += w_checked
        if not cracked_pwd:
            outcome_text = f"{fmt} Dictionary Checked / Exhausted"

if is_cancelled():
    sys.exit(0)

elapsed = max(0.01, round(time.time() - start_time, 2))
rate = round(total_checked / elapsed, 2) if total_checked > 0 else 0.0
ms_per_key = round((elapsed / total_checked) * 1000.0, 1) if total_checked > 0 else 0.0

if cracked_pwd is not None:
    msg = (
        f"[ENGINE] Active: {engine_tag}\n"
        f"[SUCCESS] Password Recovered: [{cracked_pwd}]\n"
        f"[FORMAT] {fmt} | [DICTIONARY] {wordlist_label}\n"
        f"[METRICS] Checked: {total_checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
    )
    update_status("finished", 100, msg, engine_tag)
    sync_job_result(
        job_id=job_id,
        status="cracked",
        progress=100,
        cracked_password=cracked_pwd,
        outcome=outcome_text,
        engine=engine_tag,
        last_line_index=total_checked,
        resumable=False,
    )
    sys.exit(0)

exhausted_msg = (
    f"[ENGINE] Active: {engine_tag}\n"
    f"[EXHAUSTED] {fmt} password not found in tested clues/dictionary\n"
    f"[FORMAT] {fmt} | [DICTIONARY] {wordlist_label}\n"
    f"[METRICS] Checked: {total_checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
)
update_status("finished", 100, exhausted_msg, engine_tag)
sync_job_result(
    job_id=job_id,
    status="exhausted",
    progress=100,
    outcome=outcome_text,
    engine=engine_tag,
    last_line_index=total_checked,
    resumable=False,
)
sys.exit(1)