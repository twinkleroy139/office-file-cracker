import sys
import os
import time
import io
import json
import concurrent.futures
import msoffcrypto

from clue_pattern_engine import generate_clue_candidates

try:
    from firebase_sync import sync_job_result
except Exception:
    def sync_job_result(*args, **kwargs):
        return False

if len(sys.argv) < 3:
    sys.exit(1)

file_path = sys.argv[1]
raw_clues_arg = sys.argv[2]
job_id = sys.argv[3].strip() if len(sys.argv) > 3 and sys.argv[3].strip() else os.environ.get("JOB_ID", "").strip()
start_time = time.time()

base_dir = os.path.dirname(os.path.abspath(__file__))
root_logs_dir = os.path.abspath(os.path.join(base_dir, "../logs"))
logs_dir = os.path.join(root_logs_dir, "jobs", job_id) if job_id else root_logs_dir
status_json_path = os.path.join(logs_dir, "job_status.json")
cancel_flag_path = os.path.join(logs_dir, "cancel.flag")
decrypted_out_path = os.path.join(logs_dir, "decrypted_output.docx") if job_id else os.path.abspath(os.path.join(base_dir, "../decrypted_output.docx"))

ENGINE_TAG = "PYTHON MULTI-CORE + msoffcrypto (8 Threads)"
MAX_CLUE_CANDIDATES = 100000


def is_cancelled():
    return os.path.exists(cancel_flag_path)


def update_status(state, progress, output_text):
    if not job_id:
        return
    if is_cancelled() and state == "running":
        return
    os.makedirs(logs_dir, exist_ok=True)
    data = {
        "status": state,
        "progress": progress,
        "job_id": job_id,
        "engine": ENGINE_TAG,
        "output": output_text
    }
    try:
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


if is_cancelled():
    sys.exit(0)

base_clues = [c.strip() for c in raw_clues_arg.replace("\n", ",").split(",") if c.strip()]
if not base_clues:
    print("[-] No custom clues provided.")
    sys.exit(1)

print(f"[ENGINE] Active: {ENGINE_TAG}")
print(f"[INFO] Base custom clues received: {base_clues}")
print("[INFO] Generating Clue Pattern Builder permutations...")
update_status("running", 12, f"[ENGINE] Active: {ENGINE_TAG}\n[INFO] Generating clue permutations...")

passwords_list = generate_clue_candidates(raw_clues_arg, max_candidates=MAX_CLUE_CANDIDATES)
total_passwords = len(passwords_list)
cap_note = ""
if total_passwords >= MAX_CLUE_CANDIDATES:
    cap_note = f"\n[WARN] Candidate list capped at {MAX_CLUE_CANDIDATES:,} for container safety."
print(f"[INFO] Clue Pattern Engine generated {total_passwords:,} combinations from your clues.")
if cap_note:
    print(cap_note.strip())

try:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
except Exception as e:
    print(f"[-] Error reading locked file: {e}")
    sys.exit(1)


def test_password(pwd):
    if is_cancelled():
        return None
    try:
        f_stream = io.BytesIO(file_bytes)
        enc_file = msoffcrypto.OfficeFile(f_stream)
        enc_file.load_key(password=pwd)
        os.makedirs(os.path.dirname(decrypted_out_path), exist_ok=True)
        with open(decrypted_out_path, "wb") as out:
            enc_file.decrypt(out)
        return pwd
    except Exception:
        return None


checked_count = 0
found_password = None

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(test_password, pwd) for pwd in passwords_list]

    for future in concurrent.futures.as_completed(futures):
        if is_cancelled():
            break
        checked_count += 1
        res = future.result()
        if res:
            found_password = res
            break

if is_cancelled():
    print(f"[ENGINE] Active: {ENGINE_TAG}")
    print("[STOPPED] Custom clue scan cancelled cleanly.")
    sys.exit(0)

if found_password:
    elapsed = round(time.time() - start_time, 2)
    rate = round(checked_count / elapsed, 2) if elapsed > 0 else checked_count
    ms_per_key = round((elapsed / checked_count) * 1000.0, 1) if checked_count > 0 else 0.0
    print(f"\n[ENGINE] Active: {ENGINE_TAG}")
    print(f"[SUCCESS] Smart Match Found: [{found_password}]")
    print(f"[METRICS] Checked: {checked_count:,} permutations ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s")
    update_status(
        "finished",
        100,
        f"[ENGINE] Active: {ENGINE_TAG}\n[SUCCESS] Smart Match Found: [{found_password}]\n[METRICS] Checked: {checked_count:,} permutations ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s{cap_note}"
    )
    sync_job_result(
        job_id=job_id,
        status="cracked",
        progress=100,
        cracked_password=found_password,
        outcome="Smart Clue Match Found",
        engine=ENGINE_TAG,
        resumable=False,
    )
    sys.exit(0)

print(f"[ENGINE] Active: {ENGINE_TAG}")
print("[-] Custom clues mangling exhausted. No match found.")
sys.exit(1)