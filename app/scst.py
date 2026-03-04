from dataclasses import dataclass
from .utils import normalize_text

IDENTITY_TERMS = [
    "अनुसूचित जाती", "अनुसूचित जमाती", "दलित",
    "scheduled caste", "scheduled tribe", "sc", "st", "dalit"
]
PUBLIC_CONTEXT = [
    "सार्वजनिक", "रस्त्यावर", "चौकात", "बाजार", "पोलीस स्टेशन",
    "public", "in public", "road", "street", "market", "police station"
]
ABUSE_CONTEXT = [
    "जातिवाचक", "शिवीगाळ", "अपमान", "हिणवले",
    "casteist", "slur", "abuse", "insult", "humiliate"
]

@dataclass
class SCSTSignalResult:
    is_scst: bool
    has_identity: bool
    has_public: bool
    has_abuse: bool
    reasons: list[str]

def _contains_any(text: str, terms: list[str]) -> bool:
    t = text.lower()
    return any(term.lower() in t for term in terms)

def scst_signal(text: str) -> SCSTSignalResult:
    t = normalize_text(text)

    has_identity = _contains_any(t, IDENTITY_TERMS)
    has_public   = _contains_any(t, PUBLIC_CONTEXT)
    has_abuse    = _contains_any(t, ABUSE_CONTEXT)

    reasons = []
    if has_identity: reasons.append("identity_terms")
    if has_public:   reasons.append("public_context")
    if has_abuse:    reasons.append("abuse_context")

    return SCSTSignalResult(
        is_scst = has_identity and has_public and has_abuse,
        has_identity=has_identity,
        has_public=has_public,
        has_abuse=has_abuse,
        reasons=reasons
    )