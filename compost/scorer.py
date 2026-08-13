"""Corpus aggregation and comparison metrics for Compost v0.1."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .extractor import Pattern, extract_patterns
from .normalizer import paragraphs, sentences, tokens


@dataclass
class CorpusStats:
    name: str
    documents: int = 0
    paragraphs: int = 0
    sentences: int = 0
    tokens: int = 0
    occurrences: Counter[Pattern] = field(default_factory=Counter)
    documents_with: Counter[Pattern] = field(default_factory=Counter)

    def sentence_rate(self, pattern: Pattern) -> float:
        if self.sentences == 0:
            return 0.0
        return self.occurrences[pattern] / self.sentences

    def per_10k_sentences(self, pattern: Pattern) -> float:
        return self.sentence_rate(pattern) * 10_000

    def document_prevalence(self, pattern: Pattern) -> float:
        if self.documents == 0:
            return 0.0
        return self.documents_with[pattern] / self.documents


def scan_texts(name: str, texts: Iterable[str]) -> CorpusStats:
    stats = CorpusStats(name=name)
    for text in texts:
        stats.documents += 1
        ps = paragraphs(text)
        ss = sentences(text)
        stats.paragraphs += len(ps)
        stats.sentences += len(ss)
        stats.tokens += len(tokens(text))

        seen_in_document: set[Pattern] = set()
        for sentence in ss:
            extracted = extract_patterns(sentence)
            stats.occurrences.update(extracted)
            seen_in_document.update(extracted.keys())

        for pattern in seen_in_document:
            stats.documents_with[pattern] += 1
    return stats


def scan_directory(path: str | Path, name: str) -> CorpusStats:
    root = Path(path)
    files = sorted(p for p in root.rglob("*.txt") if p.is_file())
    if not files:
        raise ValueError(f"No .txt documents found in {root}")
    return scan_texts(name, (p.read_text(encoding="utf-8") for p in files))


def smoothed_rate(occurrences: int, denominator: int, correction: float = 0.5) -> float:
    """Rate with a small continuity correction for finite zero counts.

    This is an exploratory stabiliser, not a statistical inference model.
    """
    if denominator < 0:
        raise ValueError("denominator cannot be negative")
    return (occurrences + correction) / (denominator + 1.0)


def smoothed_lift(target_occ: int, target_n: int, reference_occ: int, reference_n: int) -> float:
    target = smoothed_rate(target_occ, target_n)
    reference = smoothed_rate(reference_occ, reference_n)
    return target / reference
