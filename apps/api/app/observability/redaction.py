import re
from dataclasses import dataclass


PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)"),
    "api_key": re.compile(r"\b(?:sk|pk|api|key|token)[-_]?[A-Za-z0-9]{16,}\b", re.IGNORECASE),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
}


@dataclass
class Redaction:
    field_name: str
    pii_type: str
    redacted_count: int


def redact_text(value: str, field_name: str) -> tuple[str, list[Redaction]]:
    redactions: list[Redaction] = []
    redacted = value or ""
    for pii_type, pattern in PATTERNS.items():
        redacted, count = pattern.subn(f"[{pii_type.upper()}_REDACTED]", redacted)
        if count:
            redactions.append(Redaction(field_name, pii_type, count))
    return redacted, redactions


def redact_event_payload(payload: dict) -> tuple[dict, list[Redaction]]:
    clean = dict(payload)
    all_redactions: list[Redaction] = []
    for field in ["input_preview", "output_preview"]:
        clean[field], redactions = redact_text(str(clean.get(field) or ""), field)
        all_redactions.extend(redactions)
    return clean, all_redactions

