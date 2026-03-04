import unicodedata

def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = " ".join(s.split())
    return s