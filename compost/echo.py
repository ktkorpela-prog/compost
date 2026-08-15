"""Prompt/title echo detection for Experiment 02 (``EXPERIMENT_02.md`` §4).

Models saw a prompt; human sources did not. Uncontrolled, this manufactures
spurious lift.

Echo sets are a property of the **source**, not of the document, and are applied
symmetrically to the AI arm and its matched human control. RAID's titles derive
from the human source text, so title tokens recur in human documents; stripping
echoes from the AI arm alone would bias lift downward.

Detection runs at both representation levels. Structural echo cannot be reduced
to lexical matching: a prompt reading "write a news article titled X" and a
generation opening "write a blog post titled Y" share no 2-5-gram, yet collapse
to the same skeleton.
"""

from __future__ import annotations

from dataclasses import dataclass

from .canonical import skeletonise
from .induction import _spans
from .normalizer import iter_ngrams, tokens

LEXICAL_MIN_N = 2
LEXICAL_MAX_N = 5

# A pattern whose AI-arm occurrences are mostly echo is an artifact of RAID's
# elicitation design, not evidence about writing.
PROMPT_DERIVED_FRACTION = 0.5


@dataclass(frozen=True)
class EchoSets:
    """Per-source echo material, built once and applied to both arms."""

    lexical: frozenset[str]
    structural: frozenset[str]

    def contains_lexical(self, pattern_text: str) -> bool:
        return pattern_text in self.lexical

    def contains_structural(self, skeleton_text: str) -> bool:
        return skeleton_text in self.structural


def build_echo_sets(prompt: str, title: str, anchors: frozenset[str]) -> EchoSets:
    material = f"{title or ''} {prompt or ''}".strip()

    lexical: set[str] = set()
    toks = tokens(material)
    for n in range(LEXICAL_MIN_N, LEXICAL_MAX_N + 1):
        for gram in iter_ngrams(toks, n):
            lexical.add(" ".join(gram))

    structural = set(_spans(skeletonise(material, anchors), anchors))
    return EchoSets(frozenset(lexical), frozenset(structural))


@dataclass
class EchoCounts:
    """Full and echo-excluded counts, so the correction's size stays visible."""

    total: int = 0
    echoing: int = 0

    @property
    def primary(self) -> int:
        """Occurrences after symmetric echo exclusion — the primary metric."""
        return self.total - self.echoing

    @property
    def echo_fraction(self) -> float:
        return self.echoing / self.total if self.total else 0.0

    @property
    def prompt_derived(self) -> bool:
        return self.echo_fraction > PROMPT_DERIVED_FRACTION


def partition_lexical(pattern_text: str, occurrences: int, echo: EchoSets) -> EchoCounts:
    """Occurrences of one lexical pattern in one document against its source."""
    echoing = occurrences if echo.contains_lexical(pattern_text) else 0
    return EchoCounts(total=occurrences, echoing=echoing)


def partition_structural(skeleton_text: str, occurrences: int, echo: EchoSets) -> EchoCounts:
    echoing = occurrences if echo.contains_structural(skeleton_text) else 0
    return EchoCounts(total=occurrences, echoing=echoing)
