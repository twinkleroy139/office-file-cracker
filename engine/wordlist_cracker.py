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
wordlist_label = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].strip() else os.path.basename(wordlist_path)
start_time = time.time()

base_dir = os.path.dirname(os.path.abspath(__file__))
status_json_path = os.path.abspath(os.path.join(base_dir, "../logs/job_status.json"))
cancel_flag_path = os.path.abspath(os.path.join(base_dir, "../logs/cancel.flag"))
decrypted_out_path = os.path.abspath(os.path.join(base_dir, "../decrypted_output.docx"))

def is_cancelled():
    return os.path.exists(cancel_flag_path)

def update_status(state, progress, output_text):
    if is_cancelled() and state == "running":
        return
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

if is_cancelled():
    sys.exit(0)

update_status("running", 10, f"[INFO] High-speed stream initialized for [{wordlist_label}]. Counting dictionary keys...")

try:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
except Exception as e:
    elapsed = round(time.time() - start_time, 2)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] File read error: {e} | [TIME] {elapsed}s"
    )
    sys.exit(1)

def test_password(pwd):
    if is_cancelled():
        return None
    try:
        f_stream = io.BytesIO(file_bytes)
        enc_file = msoffcrypto.OfficeFile(f_stream)
        enc_file.load_key(password=pwd)
        with open(decrypted_out_path, "wb") as out:
            enc_file.decrypt(out)
        return pwd
    except Exception:
        return None

checked = 0
total_keys = 0
found = False
completed_full_scan = False

try:
    total_keys = count_passwords(wordlist_path)
    batch_size = 100

    update_status("running", 15, f"[INFO] Loaded {total_keys:,} keys from [{wordlist_label}]. Starting dictionary scan...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        batch = []
        for pwd in password_generator(wordlist_path):
            if is_cancelled():
                break
            batch.append(pwd)
            if len(batch) >= batch_size:
                futures = [executor.submit(test_password, p) for p in batch]
                for future in concurrent.futures.as_completed(futures):
                    if is_cancelled():
                        break
                    checked += 1
                    res = future.result()
                    if res:
                        elapsed = round(time.time() - start_time, 2)
                        success_msg = (
                            f"[SUCCESS] Password Recovered: [{res}]\n"
                            f"[DICTIONARY] {wordlist_label}\n"
                            f"[METRICS] Checked: {checked:,}/{total_keys:,} keys | Time: {elapsed}s"
                        )
                        update_status("finished", 100, success_msg)
                        found = True
                        break

                if found or is_cancelled():
                    break

                pct = 15
                if total_keys > 0:
                    pct = min(95, 15 + int((checked / total_keys) * 80))
                elapsed_now = round(time.time() - start_time, 1)
                update_status(
                    "running",
                    pct,
                    f"[STATUS] Scanning [{wordlist_label}]... Checked {checked:,}/{total_keys:,} keys (Elapsed: {elapsed_now}s)..."
                )
                batch = []

        if not found and not is_cancelled() and batch:
            futures = [executor.submit(test_password, p) for p in batch]
            for future in concurrent.futures.as_completed(futures):
                if is_cancelled():
                    break
                checked += 1
                res = future.result()
                if res:
                    elapsed = round(time.time() - start_time, 2)
                    success_msg = (
                        f"[SUCCESS] Password Recovered: [{res}]\n"
                        f"[DICTIONARY] {wordlist_label}\n"
                        f"[METRICS] Checked: {checked:,}/{total_keys:,} keys | Time: {elapsed}s"
                    )
                    update_status("finished", 100, success_msg)
                    found = True
                    break

    if is_cancelled():
        sys.exit(0)

    if not found:
        completed_full_scan = (checked >= total_keys)
        elapsed = round(time.time() - start_time, 2)
        if completed_full_scan:
            exhausted_msg = (
                f"[EXHAUSTED] full dic complete not matching with dic and exhausted\n"
                f"[DICTIONARY] {wordlist_label}\n"
                f"[METRICS] Checked: {checked:,}/{total_keys:,} keys | Time: {elapsed}s"
            )
            update_status("finished", 100, exhausted_msg)
        else:
            incomplete_msg = (
                f"[INCOMPLETE] not fully complete dic pass and try again\n"
                f"[DICTIONARY] {wordlist_label}\n"
                f"[METRICS] Checked: {checked:,}/{total_keys:,} keys | Time: {elapsed}s"
            )
            update_status("error", 100, incomplete_msg)

except Exception as e:
    if is_cancelled():
        sys.exit(0)
    elapsed = round(time.time() - start_time, 2)
    err_msg = (
        f"[INCOMPLETE] not fully complete dic pass and try again\n"
        f"[DICTIONARY] {wordlist_label}\n"
        f"[METRICS] Checked: {checked:,}/{total_keys:,} keys | Time: {elapsed}s | Error: {e}"
    )
    update_status("error", 100, err_msg)