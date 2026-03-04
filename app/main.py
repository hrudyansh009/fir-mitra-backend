# app/main.py

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.pipelines.krupaya_tapasa import krupaya_tapasa_pipeline
from app.any_rag import AnyIndex
from app.index_backend import SimpleIndexBackend


VERSION = "5.4.1"

app = FastAPI(title="FIR Mitra API", version=VERSION)

# ---------------- CORS ----------------
# Prototype/demo mode:
# - allow all origins
# - MUST keep allow_credentials=False with allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROOT ----------------
@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "FIR Mitra API",
        "status": "running",
        "version": VERSION,
        "docs": "/docs",
        "health": "/health",
    }

# ---------------- HEALTH ----------------
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": VERSION}

# ---------------- INDEX ----------------
any_index: Optional[AnyIndex] = None


def _resolve_index_path() -> Path:
    """
    Render sometimes runs with a different working directory.
    Resolve index path relative to this file, not cwd.
    app/main.py -> app -> Backend -> data/index/...
    """
    base = Path(__file__).resolve().parents[1]  # .../Backend/app
    candidate = base.parent / "data" / "index" / "scst_offences_index.jsonl"  # .../Backend/data/index/...
    # Allow override via env if needed
    env_path = os.getenv("SCST_INDEX_PATH")
    if env_path:
        return Path(env_path)
    return candidate


@app.on_event("startup")
def load_index() -> None:
    global any_index

    index_path = _resolve_index_path()

    if not index_path.exists():
        raise RuntimeError(f"Index file missing: {index_path}")

    backend = SimpleIndexBackend(index_path)
    any_index = AnyIndex(backend)

    print(f"✔ SC/ST index loaded: {len(backend.docs)} sections")


# ---------------- REQUEST MODEL ----------------
class TapasaRequest(BaseModel):
    text: str = Field(..., min_length=1)
    k: int = Field(default=7, ge=1, le=50)
    lang: str = Field(default="mr")


# ---------------- MAIN ENDPOINT ----------------
@app.post("/krupaya_tapasa")
def krupaya_tapasa(req: TapasaRequest):
    if any_index is None:
        raise HTTPException(status_code=500, detail="Index not loaded")

    try:
        return krupaya_tapasa_pipeline(
            text=req.text,
            any_index=any_index,
            k=req.k,
            lang=req.lang,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))