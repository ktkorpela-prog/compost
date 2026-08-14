"""Benchmark skeleton induction on the calibration set only.

Establishes whether the Experiment 02 design is computationally practical before
any confirmatory work is attempted. Runs on the calibration clusters — whose
sources are permanently excluded from discovery and validation — and never on
Experiment 02 corpus material.

Emits a per-document count cache for the parameter estimator, so the expensive
induction pass is not repeated.

Usage
-----
    python scripts/benchmark_induction.py
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compost.canonical import anchors_sha256, load_anchors  # noqa: E402
from compost.induction import (  # noqa: E402
    CROSS_SENTENCE,
    WITHIN_SENTENCE,
    induce_pair,
    induce_single,
)
from compost.normalizer import paragraphs, sentences  # noqa: E402

CALIB = ROOT / "corpora" / "_calibration"
COUNTS = CALIB / "counts.json"
CEILING_N = 851
DOMAINS_N = 5
SPLITS_N = 2
DOCS_PER_SOURCE = 4  # 1 human + 3 models per phase, EXPERIMENT_02.md §9


def scan(path: Path, anchors):
    """Return (exposure dict, Counter of skeletons) for one document."""
    text = path.read_text(encoding="utf-8")
    S = P = n_par = 0
    counts: Counter = Counter()
    for para in paragraphs(text):
        sents = sentences(para)
        if not sents:
            continue
        n_par += 1
        S += len(sents)
        P += max(0, len(sents) - 1)
        for s in sents:
            counts.update(induce_single(s, anchors))
        for i in range(len(sents) - 1):
            counts.update(induce_pair(sents[i], sents[i + 1], anchors))
    return {"paragraphs": n_par, "S": S, "P": P}, counts


def main() -> None:
    if not CALIB.exists():
        raise SystemExit("calibration set missing; run scripts/build_calibration.py first")
    anchors = load_anchors()
    docs = sorted(CALIB.rglob("*.txt"))
    if not docs:
        raise SystemExit("no calibration documents found")

    print(f"anchors: {len(anchors)}  sha256={anchors_sha256()}")
    print(f"documents: {len(docs):,}\n")

    tracemalloc.start()
    started = time.perf_counter()

    tot = {"documents": 0, "paragraphs": 0, "S": 0, "P": 0}
    distinct: dict[str, set] = {WITHIN_SENTENCE: set(), CROSS_SENTENCE: set()}
    occurrences: dict[str, int] = {WITHIN_SENTENCE: 0, CROSS_SENTENCE: 0}
    per_doc: list[dict] = []

    for path in docs:
        exposure, counts = scan(path, anchors)
        tot["documents"] += 1
        for k in ("paragraphs", "S", "P"):
            tot[k] += exposure[k]
        by_family: dict[str, int] = defaultdict(int)
        for skeleton, n in counts.items():
            distinct[skeleton.exposure].add(skeleton.text)
            occurrences[skeleton.exposure] += n
            by_family[skeleton.exposure] += n
        rel = path.relative_to(CALIB)
        per_doc.append({
            "domain": rel.parts[0], "source": rel.parts[1], "model": path.stem,
            "S": exposure["S"], "P": exposure["P"],
            "skeletons": {s.text: n for s, n in counts.items()},
        })

    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"{'documents':<26}{tot['documents']:>12,}")
    print(f"{'paragraphs':<26}{tot['paragraphs']:>12,}")
    print(f"{'sentences (S)':<26}{tot['S']:>12,}")
    print(f"{'adjacent pairs (P)':<26}{tot['P']:>12,}")
    print()
    for family in (WITHIN_SENTENCE, CROSS_SENTENCE):
        print(f"{family:<26}{len(distinct[family]):>12,} distinct   "
              f"{occurrences[family]:>12,} occurrences")
    print(f"{'TOTAL distinct':<26}"
          f"{len(distinct[WITHIN_SENTENCE]) + len(distinct[CROSS_SENTENCE]):>12,}")
    print()
    print(f"{'runtime (s)':<26}{elapsed:>12.1f}")
    print(f"{'docs/sec':<26}{tot['documents'] / elapsed:>12.1f}")
    print(f"{'peak python memory (MB)':<26}{peak / 1e6:>12.1f}")

    projected_docs = CEILING_N * DOMAINS_N * SPLITS_N * DOCS_PER_SOURCE
    scale = projected_docs / tot["documents"]
    print(f"\nprojected at N={CEILING_N} ({projected_docs:,} documents):")
    print(f"  runtime      ~{elapsed * scale / 60:>8.1f} min")
    print(f"  distinct skeletons (linear upper bound) "
          f"~{int((len(distinct[WITHIN_SENTENCE]) + len(distinct[CROSS_SENTENCE])) * scale):,}")
    print("  NOTE: distinct-skeleton growth is sublinear (types saturate as tokens grow),")
    print("        so the linear figure is an upper bound, not an estimate.")

    COUNTS.write_text(json.dumps(per_doc), encoding="utf-8")
    print(f"\nper-document counts -> {COUNTS.relative_to(ROOT)} (git-ignored)")


if __name__ == "__main__":
    sys.exit(main())
