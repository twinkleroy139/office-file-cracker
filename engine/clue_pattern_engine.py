import os

SMART_NUMBERS = [
    "2026", "2025", "2024", "2023", "2020",
    "123", "1234", "12345", "007", "12", "01", "07", "99"
]

DEFAULT_SYMBOLS = ["@", "$", "#", "!", "_", "-"]


def _case_variants(word: str, cases: set[str]) -> list[str]:
    out = []
    seen = set()

    def add(v: str):
        if v and v not in seen:
            seen.add(v)
            out.append(v)

    if "lower" in cases:
        add(word.lower())
    if "cap" in cases:
        add(word.capitalize())
    if "upper" in cases:
        add(word.upper())
    if "alt" in cases:
        alt = "".join(ch.upper() if idx % 2 == 0 else ch.lower() for idx, ch in enumerate(word))
        add(alt)
    if not out:
        add(word)
        add(word.lower())
        add(word.capitalize())
    return out


def _build_numbers(num_enabled: bool, num_mode: str, num_digits: str) -> list[str]:
    if not num_enabled or num_mode == "disabled":
        return []
    if num_mode == "exact":
        digits_list = [d.strip() for d in num_digits.split(",") if d.strip() in ("2", "3", "4")]
        if not digits_list:
            digits_list = ["2"]
        nums = []
        for d in digits_list:
            width = int(d)
            limit = min(10 ** width, 2500 if width == 4 else 10 ** width)
            for n in range(limit):
                nums.append(str(n).zfill(width))
        return nums
    return list(SMART_NUMBERS)


def _build_symbols(sym_enabled: bool, symbols_csv: str) -> list[str]:
    if not sym_enabled:
        return []
    if not symbols_csv.strip():
        return list(DEFAULT_SYMBOLS)
    syms = []
    for part in symbols_csv.split(","):
        s = part.strip()
        if s and s not in syms:
            syms.append(s)
    return syms


def _apply_pos(base: str, extra: str, pos: str) -> list[str]:
    if not extra:
        return [base]
    if pos == "prefix":
        return [extra + base]
    if pos == "both":
        return [extra + base + extra]
    return [base + extra]


def generate_clue_candidates(raw_clues: str, env: dict | None = None, max_candidates: int = 100000) -> list[str]:
    if not raw_clues or not raw_clues.strip():
        return []

    cfg_src = env if env is not None else os.environ
    base_clues = [c.strip() for c in raw_clues.replace("\n", ",").split(",") if c.strip()]
    if not base_clues:
        return []

    pos = (cfg_src.get("CPB_POSITION") or "suffix").strip().lower()
    if pos not in ("suffix", "prefix", "both"):
        pos = "suffix"

    num_enabled = (cfg_src.get("CPB_NUM_ENABLED") or "1").strip() == "1"
    num_mode = (cfg_src.get("CPB_NUM_MODE") or "smart").strip().lower()
    num_digits = (cfg_src.get("CPB_NUM_DIGITS") or "2,3").strip()

    sym_enabled = (cfg_src.get("CPB_SYM_ENABLED") or "1").strip() == "1"
    symbols_csv = (cfg_src.get("CPB_SYMBOLS") or "@,$").strip()

    depth = (cfg_src.get("CPB_DEPTH") or "combined").strip().lower()
    if depth not in ("single", "combined", "deep"):
        depth = "combined"

    cases_raw = (cfg_src.get("CPB_CASES") or "lower,cap").strip().lower()
    cases = {c.strip() for c in cases_raw.split(",") if c.strip()}

    nums = _build_numbers(num_enabled, num_mode, num_digits)
    syms = _build_symbols(sym_enabled, symbols_csv)

    results = []
    seen = set()

    def push(val: str):
        if len(results) >= max_candidates:
            return
        if val and val not in seen:
            seen.add(val)
            results.append(val)

    for clue in base_clues:
        variants = _case_variants(clue, cases)
        for v in variants:
            push(v)
            if depth == "single":
                for n in nums:
                    for item in _apply_pos(v, n, pos):
                        push(item)
                for s in syms:
                    for item in _apply_pos(v, s, pos):
                        push(item)
            elif depth == "combined":
                for n in nums:
                    for item in _apply_pos(v, n, pos):
                        push(item)
                for s in syms:
                    for item in _apply_pos(v, s, pos):
                        push(item)
                for n in nums:
                    for s in syms:
                        push(f"{v}{s}{n}")
                        push(f"{v}{n}{s}")
                        push(f"{s}{v}{n}")
                        push(f"{n}{v}{s}")
            else:  # deep
                for n in nums:
                    for item in _apply_pos(v, n, pos):
                        push(item)
                for s in syms:
                    for item in _apply_pos(v, s, pos):
                        push(item)
                for n in nums:
                    for s in syms:
                        push(f"{v}{s}{n}")
                        push(f"{s}{v}{n}")
                        for s2 in syms[:3]:
                            push(f"{s}{v}{s2}{n}{s2}")
            if len(results) >= max_candidates:
                break
        if len(results) >= max_candidates:
            break

    return results