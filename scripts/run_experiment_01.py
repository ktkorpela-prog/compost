"""Experiment 01 — signal validation.

Hypothesis under test:

    Can automatically extracted language patterns recur at elevated rates
    across *independent* AI samples while remaining less prevalent in
    comparable human writing?

This is not an authorship-detection experiment. Nothing here decides whether a
document was written by AI, and no combined "AI probability" or saturation
score is produced.

Method
------
1. Candidates are discovered using the AI **discovery** partition only. The
   selection rule below reads no human and no validation statistics, so the
   validation comparison cannot be tuned by construction.
2. The candidate set is frozen.
3. Those exact candidates are then measured on the AI validation partition,
   the human baseline, and the independent HC3 replication pair.

Discovery and validation draw from disjoint generating models, so replication
means a pattern survived a change of AI system rather than a change of topic.

Usage
-----
    python scripts/run_experiment_01.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compost.extractor import Pattern  # noqa: E402
from compost.scorer import CorpusStats, scan_directory, smoothed_lift  # noqa: E402

CORPORA = ROOT / "corpora"

# ---------------------------------------------------------------------------
# Thresholds.
#
# PREREGISTERED_* were fixed before the corpus existed and before any statistic
# was computed. They yielded ZERO candidates: the most widespread pattern in the
# discovery partition reaches 19.4% document prevalence, so a 25% floor was
# unreachable by construction. That null is reported as the primary result.
#
# EXPLORATORY_* were chosen afterwards from the discovery partition's own
# prevalence distribution. This is post-hoc and is labelled as such everywhere
# it appears. It reads no validation and no human statistic, so the
# discovery -> validation separation is preserved: what changed is which
# candidates were nominated, never how they were judged.
# ---------------------------------------------------------------------------
PREREGISTERED_MIN_DOC_PREVALENCE = 0.25
EXPLORATORY_MIN_DOC_PREVALENCE = 0.05

DISCOVERY_MIN_OCCURRENCES = 5         # at least 5 occurrences in discovery
MAX_LEXICAL_CANDIDATES = 300          # cap on frozen lexical candidates

REPLICATION_MIN_LIFT = 1.5            # validation prevalence >= 1.5x human
REPLICATION_MIN_DOC_PREVALENCE = 0.10 # and present in >=10% of validation docs
REPLICATION_MIN_OCCURRENCES = 5       # and at least 5 occurrences

PARTITIONS = ("ai_discovery", "ai_validation", "human_baseline", "hc3_ai", "hc3_human")


def load() -> dict[str, CorpusStats]:
    stats: dict[str, CorpusStats] = {}
    for name in PARTITIONS:
        path = CORPORA / name
        if not path.exists() or not any(path.glob("*.txt")):
            print(f"  ! partition missing or empty, skipping: {name}")
            continue
        stats[name] = scan_directory(path, name)
        s = stats[name]
        print(f"  {name:<16} {s.documents:>4} docs  {s.paragraphs:>6} paras  "
              f"{s.sentences:>7} sents  {s.tokens:>9,} tokens")
    return stats


def discover_lexical(discovery: CorpusStats, min_doc_prevalence: float) -> list[Pattern]:
    """Nominate lexical candidates from the discovery partition alone, then freeze."""
    lexical = [
        p for p, occ in discovery.occurrences.items()
        if p.kind == "ngram"
        and occ >= DISCOVERY_MIN_OCCURRENCES
        and discovery.document_prevalence(p) >= min_doc_prevalence
    ]
    lexical.sort(key=lambda p: (-discovery.document_prevalence(p),
                                -discovery.occurrences[p], p.text))
    return lexical[:MAX_LEXICAL_CANDIDATES]


def all_structural(discovery: CorpusStats) -> list[Pattern]:
    """Every structural frame observed in discovery, with no threshold at all.

    The catalogue is small enough to report exhaustively, which removes any
    possibility of selection bias on the structural side. A frame that never
    fires is itself a reportable result.
    """
    structural = [p for p in discovery.occurrences if p.kind != "ngram"]
    structural.sort(key=lambda p: (-discovery.document_prevalence(p),
                                   -discovery.occurrences[p], p.text))
    return structural


def evaluate(pattern: Pattern, stats: dict[str, CorpusStats]) -> dict:
    disc = stats["ai_discovery"]
    val = stats.get("ai_validation")
    hum = stats.get("human_baseline")

    row: dict[str, object] = {
        "pattern_kind": pattern.kind,
        "pattern": pattern.text,
        "discovery_occurrences": disc.occurrences[pattern],
        "discovery_documents_with": disc.documents_with[pattern],
        "discovery_doc_prevalence": round(disc.document_prevalence(pattern), 4),
        "discovery_per_10k_sentences": round(disc.per_10k_sentences(pattern), 3),
    }

    for label, corpus in (("validation", val), ("human", hum),
                          ("hc3_ai", stats.get("hc3_ai")), ("hc3_human", stats.get("hc3_human"))):
        if corpus is None:
            continue
        row[f"{label}_occurrences"] = corpus.occurrences[pattern]
        row[f"{label}_documents_with"] = corpus.documents_with[pattern]
        row[f"{label}_doc_prevalence"] = round(corpus.document_prevalence(pattern), 4)
        row[f"{label}_per_10k_sentences"] = round(corpus.per_10k_sentences(pattern), 3)

    if hum is not None:
        row["lift_discovery_vs_human"] = round(smoothed_lift(
            disc.occurrences[pattern], disc.sentences,
            hum.occurrences[pattern], hum.sentences), 4)
        if val is not None:
            row["lift_validation_vs_human"] = round(smoothed_lift(
                val.occurrences[pattern], val.sentences,
                hum.occurrences[pattern], hum.sentences), 4)

    hc3_ai, hc3_hum = stats.get("hc3_ai"), stats.get("hc3_human")
    if hc3_ai is not None and hc3_hum is not None:
        row["lift_hc3_ai_vs_hc3_human"] = round(smoothed_lift(
            hc3_ai.occurrences[pattern], hc3_ai.sentences,
            hc3_hum.occurrences[pattern], hc3_hum.sentences), 4)

    replicated = (
        val is not None and hum is not None
        and float(row.get("lift_validation_vs_human", 0)) >= REPLICATION_MIN_LIFT
        and float(row.get("validation_doc_prevalence", 0)) >= REPLICATION_MIN_DOC_PREVALENCE
        and int(row.get("validation_occurrences", 0)) >= REPLICATION_MIN_OCCURRENCES
    )
    elevated_in_discovery = float(row.get("lift_discovery_vs_human", 0)) >= REPLICATION_MIN_LIFT
    row["elevated_in_discovery"] = elevated_in_discovery
    row["replicated"] = replicated
    row["verdict"] = (
        "REPLICATED" if replicated
        else ("FAILED_VALIDATION" if elevated_in_discovery else "NOT_ELEVATED")
    )
    return row


def _summarise(label: str, rows: list[dict]) -> None:
    rep = [r for r in rows if r["replicated"]]
    failed = [r for r in rows if r["verdict"] == "FAILED_VALIDATION"]
    flat = [r for r in rows if r["verdict"] == "NOT_ELEVATED"]
    print(f"  {label:<34} {len(rows):>4} candidates | "
          f"{len(rep):>3} replicated | {len(failed):>3} failed validation | {len(flat):>3} not elevated")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    # Deliberately not named results*.csv: that pattern is git-ignored as
    # reproducible local output. This file is a published artifact — the corpus
    # behind it needs an 11.8 GB download to regenerate, so the results must be
    # inspectable without it.
    ap.add_argument("--output", default="experiment_01_patterns.csv")
    args = ap.parse_args()

    print("Scanning partitions:")
    stats = load()
    if "ai_discovery" not in stats:
        raise SystemExit("ai_discovery partition is required")
    disc = stats["ai_discovery"]

    prereg = discover_lexical(disc, PREREGISTERED_MIN_DOC_PREVALENCE)
    explor = discover_lexical(disc, EXPLORATORY_MIN_DOC_PREVALENCE)
    structural = all_structural(disc)
    prereg_set = {p.text for p in prereg}

    print(f"\nDiscovery nominated from ai_discovery only, then frozen.")
    print(f"  pre-registered (doc prevalence >= {PREREGISTERED_MIN_DOC_PREVALENCE}): "
          f"{len(prereg)} lexical candidates")
    print(f"  exploratory    (doc prevalence >= {EXPLORATORY_MIN_DOC_PREVALENCE}): "
          f"{len(explor)} lexical candidates  [POST-HOC]")
    print(f"  structural: {len(structural)} frames, reported exhaustively (no threshold)\n")

    rows: list[dict] = []
    for pattern in explor:
        row = evaluate(pattern, stats)
        row["candidate_set"] = "preregistered" if pattern.text in prereg_set else "exploratory"
        rows.append(row)
    for pattern in structural:
        row = evaluate(pattern, stats)
        row["candidate_set"] = "structural_exhaustive"
        rows.append(row)

    rows.sort(key=lambda r: (r["candidate_set"],
                             -float(r.get("lift_validation_vs_human", 0)),
                             -float(r.get("validation_doc_prevalence", 0))))

    out = ROOT / args.output
    if rows:
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    print("Results:")
    _summarise("LEXICAL pre-registered", [r for r in rows if r["candidate_set"] == "preregistered"])
    _summarise("LEXICAL exploratory [POST-HOC]", [r for r in rows if r["candidate_set"] == "exploratory"])
    _summarise("STRUCTURAL (exhaustive)", [r for r in rows if r["candidate_set"] == "structural_exhaustive"])

    print(f"\nwrote {len(rows)} rows -> {out.name}")


if __name__ == "__main__":
    sys.exit(main())
