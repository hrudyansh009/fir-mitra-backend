from pathlib import Path
import re

BASE = Path("data/law/sections")
SRC = Path("data/law/raw/scst_act_mr.txt")  # adjust if your path differs

def main():
    text = SRC.read_text(encoding="utf-8")

    # Split on headings like: === कलम 1 ===
    parts = re.split(r"(?m)^===\s*कलम\s*(\d+)\s*===$", text)
    # parts: [before, "1", content1, "2", content2, ...]
    if len(parts) < 3:
        raise SystemExit("No section markers found. Your scst_act_mr.txt format is wrong.")

    count = 0
    for i in range(1, len(parts), 2):
        sec_no = int(parts[i])
        sec_text = parts[i + 1].strip() + "\n"
        folder = BASE / f"section_{sec_no:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "marathi.txt").write_text(sec_text, encoding="utf-8")
        count += 1

    print(f"[OK] Rebuilt marathi.txt for {count} sections from Unicode source.")

if __name__ == "__main__":
    main()