# scripts/rebuild_scst_index.py
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # Backend/
SECTIONS_DIR = ROOT / "data" / "law" / "sections"
OUT = ROOT / "data" / "index" / "scst_offences_index.jsonl"

def read_utf8(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()

def main() -> None:
    out_lines = []
    sec_folders = sorted([p for p in SECTIONS_DIR.iterdir() if p.is_dir() and p.name.startswith("section_")])

    if not sec_folders:
        raise SystemExit(f"No section folders found in {SECTIONS_DIR}")

    for folder in sec_folders:
        # section_01 -> 1
        try:
            section_no = int(folder.name.split("_")[1])
        except Exception:
            continue

        mr_path = folder / "marathi.txt"
        en_path = folder / "english.txt"

        mr = read_utf8(mr_path) if mr_path.exists() else ""
        en = read_utf8(en_path) if en_path.exists() else ""

        text = f"SCST Act Section {section_no}\n\n[MR]\n{mr}\n\n[EN]\n{en}\n"
        obj = {
            "id": str(section_no),
            "section_no": section_no,
            "section_key": f"scst_section_{section_no:02d}",
            "title": None,
            "lang": "mr",
            "text": text,
        }
        out_lines.append(json.dumps(obj, ensure_ascii=False))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(out_lines)} docs -> {OUT}")

if __name__ == "__main__":
    main()