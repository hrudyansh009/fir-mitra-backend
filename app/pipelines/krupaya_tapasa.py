from __future__ import annotations
from typing import Dict, Any, List


def _norm_section(rec: Dict[str, Any]) -> Dict[str, Any]:

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

    rec_type = rec.get("type") or rec.get("law") or rec.get("category") or "law"
    rec_lang = rec.get("lang") or rec.get("language") or "mr"

    if isinstance(section_key, str):
        section_key = section_key.strip() or None

    if isinstance(title, str):
        title = title.strip() or None

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


def _rule_based_sections(text: str) -> List[Dict[str, Any]]:

    suggestions: List[Dict[str, Any]] = []

    def has_any(words):
        return any(w in text for w in words)

    # SC/ST insult rule
    if (
        has_any(["अनुसूचित", "जातिवाचक", "दलित"])
        and has_any(["शिवीगाळ", "अपमान"])
        and has_any(["सार्वजनिक", "लोकांसमोर"])
    ):
        suggestions.append(
            {
                "id": 0,
                "score": 0.95,
                "type": "scst",
                "section_no": "3(1)(r)",
                "section_key": "SC/ST Act 3(1)(r)",
                "title": "Intentional insult to humiliate SC/ST person in public",
                "snippet": None,
                "lang": "mr",
            }
        )

    # Criminal intimidation
    if has_any(["धमकी", "मारून टाकीन", "जीव मारण्याची धमकी"]):
        suggestions.append(
            {
                "id": 1,
                "score": 0.90,
                "type": "ipc",
                "section_no": "506",
                "section_key": "IPC 506",
                "title": "Criminal intimidation",
                "snippet": None,
                "lang": "mr",
            }
        )

    # Theft
    if has_any(["चोरी", "दागिने", "रोख", "कपाटातून"]):
        suggestions.append(
            {
                "id": 2,
                "score": 0.90,
                "type": "ipc",
                "section_no": "379",
                "section_key": "IPC 379",
                "title": "Theft",
                "snippet": None,
                "lang": "mr",
            }
        )

    return suggestions


def krupaya_tapasa_pipeline(any_index, text: str, k: int = 7, lang: str = "mr") -> Dict[str, Any]:

    text = (text or "").strip()

    if not text:
        return {
            "missing_words": [],
            "suggested_sections": [],
            "debug": {"reason": "empty_text"},
        }

    missing = _missing_fields(text)

    # RULE BASED SECTION DETECTION
    suggestions = _rule_based_sections(text)

    return {
        "missing_words": missing,
        "suggested_sections": suggestions,
        "debug": {
            "rules_triggered": len(suggestions),
            "lang": lang,
        },
    }