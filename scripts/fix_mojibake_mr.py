from pathlib import Path

ROOTS = [
    Path("data/law/raw"),
    Path("data/law/sections"),
    Path("data/index"),
]

def looks_mojibake(s: str) -> bool:
    return ("à¤" in s) or ("Ã" in s)

def repair(s: str) -> str:
    # Recover UTF-8 that was wrongly decoded as latin-1/cp1252
    try:
        return s.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    except Exception:
        # fallback: don’t destroy data if it’s not actually recoverable
        return s

def main():
    changed = 0
    scanned = 0

    for root in ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.txt"):
            scanned += 1
            data = p.read_text(encoding="utf-8", errors="replace")
            if looks_mojibake(data):
                fixed = repair(data)
                # only write if improvement happened
                if fixed != data and not looks_mojibake(fixed):
                    p.write_text(fixed, encoding="utf-8")
                    changed += 1

    # also fix jsonl
    for p in Path("data/index").rglob("*.jsonl"):
        scanned += 1
        data = p.read_text(encoding="utf-8", errors="replace")
        if looks_mojibake(data):
            fixed = repair(data)
            if fixed != data and not looks_mojibake(fixed):
                p.write_text(fixed, encoding="utf-8")
                changed += 1

    print(f"Scanned {scanned} files, fixed {changed} files.")

if __name__ == "__main__":
    main()