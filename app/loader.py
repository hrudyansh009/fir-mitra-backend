from pathlib import Path

# FIR_AI/Backend/app/loader.py
# Resolve FIR_AI/data relative to this file:
# app/loader.py -> app -> Backend -> FIR_AI
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

def load_compiled_scst_texts() -> dict:
    compiled = DATA_ROOT / "law" / "compiled"
    en = compiled / "scst_act_en.txt"
    mr = compiled / "scst_act_mr.txt"

    if not en.exists():
        raise FileNotFoundError(f"Missing: {en}")
    if not mr.exists():
        raise FileNotFoundError(f"Missing: {mr}")

    return {
        "paths": {"en": str(en), "mr": str(mr)},
        "en": en.read_text(encoding="utf-8", errors="strict"),
        "mr": mr.read_text(encoding="utf-8", errors="strict"),
    }