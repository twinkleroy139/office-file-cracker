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

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 3:
    sys.exit(1)

file_path = sys.argv[1]
wordlist_path = sys.argv[2]
cli_label = sys.argv[3].strip() if len(sys.argv) > 3 and sys.argv[3].strip() else ""
job_id = sys.argv[4].strip() if len(sys.argv) > 4 and sys.argv[4].strip() else os.environ.get("JOB_ID", "").strip()
cli_resume = sys.argv[5].strip() if len(sys.argv) > 5 and sys.argv[5].strip() else os.environ.get("RESUME_FROM_LINE", "0").strip()
try:
    resume_from_line = max(0, int(cli_resume))
except ValueError:
    resume_from_line = 0

env_label = os.environ.get("WORDLIST_LABEL", "").strip()
wordlist_label = cli_label or env_label or os.path.basename(wordlist_path)
fallback_notice = os.environ.get("FALLBACK_NOTICE", "").strip()
start_time = time.time()

base_dir = os.path.dirname(os.path.abspath(__file__))
root_logs_dir = os.path.abspath(os.path.join(base_dir, "../logs"))
job_logs_dir = os.path.join(root_logs_dir, "jobs", job_id) if job_id else root_logs_dir

status_json_path = os.path.join(job_logs_dir, "job_status.json")
cancel_flag_path = os.path.join(job_logs_dir, "cancel.flag")
checkpoint_path = os.path.join(job_logs_dir, "checkpoint.json")
decrypted_out_path = os.path.join(job_logs_dir, "decrypted_output.docx")

ENGINE_TAG = "PYTHON MULTI-CORE + msoffcrypto (4 Threads)"

os.makedirs(job_logs_dir, exist_ok=True)


def format_terminal_block(body_text: str) -> str:
    header = f"[ENGINE] Active: {ENGINE_TAG}"
    if fallback_notice:
        return f"{header}\n{fallback_notice}\n{body_text}"
    return f"{header}\n{body_text}"


def is_cancelled():
    return os.path.exists(cancel_flag_path)


def save_checkpoint(line_idx: int, checked_total: int):
    payload = {
        "job_id": job_id,
        "wordlist_label": wordlist_label,
        "file_path": file_path,
        "last_line_index": int(line_idx),
        "checked_count": int(checked_total),
        "updated_at": int(time.time())
    }
    try:
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        pass


def update_status(state, progress, body_text, resumable=False):
    if is_cancelled() and state == "running":
        return
    data = {
        "status": state,
        "progress": progress,
        "job_id": job_id,
        "engine": ENGINE_TAG,
        "resumable": resumable,
        "output": format_terminal_block(body_text)
    }
    try:
        with open(status_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def password_generator(path, skip_lines=0):
    skipped = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            pwd = line.strip()
            if pwd:
                if skipped < skip_lines:
                    skipped += 1
                    continue
                yield pwd


def format_timing(checked_count, elapsed_sec):
    if checked_count <= 0 or elapsed_sec <= 0:
        return 0.0, 0.0
    rate_per_sec = round(checked_count / elapsed_sec, 2)
    ms_per_key = round((elapsed_sec / checked_count) * 1000.0, 1)
    return rate_per_sec, ms_per_key


if is_cancelled():
    save_checkpoint(resume_from_line, 0)
    sys.exit(0)

print(format_terminal_block("[INFO] Phase 1 initialized. Parsing file metadata once..."))
update_status("running", 10, f"[INFO] Phase 1 initialized for [{wordlist_label}]. Parsing file metadata once...")

try:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    probe_stream = io.BytesIO(file_bytes)
    parsed_office_meta = msoffcrypto.OfficeFile(probe_stream)
    is_encrypted = parsed_office_meta.is_encrypted()
    if not is_encrypted:
        elapsed = round(time.time() - start_time, 2)
        update_status(
            "error",
            100,
            f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] Document is not encrypted | [TIME] {elapsed}s"
        )
        sync_job_result(
            job_id=job_id,
            status="error",
            progress=100,
            outcome="Document is not encrypted",
            engine=ENGINE_TAG,
            resumable=False,
        )
        sys.exit(1)
except Exception as e:
    elapsed = round(time.time() - start_time, 2)
    update_status(
        "error",
        100,
        f"[-] not fully complete dic pass and try again\n[DICT] {wordlist_label} | [REASON] Metadata parse error: {e} | [TIME] {elapsed}s"
    )
    sync_job_result(
        job_id=job_id,
        status="error",
        progress=100,
        outcome=f"Metadata parse error: {e}",
        engine=ENGINE_TAG,
        resumable=False,
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
current_line_pos = resume_from_line
found = False
reached_eof = False

try:
    batch_size = 100
    resume_note = f" (resuming from line #{resume_from_line:,})" if resume_from_line > 0 else ""
    update_status("running", 15, f"[INFO] Metadata cached for [{wordlist_label}]{resume_note}. Streaming keys...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        batch = []
        stream_iter = password_generator(wordlist_path, skip_lines=resume_from_line)

        while True:
            if is_cancelled():
                save_checkpoint(current_line_pos, checked)
                break

            batch.clear()
            for _ in range(batch_size):
                try:
                    batch.append(next(stream_iter))
                except StopIteration:
                    reached_eof = True
                    break

            if batch:
                futures = [executor.submit(test_password, p) for p in batch]
                for future in concurrent.futures.as_completed(futures):
                    if is_cancelled():
                        break
                    checked += 1
                    current_line_pos += 1
                    res = future.result()
                    if res:
                        if os.path.exists(checkpoint_path):
                            try:
                                os.remove(checkpoint_path)
                            except Exception:
                                pass
                        elapsed = round(time.time() - start_time, 2)
                        rate, ms_per_key = format_timing(checked, elapsed)
                        success_msg = (
                            f"[SUCCESS] Password Recovered: [{res}]\n"
                            f"[DICTIONARY] {wordlist_label}\n"
                            f"[METRICS] Checked: {checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
                        )
                        update_status("finished", 100, success_msg, resumable=False)
                        sync_job_result(
                            job_id=job_id,
                            status="cracked",
                            progress=100,
                            cracked_password=res,
                            outcome="Password Recovered",
                            engine=ENGINE_TAG,
                            last_line_index=current_line_pos,
                            resumable=False,
                        )
                        found = True
                        break

                save_checkpoint(current_line_pos, checked)

                if found or is_cancelled():
                    break

                elapsed_now = max(0.1, round(time.time() - start_time, 1))
                rate_now, ms_now = format_timing(checked, elapsed_now)
                pct = min(95, 15 + (current_line_pos // 250))
                update_status(
                    "running",
                    pct,
                    f"[STATUS] Scanning [{wordlist_label}] (Line #{current_line_pos:,})... Checked {checked:,} keys ({rate_now} keys/s | {ms_now} ms/key | Elapsed: {elapsed_now}s)..."
                )

            if reached_eof:
                break

    if is_cancelled():
        save_checkpoint(current_line_pos, checked)
        sys.exit(0)

    if not found:
        elapsed = round(time.time() - start_time, 2)
        rate, ms_per_key = format_timing(checked, elapsed)
        if reached_eof:
            if os.path.exists(checkpoint_path):
                try:
                    os.remove(checkpoint_path)
                except Exception:
                    pass
            exhausted_msg = (
                f"[EXHAUSTED] full dic complete not matching with dic and exhausted\n"
                f"[DICTIONARY] {wordlist_label}\n"
                f"[METRICS] Checked: {checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
            )
            update_status("finished", 100, exhausted_msg, resumable=False)
            sync_job_result(
                job_id=job_id,
                status="exhausted",
                progress=100,
                outcome="Dictionary Exhausted",
                engine=ENGINE_TAG,
                last_line_index=current_line_pos,
                resumable=False,
            )
        else:
            save_checkpoint(current_line_pos, checked)
            incomplete_msg = (
                f"[INCOMPLETE] Interrupted at line #{current_line_pos:,} — ready to resume\n"
                f"[DICTIONARY] {wordlist_label}\n"
                f"[METRICS] Checked: {checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s"
            )
            update_status("error", 100, incomplete_msg, resumable=True)
            sync_job_result(
                job_id=job_id,
                status="incomplete",
                progress=100,
                outcome="Interrupted Scan",
                engine=ENGINE_TAG,
                last_line_index=current_line_pos,
                resumable=True,
            )

except Exception as e:
    save_checkpoint(current_line_pos, checked)
    if is_cancelled():
        sys.exit(0)
    elapsed = round(time.time() - start_time, 2)
    rate, ms_per_key = format_timing(checked, elapsed)
    err_msg = (
        f"[INCOMPLETE] Interrupted at line #{current_line_pos:,} — ready to resume\n"
        f"[DICTIONARY] {wordlist_label}\n"
        f"[METRICS] Checked: {checked:,} keys ({rate} keys/s | {ms_per_key} ms/key) | Time: {elapsed}s | Error: {e}"
    )
    update_status("error", 100, err_msg, resumable=True)
    sync_job_result(
        job_id=job_id,
        status="incomplete",
        progress=100,
        outcome=f"Scan Error: {e}",
        engine=ENGINE_TAG,
        last_line_index=current_line_pos,
        resumable=True,
    )