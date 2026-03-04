import re
from pathlib import Path

RAW_DIR = Path("data/law/raw")
OUT_DIR = Path("data/law/sections")

EN_IN = RAW_DIR / "scst_act_en.txt"
MR_IN = RAW_DIR / "scst_act_mr.txt"

def split_english(text: str) -> dict[int, str]:
    parts = re.split(r"^===\s*SECTION\s+(\d+)\s*===\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1].strip()
        if body:
            out[n] = body
    return out

def split_marathi(text: str) -> dict[int, str]:
    parts = re.split(r"^===\s*कलम\s+(\d+)\s*===\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1].strip()
        if body:
            out[n] = body
    return out

def main():
    if not EN_IN.exists():
        raise SystemExit(f"Missing: {EN_IN}")
    if not MR_IN.exists():
        raise SystemExit(f"Missing: {MR_IN}")

    en_text = EN_IN.read_text(encoding="utf-8", errors="replace")
    mr_text = MR_IN.read_text(encoding="utf-8", errors="replace")

    en_map = split_english(en_text)
    mr_map = split_marathi(mr_text)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_nums = sorted(set(en_map) | set(mr_map))
    if not all_nums:
        raise SystemExit("No sections detected. Check the markers in raw files.")

    for n in all_nums:
        sec_dir = OUT_DIR / f"section_{n:02d}"
        sec_dir.mkdir(parents=True, exist_ok=True)
        if n in en_map:
            (sec_dir / "english.txt").write_text(en_map[n] + "\n", encoding="utf-8")
        if n in mr_map:
            (sec_dir / "marathi.txt").write_text(mr_map[n] + "\n", encoding="utf-8")

    print(f"Built {len(all_nums)} section folders in {OUT_DIR}")

if __name__ == "__main__":
    main()