import sys
import os
import re

if len(sys.argv) < 2:
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""

dedup_trim = os.environ.get("FILTER_DEDUP_TRIM", "1") == "1"
min_len_raw = os.environ.get("FILTER_MIN_LEN", "").strip()
max_len_raw = os.environ.get("FILTER_MAX_LEN", "").strip()
char_rule = os.environ.get("FILTER_CHAR_RULE", "any").strip().lower()
order_mode = os.environ.get("FILTER_ORDER", "default").strip().lower()

min_len = int(min_len_raw) if min_len_raw.isdigit() else None
max_len = int(max_len_raw) if max_len_raw.isdigit() else None

if not input_path or not os.path.exists(input_path):
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            pass
    sys.exit(0)

def matches_char_rule(pwd, rule):
    if rule == "numeric":
        return pwd.isdigit()
    if rule == "alpha":
        return pwd.isalpha()
    if rule == "alnum":
        return pwd.isalnum()
    if rule == "lower":
        return pwd.islower()
    if rule == "no_spaces":
        return not any(ch.isspace() for ch in pwd)
    return True

candidates = []
seen = set()

with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    for raw_line in f:
        pwd = raw_line.strip() if dedup_trim else raw_line.rstrip("\r\n")
        if not pwd:
            continue

        if dedup_trim:
            if pwd in seen:
                continue
            seen.add(pwd)

        if min_len is not None and len(pwd) < min_len:
            continue
        if max_len is not None and len(pwd) > max_len:
            continue
        if not matches_char_rule(pwd, char_rule):
            continue

        candidates.append(pwd)

if order_mode == "short_first":
    candidates.sort(key=lambda s: (len(s), s))
elif order_mode == "common_patterns":
    common_re = re.compile(r"^[a-zA-Z]+\d+$|^\d+$|^[A-Z][a-z]+\d*$")
    candidates.sort(key=lambda s: (0 if common_re.match(s) else 1, len(s)))

if not output_path:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(base_dir, "../logs/filtered_wordlist.txt"))

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as out:
    for pwd in candidates:
        out.write(pwd + "\n")

print(f"[FILTER] Kept {len(candidates):,} filtered passwords -> {output_path}")