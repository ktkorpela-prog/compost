"""Power and stress-test plumbing for Experiment 02 (``EXPERIMENT_02.md`` §8).

Sample size N is an **output** of this simulation, never an intuition and never a
closed-form Poisson calculation. The independent-Poisson approach was discarded
because occurrences are clustered three ways: generations from one source share a
prompt and content, generations from one model share a generator, and documents
in one domain share genre.

Clustering parameters are **explicit inputs with no defaults**. Either measure
them with :func:`estimate_cluster_params` against a real corpus, or supply them
deliberately. The script refuses to run without them, so N can never be produced
from a silent assumption.

This module runs no confirmatory extraction. It simulates counts and pushes them
through the frozen §6 decision rule.

Usage
-----
    python scripts/simulate_power.py --params params.json
    python scripts/simulate_power.py --params params.json --smoke
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Frozen decision rule, EXPERIMENT_02.md §6.
CELL_MIN_LIFT = 1.5
CELL_MIN_OCCURRENCES = 10
CELL_MIN_DOC_PREVALENCE = 0.10
DOMAIN_MIN_PASSING_MODELS = 2
DOMAIN_NO_REVERSAL_LIFT = 0.8
PATTERN_MIN_DOMAINS = 3

DOMAINS = 5
MODELS_PER_PHASE = 3
PHASES = 2

# Frozen ceiling, EXPERIMENT_02.md §9: abstracts is the binding domain.
MAX_N = 851

POWER_TARGET = 0.80

# The qualification CRITERION (CELL_MIN_LIFT, above) and the effect size power is
# evaluated AT are different quantities. Conflating them was the Phase 1 defect:
# an effect exactly on the decision boundary passes ~50% of the time per cell at
# any N, so >=80% power at true lift 1.5 is unreachable by construction.
# See EXPERIMENT_02.md 8.1-8.3.
MIN_EFFECT_OF_INTEREST = 2.0
TARGET_LIFT = MIN_EFFECT_OF_INTEREST


@dataclass
class ClusterParams:
    """Measured, not assumed. See :func:`estimate_cluster_params`."""

    base_rate_per_unit: float      # human-arm occurrences per exposure unit
    exposure_per_doc: float        # mean sentences (or pairs) per document
    source_dispersion: float       # variance of the source random effect
    model_dispersion: float        # variance of the model random effect
    provenance: str                # how these numbers were obtained

    def validate(self) -> None:
        if self.base_rate_per_unit <= 0 or self.exposure_per_doc <= 0:
            raise ValueError("base_rate_per_unit and exposure_per_doc must be positive")
        if self.source_dispersion < 0 or self.model_dispersion < 0:
            raise ValueError("dispersions must be non-negative")
        if not self.provenance.strip():
            raise ValueError("provenance must state how the parameters were obtained")


@dataclass
class StressScenario:
    """Document-shape asymmetries measured in Experiment 01, imposed under H0."""

    name: str
    ai_exposure_ratio: float = 1.0   # Exp 01: AI documents were shorter than human
    ai_pair_ratio: float = 1.0       # Exp 01: human text yielded 1.17-1.19x more pairs


NO_STRESS = StressScenario("none")
LENGTH_ONLY = StressScenario("length_asymmetry", ai_exposure_ratio=80_300 / 104_984)
LENGTH_AND_PARAGRAPH = StressScenario(
    "length_and_paragraph", ai_exposure_ratio=80_300 / 104_984, ai_pair_ratio=1 / 1.169
)
STRESS_SCENARIOS = (NO_STRESS, LENGTH_ONLY, LENGTH_AND_PARAGRAPH)


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam < 30:
        target, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= rng.random()
            if p <= target:
                return k
            k += 1
    return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))


def _effect(rng: random.Random, variance: float) -> float:
    """Multiplicative random effect with mean 1 and the given variance."""
    if variance <= 0:
        return 1.0
    shape = 1.0 / variance
    return rng.gammavariate(shape, variance)


def _simulate_arm(rng, params, n_sources, lift, exposure_ratio, source_effects, model_effect):
    """Return (total occurrences, documents containing, documents)."""
    total = docs_with = 0
    exposure = params.exposure_per_doc * exposure_ratio
    for effect in source_effects[:n_sources]:
        lam = exposure * params.base_rate_per_unit * lift * effect * model_effect
        count = _poisson(rng, lam)
        total += count
        docs_with += 1 if count > 0 else 0
    return total, docs_with, n_sources


def _smoothed_lift(t_occ, t_n, r_occ, r_n, correction=0.5) -> float:
    return ((t_occ + correction) / (t_n + 1.0)) / ((r_occ + correction) / (r_n + 1.0))


def _phase_qualifies(rng, params, n_sources, lift, scenario) -> bool:
    """Apply the frozen §6 rule to one simulated phase."""
    qualifying_domains = 0
    for _ in range(DOMAINS):
        source_effects = [_effect(rng, params.source_dispersion) for _ in range(n_sources)]
        h_occ, h_docs_with, h_docs = _simulate_arm(
            rng, params, n_sources, 1.0, 1.0, source_effects, 1.0
        )
        h_units = h_docs * params.exposure_per_doc

        lifts, passes = [], 0
        for _ in range(MODELS_PER_PHASE):
            model_effect = _effect(rng, params.model_dispersion)
            a_occ, a_docs_with, a_docs = _simulate_arm(
                rng, params, n_sources, lift, scenario.ai_exposure_ratio,
                source_effects, model_effect,
            )
            a_units = a_docs * params.exposure_per_doc * scenario.ai_exposure_ratio
            cell_lift = _smoothed_lift(a_occ, a_units, h_occ, h_units)
            lifts.append(cell_lift)
            if (cell_lift >= CELL_MIN_LIFT
                    and a_occ >= CELL_MIN_OCCURRENCES
                    and a_docs_with / a_docs >= CELL_MIN_DOC_PREVALENCE):
                passes += 1
        if passes >= DOMAIN_MIN_PASSING_MODELS and min(lifts) >= DOMAIN_NO_REVERSAL_LIFT:
            qualifying_domains += 1
    return qualifying_domains >= PATTERN_MIN_DOMAINS


def power_at(params, n_sources, lift, replicates, seed, scenario=NO_STRESS) -> float:
    """Proportion of replicates in which the pattern reaches the §6.3 verdict."""
    params.validate()
    if n_sources > MAX_N:
        raise ValueError(f"n_sources {n_sources} exceeds the RAID ceiling of {MAX_N}")
    rng = random.Random(seed)
    hits = sum(
        1 for _ in range(replicates)
        if all(_phase_qualifies(rng, params, n_sources, lift, scenario) for _ in range(PHASES))
    )
    return hits / replicates


def power_curve(params, n_grid, lifts, replicates, seed, scenario=NO_STRESS):
    return {
        lift: {n: power_at(params, n, lift, replicates, seed + i, scenario)
               for i, n in enumerate(n_grid)}
        for lift in lifts
    }


def select_n(curve, lift=TARGET_LIFT, target=POWER_TARGET) -> int | None:
    """Smallest N on the grid reaching the power target. None means unreachable."""
    for n in sorted(curve[lift]):
        if curve[lift][n] >= target:
            return n
    return None


CALIBRATION_COUNTS = ROOT / "corpora" / "_calibration" / "counts.json"
HUMAN_PREVALENCE_FLOOR = 0.10  # matches the §6 scope decision
MIN_SKELETONS_FOR_ESTIMATE = 5


def _moment_dispersion(counts: list[int]) -> float | None:
    """Method-of-moments overdispersion for Poisson counts: (Var - mean) / mean^2.

    Returns None when the sample cannot support an estimate, and clips at 0 —
    under-dispersion relative to Poisson is not representable by a multiplicative
    random effect with positive variance.
    """
    if len(counts) < 3:
        return None
    mean = sum(counts) / len(counts)
    if mean <= 0:
        return None
    var = sum((c - mean) ** 2 for c in counts) / (len(counts) - 1)
    return max(0.0, (var - mean) / (mean ** 2))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(q * (len(ordered) - 1) + 0.5), len(ordered) - 1)
    return ordered[idx]


def estimate_cluster_params(counts_path: Path | str = CALIBRATION_COUNTS,
                            exposure_field: str = "S"):
    """Measure clustering from the calibration set rather than assuming it.

    Returns ``(ClusterParams, sensitivity)`` where ``sensitivity`` carries
    interquartile ranges for parameters that a set this size cannot pin down. Per
    EXPERIMENT_02.md §8, anything not credibly estimable is carried as a range
    rather than invented as a point estimate.

    The calibration set may inform nuisance parameters and runtime only. It can
    never alter thresholds, anchors, nomination rules or replication criteria.
    """
    path = Path(counts_path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing. Run scripts/build_calibration.py then "
            f"scripts/benchmark_induction.py before estimating parameters."
        )
    rows = json.loads(path.read_text(encoding="utf-8"))
    human = [r for r in rows if r["model"] == "human"]
    ai = [r for r in rows if r["model"] != "human"]
    if not human or not ai:
        raise ValueError("calibration counts lack a human arm or an AI arm")

    exposure_per_doc = sum(r[exposure_field] for r in human) / len(human)
    total_human_exposure = sum(r[exposure_field] for r in human)

    # Skeletons common enough to be in scope for Experiment 02 at all.
    doc_freq: dict[str, int] = {}
    for r in human:
        for text in r["skeletons"]:
            doc_freq[text] = doc_freq.get(text, 0) + 1
    qualifying = [t for t, n in doc_freq.items()
                  if n / len(human) >= HUMAN_PREVALENCE_FLOOR]

    rates, source_phis, model_phis = [], [], []
    for text in qualifying:
        human_counts = [r["skeletons"].get(text, 0) for r in human]
        total = sum(human_counts)
        if total <= 0:
            continue
        rates.append(total / total_human_exposure)
        phi = _moment_dispersion(human_counts)
        if phi is not None:
            source_phis.append(phi)

        by_model: dict[str, list[int]] = {}
        by_model_exposure: dict[str, int] = {}
        for r in ai:
            by_model.setdefault(r["model"], []).append(r["skeletons"].get(text, 0))
            by_model_exposure[r["model"]] = by_model_exposure.get(r["model"], 0) + r[exposure_field]
        model_rates = [sum(v) / by_model_exposure[m] for m, v in by_model.items()
                       if by_model_exposure.get(m)]
        if len(model_rates) >= 3:
            mean = sum(model_rates) / len(model_rates)
            if mean > 0:
                var = sum((x - mean) ** 2 for x in model_rates) / (len(model_rates) - 1)
                model_phis.append(var / mean ** 2)

    if len(rates) < MIN_SKELETONS_FOR_ESTIMATE:
        raise ValueError(
            f"only {len(rates)} skeletons cleared the {HUMAN_PREVALENCE_FLOOR:.0%} human "
            f"prevalence floor; too few to estimate parameters credibly"
        )

    params = ClusterParams(
        base_rate_per_unit=_quantile(rates, 0.5),
        exposure_per_doc=exposure_per_doc,
        source_dispersion=_quantile(source_phis, 0.5) if source_phis else 0.0,
        model_dispersion=_quantile(model_phis, 0.5) if model_phis else 0.0,
        provenance=(
            f"measured from Experiment 02 calibration set: {len(human)} human and "
            f"{len(ai)} model documents, {len(rates)} skeletons above the "
            f"{HUMAN_PREVALENCE_FLOOR:.0%} human document-prevalence floor; "
            f"medians reported, dispersions by method of moments"
        ),
    )
    sensitivity = {
        "base_rate_per_unit": (_quantile(rates, 0.25), _quantile(rates, 0.75)),
        "source_dispersion": (_quantile(source_phis, 0.25), _quantile(source_phis, 0.75))
        if source_phis else (0.0, 0.0),
        "model_dispersion": (_quantile(model_phis, 0.25), _quantile(model_phis, 0.75))
        if model_phis else (0.0, 0.0),
        "n_skeletons": len(rates),
        "n_models_observed": len({r["model"] for r in ai}),
        "note": (
            "model_dispersion rests on 6 model arms and is not credibly a point "
            "estimate; treat the interquartile range as the operative uncertainty."
        ),
    }
    return params, sensitivity


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--params", required=True, help="JSON file of ClusterParams fields")
    ap.add_argument("--replicates", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260814)
    ap.add_argument("--smoke", action="store_true", help="tiny grid, mechanics only")
    args = ap.parse_args()

    params = ClusterParams(**json.loads(Path(args.params).read_text(encoding="utf-8")))
    params.validate()
    print(f"parameters: {asdict(params)}\n")

    n_grid = [50, 100] if args.smoke else [100, 200, 400, 600, 851]
    lifts = [TARGET_LIFT] if args.smoke else [1.3, 1.5, 2.0]
    replicates = 20 if args.smoke else args.replicates

    curve = power_curve(params, n_grid, lifts, replicates, args.seed)
    for lift in sorted(curve):
        print(f"lift {lift}:")
        for n in sorted(curve[lift]):
            print(f"  N={n:<5} power={curve[lift][n]:.3f}")

    chosen = select_n(curve, TARGET_LIFT) if TARGET_LIFT in curve else None
    print(f"\nselected N at lift {TARGET_LIFT}, target {POWER_TARGET}: {chosen}")
    if chosen is None:
        if MAX_N in n_grid:
            print(f"STOP CONDITION: {POWER_TARGET:.0%} power at lift {TARGET_LIFT} "
                  f"unreachable at the ceiling N={MAX_N}. Report and stop; "
                  f"do not weaken thresholds.")
        else:
            print(f"Target not reached on the tested grid (max N={max(n_grid)}). "
                  f"This is NOT the stop condition: the ceiling N={MAX_N} was not "
                  f"tested. Re-run with the full grid before concluding anything.")

    print("\nstress scenarios (lift=1.0, no true effect):")
    for scenario in STRESS_SCENARIOS:
        rate = power_at(params, n_grid[-1], 1.0, replicates, args.seed, scenario)
        print(f"  {scenario.name:<22} qualifying rate={rate:.3f}")


if __name__ == "__main__":
    sys.exit(main())
