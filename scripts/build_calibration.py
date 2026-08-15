"""Reconstruct the Experiment 02 calibration set (``EXPERIMENT_02.md`` §8).

Takes the source IDs already used in Experiment 01 and pulls them from RAID into
complete matched clusters: 1 human plus all 6 selected models, under
``attack=none``, ``decoding=greedy``, ``repetition_penalty=no``.

Those source IDs are **permanently excluded** from Experiment 02 discovery and
validation. This script writes the exclusion list to
``compost/calibration_sources_v1.txt``, which the Phase 2 corpus builder must
read as a hard filter. A source that calibrated the experiment can never also be
evidence in it.

Raw text lands in ``corpora/_calibration/`` and is git-ignored. Only the source
ID list and the summary are committed.

Usage
-----
    python scripts/build_calibration.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAID_CSV = ROOT / "corpora" / "_raw" / "raid_train.csv"
EXP01_META = ROOT / "corpora" / "metadata.csv"
OUT_DIR = ROOT / "corpora" / "_calibration"
EXCLUSION_LIST = ROOT / "compost" / "calibration_sources_v1.txt"
SUMMARY = ROOT / "corpora" / "_calibration" / "summary.json"

csv.field_size_limit(2**31 - 1)

DOMAINS = ("abstracts", "books", "news", "recipes", "wiki")  # reddit excluded, §2.2
MODELS = ("chatgpt", "mistral-chat", "mpt-chat", "gpt4", "llama-chat", "cohere-chat")
MIN_CHARS = 400


def experiment_01_sources() -> set[str]:
    """Every RAID source ID Experiment 01 touched, AI-side and human-side."""
    wanted: set[str] = set()
    with EXP01_META.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["source"] != "RAID":
                continue
            if row["matched_source_id"]:
                wanted.add(row["matched_source_id"])
            if row["model"] == "human":
                wanted.add(row["source_id"])
    return wanted


def collect(wanted: set[str]) -> dict[str, dict]:
    """One streaming pass. Returns source_id -> {domain, docs: {model: text}}."""
    clusters: dict[str, dict] = defaultdict(lambda: {"domain": None, "docs": {}})
    with RAID_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["attack"] != "none" or row["domain"] not in DOMAINS:
                continue
            src = row["source_id"]
            if src not in wanted:
                continue
            model = row["model"]
            if model == "human":
                pass  # human rows carry empty decoding / repetition_penalty
            elif model in MODELS:
                if row["decoding"] != "greedy" or row["repetition_penalty"] != "no":
                    continue
            else:
                continue
            text = (row["generation"] or "").strip()
            if len(text) < MIN_CHARS:
                continue
            cluster = clusters[src]
            cluster["domain"] = row["domain"]
            cluster["docs"][model] = text
    return clusters


def main() -> None:
    wanted = experiment_01_sources()
    print(f"Experiment 01 source IDs: {len(wanted):,}")

    clusters = collect(wanted)
    print(f"sources with any qualifying row: {len(clusters):,}")

    required = {"human", *MODELS}
    complete = {src: c for src, c in clusters.items() if required <= set(c["docs"])}
    print(f"COMPLETE 7-document clusters (1 human + 6 models): {len(complete):,}\n")

    by_domain: dict[str, int] = defaultdict(int)
    for c in complete.values():
        by_domain[c["domain"]] += 1
    print(f"{'domain':<12}{'complete':>10}")
    for d in DOMAINS:
        print(f"  {d:<10}{by_domain[d]:>10,}")
    print(f"  {'TOTAL':<10}{len(complete):>10,}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src, c in complete.items():
        target = OUT_DIR / c["domain"] / src
        target.mkdir(parents=True, exist_ok=True)
        for model, text in c["docs"].items():
            (target / f"{model}.txt").write_text(text, encoding="utf-8")

    EXCLUSION_LIST.write_text(
        "# Experiment 02 calibration sources — PERMANENTLY EXCLUDED from discovery\n"
        "# and validation (EXPERIMENT_02.md §8). Read as a hard filter by the Phase 2\n"
        "# corpus builder. One RAID source_id per line.\n"
        + "".join(f"{src}\n" for src in sorted(complete)),
        encoding="utf-8",
    )
    SUMMARY.write_text(json.dumps({
        "experiment_01_source_ids": len(wanted),
        "complete_clusters": len(complete),
        "by_domain": dict(by_domain),
        "models": list(MODELS),
        "filters": {"attack": "none", "decoding": "greedy",
                    "repetition_penalty": "no", "min_chars": MIN_CHARS},
    }, indent=2), encoding="utf-8")

    print(f"\nexclusion list -> {EXCLUSION_LIST.relative_to(ROOT)} ({len(complete):,} ids)")
    print(f"raw text       -> {OUT_DIR.relative_to(ROOT)} (git-ignored)")


if __name__ == "__main__":
    sys.exit(main())
