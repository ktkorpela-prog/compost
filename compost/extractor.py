"""Mechanical candidate-pattern extraction for Compost v0.1."""

from __future__ import annotations

from collections import Counter, defaultdict
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
)

# Withdrawn frames, kept documented rather than silently deleted.
#
# "whether <X> or <Y>" was removed before the first signal-validation run.
# It is ordinary English subordination, not a rhetorical construction: it
# matches indirect questions ("we asked whether it was ready or not"),
# disjunctive complements and plain conditionals. Its prevalence would be
# dominated by grammar rather than by style, so it would add denominator noise
# to every corpus equally and rank on lift only through sampling variation.
#
# It is not replaced by a hand-curated phrase list. A frame earns readmission
# only if it can be constrained to a genuinely rhetorical shape.
WITHDRAWN_STRUCTURAL_RULES: tuple[str, ...] = ("whether_or",)


def _valid_ngram(gram: tuple[str, ...]) -> bool:
    if not gram:
        return False
    if all(token in FUNCTION_WORDS for token in gram):
        return False
    if all(token.isdigit() for token in gram):
        return False
    return True


def extract_ngrams(sentence: str, min_n: int = 2, max_n: int = 5) -> Counter[Pattern]:
    """Return n-gram occurrence counts for one sentence.

    N-grams never span a sentence boundary. Only structural frames do.
    """
    out: Counter[Pattern] = Counter()
    toks = tokens(sentence)
    for n in range(min_n, max_n + 1):
        for gram in iter_ngrams(toks, n):
            if _valid_ngram(gram):
                out[Pattern("ngram", " ".join(gram))] += 1
    return out


def _extraction_units(sents: list[str]) -> list[tuple[str, int]]:
    """Return (text, absolute_offset) units to scan for structural frames.

    Two unit families, both confined to the caller's segment:

    1. each individual sentence;
    2. each pair of *directly adjacent* sentences.

    Non-adjacent sentences are never combined, so a frame cannot be
    manufactured by stitching together distant text.
    """
    offsets: list[int] = []
    pos = 0
    for s in sents:
        offsets.append(pos)
        pos += len(s) + 1  # +1 for the single space used to join units

    units = [(s, offsets[i]) for i, s in enumerate(sents)]
    units += [
        (f"{sents[i]} {sents[i + 1]}", offsets[i]) for i in range(len(sents) - 1)
    ]
    return units


def extract_structural(sents: list[str]) -> Counter[Pattern]:
    """Count structural frames over one segment's sentences.

    A frame occurring inside a single sentence is also visible inside the
    adjacent pair that contains that sentence. Counting both would inflate the
    occurrence by the number of extraction paths that happened to see it, so
    matches are resolved in absolute segment coordinates and overlapping
    matches of the same frame collapse to one occurrence.
    """
    out: Counter[Pattern] = Counter()
    if not sents:
        return out

    spans_by_pattern: dict[Pattern, list[tuple[int, int]]] = defaultdict(list)
    for unit_text, unit_start in _extraction_units(sents):
        # Length-preserving: apostrophe folding is a 1:1 character swap, so
        # match offsets remain valid segment coordinates.
        normalised = normalise_apostrophes(unit_text)
        for kind, rule, template in _STRUCTURAL_RULES:
            for match in rule.finditer(normalised):
                spans_by_pattern[Pattern(kind, template)].append(
                    (unit_start + match.start(), unit_start + match.end())
                )

    for pattern, spans in spans_by_pattern.items():
        # Earliest first, longest first on ties, then greedily keep only
        # mutually non-overlapping matches.
        spans.sort(key=lambda span: (span[0], -span[1]))
        kept: list[tuple[int, int]] = []
        for start, end in spans:
            if any(start < k_end and end > k_start for k_start, k_end in kept):
                continue
            kept.append((start, end))
        out[pattern] += len(kept)

    return out


def extract_segment_patterns(
    sents: list[str], min_n: int = 2, max_n: int = 5
) -> Counter[Pattern]:
    """Return all candidate patterns for one segment (e.g. one paragraph)."""
    out: Counter[Pattern] = Counter()
    for sentence in sents:
        out.update(extract_ngrams(sentence, min_n, max_n))
    out.update(extract_structural(sents))
    return out


def extract_patterns(sentence: str, min_n: int = 2, max_n: int = 5) -> Counter[Pattern]:
    """Return candidate patterns for a single isolated sentence.

    Retained for single-sentence inspection. Corpus scans use
    ``extract_segment_patterns`` so that cross-sentence frames are visible.
    """
    return extract_segment_patterns([sentence], min_n, max_n)
