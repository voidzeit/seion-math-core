"""Analysis for M30, computed entirely from results/branching_interaction_raw.json.

Three questions:

  gate       does the low-rank structure survive branching? (R1/R2/R4, r_eff)
  driver     is |I_uv| explained by topological distance or by shared
             downstream? In a chain these are confounded; in branched families
             they are not, so partial correlations separate them.
  mechanism  do negative marginals show delta_self < 0 with
             delta_cross > |delta_self|, i.e. a destroyed cancellation?
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

from metrics import spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
FAMILIES = ("chain", "balanced", "asymmetric", "random")


def spectrum(interaction: np.ndarray) -> dict:
    singular = np.linalg.svd(interaction, compute_uv=False)
    total = float(np.sum(singular**2))
    if total <= 0:
        return {}
    return {
        "R1": float(singular[0] ** 2 / total),
        "R2": float(np.sum(singular[:2] ** 2) / total),
        "R4": float(np.sum(singular[:4] ** 2) / total),
        "r_eff": float(np.sum(singular) ** 2 / total),
        "r_eff_over_m": float(np.sum(singular) ** 2 / total / interaction.shape[0]),
    }


def partial_spearman(x, y, z) -> float:
    """Spearman of x,y after removing z, via ranks and linear residualization."""
    def rank(values):
        order = np.argsort(np.argsort(np.asarray(values, dtype=float)))
        return (order - order.mean()) / max(order.std(), 1e-30)

    rx, ry, rz = rank(x), rank(y), rank(z)
    rx = rx - np.dot(rx, rz) / max(np.dot(rz, rz), 1e-30) * rz
    ry = ry - np.dot(ry, rz) / max(np.dot(rz, rz), 1e-30) * rz
    denominator = np.linalg.norm(rx) * np.linalg.norm(ry)
    return float(np.dot(rx, ry) / denominator) if denominator > 0 else float("nan")


def main() -> None:
    records = json.loads((RESULTS_DIR / "branching_interaction_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    report: dict = {}
    print("=== GATE: does low-rank survive branching? (m=14 allocatable, 15 internal) ===")
    print(f"{'family':>12} {'regime':>14} {'||I||/||U||':>12} {'R1':>7} {'R2':>7} "
          f"{'R4':>7} {'r_eff':>7} {'r_eff/m':>8}")
    for family in FAMILIES:
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in records if r["family"] == family and r["regime"] == regime]
            spectra, strength = [], []
            for record in rows:
                interaction = np.asarray(record["interaction"], dtype=float)
                utility = np.asarray(list(record["utility"].values()), dtype=float)
                s = spectrum(interaction)
                if s:
                    spectra.append(s)
                if np.linalg.norm(utility) > 0:
                    strength.append(float(np.linalg.norm(interaction) / np.linalg.norm(utility)))
            agg = {k: statistics.fmean([s[k] for s in spectra]) for k in spectra[0]}
            agg["strength"] = statistics.fmean(strength)
            report[f"{family}_{regime}"] = agg
            print(f"{family:>12} {regime:>14} {agg['strength']:12.2f} {agg['R1']:7.3f} "
                  f"{agg['R2']:7.3f} {agg['R4']:7.3f} {agg['r_eff']:7.2f} {agg['r_eff_over_m']:8.3f}")

    print("\n=== DRIVER: distance vs shared downstream ===")
    print(f"{'family':>12} {'n_pairs':>9} {'rho(|I|,dist)':>15} {'rho(|I|,shared)':>16} "
          f"{'partial|shared':>15} {'partial|dist':>13}")
    driver: dict = {}
    for family in FAMILIES:
        pairs = [p for r in records if r["family"] == family for p in r["pair_geometry"]]
        magnitude = [abs(p["value"]) for p in pairs]
        distance = [p["distance"] for p in pairs]
        shared = [p["shared_downstream"] for p in pairs]
        entry = {
            "n_pairs": len(pairs),
            "rho_distance": spearman_corr(magnitude, distance),
            "rho_shared": spearman_corr(magnitude, shared),
            "partial_distance_given_shared": partial_spearman(magnitude, distance, shared),
            "partial_shared_given_distance": partial_spearman(magnitude, shared, distance),
        }
        driver[family] = entry
        print(f"{family:>12} {entry['n_pairs']:9d} {entry['rho_distance']:+15.3f} "
              f"{entry['rho_shared']:+16.3f} {entry['partial_distance_given_shared']:+15.3f} "
              f"{entry['partial_shared_given_distance']:+13.3f}")

    print("\n=== relation class: mean |I_uv| ===")
    print(f"{'family':>12} {'ancestor_desc':>15} {'diff_branch':>13} {'ratio':>7}")
    for family in FAMILIES:
        pairs = [p for r in records if r["family"] == family for p in r["pair_geometry"]]
        groups = defaultdict(list)
        for p in pairs:
            groups[p["relation"]].append(abs(p["value"]))
        anc = statistics.fmean(groups["ancestor_descendant"]) if groups["ancestor_descendant"] else float("nan")
        dif = statistics.fmean(groups["different_branch"]) if groups["different_branch"] else float("nan")
        ratio = anc / dif if dif and dif == dif and dif > 0 else float("nan")
        print(f"{family:>12} {anc:15.3e} {dif:13.3e} {ratio:7.2f}")

    print("\n=== MECHANISM: single-source decomposition of negative marginals ===")
    linearity = [r["linearity_residual"] for r in records]
    print(f"linearity residual ||sum c_v - E_total|| / ||E_total||: "
          f"median {statistics.median(linearity):.3f}, p90 {np.percentile(linearity, 90):.3f}")
    entries = [m for r in records for m in r["mechanism"]]
    negative = [m for m in entries if m["utility"] < 0]
    positive = [m for m in entries if m["utility"] >= 0]
    print(f"\n{'group':>10} {'n':>6} {'self<0':>8} {'cross>0':>9} "
          f"{'cross>|self|':>13} {'both':>7}")
    for label, group in (("negative", negative), ("positive", positive)):
        n = len(group)
        self_neg = sum(1 for m in group if m["delta_self"] < 0)
        cross_pos = sum(1 for m in group if m["delta_cross"] > 0)
        dominates = sum(1 for m in group if m["delta_cross"] > abs(m["delta_self"]))
        both = sum(1 for m in group
                   if m["delta_self"] < 0 and m["delta_cross"] > abs(m["delta_self"]))
        print(f"{label:>10} {n:6d} {100*self_neg/n:7.1f}% {100*cross_pos/n:8.1f}% "
              f"{100*dominates/n:12.1f}% {100*both/n:6.1f}%")

    report["driver"] = driver
    (RESULTS_DIR / "branching_interaction_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/branching_interaction_analysis.json")


if __name__ == "__main__":
    main()
