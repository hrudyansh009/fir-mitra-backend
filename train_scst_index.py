# train_scst_index.py
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from openai import OpenAI


def load_dataset(dataset_path: Path) -> list[dict]:
    rows = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def embed_texts(client: OpenAI, texts: list[str], model: str = "text-embedding-3-small") -> np.ndarray:
    # Batch embedding to avoid huge single request
    vecs = []
    batch_size = 128
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        vecs.extend([d.embedding for d in resp.data])
    return np.array(vecs, dtype=np.float32)


def main() -> None:
    ROOT = Path(__file__).resolve().parent  # Backend/
    dataset_path = ROOT / "data" / "index" / "scst_dataset.jsonl"
    out_index = ROOT / "data" / "index" / "scst_index.jsonl"
    out_emb = ROOT / "data" / "index" / "scst_embeddings.npy"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Missing dataset: {dataset_path}")

    rows = load_dataset(dataset_path)
    if not rows:
        raise RuntimeError("Dataset is empty. Build dataset first.")

    texts = [r["text"] for r in rows]

    client = OpenAI()  # uses OPENAI_API_KEY env var
    embeddings = embed_texts(client, texts)

    # Save embeddings
    out_emb.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_emb, embeddings)

    # Save index metadata (id + dataset + source_file + text)
    with out_index.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"OK: {len(rows)} rows")
    print(f"Wrote: {out_index}")
    print(f"Wrote: {out_emb}  shape={embeddings.shape}")


if __name__ == "__main__":
    main()