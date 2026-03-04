# app/main.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.pipelines.krupaya_tapasa import krupaya_tapasa_pipeline

APP_VERSION = os.getenv("APP_VERSION", "demo-krupaya+generator")

app = FastAPI(title="FIR-Mitra Backend", version=APP_VERSION)

# --- CORS (Render + Vercel) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global index (required by pipeline)
# -----------------------------
ANY_INDEX = None  # will be loaded at startup


def _try_load_any_index():
    """
    Try to load whatever index your pipeline expects.
    This function is defensive: it won't crash the app if the index isn't present.
    Adjust the import/loader name if you know the exact loader.
    """
    # Try a few common loader names/modules (use the one you actually have)
    candidates = [
        ("app.index.any_index", "load_any_index"),
        ("app.index.loader", "load_any_index"),
        ("app.index.loader", "load_index"),
        ("app.pipelines.krupaya_tapasa", "load_any_index"),
        ("app.pipelines.krupaya_tapasa", "load_index"),
    ]

    last_err = None
    for mod_name, fn_name in candidates:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                return fn()
        except Exception as e:
            last_err = e

    # If nothing found, return None (demo-safe; no 500)
    if last_err:
        print(f"[WARN] Could not load any_index (demo will return empty suggestions). Last error: {last_err}")
    else:
        print("[WARN] Could not load any_index (no loader found). Demo will return empty suggestions.")
    return None


@app.on_event("startup")
def startup():
    global ANY_INDEX
    ANY_INDEX = _try_load_any_index()
    if ANY_INDEX is None:
        print("[WARN] ANY_INDEX is None. krupaya_tapasa will return empty results instead of crashing.")
    else:
        print("[OK] ANY_INDEX loaded.")


# -----------------------------
# Health
# -----------------------------
@app.get("/")
def root():
    return {"name": "FIR-Mitra Backend", "version": APP_VERSION}


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "index_loaded": ANY_INDEX is not None}


# -----------------------------
# Krupaya Tapasa
# -----------------------------
class TapasaRequest(BaseModel):
    text: str
    k: int = 7
    lang: str = "mr"


class SuggestedSection(BaseModel):
    id: Optional[int] = None
    score: Optional[float] = None
    type: Optional[str] = None          # e.g. "scst"
    section_no: Optional[int] = None
    section_key: Optional[str] = None   # e.g. "SCST_10"
    title: Optional[str] = None         # Marathi title
    snippet: Optional[str] = None       # Marathi snippet (frontend will NOT display)
    lang: Optional[str] = None


class TapasaResponse(BaseModel):
    missing_words: List[str] = Field(default_factory=list)
    suggested_sections: List[SuggestedSection] = Field(default_factory=list)
    debug: Optional[Dict[str, Any]] = None


@app.post("/krupaya_tapasa", response_model=TapasaResponse)
def krupaya_tapasa(req: TapasaRequest):
    """
    Calls your pipeline.

    Expected dict shape:
      {
        "missing_words": [...],
        "suggested_sections": [...],
        "debug": {...}
      }
    """
    # DEMO-SAFE: if index didn't load, do not crash the whole endpoint
    if ANY_INDEX is None:
        return TapasaResponse(missing_words=[], suggested_sections=[], debug={"warn": "index_not_loaded"})

    # FIX: pass any_index (this is what your traceback demanded)
    result = (
        krupaya_tapasa_pipeline(any_index=ANY_INDEX, text=req.text, k=req.k, lang=req.lang)
        or {}
    )

    missing_words = result.get("missing_words") or []
    suggested = result.get("suggested_sections") or []
    debug = result.get("debug")

    return TapasaResponse(
        missing_words=list(missing_words),
        suggested_sections=suggested,
        debug=debug,
    )


# -----------------------------
# Auto FIR Generator
# -----------------------------
class GenerateFIRRequest(BaseModel):
    incident: str = Field(..., description="Short incident summary")
    lang: str = Field(default="mr")
    format_id: str = Field(default="FIR")
    sections: List[str] = Field(default_factory=list)
    fields: Dict[str, Any] = Field(default_factory=dict)


class GenerateFIRResponse(BaseModel):
    draft: str
    filled_fields: Dict[str, Any]
    missing_fields: List[str]


def build_fir_template_mr(fields: Dict[str, Any], sections: List[str], incident: str):
    required = ["date", "time", "place", "victim_name", "accused_name"]
    missing = [k for k in required if not str(fields.get(k, "")).strip()]

    date = fields.get("date", "________")
    time = fields.get("time", "________")
    place = fields.get("place", "________")
    victim = fields.get("victim_name", "________")
    accused = fields.get("accused_name", "________")
    witness = fields.get("witness_name", "________")

    sections_line = ", ".join(sections) if sections else "________"

    draft = f"""\
नाशिक शहर पोलीस ठाणे
एफ.आय.आर. (प्रथम माहिती अहवाल)

दिनांक: {date}
वेळ: {time}
ठिकाण: {place}

फिर्यादी / पीडित: {victim}
आरोपी: {accused}
साक्षीदार: {witness}

लागू कलमे: {sections_line}

घटनावर्णन:
{incident}

नोंद:
वरील माहिती माझ्या माहितीप्रमाणे खरी व बरोबर आहे.

स्वाक्षरी (फिर्यादी/पीडित): ____________
स्वाक्षरी (नोंद घेणारा अधिकारी): ____________
"""
    return draft, missing


@app.post("/generate_fir", response_model=GenerateFIRResponse)
def generate_fir(req: GenerateFIRRequest):
    incident = (req.incident or "").strip()
    if not incident:
        return GenerateFIRResponse(draft="", filled_fields=req.fields, missing_fields=["incident"])

    # demo-safe: MR only for now
    draft, missing = build_fir_template_mr(req.fields, req.sections, incident)
    return GenerateFIRResponse(draft=draft, filled_fields=req.fields, missing_fields=missing)