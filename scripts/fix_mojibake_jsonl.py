# scripts/fix_mojibake_jsonl.py
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INP = ROOT / "data" / "index" / "scst_offences_index.jsonl"
OUT = ROOT / "data" / "index" / "scst_offences_index.fixed.jsonl"

def fix_text(s: str) -> str:
    # Reverse: UTF-8 bytes incorrectly decoded as latin-1
    # If it fails, return original.
    try:
        return s.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    except Exception:
        return s

def fix_obj(o):
    if isinstance(o, dict):
        return {k: fix_obj(v) for k, v in o.items()}
    if isinstance(o, list):
        return [fix_obj(x) for x in o]
    if isinstance(o, str):
        return fix_text(o)
    return o

def main() -> None:
    if not INP.exists():
        raise SystemExit(f"Missing: {INP}")

    fixed_lines = 0
    total = 0

    with INP.open("r", encoding="utf-8", errors="replace") as fin, OUT.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            total += 1
            obj = json.loads(line)
            fixed = fix_obj(obj)
            # count if any typical mojibake marker existed
            if "à¤" in json.dumps(obj, ensure_ascii=False):
                fixed_lines += 1
            fout.write(json.dumps(fixed, ensure_ascii=False) + "\n")

    print(f"Read {total} docs. Fixed-likely {fixed_lines}. Wrote: {OUT}")

if __name__ == "__main__":
    main()