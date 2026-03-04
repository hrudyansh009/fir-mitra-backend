# app/pipelines/krupaya_tapasa.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _dedupe_by_id(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for h in hits:
        sid = h.get("id")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        out.append(h)
    return out


def analyze_missing_words_mr(text: str) -> List[str]:
    """
    BASELINE checks. Expand later.
    Goal: tell constable what is missing, not lecture them.
    """
    missing = []

    # Date
    if ("दि." not in text) and ("दिनांक" not in text) and ("/" not in text):
        missing.append("दिनांक/तारीख नाही (Date missing)")

    # Time
    if ("वाजता" not in text) and (":" not in text):
        missing.append("वेळ नाही (Time missing)")

    # Place
    if ("येथे" not in text) and ("ठिकाणी" not in text) and ("जवळ" not in text):
        missing.append("घटनास्थळ नाही (Place missing)")

    # Victim mention
    if ("पीडित" not in text) and ("फिर्यादी" not in text) and ("व्यक्ती" not in text):
        # very loose — refine later
        missing.append("पीडित/फिर्यादीचा उल्लेख अस्पष्ट आहे (Victim/complainant unclear)")

    return missing


def _pick_lang_text(meta: dict, fallback_text: str, lang: str) -> str:
    if lang == "mr":
        return meta.get("text_mr") or fallback_text
    return meta.get("text_en") or fallback_text


def _pick_lang_title(meta: dict, lang: str) -> Optional[str]:
    if lang == "mr":
        return meta.get("title_mr")
    return meta.get("title_en")


def krupaya_tapasa_pipeline(
    text: str,
    any_index,
    k: int = 7,
    filters: Optional[dict] = None,
    lang: str = "mr",
) -> Dict[str, Any]:
    # 1) Retrieve
    hits = any_index.search(query=text, k=k, filters=filters)

    # 2) Minimal filtering (keep docs with some text)
    filtered = [h for h in hits if (h.get("text") or (h.get("meta") or {}).get("text_mr") or (h.get("meta") or {}).get("text_en"))]

    # 3) Dedupe
    deduped = _dedupe_by_id(filtered)

    # 4) Missing words (Marathi baseline for now)
    missing_words = analyze_missing_words_mr(text) if lang == "mr" else []

    # 5) Build response sections
    suggested_sections: List[Dict[str, Any]] = []
    for h in deduped:
        meta = h.get("meta", {}) or {}
        chosen_text = _pick_lang_text(meta, h.get("text", ""), lang)
        title = _pick_lang_title(meta, lang)

        snippet = chosen_text or ""
        if len(snippet) > 260:
            snippet = snippet[:260] + "…"

        suggested_sections.append(
            {
                "id": h.get("id", 0),
                "score": h.get("score", 0.0),
                "type": meta.get("type"),
                "section_no": meta.get("section_no"),
                "section_key": meta.get("section_key"),
                "title": title,
                "snippet": snippet,
                "lang": lang,
            }
        )

    return {
        "missing_words": missing_words,
        "suggested_sections": suggested_sections,
        "debug": {
            "k": k,
            "lang": lang,
            "hits_count": len(hits),
            "filtered_count": len(filtered),
            "deduped_count": len(deduped),
        },
    }