import sys
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
status_json_path = "../logs/job_status.json"

def update_status(state, progress, output_text):
    data = {
        "status": state,
        "progress": progress,
        "output": output_text
    }
    try:
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except:
        pass

update_status("running", 10, "[INFO] High-speed stream initialized. Starting dictionary scan...")

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
        with open("../decrypted_output.docx", "wb") as out:
            enc_file.decrypt(out)
        return pwd
    except Exception:
        return None

try:
    checked = 0
    found = False
    batch_size = 1000

    def password_generator(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                pwd = line.strip()
                if pwd:
                    yield pwd

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        batch = []
        for pwd in password_generator(wordlist_path):
            batch.append(pwd)
            if len(batch) >= batch_size:
                futures = {executor.submit(test_password, p): p for p in batch}
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
                
                update_status("running", 60, f"[STATUS] Scanning high-speed wordlist... Checked {checked:,} keys (Elapsed: {round(time.time() - start_time, 1)}s)...")
                batch = []

        if not found and batch:
            futures = {executor.submit(test_password, p): p for p in batch}
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
        update_status("finished", 100, f"[-] Wordlist exhausted. Checked {checked:,} keys. No match found.")

except Exception as e:
    update_status("error", 100, f"[-] Cracker Engine Exception: {e}")