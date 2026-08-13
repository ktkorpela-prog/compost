"""Small, dependency-free text normalisation helpers for Compost v0.1."""

from __future__ import annotations

import re
from typing import Iterable

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:[\"'”’)]*)\s+(?=[A-Z0-9\"'“‘(])")
_PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n+")
_TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:[.,]\d+)*")


def normalise_apostrophes(text: str) -> str:
    return text.replace("’", "'").replace("‘", "'")


def normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(text: str) -> list[str]:
    return [normalise_whitespace(p) for p in _PARAGRAPH_BOUNDARY.split(text) if p.strip()]


def sentences(text: str) -> list[str]:
    """Segment prose conservatively without external NLP packages.

    This is intentionally simple. Sentence segmentation error is a known v0.1
    limitation and should be benchmarked before research claims are made.
    """
    text = normalise_whitespace(text)
    if not text:
        return []
    parts = _SENTENCE_BOUNDARY.split(text)
    return [p.strip() for p in parts if p.strip()]


def tokens(text: str) -> list[str]:
    text = normalise_apostrophes(text).lower()
    return [m.group(0) for m in _TOKEN_RE.finditer(text)]


def iter_ngrams(items: list[str], n: int) -> Iterable[tuple[str, ...]]:
    if n <= 0:
        return
    for i in range(0, len(items) - n + 1):
        yield tuple(items[i : i + n])
