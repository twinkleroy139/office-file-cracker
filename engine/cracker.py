import sys
import subprocess
import os
import shutil

from job_cleanup import cleanup_old_jobs

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 4:
    print("[-] Error: cracker.py expects at least 3 arguments.")
    sys.exit(1)

locked_file = sys.argv[1]
wordlist_path = sys.argv[2]
custom_clues = sys.argv[3]
wordlist_label = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4].strip() else os.path.basename(wordlist_path)
job_id = sys.argv[5].strip() if len(sys.argv) > 5 and sys.argv[5].strip() else os.environ.get("JOB_ID", "").strip()

executed_module = "None"
engine_dir = os.path.dirname(os.path.abspath(__file__))

# Detect python executable name
py_cmd = "python" if os.name == "nt" else "python3"

try:
    timeout_sec = int(os.environ.get("SUBPROCESS_TIMEOUT_SEC", "600"))
    if timeout_sec < 10:
        timeout_sec = 600
except ValueError:
    timeout_sec = 600

child_env = os.environ.copy()
child_env["WORDLIST_LABEL"] = wordlist_label
if job_id:
    child_env["JOB_ID"] = job_id


def run_sub_module(args_list, module_label):
    try:
        res = subprocess.run(
            args_list,
            capture_output=True,
            text=True,
            env=child_env,
            timeout=timeout_sec
        )
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(f"[-] Sub-Module stderr ({module_label}): {res.stderr}")
        return res.returncode
    except subprocess.TimeoutExpired as te:
        if te.stdout:
            out_str = te.stdout.decode("utf-8", errors="ignore") if isinstance(te.stdout, bytes) else te.stdout
            print(out_str)
        print(f"[-] Timeout in [{module_label}] after {timeout_sec}s (container safety limit reached).")
        return 124


try:
    cleaned = cleanup_old_jobs(max_age_seconds=86400, keep_latest=10)
    if cleaned.get("removed_dirs", 0) > 0:
        print(f"[CLEANUP] Pruned {cleaned['removed_dirs']} old job folders ({cleaned['freed_bytes']:,} bytes freed).")

    # Step 1: Run custom clues engine (Python Multi-Core + msoffcrypto)
    if custom_clues and custom_clues.strip():
        executed_module = "custom_cracker.py"
        sub_script = os.path.join(engine_dir, "custom_cracker.py")
        print("[ENGINE] Selected: PYTHON MULTI-CORE + msoffcrypto (Custom Clues & Mangling)")
        print("[MASTER] Initiating Custom Clues & Smart Mangling Engine...")
        args = [py_cmd, sub_script, locked_file, custom_clues]
        if job_id:
            args.append(job_id)
        rc = run_sub_module(args, executed_module)
        if rc == 0:
            sys.exit(0)

    # Step 2: Run Phase 2 Hashcat wordlist engine (fallback to Phase 1 Python Multi-Core + msoffcrypto)
    if wordlist_path and os.path.exists(wordlist_path):
        phase2_script = os.path.join(engine_dir, "hashcat_cracker.py")
        phase1_script = os.path.join(engine_dir, "wordlist_cracker_phase1.py")
        fallback_script = os.path.join(engine_dir, "wordlist_cracker.py")

        hashcat_found = shutil.which("hashcat") is not None
        if hashcat_found and os.path.exists(phase2_script):
            sub_script = phase2_script
            print("[ENGINE] Selected: HASHCAT (Primary Wordlist Engine)")
        elif os.path.exists(phase1_script):
            sub_script = phase1_script
            print("[ENGINE] Selected: PYTHON MULTI-CORE + msoffcrypto (Hashcat binary not found)")
        else:
            sub_script = fallback_script
            print("[ENGINE] Selected: PYTHON MULTI-CORE + msoffcrypto (Legacy Fallback)")

        executed_module = os.path.basename(sub_script)
        print(f"[MASTER] Initiating Wordlist Cracker ({executed_module})...")
        args = [py_cmd, sub_script, locked_file, wordlist_path, wordlist_label]
        if job_id:
            args.append(job_id)
        rc = run_sub_module(args, executed_module)
        sys.exit(rc)

    print("[-] Error: No valid wordlist or custom clues provided.")
    sys.exit(1)

except Exception as e:
    print(f"[-] Critical Error in Master Controller [Module: {executed_module}]: {str(e)}")
    sys.exit(1)