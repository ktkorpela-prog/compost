"""Structural canonicalisation and skeletonisation for Experiment 02.

Implements the frozen normalisation rules of ``EXPERIMENT_02.md`` §3.2, in the
fixed order specified there. Standard library only.

This module is used **only** by structural induction. Lexical n-gram extraction
in :mod:`compost.extractor` is untouched and continues to see original surface
forms; see :func:`assert_lexical_unaffected` in the tests.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

SLOT = "<X>"
NUM_SLOT = "<NUM>"
KEPT_PUNCTUATION = frozenset(".!?,;:")

LEXICON_PATH = Path(__file__).resolve().parent / "lexicon" / "structural_anchors_v1.txt"

# Rule 4, structural only. Every expansion below is deterministic and has
# exactly one reading, so no interpretation is introduced.
NEGATIVE_CONTRACTIONS: dict[str, tuple[str, ...]] = {
    "isn't": ("is", "not"),
    "aren't": ("are", "not"),
    "wasn't": ("was", "not"),
    "weren't": ("were", "not"),
    "don't": ("do", "not"),
    "doesn't": ("does", "not"),
    "didn't": ("did", "not"),
    "won't": ("will", "not"),
    "can't": ("can", "not"),
    "couldn't": ("could", "not"),
    "shouldn't": ("should", "not"),
    "wouldn't": ("would", "not"),
}

# Ambiguous between "is" and "has". Deliberately left unresolved: resolving them
# would require a judgement this pipeline refuses to make.
AMBIGUOUS_CONTRACTIONS = frozenset({"it's", "that's", "there's", "here's"})

_TOKEN_RE = re.compile(
    r"[A-Za-z]+(?:'[A-Za-z]+)?"      # words, apostrophes kept
    r"|\d+(?:[.,]\d+)*"              # numerals
    r"|[.!?,;:]"                     # retained punctuation
)


def load_anchors(path: Path | str = LEXICON_PATH) -> frozenset[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip())


def anchors_sha256(path: Path | str = LEXICON_PATH) -> str:
    """Full-file SHA-256 of the anchor set, for recording in result artifacts."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def structural_tokens(text: str) -> list[str]:
    """Rules 1-3 plus tokenisation, with rule 8 punctuation retention.

    Punctuation outside ``.!?,;:`` is discarded by never being emitted.
    """
    text = unicodedata.normalize("NFKC", text)                       # rule 1
    text = text.replace("’", "'").replace("‘", "'")        # rule 2
    text = text.lower()                                              # rule 3
    return _TOKEN_RE.findall(text)


def canonicalise_negatives(tokens: list[str]) -> list[str]:
    """Rule 4, structural only.

    Unambiguous negative contractions expand so that equivalent frames do not
    split into two skeletons. Ambiguous contractions are returned untouched.
    """
    out: list[str] = []
    for token in tokens:
        expansion = NEGATIVE_CONTRACTIONS.get(token)
        if expansion is None:
            out.append(token)
        else:
            out.extend(expansion)
    return out


def _is_numeral(token: str) -> bool:
    return token[0].isdigit()


def collapse_slots(tokens: list[str]) -> list[str]:
    """Rule 7: runs of the same slot collapse to one occurrence of that slot."""
    out: list[str] = []
    for token in tokens:
        if token in (SLOT, NUM_SLOT) and out and out[-1] == token:
            continue
        out.append(token)
    return out


def skeletonise(text: str, anchors: frozenset[str]) -> list[str]:
    """Apply the full frozen rule order and return the skeleton token sequence."""
    tokens = canonicalise_negatives(structural_tokens(text))
    mapped: list[str] = []
    for token in tokens:
        if token in KEPT_PUNCTUATION:
            mapped.append(token)                                     # rule 8
        elif _is_numeral(token):
            mapped.append(NUM_SLOT)                                  # rule 5
        elif token in anchors:
            mapped.append(token)                                     # rule 6, anchor survives
        else:
            mapped.append(SLOT)                                      # rule 6, content -> slot
    return collapse_slots(mapped)                                    # rule 7


def is_anchor_token(token: str, anchors: frozenset[str]) -> bool:
    """Slots and punctuation are never anchors, whatever the lexicon contains."""
    return token in anchors and token not in KEPT_PUNCTUATION
