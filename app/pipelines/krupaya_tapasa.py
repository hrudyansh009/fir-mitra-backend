import re
from typing import Dict, Any, List


def krupaya_tapasa_pipeline(any_index, text: str, k: int = 7, lang: str = "mr") -> Dict[str, Any]:

    if not text:
        return {
            "missing_words": [],
            "suggested_sections": []
        }

    suggestions: List[Dict[str, Any]] = []

    # simple keyword matching for demo stability
    keywords = [
        "जातिवाचक",
        "अनुसूचित",
        "शिवीगाळ",
        "अपमान",
        "धमकी"
    ]

    score = 0
    for kw in keywords:
        if kw in text:
            score += 1

    # if relevant keywords found → suggest SCST sections
    if score > 0 and any_index:

        for i, rec in enumerate(any_index[:k]):
            suggestions.append({
                "id": i,
                "score": 0.9 - i * 0.05,
                "type": rec.get("type"),
                "section_no": rec.get("section_no"),
                "section_key": rec.get("section_key"),
                "title": rec.get("title"),
                "snippet": None,
                "lang": rec.get("lang")
            })

    # simple missing fields detector
    missing = []

    if "दिनांक" not in text:
        missing.append("date")

    if "वेळ" not in text:
        missing.append("time")

    if "ठिकाण" not in text:
        missing.append("place")

    if "आरोपी" not in text:
        missing.append("accused_name")

    if "फिर्यादी" not in text:
        missing.append("victim_name")

    return {
        "missing_words": missing,
        "suggested_sections": suggestions
    }