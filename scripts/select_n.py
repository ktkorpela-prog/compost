"""Select the frozen Experiment 02 sample size N (``EXPERIMENT_02.md`` §8.3).

N is the smallest value achieving >=80% power at true lift 2.0 **across the full
measured nuisance-parameter sensitivity range** — optimistic, point estimate and
pessimistic must all clear 0.80. Selecting at the point estimate alone would
treat measured uncertainty as zero.

High Monte Carlo precision by design: at >=2,000 simulations the standard error
near p=0.80 is about 0.009, enough to resolve the crossing to roughly one grid
step. Nothing here changes thresholds, parameter ranges or the effect size.

Runs no pattern discovery and no confirmatory extraction.

Usage
-----
    python scripts/select_n.py [--replicates 2000]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("sim", ROOT / "scripts" / "simulate_power.py")
sim = importlib.util.module_from_spec(spec)
sys.modules["sim"] = sim
spec.loader.exec_module(sim)

GRID = [50, 60, 65, 70, 75, 80, 90, 100]
EXTENSION = [125, 150, 200, 300, 400, 600, 851]  # used only if the grid is exhausted


def scenarios(params, sens):
    lo_s, hi_s = sens["source_dispersion"]
    lo_m, hi_m = sens["model_dispersion"]
    lo_r, hi_r = sens["base_rate_per_unit"]
    return [
        ("optimistic", replace(params, source_dispersion=lo_s,
                               model_dispersion=lo_m, base_rate_per_unit=hi_r)),
        ("point", params),
        ("pessimistic", replace(params, source_dispersion=hi_s,
                                model_dispersion=hi_m, base_rate_per_unit=lo_r)),
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260815)
    args = ap.parse_args()
    if args.replicates < 2000:
        raise SystemExit("§8.3 requires at least 2,000 simulations per point")

    params, sens = sim.estimate_cluster_params()
    params.validate()
    se = math.sqrt(0.8 * 0.2 / args.replicates)
    print(f"provenance: {params.provenance}")
    print(f"replicates/point: {args.replicates:,}   SE at p=0.80: {se:.4f}")
    print(f"criterion: cell lift >= {sim.CELL_MIN_LIFT}   "
          f"power evaluated at true lift {sim.MIN_EFFECT_OF_INTEREST}\n")

    cases = scenarios(params, sens)
    print(f"{'N':>6}" + "".join(f"{name:>14}" for name, _ in cases) + f"{'all>=0.80':>12}")

    selected = None
    for n in GRID + EXTENSION:
        if n > sim.MAX_N:
            break
        powers = []
        for i, (_, p) in enumerate(cases):
            powers.append(sim.power_at(p, n, sim.MIN_EFFECT_OF_INTEREST,
                                       args.replicates, args.seed + 1000 * i))
        ok = all(v >= sim.POWER_TARGET for v in powers)
        print(f"{n:>6}" + "".join(f"{v:>14.4f}" for v in powers) + f"{'YES' if ok else 'no':>12}")
        if ok and selected is None:
            selected = n
            break
        if n == GRID[-1] and selected is None:
            print(f"  -- grid exhausted at N={n}; extending upward, nothing else changed --")

    print()
    if selected is None:
        print(f"STOP CONDITION: no N <= {sim.MAX_N} reaches {sim.POWER_TARGET:.0%} power "
              f"in all three scenarios. Report and stop; do not weaken thresholds.")
        return

    docs = selected * 5 * 2 * 4  # N x domains x phases x (1 human + 3 AI)
    ceiling_docs = sim.MAX_N * 5 * 2 * 4
    print(f"SELECTED N = {selected}  (smallest N with all three scenarios >= "
          f"{sim.POWER_TARGET:.0%})")
    print(f"  corpus  : {selected} x 5 domains x 2 phases x 4 docs/source = {docs:,} documents")
    print(f"  ceiling : N={sim.MAX_N} -> {ceiling_docs:,} documents")
    print(f"  margin  : N is {sim.MAX_N - selected} below the ceiling "
          f"({selected / sim.MAX_N:.1%} of it); corpus is {docs / ceiling_docs:.1%} of maximum")
    print("\nN is frozen at this value. Unused RAID capacity is not a reason to raise it.")


if __name__ == "__main__":
    sys.exit(main())
