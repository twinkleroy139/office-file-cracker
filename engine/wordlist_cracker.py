import sys
import os
import time
import io
import json
import concurrent.futures
import msoffcrypto

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 3:
    sys.exit(1)

file_path = sys.argv[1]
wordlist_path = sys.argv[2]
start_time = time.time()

base_dir = os.path.dirname(os.path.abspath(__file__))
status_json_path = os.path.abspath(os.path.join(base_dir, "../logs/job_status.json"))
decrypted_out_path = os.path.abspath(os.path.join(base_dir, "../decrypted_output.docx"))

def update_status(state, progress, output_text):
    data = {
        "status": state,
        "progress": progress,
        "output": output_text
    }
    try:
        os.makedirs(os.path.dirname(status_json_path), exist_ok=True)
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def password_generator(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pwd = line.strip()
            if pwd:
                yield pwd

def count_passwords(path):
    total = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip():
                total += 1
    return total

update_status("running", 10, "[INFO] High-speed stream initialized. Counting dictionary keys...")

try:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
except Exception as e:
    update_status("error", 100, f"[-] Error reading locked file: {e}")
    sys.exit(1)

def test_password(pwd):
    try:
        f_stream = io.BytesIO(file_bytes)
        enc_file = msoffcrypto.OfficeFile(f_stream)
        enc_file.load_key(password=pwd)
        with open(decrypted_out_path, "wb") as out:
            enc_file.decrypt(out)
        return pwd
    except Exception:
        return None

try:
    total_keys = count_passwords(wordlist_path)
    checked = 0
    found = False
    batch_size = 100

    update_status("running", 15, f"[INFO] Loaded {total_keys:,} keys. Starting dictionary scan...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        batch = []
        for pwd in password_generator(wordlist_path):
            batch.append(pwd)
            if len(batch) >= batch_size:
                futures = [executor.submit(test_password, p) for p in batch]
                for future in concurrent.futures.as_completed(futures):
                    checked += 1
                    res = future.result()
                    if res:
                        elapsed = round(time.time() - start_time, 2)
                        success_msg = f"[SUCCESS] Password Found: [{res}]\n[METRICS] Checked: {checked:,} keys | Time: {elapsed}s"
                        update_status("finished", 100, success_msg)
                        found = True
                        break

                if found:
                    break

                pct = 15
                if total_keys > 0:
                    pct = min(95, 15 + int((checked / total_keys) * 80))
                elapsed_now = round(time.time() - start_time, 1)
                update_status(
                    "running",
                    pct,
                    f"[STATUS] Scanning dictionary... Checked {checked:,}/{total_keys:,} keys (Elapsed: {elapsed_now}s)..."
                )
                batch = []

        if not found and batch:
            futures = [executor.submit(test_password, p) for p in batch]
            for future in concurrent.futures.as_completed(futures):
                checked += 1
                res = future.result()
                if res:
                    elapsed = round(time.time() - start_time, 2)
                    success_msg = f"[SUCCESS] Password Found: [{res}]\n[METRICS] Checked: {checked:,} keys | Time: {elapsed}s"
                    update_status("finished", 100, success_msg)
                    found = True
                    break

    if not found:
        elapsed = round(time.time() - start_time, 2)
        not_match_msg = f"[NOT MATCH] Dictionary exhausted. Checked {checked:,} keys in {elapsed}s. Password not found in dictionary."
        update_status("finished", 100, not_match_msg)

except Exception as e:
    update_status("error", 100, f"[-] Cracker Engine Exception: {e}")