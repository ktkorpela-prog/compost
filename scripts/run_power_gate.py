"""Run the Experiment 02 power gate (``EXPERIMENT_02.md`` §8).

Uses parameters measured from the calibration set, and reports the selected N
across the credible sensitivity ranges rather than at a single point estimate.

Runs no pattern discovery and no confirmatory extraction.

Usage
-----
    python scripts/run_power_gate.py [--replicates N]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("sim", ROOT / "scripts" / "simulate_power.py")
sim = importlib.util.module_from_spec(spec)
sys.modules["sim"] = sim
spec.loader.exec_module(sim)

GRID = [100, 200, 400, 600, 851]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicates", type=int, default=120)
    ap.add_argument("--seed", type=int, default=20260814)
    args = ap.parse_args()

    params, sens = sim.estimate_cluster_params()
    params.validate()
    print(f"provenance: {params.provenance}\n")
    print(f"point estimates: base_rate={params.base_rate_per_unit:.5f} "
          f"exposure/doc={params.exposure_per_doc:.2f} "
          f"source_phi={params.source_dispersion:.3f} "
          f"model_phi={params.model_dispersion:.3f}\n")

    print(f"=== POWER CURVE, lift {sim.TARGET_LIFT}, {args.replicates} replicates ===")
    curve = sim.power_curve(params, GRID, [sim.TARGET_LIFT], args.replicates, args.seed)
    for n in GRID:
        print(f"  N={n:<5} power={curve[sim.TARGET_LIFT][n]:.3f}")
    chosen = sim.select_n(curve, sim.TARGET_LIFT)
    print(f"\nselected N (>= {sim.POWER_TARGET:.0%} power): {chosen}")
    print(f"within ceiling N<={sim.MAX_N}: "
          f"{'YES' if chosen is not None else 'NOT REACHED ON GRID'}")

    print("\n=== SENSITIVITY across credible clustering ranges ===")
    lo_s, hi_s = sens["source_dispersion"]
    lo_m, hi_m = sens["model_dispersion"]
    lo_r, hi_r = sens["base_rate_per_unit"]
    scenarios = [
        ("optimistic  (low phi, high rate)", replace(params, source_dispersion=lo_s,
                                                     model_dispersion=lo_m,
                                                     base_rate_per_unit=hi_r)),
        ("point estimate", params),
        ("pessimistic (high phi, low rate)", replace(params, source_dispersion=hi_s,
                                                     model_dispersion=hi_m,
                                                     base_rate_per_unit=lo_r)),
    ]
    for label, p in scenarios:
        c = sim.power_curve(p, GRID, [sim.TARGET_LIFT], args.replicates, args.seed)
        n = sim.select_n(c, sim.TARGET_LIFT)
        powers = " ".join(f"{k}:{c[sim.TARGET_LIFT][k]:.2f}" for k in GRID)
        print(f"  {label:<34} selected N={str(n):<6} [{powers}]")

    print("\n=== STRESS SCENARIOS (lift 1.0, no true effect) ===")
    for scenario in sim.STRESS_SCENARIOS:
        rate = sim.power_at(params, sim.MAX_N, 1.0, args.replicates, args.seed, scenario)
        print(f"  {scenario.name:<24} qualifying rate={rate:.3f}")


if __name__ == "__main__":
    sys.exit(main())
