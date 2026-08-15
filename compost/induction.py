"""Mechanical structural-frame induction for Experiment 02.

Skeletons are mined from data under the frozen constraints of
``EXPERIMENT_02.md`` §3.2. No LLM is consulted and no hand-written frame list is
used; the four frames on ``main`` serve only as a recovery test.

Two window families, both confined to a single paragraph (§5):

``single``  each individual sentence          -> exposure denominator S
``pair``    each pair of adjacent sentences   -> exposure denominator P

Occurrences are attributed to the **minimal window containing them**: a span
lying entirely inside one sentence is a single-window occurrence, so pair
windows count only spans that genuinely cross the sentence boundary. Nothing is
therefore counted twice, and the two exposure types never share a denominator.

Implementation note, flagged for Phase 2 review: a sentence pair is skeletonised
per sentence and the two skeletons concatenated, rather than skeletonising the
joined string. Joining first would let rule 7 collapse a slot across the
sentence boundary, making "crosses the boundary" ill-defined. Concatenating
preserves a well-defined boundary index at the cost of never collapsing a slot
pair that straddles it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .canonical import NUM_SLOT, SLOT, is_anchor_token, skeletonise
from .normalizer import paragraphs, sentences

# Frozen qualification constraints (EXPERIMENT_02.md §3.2).
MIN_ANCHORS = 2
MIN_SLOTS = 1
MAX_SLOTS = 3
MAX_TOKENS = 12
MIN_TOKENS = 3  # 2 anchors + 1 slot is the shortest qualifying shape

WITHIN_SENTENCE = "within_sentence"
CROSS_SENTENCE = "cross_sentence"


@dataclass(frozen=True, order=True)
class Skeleton:
    """An induced structural frame. ``exposure`` names its denominator family."""

    exposure: str
    text: str


def _qualifies(span: list[str], anchors: frozenset[str]) -> bool:
    if not (MIN_TOKENS <= len(span) <= MAX_TOKENS):
        return False
    slots = sum(1 for t in span if t in (SLOT, NUM_SLOT))
    if not (MIN_SLOTS <= slots <= MAX_SLOTS):
        return False
    n_anchors = sum(1 for t in span if is_anchor_token(t, anchors))
    return n_anchors >= MIN_ANCHORS


def _spans(tokens: list[str], anchors: frozenset[str], boundary: int | None = None):
    """Yield qualifying contiguous spans.

    When ``boundary`` is given, only spans containing tokens from both sides of
    it are yielded, which is what makes a pair window count cross-sentence
    occurrences exclusively.
    """
    n = len(tokens)
    for start in range(n):
        for end in range(start + MIN_TOKENS, min(start + MAX_TOKENS, n) + 1):
            if boundary is not None and not (start < boundary < end):
                continue
            span = tokens[start:end]
            if _qualifies(span, anchors):
                yield " ".join(span)


def induce_single(sentence: str, anchors: frozenset[str]) -> Counter[Skeleton]:
    out: Counter[Skeleton] = Counter()
    for text in _spans(skeletonise(sentence, anchors), anchors):
        out[Skeleton(WITHIN_SENTENCE, text)] += 1
    return out


def induce_pair(first: str, second: str, anchors: frozenset[str]) -> Counter[Skeleton]:
    left = skeletonise(first, anchors)
    right = skeletonise(second, anchors)
    tokens = left + right
    out: Counter[Skeleton] = Counter()
    for text in _spans(tokens, anchors, boundary=len(left)):
        out[Skeleton(CROSS_SENTENCE, text)] += 1
    return out


@dataclass
class Exposure:
    """Denominators tracked separately, never pooled (EXPERIMENT_02.md §5)."""

    documents: int = 0
    paragraphs: int = 0
    sentences: int = 0          # S — exposure for within-sentence skeletons
    adjacent_pairs: int = 0     # P — exposure for cross-sentence skeletons

    def denominator(self, exposure: str) -> int:
        if exposure == WITHIN_SENTENCE:
            return self.sentences
        if exposure == CROSS_SENTENCE:
            return self.adjacent_pairs
        raise ValueError(f"unknown exposure family: {exposure!r}")


@dataclass
class StructuralStats:
    name: str
    exposure: Exposure = field(default_factory=Exposure)
    occurrences: Counter[Skeleton] = field(default_factory=Counter)
    documents_with: Counter[Skeleton] = field(default_factory=Counter)

    def rate_per_10k(self, skeleton: Skeleton) -> float:
        denom = self.exposure.denominator(skeleton.exposure)
        if denom == 0:
            return 0.0
        return self.occurrences[skeleton] / denom * 10_000

    def document_prevalence(self, skeleton: Skeleton) -> float:
        if self.exposure.documents == 0:
            return 0.0
        return self.documents_with[skeleton] / self.exposure.documents


def scan_document(text: str, anchors: frozenset[str], stats: StructuralStats) -> None:
    """Accumulate one document into ``stats``, paragraph by paragraph."""
    stats.exposure.documents += 1
    seen: set[Skeleton] = set()
    for paragraph in paragraphs(text):
        stats.exposure.paragraphs += 1
        sents = sentences(paragraph)
        if not sents:
            continue
        stats.exposure.sentences += len(sents)
        stats.exposure.adjacent_pairs += max(0, len(sents) - 1)
        for sentence in sents:
            found = induce_single(sentence, anchors)
            stats.occurrences.update(found)
            seen.update(found)
        for i in range(len(sents) - 1):
            found = induce_pair(sents[i], sents[i + 1], anchors)
            stats.occurrences.update(found)
            seen.update(found)
    for skeleton in seen:
        stats.documents_with[skeleton] += 1


def scan_texts(name: str, texts, anchors: frozenset[str]) -> StructuralStats:
    stats = StructuralStats(name=name)
    for text in texts:
        scan_document(text, anchors, stats)
    return stats


def group_by_exposure(skeletons) -> dict[str, list[Skeleton]]:
    """Partition skeletons by exposure family.

    Callers must report the families separately: within-sentence and
    cross-sentence rates are computed against different denominators and are not
    comparable, so ranking them in one ordering is prohibited (§5).
    """
    grouped: dict[str, list[Skeleton]] = {WITHIN_SENTENCE: [], CROSS_SENTENCE: []}
    for skeleton in skeletons:
        grouped[skeleton.exposure].append(skeleton)
    return grouped
