import json
from pathlib import Path

def load_any_index():
    index_path = Path("data/index/scst_offences_index.jsonl")

    if not index_path.exists():
        print("Index file not found:", index_path)
        return None

    records = []
    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except:
                pass

    print(f"Loaded {len(records)} index records")
    return records