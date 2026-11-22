import sys
import os
import time
import io
import json
import concurrent.futures
import msoffcrypto

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


# Parse custom clues separated by commas
base_clues = [c.strip() for c in raw_clues_arg.split(",") if c.strip()]
if not base_clues:
    print("[-] No custom clues provided.")
    sys.exit(1)

print(f"[ENGINE] Active: {ENGINE_TAG}")
print(f"[INFO] Base custom clues received: {base_clues}")
print("[INFO] Generating Smart Rule-Based Mangling permutations...")
update_status("running", 12, f"[ENGINE] Active: {ENGINE_TAG}\n[INFO] Generating clue permutations...")

# Smart Rule-Based Mangling Engine
mangled_passwords = set()
years = ["2026", "2025", "2024", "2023", "2020", "123", "1234", "12345", "!", "@", "#", "01", "07"]

for word in base_clues:
    mangled_passwords.add(word)
    mangled_passwords.add(word.lower())
    mangled_passwords.add(word.upper())
    mangled_passwords.add(word.capitalize())
    mangled_passwords.add(word[::-1])

    for y in years:
        mangled_passwords.add(word + y)
        mangled_passwords.add(word.capitalize() + y)
        mangled_passwords.add(word.upper() + y)
        mangled_passwords.add(y + word)

    leetspeak = word.lower().replace('a', '@').replace('e', '3').replace('i', '1').replace('o', '0').replace('s', '$')
    mangled_passwords.add(leetspeak)
    for y in years:
        mangled_passwords.add(leetspeak + y)

passwords_list = list(mangled_passwords)
total_passwords = len(passwords_list)
print(f"[INFO] Smart Mangling generated {total_passwords:,} intelligent combinations from your clues.")

try:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
except Exception as e:
    print(f"[-] Error reading locked file: {e}")
    sys.exit(1)


def test_password(pwd):
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
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(test_password, pwd): pwd for pwd in passwords_list}

    for future in concurrent.futures.as_completed(futures):
        checked_count += 1
        res = future.result()
        if res:
            elapsed = round(time.time() - start_time, 2)
            rate = round(checked_count / elapsed, 2) if elapsed > 0 else checked_count
            ms_per_key = round((elapsed / checked_count) * 1000.0, 1) if checked_count > 0 else 0.0
            print(f"\n[ENGINE] Active: {ENGINE_TAG}")
            print(f"[SUCCESS] Smart Match Found: [{res}]")
            print(f"[METRICS] Checked: {checked_count:,} permutations ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s")
            update_status(
                "finished",
                100,
                f"[ENGINE] Active: {ENGINE_TAG}\n[SUCCESS] Smart Match Found: [{res}]\n[METRICS] Checked: {checked_count:,} permutations ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
            )
            sync_job_result(
                job_id=job_id,
                status="cracked",
                progress=100,
                cracked_password=res,
                outcome="Smart Clue Match Found",
                engine=ENGINE_TAG,
                resumable=False,
            )
            sys.exit(0)

print(f"[ENGINE] Active: {ENGINE_TAG}")
print("[-] Custom clues mangling exhausted. No match found.")
sys.exit(1)