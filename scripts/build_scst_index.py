#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build SC/ST Act index JSONL with clean Unicode (no mojibake).
Reads:
  data/law/sections/section_XX/marathi.txt
  data/law/sections/section_XX/english.txt

Writes:
  data/index/scst_offences_index.jsonl

Key points:
- Always write UTF-8 JSON with ensure_ascii=False
- Detect+repair common mojibake (à¤..., Ã¢..., etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Tuple


MOJIBAKE_MARKERS = (
    "à¤", "à¥", "Ã¢", "Ãƒ", "Â", "â€“", "â€”", "â€™", "â€œ", "â€", "â€¢"
)

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")  # Devanagari block


def looks_mojibake(s: str) -> bool:
    if not s:
        return False
    return any(m in s for m in MOJIBAKE_MARKERS)


def has_devanagari(s: str) -> bool:
    return bool(DEVANAGARI_RE.search(s or ""))


def normalize_text(s: str) -> str:
    # Normalize to prevent weird composition issues
    s = unicodedata.normalize("NFC", s)
    # Remove BOM if any
    s = s.replace("\ufeff", "")
    # Standardize newlines
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Trim trailing spaces per line
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    return s.strip()


def try_mojibake_fix(s: str) -> str:
    """
    Try to reverse common wrong decode:
    e.g. UTF-8 bytes decoded as cp1252/latin1 -> shows à¤…
    Fix attempt: encode as latin1 -> decode as utf-8.
    Only apply if it helps (more Devanagari / fewer markers).
    """
    if not s:
        return s

    if not looks_mojibake(s):
        return s

    # Attempt 1: latin1 -> utf8
    try:
        cand = s.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
        cand = normalize_text(cand)
        # Heuristic: prefer candidate if it introduces Devanagari or removes mojibake markers
        if (has_devanagari(cand) and not has_devanagari(s)) or (
            looks_mojibake(s) and not looks_mojibake(cand)
        ):
            return cand
    except Exception:
        pass

    # Attempt 2: cp1252 -> utf8 (close to latin1 but slightly different)
    try:
        cand = s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        cand = normalize_text(cand)
        if (has_devanagari(cand) and not has_devanagari(s)) or (
            looks_mojibake(s) and not looks_mojibake(cand)
        ):
            return cand
    except Exception:
        pass

    return s


def read_text_safely(path: Path) -> str:
    """
    Read file text with sane fallbacks and mojibake repair.
    """
    raw: Optional[str] = None
    # Best case
    for enc in ("utf-8-sig", "utf-8"):
        try:
            raw = path.read_text(encoding=enc, errors="strict")
            break
        except Exception:
            raw = None

    # Fallbacks (you used Windows terminals — files often end up here)
    if raw is None:
        for enc in ("cp1252", "latin-1", "utf-16", "utf-16le", "utf-16be"):
            try:
                raw = path.read_text(encoding=enc, errors="strict")
                break
            except Exception:
                raw = None

    if raw is None:
        # Last resort: replace errors, but keep going
        raw = path.read_text(encoding="utf-8", errors="replace")

    raw = normalize_text(raw)
    raw = try_mojibake_fix(raw)
    return raw


def infer_title(text: str) -> Optional[str]:
    """
    Try to grab a title-like first line.
    """
    if not text:
        return None
    first = text.split("\n", 1)[0].strip()
    if 3 <= len(first) <= 120:
        return first
    return None


def build_records(sections_dir: Path) -> list[dict]:
    records: list[dict] = []

    # Expect folders like section_01 .. section_23
    folders = sorted([p for p in sections_dir.iterdir() if p.is_dir()])

    for folder in folders:
        m = re.match(r"section_(\d+)", folder.name)
        if not m:
            continue
        sec_no = int(m.group(1))
        section_key = f"SCST_{sec_no:02d}"

        mr_path = folder / "marathi.txt"
        en_path = folder / "english.txt"

        if mr_path.exists():
            mr_text = read_text_safely(mr_path)
            mr_title = infer_title(mr_text)
            records.append(
                {
                    "id": f"{section_key}_MR",
                    "type": "scst",
                    "section_no": sec_no,
                    "section_key": section_key,
                    "title": mr_title,
                    "lang": "mr",
                    "text": mr_text,
                }
            )

        if en_path.exists():
            en_text = read_text_safely(en_path)
            en_title = infer_title(en_text)
            records.append(
                {
                    "id": f"{section_key}_EN",
                    "type": "scst",
                    "section_no": sec_no,
                    "section_key": section_key,
                    "title": en_title,
                    "lang": "en",
                    "text": en_text,
                }
            )

    return records


def write_jsonl(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            # Non-negotiable: ensure_ascii=False keeps Marathi as Marathi.
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def quick_sanity_check(out_path: Path) -> Tuple[int, int]:
    """
    Returns (lines, mojibake_lines)
    """
    lines = 0
    bad = 0
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            lines += 1
            if looks_mojibake(line):
                bad += 1
    return lines, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections-dir", default="data/law/sections", help="Path to sections folder")
    ap.add_argument("--out", default="data/index/scst_offences_index.jsonl", help="Output JSONL path")
    args = ap.parse_args()

    sections_dir = Path(args.sections_dir)
    out_path = Path(args.out)

    if not sections_dir.exists():
        print(f"[FATAL] sections dir not found: {sections_dir}", file=sys.stderr)
        return 2

    records = build_records(sections_dir)
    if not records:
        print("[FATAL] No records built. Check your section_XX folders.", file=sys.stderr)
        return 3

    write_jsonl(records, out_path)
    lines, bad = quick_sanity_check(out_path)

    print(f"[OK] Wrote {lines} lines to {out_path}")
    if bad:
        print(f"[WARN] {bad} lines still look like mojibake. Your source txt files are corrupted.", file=sys.stderr)
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())