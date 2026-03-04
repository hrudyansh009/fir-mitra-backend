import os
import re
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np

# Optional deps (only used if files exist)
try:
    import pdfplumber  # type: ignore
except Exception:
    pdfplumber = None

try:
    from docx import Document  # type: ignore
except Exception:
    Document = None

from openai import OpenAI


# ----------------------------
# Config
# ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CORPUS_DIR = os.path.join(DATA_DIR, "corpus")
INDEX_DIR = os.path.join(DATA_DIR, "index")

DEFAULT_EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

MAX_CHARS = 1400
MIN_CHARS = 120
OVERLAP_CHARS = 150

BATCH_SIZE = 64
SLEEP_BETWEEN_BATCHES_SEC = 0.2


@dataclass
class Doc:
    id: str
    text: str
    meta: Dict


# ----------------------------
# Helpers
# ----------------------------

def require_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENAI_API_KEY not set")
    return key


def norm_ws(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def chunk_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> List[str]:
    text = norm_ws(text)
    if len(text) <= max_chars:
        return [text] if len(text) >= MIN_CHARS else []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)

        cut = text.rfind("\n\n", start, end)
        if cut == -1 or cut <= start + 200:
            cut = end

        chunk = text[start:cut].strip()
        if len(chunk) >= MIN_CHARS:
            chunks.append(chunk)

        if cut >= len(text):
            break
        start = max(0, cut - overlap)

    return chunks


def read_utf8(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_txt_file(path: str, prefix_id: str) -> List[Doc]:
    raw = read_utf8(path)
    chunks = chunk_text(raw)
    out: List[Doc] = []
    for i, c in enumerate(chunks, 1):
        out.append(
            Doc(
                id=f"{prefix_id}::chunk_{i:03d}",
                text=c,
                meta={"source_file": path, "type": "txt"},
            )
        )
    return out


def load_jsonl_file(path: str, prefix_id: str) -> List[Doc]:
    out: List[Doc] = []
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            doc_id = obj.get("id")
            if doc_id is None:
                doc_id = f"{prefix_id}::line_{ln:05d}"

            # ✅ force string ids in the index file; AnyIndex can still cast if it wants
            doc_id = str(doc_id)

            text = str(obj.get("text") or obj.get("content") or "")
            meta = obj.get("meta") or {}
            if not isinstance(meta, dict):
                meta = {"meta": meta}

            # ✅ AnyIndex expects source_file
            if "source_file" not in meta:
                meta["source_file"] = path

            meta.update({"type": "jsonl"})

            text = norm_ws(text)
            if len(text) < MIN_CHARS:
                continue

            out.append(Doc(id=doc_id, text=text, meta=meta))
    return out


def load_docx_file(path: str, prefix_id: str) -> List[Doc]:
    if Document is None:
        print(f"NOTE: python-docx not installed; skipping docx: {path}")
        return []
    doc = Document(path)
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    chunks = chunk_text(text)
    out: List[Doc] = []
    for i, c in enumerate(chunks, 1):
        out.append(
            Doc(
                id=f"{prefix_id}::chunk_{i:03d}",
                text=c,
                meta={"source_file": path, "type": "docx"},
            )
        )
    return out


def load_pdf_file(path: str, prefix_id: str) -> List[Doc]:
    if pdfplumber is None:
        print(f"NOTE: pdfplumber not installed; skipping pdf: {path}")
        return []
    text_parts: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = (page.extract_text() or "").strip()
            if t:
                text_parts.append(t)

    text = "\n\n".join(text_parts).strip()
    if not text:
        print(f"NOTE: skipped scanned PDF (no embedded text): {path}")
        return []

    chunks = chunk_text(text)
    out: List[Doc] = []
    for i, c in enumerate(chunks, 1):
        out.append(
            Doc(
                id=f"{prefix_id}::chunk_{i:03d}",
                text=c,
                meta={"source_file": path, "type": "pdf"},
            )
        )
    return out


def scan_corpus_dir(dir_path: str, dataset_name: str) -> List[Doc]:
    docs: List[Doc] = []
    if not os.path.exists(dir_path):
        print(f"NOTE: corpus dir missing: {dir_path}")
        return docs

    for root, _, files in os.walk(dir_path):
        for fn in files:
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, dir_path).replace("\\", "/")
            prefix_id = f"{dataset_name}::{rel}"

            ext = os.path.splitext(fn.lower())[1]
            if ext == ".txt":
                docs.extend(load_txt_file(path, prefix_id))
            elif ext == ".jsonl":
                docs.extend(load_jsonl_file(path, dataset_name))
            elif ext == ".docx":
                docs.extend(load_docx_file(path, prefix_id))
            elif ext == ".pdf":
                docs.extend(load_pdf_file(path, prefix_id))
            else:
                pass

    return docs


def embed_texts(client: OpenAI, texts: List[str], model: str) -> np.ndarray:
    vectors: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=model, input=batch)
        vectors.extend([d.embedding for d in resp.data])
        time.sleep(SLEEP_BETWEEN_BATCHES_SEC)
    return np.array(vectors, dtype=np.float32)


def write_index(dataset_name: str, docs: List[Doc], embeddings: np.ndarray) -> Tuple[str, str]:
    os.makedirs(INDEX_DIR, exist_ok=True)
    idx_path = os.path.join(INDEX_DIR, f"{dataset_name}_index.jsonl")
    emb_path = os.path.join(INDEX_DIR, f"{dataset_name}_embeddings.npy")

    with open(idx_path, "w", encoding="utf-8") as w:
        for d in docs:
            meta_out = dict(d.meta or {})
            # ✅ HARD GUARANTEE: AnyIndex expects this
            if "source_file" not in meta_out:
                meta_out["source_file"] = ""

            w.write(
                json.dumps(
                    {"id": d.id, "text": d.text, "meta": meta_out},
                    ensure_ascii=False,
                )
                + "\n"
            )

    np.save(emb_path, embeddings)
    return idx_path, emb_path


# ----------------------------
# Dataset definitions
# ----------------------------

def dataset_sources() -> Dict[str, Dict]:
    """
    scst_offences is REQUIRED for /krupaya_tapasa suggestions.
    """
    return {
        "scst": {
            "type": "dir",
            "path": os.path.join(CORPUS_DIR, "scst"),
        },
        "templates": {
            "type": "dir",
            "path": os.path.join(DATA_DIR, "templates"),
        },
        "examples": {
            "type": "dir",
            "path": os.path.join(CORPUS_DIR, "examples"),
        },
        "scst_offences": {
            "type": "jsonl",
            "path": os.path.join(CORPUS_DIR, "scst_offences", "offences.jsonl"),
        },
    }


def load_dataset_docs(name: str, cfg: Dict) -> List[Doc]:
    typ = cfg["type"]
    path = cfg["path"]

    if typ == "dir":
        return scan_corpus_dir(path, name)

    if typ == "jsonl":
        if not os.path.exists(path):
            print(f"NOTE: dataset '{name}' missing file: {path}")
            return []
        return load_jsonl_file(path, name)

    raise ValueError(f"Unknown dataset type: {typ}")


# ----------------------------
# Main
# ----------------------------

def main():
    require_key()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = DEFAULT_EMBED_MODEL

    srcs = dataset_sources()

    import sys
    targets = sys.argv[1:]
    if targets:
        bad = [t for t in targets if t not in srcs]
        if bad:
            raise SystemExit(f"Unknown datasets: {bad}. Known: {list(srcs.keys())}")
    else:
        targets = list(srcs.keys())

    for ds in targets:
        docs = load_dataset_docs(ds, srcs[ds])

        if not docs:
            print(f"{ds}: 0 docs (skipped)")
            continue

        print(f"{ds}: {len(docs)}/{len(docs)}")
        texts = [d.text for d in docs]
        embeddings = embed_texts(client, texts, model)

        idx_path, emb_path = write_index(ds, docs, embeddings)
        print(f"Wrote: {idx_path}")
        print(f"Wrote: {emb_path}")

    print("DONE")


if __name__ == "__main__":
    main()