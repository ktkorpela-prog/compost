"""Build the Experiment 02 confirmatory corpus (``EXPERIMENT_02.md`` §2, §8.4).

Every value here is frozen by the spec. Nothing in this script may be tuned.

Invariants are verified before any extraction runs, and **any failure stops the
build**. Raw text and prompts stay in git-ignored ``corpora/_exp02/``; only
non-text provenance metadata is tracked.

Usage
-----
    python scripts/build_exp02_corpus.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compost.integrity import (  # noqa: E402
    canonical_json_sha256, canonical_text_file_sha256, canonical_text_sha256)

ROOT = Path(__file__).resolve().parent.parent
RAID_CSV = ROOT / "corpora" / "_raw" / "raid_train.csv"
EXCLUSIONS = ROOT / "compost" / "calibration_sources_v1.txt"
OUT = ROOT / "corpora" / "_exp02"
META = OUT / "metadata.csv"
PROVENANCE = ROOT / "experiment_02_corpus_provenance.json"

csv.field_size_limit(2**31 - 1)

# --- frozen, EXPERIMENT_02.md -------------------------------------------------
DOMAINS = ("abstracts", "books", "news", "recipes", "wiki")          # §2.2
DISCOVERY_MODELS = ("chatgpt", "mistral-chat", "mpt-chat")           # §2.4
VALIDATION_MODELS = ("gpt4", "llama-chat", "cohere-chat")            # §2.4
ALL_MODELS = DISCOVERY_MODELS + VALIDATION_MODELS
N_PER_DOMAIN_PER_PHASE = 70                                          # §8.4
MIN_CHARS = 400                                                      # §2.4
DECODING = "greedy"                                                  # §2.3
REPETITION_PENALTY = "no"                                            # §2.3
ATTACK = "none"                                                      # §2.3
EXPECTED_DOCS = N_PER_DOMAIN_PER_PHASE * len(DOMAINS) * 2 * 4        # 2,800


def load_exclusions() -> set[str]:
    lines = EXCLUSIONS.read_text(encoding="utf-8").splitlines()
    return {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}


def rank(source_id: str) -> str:
    return hashlib.sha256(source_id.encode("utf-8")).hexdigest()


def collect() -> dict[str, dict]:
    clusters: dict[str, dict] = defaultdict(
        lambda: {"domain": None, "prompt": "", "title": "", "docs": {}}
    )
    with RAID_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["attack"] != ATTACK or row["domain"] not in DOMAINS:
                continue
            model = row["model"]
            if model == "human":
                pass  # human rows carry empty decoding / repetition_penalty
            elif model in ALL_MODELS:
                if row["decoding"] != DECODING or row["repetition_penalty"] != REPETITION_PENALTY:
                    continue
            else:
                continue
            text = (row["generation"] or "").strip()
            if len(text) < MIN_CHARS:
                continue
            c = clusters[row["source_id"]]
            c["domain"] = row["domain"]
            c["docs"][model] = text
            if row.get("prompt"):
                c["prompt"] = row["prompt"]
            if row.get("title"):
                c["title"] = row["title"]
    return clusters


def main() -> None:
    excluded = load_exclusions()
    print(f"calibration exclusions loaded: {len(excluded):,}\n")

    clusters = collect()
    required = {"human", *ALL_MODELS}          # §2.4: ALL SIX models, not three
    complete = {s: c for s, c in clusters.items()
                if required <= set(c["docs"]) and s not in excluded}
    print(f"sources with any qualifying row : {len(clusters):,}")
    print(f"complete 7-doc, non-calibration : {len(complete):,}\n")

    by_domain: dict[str, list[str]] = defaultdict(list)
    for s, c in complete.items():
        by_domain[c["domain"]].append(s)

    selected: dict[tuple[str, str], list[str]] = {}
    failures: list[str] = []
    for d in DOMAINS:
        ordered = sorted(by_domain[d], key=rank)
        need = 2 * N_PER_DOMAIN_PER_PHASE
        if len(ordered) < need:
            failures.append(f"{d}: only {len(ordered)} eligible sources, need {need}")
            continue
        selected[(d, "discovery")] = ordered[:N_PER_DOMAIN_PER_PHASE]
        selected[(d, "validation")] = ordered[N_PER_DOMAIN_PER_PHASE:need]

    if failures:
        print("STOP — insufficient eligible sources:")
        for f in failures:
            print(f"  {f}")
        raise SystemExit(1)

    # --- invariant verification, before any extraction ------------------------
    print("=== INVARIANT CHECKS ===")
    ok = True

    print(f"{'domain':<12}{'discovery':>11}{'validation':>12}{'eligible':>10}")
    for d in DOMAINS:
        nd, nv = len(selected[(d, "discovery")]), len(selected[(d, "validation")])
        print(f"  {d:<10}{nd:>11}{nv:>12}{len(by_domain[d]):>10}")
        if nd != N_PER_DOMAIN_PER_PHASE or nv != N_PER_DOMAIN_PER_PHASE:
            ok = False

    disc = {s for d in DOMAINS for s in selected[(d, "discovery")]}
    val = {s for d in DOMAINS for s in selected[(d, "validation")]}
    overlap = disc & val
    calib_overlap = (disc | val) & excluded
    print(f"\n  discovery sources            : {len(disc)}")
    print(f"  validation sources           : {len(val)}")
    print(f"  discovery n validation       : {len(overlap)}  (must be 0)")
    print(f"  selected n calibration       : {len(calib_overlap)}  (must be 0)")
    ok &= not overlap and not calib_overlap

    incomplete = [s for s in disc | val if not required <= set(complete[s]["docs"])]
    print(f"  sources missing a model      : {len(incomplete)}  (must be 0)")
    ok &= not incomplete

    if not ok:
        print("\nSTOP — invariant failure. No extraction performed.")
        raise SystemExit(1)

    # --- write ---------------------------------------------------------------
    meta_rows: list[dict] = []
    for (d, phase), sources in sorted(selected.items()):
        models = DISCOVERY_MODELS if phase == "discovery" else VALIDATION_MODELS
        for s in sources:
            c = complete[s]
            target = OUT / phase / d / s
            target.mkdir(parents=True, exist_ok=True)
            (target / "prompt.txt").write_text(c["prompt"], encoding="utf-8")
            (target / "title.txt").write_text(c["title"], encoding="utf-8")
            for model in ("human", *models):
                text = c["docs"][model]
                (target / f"{model}.txt").write_text(text, encoding="utf-8")
                meta_rows.append({
                    "phase": phase, "domain": d, "source_id": s, "model": model,
                    "chars": len(text),
                    "sha256": canonical_text_sha256(text),
                })

    if len(meta_rows) != EXPECTED_DOCS:
        print(f"\nSTOP — expected {EXPECTED_DOCS} documents, wrote {len(meta_rows)}.")
        raise SystemExit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    with META.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()))
        w.writeheader()
        w.writerows(meta_rows)
    meta_hash = canonical_text_file_sha256(META)

    corpus_digest = canonical_text_sha256(chr(10).join(sorted(r["sha256"] for r in meta_rows)))

    provenance = {
        "documents": len(meta_rows),
        "sources_per_domain_per_phase": N_PER_DOMAIN_PER_PHASE,
        "domains": list(DOMAINS),
        "discovery_models": list(DISCOVERY_MODELS),
        "validation_models": list(VALIDATION_MODELS),
        "filters": {"attack": ATTACK, "decoding": DECODING,
                    "repetition_penalty": REPETITION_PENALTY, "min_chars": MIN_CHARS,
                    "required_model_coverage": "all six (EXPERIMENT_02.md 2.4)"},
        "calibration_sources_excluded": len(excluded),
        "discovery_validation_overlap": 0,
        "calibration_overlap": 0,
        "raid_train_sha256":
            "52f04ceebc126064e68fbd22d8b736964065745464f4bfd52e488150b49f84e4",
        "metadata_sha256": meta_hash,
        "corpus_content_digest": corpus_digest,
    }
    provenance["provenance_canonical_sha256"] = canonical_json_sha256(provenance)
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")

    print(f"\n=== WRITTEN ===")
    print(f"  documents            : {len(meta_rows):,} (expected {EXPECTED_DOCS:,})")
    print(f"  metadata sha256      : {meta_hash}")
    print(f"  corpus content digest: {corpus_digest}")
    print(f"  provenance           -> {PROVENANCE.relative_to(ROOT)}")
    print("\nALL INVARIANTS PASSED.")


if __name__ == "__main__":
    sys.exit(main())
