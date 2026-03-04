import json
from pathlib import Path
import numpy as np
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]  # FIR_AI
INDEX = ROOT / "data" / "index"

def _load_jsonl(path: Path):
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out

class RAGIndex:
    def __init__(self, lang: str, api_key: str, model: str = "text-embedding-3-small"):
        self.lang = lang
        self.model = model
        self.client = OpenAI(api_key=api_key)

        self.meta_path = INDEX / f"scst_{lang}_index.jsonl"
        self.emb_path = INDEX / f"scst_{lang}_embeddings.npy"

        if not self.meta_path.exists() or not self.emb_path.exists():
            raise FileNotFoundError(
                f"Missing index files for {lang}. Run train_scst_index.py first."
            )

        self.meta = _load_jsonl(self.meta_path)
        self.emb = np.load(self.emb_path)  # [N, D]
        self.emb = self.emb / (np.linalg.norm(self.emb, axis=1, keepdims=True) + 1e-9)

    def _embed_query(self, q: str):
        resp = self.client.embeddings.create(model=self.model, input=[q])
        v = np.array(resp.data[0].embedding, dtype=np.float32)
        v = v / (np.linalg.norm(v) + 1e-9)
        return v

    def search(self, q: str, k: int = 5):
        v = self._embed_query(q)
        sims = self.emb @ v
        idx = np.argsort(-sims)[:k]
        return [
            {
                "score": float(sims[i]),
                "id": int(self.meta[i]["id"]),
                "text": self.meta[i]["text"],
                "lang": self.lang,
            }
            for i in idx
        ]