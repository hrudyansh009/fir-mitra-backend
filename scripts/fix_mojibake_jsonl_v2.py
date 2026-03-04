# scripts/fix_mojibake_jsonl_v2.py
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INP = ROOT / "data" / "index" / "scst_offences_index.jsonl"
OUT = ROOT / "data" / "index" / "scst_offences_index.fixed.jsonl"

MARK = "à¤"  # typical marker for broken Devanagari

def try_decode(s: str, enc_from: str, enc_to: str) -> str | None:
    try:
        return s.encode(enc_from, errors="strict").decode(enc_to, errors="strict")
    except Exception:
        return None

def score(s: str) -> int:
    # lower is better (fewer mojibake markers)
    return s.count(MARK)

def fix_string(s: str) -> str:
    if MARK not in s:
        return s

    candidates = [s]

    # Common single-step reversals
    for enc_from in ("latin-1", "cp1252"):
        for enc_to in ("utf-8",):
            r = try_decode(s, enc_from, enc_to)
            if r is not None:
                candidates.append(r)

    # Double-step (when file got mangled twice)
    # s -> (latin1->utf8) -> again (latin1->utf8)
    for c in list(candidates):
        if MARK in c:
            for enc_from in ("latin-1", "cp1252"):
                r2 = try_decode(c, enc_from, "utf-8")
                if r2 is not None:
                    candidates.append(r2)

    # Pick best by marker count
    best = min(candidates, key=score)
    return best

def fix_obj(o):
    if isinstance(o, dict):
        return {k: fix_obj(v) for k, v in o.items()}
    if isinstance(o, list):
        return [fix_obj(x) for x in o]
    if isinstance(o, str):
        return fix_string(o)
    return o

def main() -> None:
    if not INP.exists():
        raise SystemExit(f"Missing: {INP}")

    total = 0
    changed = 0

    with INP.open("r", encoding="utf-8", errors="replace") as fin, OUT.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            total += 1
            obj = json.loads(line)
            before = json.dumps(obj, ensure_ascii=False)
            fixed = fix_obj(obj)
            after = json.dumps(fixed, ensure_ascii=False)

            if score(after) < score(before):
                changed += 1

            fout.write(after + "\n")

    print(f"Docs: {total} | improved: {changed} | wrote: {OUT}")

if __name__ == "__main__":
    main()