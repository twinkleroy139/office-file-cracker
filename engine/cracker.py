import sys
import subprocess
import os
import shutil

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

child_env = os.environ.copy()
child_env["WORDLIST_LABEL"] = wordlist_label
if job_id:
    child_env["JOB_ID"] = job_id

try:
    # Step 1: Run custom clues engine (Python Multi-Core + msoffcrypto)
    if custom_clues and custom_clues.strip():
        executed_module = "custom_cracker.py"
        sub_script = os.path.join(engine_dir, "custom_cracker.py")
        print("[ENGINE] Selected: PYTHON MULTI-CORE + msoffcrypto (Custom Clues & Mangling)")
        print("[MASTER] Initiating Custom Clues & Smart Mangling Engine...")
        args = [py_cmd, sub_script, locked_file, custom_clues]
        if job_id:
            args.append(job_id)
        res = subprocess.run(args, capture_output=True, text=True, env=child_env)
        print(res.stdout)
        if res.stderr:
            print(f"[-] Sub-Module stderr: {res.stderr}")
        if res.returncode == 0:
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
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            env=child_env
        )
        print(res.stdout)
        if res.stderr:
            print(f"[-] Sub-Module stderr: {res.stderr}")
        sys.exit(res.returncode)

    print("[-] Error: No valid wordlist or custom clues provided.")
    sys.exit(1)

except Exception as e:
    print(f"[-] Critical Error in Master Controller [Module: {executed_module}]: {str(e)}")
    sys.exit(1)