import sys
import subprocess
import os

sys.stdout.reconfigure(line_buffering=True)

if len(sys.argv) < 4:
    print("[-] Error: cracker.py expects 3 arguments.")
    sys.exit(1)

locked_file = sys.argv[1]
wordlist_path = sys.argv[2]
custom_clues = sys.argv[3]
wordlist_label = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4].strip() else os.path.basename(wordlist_path)

executed_module = "None"
engine_dir = os.path.dirname(os.path.abspath(__file__))

# Detect python executable name
py_cmd = "python" if os.name == "nt" else "python3"

try:
    # Step 1: Run custom clues engine
    if custom_clues and custom_clues.strip():
        executed_module = "custom_cracker.py"
        sub_script = os.path.join(engine_dir, "custom_cracker.py")
        print(f"[MASTER] Initiating Custom Clues & Smart Mangling Engine...")
        res = subprocess.run([py_cmd, sub_script, locked_file, custom_clues], capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print(f"[-] Sub-Module stderr: {res.stderr}")
        if res.returncode == 0:
            sys.exit(0)

    # Step 2: Run high-speed wordlist engine
    if wordlist_path and os.path.exists(wordlist_path):
        executed_module = "wordlist_cracker.py"
        sub_script = os.path.join(engine_dir, "wordlist_cracker.py")
        print(f"[MASTER] Initiating High-Speed Wordlist Cracker...")
        child_env = os.environ.copy()
        child_env["WORDLIST_LABEL"] = wordlist_label
        res = subprocess.run(
            [py_cmd, sub_script, locked_file, wordlist_path, wordlist_label],
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