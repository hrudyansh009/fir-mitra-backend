import json
from pathlib import Path
from typing import Any, List, Optional


def load_any_index() -> Optional[List[Any]]:
    """
    Loads the JSONL index from data/index/scst_offences_index.jsonl
    Returns list of dict records or None if missing/empty.
    """
    index_path = Path("data/index/scst_offences_index.jsonl")

    if not index_path.exists():
        print(f"[FATAL] Index file not found: {index_path.resolve()}")
        return None

    records: List[Any] = []
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                # skip broken lines; do not crash deployment
                continue

    print(f"[OK] Loaded {len(records)} index records from {index_path}")
    return records if records else None