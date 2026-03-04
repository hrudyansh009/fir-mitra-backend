# scripts/build_scst_dataset.py
from __future__ import annotations

import json
import re
from pathlib import Path


def chunk_text(text: str, chunk_chars: int = 1800, overlap: int = 200) -> list[str]:
    """
    Simple char-based chunking with overlap.
    Keeps chunks fairly small for embedding + retrieval.
    """
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    if not text:
        return []

    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + chunk_chars)
        chunk = text[i:j].strip()
        if chunk:
            chunks.append(chunk)
        if j >= n:
            break
        i = max(0, j - overlap)
    return chunks


def build_dataset(
    en_path: Path,
    mr_path: Path,
    out_path: Path,
    chunk_chars: int = 1800,
    overlap: int = 200,
) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rec_id = 0
    with out_path.open("w", encoding="utf-8") as f:
        for src in [en_path, mr_path]:
            raw = src.read_text(encoding="utf-8", errors="ignore")
            pieces = chunk_text(raw, chunk_chars=chunk_chars, overlap=overlap)
            for p in pieces:
                rec = {
                    "id": rec_id,
                    "dataset": "scst",
                    "source_file": str(src).replace("\\", "\\\\"),
                    "text": p,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                rec_id += 1

    return rec_id


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[1]  # Backend/
    en = ROOT / "data" / "corpus" / "scst" / "scst_act_en.txt"
    mr = ROOT / "data" / "corpus" / "scst" / "scst_act_mr.txt"
    out = ROOT / "data" / "index" / "scst_dataset.jsonl"

    if not en.exists():
        raise FileNotFoundError(f"Missing: {en}")
    if not mr.exists():
        raise FileNotFoundError(f"Missing: {mr}")

    n = build_dataset(en, mr, out)
    print(f"OK: wrote {n} records to {out}")