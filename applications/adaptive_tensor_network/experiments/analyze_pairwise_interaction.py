"""Analysis for M29, computed entirely from results/pairwise_interaction_raw.json.

Decides between the four structural hypotheses for the interaction matrix I:

  local            |I_uv| decays with topological distance d_T(u,v)
  low-rank         few singular values carry the energy
  sparse-nonlocal  most pairs negligible, a few strong
  dense high-rank  allocation is genuinely global

Metrics:
  strength   ||I||_F / ||U||_2, i.e. second-order size against first-order
  decay      E[|I_uv| | d_T(u,v) = d]
  r_eff      (sum sigma_i)^2 / sum sigma_i^2, participation ratio of the spectrum
  R_q        fraction of spectral energy in the top q modes
  sparsity   fraction of pairs carrying 50 / 80 / 95% of sum I_uv^2
  reversals  how often bumping one node flips the utility order of two others
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def per_record(record: dict) -> dict:
    interaction = np.asarray(record["interaction"], dtype=float)
    distance = np.asarray(record["distance"], dtype=int)
    utility = np.asarray([record["utility"][n] for n in record["eligible"]], dtype=float)
    m = interaction.shape[0]

    upper = np.triu_indices(m, k=1)
    pair_values = interaction[upper]
    energy = float(np.sum(pair_values**2))

    singular = np.linalg.svd(interaction, compute_uv=False)
    total = float(np.sum(singular**2))
    spectrum = {
        f"R{q}": (float(np.sum(singular[:q] ** 2) / total) if total > 0 and m >= q else None)
        for q in (1, 2, 4, 8)
    }
    r_eff = (float(np.sum(singular) ** 2 / total) if total > 0 else float("nan"))

    ordered = np.sort(pair_values**2)[::-1]
    cumulative = np.cumsum(ordered) / energy if energy > 0 else np.zeros_like(ordered)
    sparsity = {
        f"frac_pairs_for_{int(100 * level)}pct":
            (float((np.searchsorted(cumulative, level) + 1) / len(ordered))
             if energy > 0 else None)
        for level in (0.5, 0.8, 0.95)
    }

    by_distance = defaultdict(list)
    for i, j in zip(*upper):
        by_distance[int(distance[i, j])].append(abs(float(interaction[i, j])))

    return {
        "m": m,
        "strength": (float(np.linalg.norm(interaction) / np.linalg.norm(utility))
                     if np.linalg.norm(utility) > 0 else float("nan")),
        "r_eff": r_eff,
        "r_eff_over_m": r_eff / m,
        **spectrum,
        **sparsity,
        "by_distance": {d: statistics.fmean(v) for d, v in by_distance.items()},
        "reversal_rate": (record["order_reversals"] / record["order_comparisons"]
                          if record["order_comparisons"] else float("nan")),
    }


def main() -> None:
    records = json.loads((RESULTS_DIR / "pairwise_interaction_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    grouped = defaultdict(list)
    for record in records:
        grouped[(record["regime"], record["depth"])].append(per_record(record))

    report = {}
    for key, rows in sorted(grouped.items()):
        def mean_of(field):
            values = [r[field] for r in rows if r[field] is not None and r[field] == r[field]]
            return statistics.fmean(values) if values else None

        distance_curve = defaultdict(list)
        for row in rows:
            for d, value in row["by_distance"].items():
                distance_curve[int(d)].append(value)

        report[f"{key[0]}_k{key[1]}"] = {
            "n_configs": len(rows),
            "mean_eligible_nodes": mean_of("m"),
            "interaction_strength": mean_of("strength"),
            "r_eff": mean_of("r_eff"),
            "r_eff_over_m": mean_of("r_eff_over_m"),
            "spectral_energy": {q: mean_of(q) for q in ("R1", "R2", "R4", "R8")},
            "sparsity": {q: mean_of(q) for q in (
                "frac_pairs_for_50pct", "frac_pairs_for_80pct", "frac_pairs_for_95pct")},
            "reversal_rate": mean_of("reversal_rate"),
            "mean_abs_interaction_by_distance": {
                str(d): statistics.fmean(v) for d, v in sorted(distance_curve.items())
            },
        }

    (RESULTS_DIR / "pairwise_interaction_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print(f"{'regime':>15} {'k':>4} {'m':>5} {'||I||/||U||':>12} {'r_eff':>7} "
          f"{'r_eff/m':>8} {'R1':>6} {'R2':>6} {'R4':>6} {'pairs@80%':>10} {'revers':>7}")
    for key in sorted(grouped, key=lambda x: (x[0], x[1])):
        e = report[f"{key[0]}_k{key[1]}"]
        s, sp = e["spectral_energy"], e["sparsity"]
        print(f"{key[0]:>15} {key[1]:4d} {e['mean_eligible_nodes']:5.1f} "
              f"{e['interaction_strength']:12.2f} {e['r_eff']:7.2f} {e['r_eff_over_m']:8.3f} "
              f"{s['R1']:6.3f} {s['R2']:6.3f} {s['R4']:6.3f} "
              f"{sp['frac_pairs_for_80pct']:10.3f} {e['reversal_rate']:7.3f}")

    print("\n=== decay of mean |I_uv| with topological distance ===")
    for regime in ("iid", "heterogeneous"):
        for depth in (10, 24):
            key = f"{regime}_k{depth}"
            if key not in report:
                continue
            curve = report[key]["mean_abs_interaction_by_distance"]
            head = sorted(curve.items(), key=lambda kv: int(kv[0]))[:8]
            shown = "  ".join(f"d={d}:{v:.2e}" for d, v in head)
            print(f"{regime:>15} k={depth:2d}  {shown}")

    print("\nWrote analysis to results/pairwise_interaction_analysis.json")


if __name__ == "__main__":
    main()
