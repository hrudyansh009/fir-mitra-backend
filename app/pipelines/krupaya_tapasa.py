from __future__ import annotations

from typing import Dict, Any, List, Optional


def _norm_section(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize index record fields to a stable shape.
    Your JSONL may use different key names depending on builder versions.
    """
    # Common variants
    section_key = (
        rec.get("section_key")
        or rec.get("sectionKey")
        or rec.get("key")
        or rec.get("section_id")
        or rec.get("sectionId")
    )

    section_no = (
        rec.get("section_no")
        or rec.get("sectionNo")
        or rec.get("section")
        or rec.get("sec_no")
        or rec.get("secNo")
    )

    title = (
        rec.get("title")
        or rec.get("heading")
        or rec.get("name")
        or rec.get("section_title")
        or rec.get("sectionTitle")
    )

    rec_type = rec.get("type") or rec.get("law") or rec.get("category") or "scst"
    rec_lang = rec.get("lang") or rec.get("language") or "mr"

    # Clean strings
    if isinstance(section_key, str):
        section_key = section_key.strip() or None
    if isinstance(title, str):
        title = title.strip() or None

    # Cast section_no if string digit
    if isinstance(section_no, str):
        s = section_no.strip()
        if s.isdigit():
            section_no = int(s)
        else:
            section_no = None

    return {
        "section_key": section_key,
        "section_no": section_no,
        "title": title,
        "type": rec_type,
        "lang": rec_lang,
    }


def _build_suggestions(any_index: Any, k: int) -> List[Dict[str, Any]]:
    """
    Build top-k suggestions from the index.
    Demo mode: deterministic ordering (first valid k records).
    """
    suggestions: List[Dict[str, Any]] = []

    if not any_index:
        return suggestions

    # any_index could be list[dict] (your JSONL loader)
    if not isinstance(any_index, list):
        # Unknown type: fail safe
        return suggestions

    for rec in any_index:
        if len(suggestions) >= k:
            break
        if not isinstance(rec, dict):
            continue

        n = _norm_section(rec)

        # HARD FILTER: must have section_key (otherwise UI chips are useless)
        if not n["section_key"]:
            continue

        suggestions.append(
            {
                "id": len(suggestions),
                "score": round(0.90 - (len(suggestions) * 0.05), 2),
                "type": n["type"],
                "section_no": n["section_no"],
                "section_key": n["section_key"],
                "title": n["title"],
                "snippet": None,  # IMPORTANT: UI won't show snippet
                "lang": n["lang"],
            }
        )

    return suggestions


def _missing_fields(text: str) -> List[str]:
    missing: List[str] = []

    if "दिनांक" not in text:
        missing.append("date")

    if "वेळ" not in text:
        missing.append("time")

    if "ठिकाण" not in text:
        missing.append("place")

    if "आरोपी" not in text:
        missing.append("accused_name")

    if "फिर्यादी" not in text and "पीडित" not in text:
        missing.append("victim_name")

    return missing


def krupaya_tapasa_pipeline(any_index, text: str, k: int = 7, lang: str = "mr") -> Dict[str, Any]:
    """
    Demo-stable pipeline:
    - Keyword trigger for SCST-ish cases
    - Returns missing_words + suggested_sections
    - Never crashes, never returns null section_key
    """
    text = (text or "").strip()
    if not text:
        return {"missing_words": [], "suggested_sections": [], "debug": {"reason": "empty_text"}}

    # keyword trigger (demo)
    keywords = ["जातिवाचक", "अनुसूचित", "शिवीगाळ", "अपमान", "धमकी"]
    score = sum(1 for kw in keywords if kw in text)

    # If no SCST signal, still return missing fields but suggestions empty
    if score <= 0:
        return {
            "missing_words": _missing_fields(text),
            "suggested_sections": [],
            "debug": {"signal": 0, "lang": lang},
        }

    suggestions = _build_suggestions(any_index, k)

    return {
        "missing_words": _missing_fields(text),
        "suggested_sections": suggestions,
        "debug": {"signal": score, "k": k, "lang": lang, "suggestions": len(suggestions)},
    }