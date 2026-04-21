"""Shared helpers for L2 validators (language sniffing, keyword extraction)."""

from __future__ import annotations

import re

_ES_HINTS = {
    "si", "porfi", "revisá", "buenas", "gracias", "porque", "como", "este",
    "agente", "muy", "más",
}
_EN_HINTS = {"the", "of", "and", "to", "is", "a", "in", "for", "with"}
_TOKEN_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)


def sniff_language(text: str) -> str | None:
    """Return 'en' | 'es' | None (unknown). Simple hint-word majority vote."""
    tokens = {t.lower() for t in _TOKEN_RE.findall(text)}
    if not tokens:
        return None
    es_hits = len(tokens & _ES_HINTS)
    en_hits = len(tokens & _EN_HINTS)
    if es_hits > en_hits and es_hits > 0:
        return "es"
    if en_hits > 0:
        return "en"
    return None


def extract_keywords(text: str, top_k: int = 20) -> list[str]:
    """Lowercased tokens ≥4 chars, unique, order-preserving."""
    seen: dict[str, None] = {}
    for t in _TOKEN_RE.findall(text.lower()):
        if len(t) >= 4 and t not in seen:
            seen[t] = None
    return list(seen.keys())[:top_k]
