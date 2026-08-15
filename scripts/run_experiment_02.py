"""Experiment 02 confirmatory analysis (``EXPERIMENT_02.md`` §3-§7).

Every threshold, model set, domain set, denominator and stop condition is frozen
by the spec and read from it, never chosen here.

Sequence, strictly ordered:
  1. discovery nomination, using the discovery phase ONLY
  2. freeze the candidate set to a hashed artifact
  3. held-out validation of exactly those frozen candidates
  4. source-cluster bootstrap for replicated patterns
No candidate is added or removed after step 2.

Usage
-----
    python scripts/run_experiment_02.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compost.canonical import anchors_sha256, load_anchors            # noqa: E402
from compost.echo import build_echo_sets                              # noqa: E402
from compost.extractor import extract_ngrams                          # noqa: E402
from compost.induction import induce_pair, induce_single              # noqa: E402
from compost.integrity import canonical_json_sha256, canonical_text_sha256  # noqa: E402
from compost.normalizer import paragraphs, sentences                  # noqa: E402

CORPUS = ROOT / "corpora" / "_exp02"

# --- frozen, EXPERIMENT_02.md -------------------------------------------------
DOMAINS = ("abstracts", "books", "news", "recipes", "wiki")
DISCOVERY_MODELS = ("chatgpt", "mistral-chat", "mpt-chat")
VALIDATION_MODELS = ("gpt4", "llama-chat", "cohere-chat")
PHASE_MODELS = {"discovery": DISCOVERY_MODELS, "validation": VALIDATION_MODELS}

CELL_MIN_LIFT = 1.5              # §6.1
CELL_MIN_OCCURRENCES = 10        # §6.1
CELL_MIN_DOC_PREVALENCE = 0.10   # §6.1
DOMAIN_MIN_PASSING_MODELS = 2    # §6.2
DOMAIN_NO_REVERSAL_LIFT = 0.8    # §6.2
PATTERN_MIN_DOMAINS = 3          # §6.3
SMOOTHING = 0.5                  # §5

BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20260815

NGRAM, WITHIN, CROSS = "ngram", "within_sentence", "cross_sentence"


@dataclass
class Cell:
    """One (phase, domain, model) arm."""
    documents: int = 0
    S: int = 0
    P: int = 0
    primary: Counter = field(default_factory=Counter)
    total: Counter = field(default_factory=Counter)
    docs_with: Counter = field(default_factory=Counter)

    def denom(self, kind: str) -> int:
        return self.P if kind == CROSS else self.S

    def rate(self, key) -> float:
        d = self.denom(key[0])
        return self.primary[key] / d if d else 0.0

    def prevalence(self, key) -> float:
        return self.docs_with[key] / self.documents if self.documents else 0.0


def smoothed_lift(t_occ, t_n, r_occ, r_n) -> float:
    return ((t_occ + SMOOTHING) / (t_n + 1.0)) / ((r_occ + SMOOTHING) / (r_n + 1.0))


def extract_document(text: str, anchors, echo):
    """Return (exposure, primary Counter, total Counter) for one document."""
    S = P = 0
    total: Counter = Counter()
    echoing: Counter = Counter()
    for para in paragraphs(text):
        sents = sentences(para)
        if not sents:
            continue
        S += len(sents)
        P += max(0, len(sents) - 1)
        for s in sents:
            for pat, n in extract_ngrams(s).items():
                key = (NGRAM, pat.text)
                total[key] += n
                if echo.contains_lexical(pat.text):
                    echoing[key] += n
            for sk, n in induce_single(s, anchors).items():
                key = (WITHIN, sk.text)
                total[key] += n
                if echo.contains_structural(sk.text):
                    echoing[key] += n
        for i in range(len(sents) - 1):
            for sk, n in induce_pair(sents[i], sents[i + 1], anchors).items():
                key = (CROSS, sk.text)
                total[key] += n
                if echo.contains_structural(sk.text):
                    echoing[key] += n
    primary = Counter({k: v - echoing[k] for k, v in total.items() if v - echoing[k] > 0})
    return {"S": S, "P": P}, primary, total, echoing


def scan_phase(phase: str, anchors, keep=None):
    """Aggregate cells for a phase. ``keep`` restricts per-source detail to
    frozen candidates, so pass 2 stays small enough to bootstrap."""
    cells: dict[tuple[str, str], Cell] = defaultdict(Cell)
    per_source: dict[tuple[str, str, str], dict] = {}
    echo_stats = Counter()
    for domain in DOMAINS:
        base = CORPUS / phase / domain
        for src_dir in sorted(base.iterdir()):
            echo = build_echo_sets(
                (src_dir / "prompt.txt").read_text(encoding="utf-8"),
                (src_dir / "title.txt").read_text(encoding="utf-8"),
                anchors,
            )
            for model in ("human", *PHASE_MODELS[phase]):
                exposure, primary, total, echoing = extract_document(
                    (src_dir / f"{model}.txt").read_text(encoding="utf-8"), anchors, echo
                )
                cell = cells[(domain, model)]
                cell.documents += 1
                cell.S += exposure["S"]
                cell.P += exposure["P"]
                cell.primary.update(primary)
                cell.total.update(total)
                for k in primary:
                    cell.docs_with[k] += 1
                echo_stats["total"] += sum(total.values())
                echo_stats["echoing"] += sum(echoing.values())
                if keep is not None:
                    per_source[(domain, model, src_dir.name)] = {
                        "S": exposure["S"], "P": exposure["P"],
                        "c": {k: primary[k] for k in keep if primary[k]},
                    }
    return cells, per_source, echo_stats


def cell_passes(ai: Cell, hum: Cell, key):
    occ = ai.primary[key]
    lift = smoothed_lift(occ, ai.denom(key[0]), hum.primary[key], hum.denom(key[0]))
    passed = (lift >= CELL_MIN_LIFT and occ >= CELL_MIN_OCCURRENCES
              and ai.prevalence(key) >= CELL_MIN_DOC_PREVALENCE)
    return passed, lift, occ, ai.prevalence(key)


def qualifying_domains(cells, phase, key):
    """Apply §6.1-6.2. Returns (list of qualifying domains, per-cell detail)."""
    quals, detail = [], {}
    for domain in DOMAINS:
        hum = cells[(domain, "human")]
        lifts, passes = [], 0
        for model in PHASE_MODELS[phase]:
            ok, lift, occ, prev = cell_passes(cells[(domain, model)], hum, key)
            detail[(domain, model)] = {"lift": lift, "occ": occ, "prev": prev, "pass": ok}
            lifts.append(lift)
            passes += 1 if ok else 0
        if passes >= DOMAIN_MIN_PASSING_MODELS and min(lifts) >= DOMAIN_NO_REVERSAL_LIFT:
            quals.append(domain)
    return quals, detail


def bootstrap_cell(per_source, domain, model, hum_model, key, rng):
    """Source-cluster bootstrap: resample sources, carry whole clusters."""
    sources = sorted({s for (d, m, s) in per_source if d == domain and m == model})
    if not sources:
        return None
    lifts = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        picked = [sources[int(rng.random() * len(sources))] for _ in sources]
        a_occ = a_n = h_occ = h_n = 0
        for s in picked:
            a = per_source[(domain, model, s)]
            h = per_source[(domain, hum_model, s)]
            unit = "P" if key[0] == CROSS else "S"
            a_occ += a["c"].get(key, 0); a_n += a[unit]
            h_occ += h["c"].get(key, 0); h_n += h[unit]
        lifts.append(smoothed_lift(a_occ, a_n, h_occ, h_n))
    lifts.sort()
    lo = lifts[int(0.025 * (len(lifts) - 1))]
    hi = lifts[int(0.975 * (len(lifts) - 1))]
    return lo, hi


def main() -> None:
    anchors = load_anchors()
    a_sha = anchors_sha256()
    print(f"anchors: {len(anchors)}  sha256={a_sha}")
    excl = ROOT / "compost" / "calibration_sources_v1.txt"
    n_excl = sum(1 for ln in excl.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#"))
    print(f"calibration sources excluded: {n_excl}\n")

    # --- 1. DISCOVERY -------------------------------------------------------
    print("=== DISCOVERY (nomination uses the discovery phase only) ===")
    disc_cells, _, disc_echo = scan_phase("discovery", anchors)
    for domain in DOMAINS:
        c = disc_cells[(domain, "human")]
        print(f"  {domain:<10} human docs={c.documents:>3} S={c.S:>6} P={c.P:>6}")

    universe = set()
    for domain in DOMAINS:
        for model in DISCOVERY_MODELS:
            cell = disc_cells[(domain, model)]
            for key, occ in cell.primary.items():
                if occ >= CELL_MIN_OCCURRENCES and cell.prevalence(key) >= CELL_MIN_DOC_PREVALENCE:
                    universe.add(key)
    print(f"\n  patterns reaching cell floors in >=1 discovery cell: {len(universe):,}")

    candidates = {}
    for key in universe:
        quals, detail = qualifying_domains(disc_cells, "discovery", key)
        if len(quals) >= PATTERN_MIN_DOMAINS:
            candidates[key] = {"domains": quals, "detail": detail}
    print(f"  DISCOVERY CANDIDATES (>= {PATTERN_MIN_DOMAINS} domains): {len(candidates):,}")

    by_kind = Counter(k[0] for k in candidates)
    print(f"    lexical (ngram)      : {by_kind[NGRAM]}")
    print(f"    within_sentence      : {by_kind[WITHIN]}")
    print(f"    cross_sentence       : {by_kind[CROSS]}")

    # --- 2. FREEZE ----------------------------------------------------------
    frozen = sorted(candidates)
    art = {
        "anchor_sha256": a_sha,
        "candidate_count": len(frozen),
        "by_kind": {k: by_kind[k] for k in (NGRAM, WITHIN, CROSS)},
        "candidates": [
            {"kind": k, "pattern": t,
             "discovery_domains": candidates[(k, t)]["domains"],
             "discovery_models_passing": sorted(
                 f"{d}/{m}" for (d, m), v in candidates[(k, t)]["detail"].items() if v["pass"]
             )}
            for k, t in frozen
        ],
    }
    path = ROOT / "experiment_02_discovery_candidates.json"
    payload = json.dumps(art, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    cand_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    (ROOT / "experiment_02_discovery_candidates.sha256").write_text(
        f"{cand_sha}  experiment_02_discovery_candidates.json\n", encoding="utf-8")
    print(f"\n  FROZEN -> {path.name}")
    print(f"  candidate artifact sha256: {cand_sha}")

    if not frozen:
        print("\nNo candidates. Validation not run; nothing to replicate.")
        _write_results(a_sha, n_excl, cand_sha, 0, [], {}, disc_echo, Counter(), {}, {})
        return

    # --- 3. VALIDATION ------------------------------------------------------
    print("\n=== HELD-OUT VALIDATION (frozen candidates only) ===")
    keep = set(frozen)
    disc_cells2, disc_src, _ = scan_phase("discovery", anchors, keep=keep)
    val_cells, val_src, val_echo = scan_phase("validation", anchors, keep=keep)

    replicated, matrix = [], {}
    for key in frozen:
        dq, dd = qualifying_domains(disc_cells2, "discovery", key)
        vq, vd = qualifying_domains(val_cells, "validation", key)
        matrix[key] = {"discovery": dd, "validation": vd,
                       "discovery_domains": dq, "validation_domains": vq}
        if len(dq) >= PATTERN_MIN_DOMAINS and len(vq) >= PATTERN_MIN_DOMAINS:
            replicated.append(key)
    print(f"  candidates evaluated : {len(frozen)}")
    print(f"  REPLICATED           : {len(replicated)}")

    # --- 4. BOOTSTRAP -------------------------------------------------------
    rng = random.Random(BOOTSTRAP_SEED)
    boots = {}
    for key in replicated:
        for phase, cells_src in (("discovery", disc_src), ("validation", val_src)):
            for domain in DOMAINS:
                for model in PHASE_MODELS[phase]:
                    ci = bootstrap_cell(cells_src, domain, model, "human", key, rng)
                    if ci:
                        boots[(key, phase, domain, model)] = ci
    print(f"  bootstrap intervals  : {len(boots)} cells "
          f"({BOOTSTRAP_RESAMPLES} resamples, sources resampled, models fixed)")

    _write_results(a_sha, n_excl, cand_sha, len(frozen), replicated, matrix,
                   disc_echo, val_echo, boots, by_kind)


def _write_results(a_sha, n_excl, cand_sha, n_cand, replicated, matrix,
                   disc_echo, val_echo, boots, by_kind):
    rows = []
    for key, m in matrix.items():
        for phase in ("discovery", "validation"):
            for (domain, model), v in m[phase].items():
                ci = boots.get((key, phase, domain, model))
                rows.append({
                    "kind": key[0], "pattern": key[1], "phase": phase,
                    "domain": domain, "model": model,
                    "lift": round(v["lift"], 4), "occurrences": v["occ"],
                    "doc_prevalence": round(v["prev"], 4), "cell_pass": v["pass"],
                    "bootstrap_ci_lo": round(ci[0], 4) if ci else "",
                    "bootstrap_ci_hi": round(ci[1], 4) if ci else "",
                    "replicated_pattern": key in replicated,
                })
    out = ROOT / "experiment_02_lift_matrix.csv"
    if rows:
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    summary = {
        "anchor_sha256": a_sha,
        "calibration_sources_excluded": n_excl,
        "discovery_candidate_artifact_sha256": cand_sha,
        "discovery_candidates": n_cand,
        "candidates_by_kind": dict(by_kind),
        "replicated_patterns": len(replicated),
        "replicated": [{"kind": k, "pattern": t} for k, t in replicated],
        "echo": {
            "discovery_total_occurrences": disc_echo["total"],
            "discovery_echoing_occurrences": disc_echo["echoing"],
            "discovery_echo_fraction": round(
                disc_echo["echoing"] / disc_echo["total"], 6) if disc_echo["total"] else 0.0,
            "validation_total_occurrences": val_echo["total"],
            "validation_echoing_occurrences": val_echo["echoing"],
            "validation_echo_fraction": round(
                val_echo["echoing"] / val_echo["total"], 6) if val_echo["total"] else 0.0,
        },
        "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES, "cells": len(boots),
                      "unit": "source clusters; models fixed, never resampled",
                      "interval": "95% percentile", "p_values": None},
        "lift_matrix_rows": len(rows),
    }
    (ROOT / "experiment_02_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n  results -> experiment_02_summary.json, experiment_02_lift_matrix.csv")
    print(f"  echo fraction: discovery {summary['echo']['discovery_echo_fraction']:.4%}  "
          f"validation {summary['echo']['validation_echo_fraction']:.4%}")


if __name__ == "__main__":
    sys.exit(main())
