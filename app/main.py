# app/main.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.pipelines.krupaya_tapasa import krupaya_tapasa_pipeline
from app.any_rag import AnyIndex
from app.index_backend import SimpleIndexBackend


VERSION = "5.4.0"

app = FastAPI(title="FIR Mitra API", version=VERSION)

# ---------------- CORS ----------------
# For demo/prototype: allow all origins so browser preflight never blocks.
# After demo, lock this down to your exact Vercel domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # must be False when allow_origins=["*"]
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

# ---------------- LOAD INDEX ----------------
any_index: AnyIndex | None = None


@app.on_event("startup")
def load_index() -> None:
    global any_index

    index_path = Path("data/index/scst_offences_index.jsonl")
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