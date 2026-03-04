# app/any_rag.py
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def _safe_int_from_any(value: Any, default: int = 0) -> int:
    """
    Accepts: 10, "10", "scst_section_10", "scst_section_01"
    Returns: int
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    s = str(value)
    m = re.search(r"(\d+)$", s)
    return int(m.group(1)) if m else default


class AnyIndex:
    """
    Backend adapter:
      backend.search(query, k, filters) -> one of:
        - list[(score, doc_dict)]
        - list[{"score":..., "doc": {...}}]
        - list[doc_dict]
    """

    def __init__(self, backend):
        self.backend = backend

    def search(self, query: str, k: int = 7, filters: Optional[dict] = None) -> List[Dict[str, Any]]:
        results = self.backend.search(query=query, k=k, filters=filters)

        hits: List[Dict[str, Any]] = []
        for item in results:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                score, doc = item
            elif isinstance(item, dict) and "doc" in item:
                score = item.get("score", 0.0)
                doc = item.get("doc") or {}
            elif isinstance(item, dict):
                score = item.get("score", 0.0)
                doc = item
            else:
                score = 0.0
                doc = {}

            meta = doc.get("meta", {}) or {}

            hit = {
                "score": float(score),
                "id": _safe_int_from_any(doc.get("id") or meta.get("section_no") or meta.get("section_key")),
                "text": doc.get("text", "") or "",
                "meta": {
                    "section_no": meta.get("section_no"),
                    "section_key": meta.get("section_key"),
                    "source_file": meta.get("source_file", None),
                    "type": meta.get("type", None),

                    # optional multilingual fields (we will use these)
                    "title_mr": meta.get("title_mr"),
                    "title_en": meta.get("title_en"),
                    "text_mr": meta.get("text_mr"),
                    "text_en": meta.get("text_en"),
                },
            }
            hits.append(hit)

        hits.sort(key=lambda h: h.get("score", 0.0), reverse=True)
        return hits