"""Mechanical candidate-pattern extraction for Compost v0.1."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re

from .normalizer import iter_ngrams, normalise_apostrophes, tokens

# Used only to suppress n-grams that contain no lexical content at all.
# We intentionally keep this small and transparent rather than importing a
# model-derived stop-word inventory.
FUNCTION_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "he", "her", "hers", "him", "his", "i",
    "if", "in", "into", "is", "it", "its", "me", "my", "not", "of", "on",
    "or", "our", "ours", "she", "so", "that", "the", "their", "theirs",
    "them", "they", "this", "to", "us", "was", "we", "were", "what",
    "when", "where", "which", "who", "why", "will", "with", "you", "your",
}


@dataclass(frozen=True, order=True)
class Pattern:
    kind: str
    text: str


# Structural frames are intentionally generic and inspectable. Captured
# content spans are replaced by placeholders; source text is never stored in
# the pattern key.
_STRUCTURAL_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "contrast_not_but",
        re.compile(r"\bnot\s+(.{1,120}?)\s*,?\s+but\s+(.{1,120}?)(?:[.!?]|$)", re.I),
        "not <X> but <Y>",
    ),
    (
        "reframe_isnt_its",
        re.compile(r"\b(?:isn't|is not)\s+(.{1,120}?)(?:[.!?;:,]|\s+)\s+(?:it'?s|it is)\s+(.{1,120}?)(?:[.!?]|$)", re.I),
        "isn't <X> it's <Y>",
    ),
    (
        "reframe_about",
        re.compile(r"\b(?:isn't|is not)\s+about\s+(.{1,100}?)[.!?;:,]\s+(?:it'?s|it is)\s+about\s+(.{1,100}?)(?:[.!?]|$)", re.I),
        "isn't about <X> it's about <Y>",
    ),
    (
        "not_only_but_also",
        re.compile(r"\bnot\s+only\s+(.{1,120}?)\s+but\s+also\s+(.{1,120}?)(?:[.!?]|$)", re.I),
        "not only <X> but also <Y>",
    ),
    (
        "whether_or",
        re.compile(r"\bwhether\s+(.{1,100}?)\s+or\s+(.{1,100}?)(?:[.!?]|$)", re.I),
        "whether <X> or <Y>",
    ),
)


def _valid_ngram(gram: tuple[str, ...]) -> bool:
    if not gram:
        return False
    if all(token in FUNCTION_WORDS for token in gram):
        return False
    if all(token.isdigit() for token in gram):
        return False
    return True


def extract_patterns(sentence: str, min_n: int = 2, max_n: int = 5) -> Counter[Pattern]:
    """Return occurrence counts for candidate patterns in one sentence."""
    out: Counter[Pattern] = Counter()
    toks = tokens(sentence)

    for n in range(min_n, max_n + 1):
        for gram in iter_ngrams(toks, n):
            if _valid_ngram(gram):
                out[Pattern("ngram", " ".join(gram))] += 1

    normalised_sentence = normalise_apostrophes(sentence)
    for kind, rule, template in _STRUCTURAL_RULES:
        matches = list(rule.finditer(normalised_sentence))
        if matches:
            out[Pattern(kind, template)] += len(matches)

    return out
