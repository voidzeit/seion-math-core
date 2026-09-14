"""Analysis for M37: falsification of the heterogeneity mechanism.

Merges every m37_raw*.json shard (the campaign was run in per-D shards after a
crash, and the shards checkpoint independently).

Hypotheses under test, as stated in the M37 brief:
  H1 heterogeneity WIDTH controls effective interaction dimension
  H2 effective dimension counts distinct spectral SCALES
  H3 topological PLACEMENT matters at fixed multiset
  H4 r_eff is stable in ambient dimension D
  H5 spectrally low rank implies operationally low rank

Every conclusion is labelled EXPERIMENTAL, OPEN, or REFUTED IN TESTED REGIME.
`r_eff_participation` is M31's frozen definition and is what the tables use;
`r_eff_entropy` is the M37 brief's formula and is reported alongside.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci, spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def load_runs() -> list[dict]:
    runs = []
    for path in sorted(RESULTS_DIR.glob("m37_raw*.json")):
        if "placement" in path.name or "smoke" in path.name:
            continue
        runs.extend(json.loads(path.read_text(encoding="utf-8"))["runs"])
    return runs


def ols(x, y):
    """Slope, intercept and a paired bootstrap CI for the slope."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    slope, intercept = np.polyfit(x, y, 1)
    rng = np.random.default_rng(0)
    slopes = []
    for _ in range(2000):
        idx = rng.integers(0, len(x), len(x))
        if len(np.unique(x[idx])) > 1:
            slopes.append(np.polyfit(x[idx], y[idx], 1)[0])
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    return float(slope), float(intercept), float(lo), float(hi)


def main() -> None:
    runs = load_runs()
    dims = sorted({r["dim"] for r in runs})
    print(f"Loaded {len(runs)} runs over D = {dims}\n")

    # ---- per-family table ------------------------------------------------
    print("=== per-family spectral summary (M31 participation-ratio r_eff) ===")
    print(f"{'family':>28} {'D':>4} {'n':>3} {'a_mean':>7} {'a_std':>6} "
          f"{'r_eff':>16} {'R1':>6} {'R4':>6} {'stable':>7} {'|I|/|U|':>8}")
    grouped = defaultdict(list)
    for run in runs:
        grouped[(run["family"], run["dim"])].append(run)

    spectral_rows = []
    for (family, dim) in sorted(grouped, key=lambda k: (k[1], k[0])):
        sel = grouped[(family, dim)]
        reff = [r["r_eff_participation"] for r in sel]
        mean, lo, hi = bootstrap_ci(reff)
        row = {
            "family": family, "dim": dim, "n": len(sel),
            "alpha_mean": statistics.fmean([r["alpha_mean"] for r in sel]),
            "alpha_std": statistics.fmean([r["alpha_std"] for r in sel]),
            "r_eff": mean, "r_eff_lo": lo, "r_eff_hi": hi,
            "r_eff_entropy": statistics.fmean([r["r_eff_entropy"] for r in sel]),
            "R1": statistics.fmean([r["R1"] for r in sel]),
            "R4": statistics.fmean([r["R4"] for r in sel]),
            "stable_rank": statistics.fmean([r["stable_rank"] for r in sel]),
            "interaction_over_first_order": statistics.fmean(
                [r["interaction_over_first_order"] for r in sel]),
            "neg_energy": statistics.fmean([r["negative_energy_fraction"] for r in sel]),
        }
        spectral_rows.append(row)
        print(f"{family:>28} {dim:4d} {len(sel):3d} {row['alpha_mean']:7.3f} "
              f"{row['alpha_std']:6.3f} {mean:6.2f} [{lo:5.2f},{hi:5.2f}] "
              f"{row['R1']:6.3f} {row['R4']:6.3f} {row['stable_rank']:7.3f} "
              f"{row['interaction_over_first_order']:8.2f}")

    # ---- H1 vs the mean-decay alternative --------------------------------
    print("\n=== H1 (width) versus the mean-decay alternative ===")
    print(f"{'D':>4} {'predictor':>12} {'slope':>9} {'CI95':>22} {'Spearman':>9}")
    stats = {}
    for dim in dims:
        sel = [r for r in runs if r["dim"] == dim]
        y = [r["r_eff_participation"] for r in sel]
        for label, key in (("alpha_std", "alpha_std"), ("alpha_mean", "alpha_mean")):
            x = [r[key] for r in sel]
            slope, _, lo, hi = ols(x, y)
            rho = spearman_corr(x, y)
            stats[f"D{dim}_{label}"] = {"slope": slope, "ci": [lo, hi], "spearman": rho}
            print(f"{dim:4d} {label:>12} {slope:9.3f} [{lo:9.3f},{hi:9.3f}] {rho:+9.3f}")

    # degenerate vs baseline, the decisive H1 contrast
    print("\n  decisive H1 contrast (alpha_std = 0 versus the M31 baseline):")
    for dim in dims:
        deg = [r["r_eff_participation"] for r in runs
               if r["dim"] == dim and r["family"].startswith("A0_")]
        base = [r["r_eff_participation"] for r in runs
                if r["dim"] == dim and r["family"].startswith("A3_")]
        if deg and base:
            m1, l1, h1 = bootstrap_ci(deg)
            m2, l2, h2 = bootstrap_ci(base)
            verdict = ("H1 INVERTED" if l1 > h2 else
                       "H1 refuted (no increase)" if m1 >= m2 else "consistent with H1")
            print(f"    D={dim:2d}  degenerate {m1:5.2f} [{l1:.2f},{h1:.2f}]   "
                  f"baseline {m2:5.2f} [{l2:.2f},{h2:.2f}]   -> {verdict}")

    # ---- H4: ambient dimension -------------------------------------------
    if len(dims) > 1:
        print("\n=== H4 (r_eff stable in D) ===")
        print(f"{'family':>28} " + " ".join(f"{'D=' + str(d):>10}" for d in dims))
        for family in sorted({r["family"] for r in runs}):
            cells = []
            for dim in dims:
                sel = [r["r_eff_participation"] for r in runs
                       if r["family"] == family and r["dim"] == dim]
                cells.append(statistics.fmean(sel) if sel else float("nan"))
            print(f"{family:>28} " + " ".join(f"{c:10.2f}" for c in cells))

    # ---- H5: operational value -------------------------------------------
    print("\n=== H5 (spectral low rank implies operational low rank) ===")
    print(f"{'D':>4} {'surrogate':>14} {'R2':>8} {'Spearman':>9} {'regret':>8} "
          f"{'top3':>6}")
    operational_rows = []
    for dim in dims:
        sel = [r for r in runs if r["dim"] == dim]
        names = sorted({k for r in sel for k in r["operational"]})
        for name in names:
            entries = [r["operational"][name] for r in sel if name in r["operational"]]
            row = {
                "dim": dim, "surrogate": name, "n": len(entries),
                "r2": statistics.fmean([e["r2"] for e in entries]),
                "spearman": statistics.fmean([e["spearman"] for e in entries]),
                "decision_regret": statistics.fmean([e["decision_regret"] for e in entries]),
                "top3": statistics.fmean([e["top3_overlap"] for e in entries]),
            }
            operational_rows.append(row)
            print(f"{dim:4d} {name:>14} {row['r2']:8.3f} {row['spearman']:9.3f} "
                  f"{row['decision_regret']:8.3f} {row['top3']:6.3f}")

    # does small r_eff predict small decision regret?
    print("\n  correlation between r_eff and lowrank_q4 decision regret:")
    for dim in dims:
        sel = [r for r in runs if r["dim"] == dim and "lowrank_q4" in r["operational"]]
        if len(sel) > 5:
            x = [r["r_eff_participation"] for r in sel]
            y = [r["operational"]["lowrank_q4"]["decision_regret"] for r in sel]
            print(f"    D={dim:2d}  Spearman(r_eff, regret) = {spearman_corr(x, y):+.3f}"
                  f"   (n={len(sel)})")

    for name, rows in (("m37_spectral_summary.csv", spectral_rows),
                       ("m37_operational_summary.csv", operational_rows)):
        if rows:
            with (RESULTS_DIR / name).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    (RESULTS_DIR / "m37_statistics.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8")
    print("\nWrote m37_spectral_summary.csv, m37_operational_summary.csv, "
          "m37_statistics.json")


if __name__ == "__main__":
    main()
