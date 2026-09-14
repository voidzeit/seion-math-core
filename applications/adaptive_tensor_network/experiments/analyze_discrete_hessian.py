"""Analysis for the M31 inertia correction.

Reports, side by side:

  I = H with its diagonal zeroed -- what M31 actually measured. Its inertia is
      forced: tr(I) = 0 means the eigenvalues sum to zero, so any nonzero I is
      indefinite with roughly balanced counts and ~50% negative energy. This
      column is a design tautology and is shown only to make that visible.

  H = the full discrete Hessian, diagonal included. This is the object whose
      inertia decides whether the quadratic surrogate is convex.

Also reported: the sign of the diagonal itself (is the error convex in a single
coordinate?) and the diagonal dominance ratio, which controls how much the
off-diagonal coupling can overturn.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def inertia(matrix: np.ndarray) -> dict:
    eigenvalues = np.linalg.eigvalsh(matrix)
    energy = float(np.sum(eigenvalues**2))
    if energy <= 0:
        return {"neg_energy": 0.0, "n_pos": 0, "n_neg": 0, "min_eig": 0.0, "psd": True}
    return {
        "neg_energy": float(np.sum(eigenvalues[eigenvalues < 0] ** 2) / energy),
        "n_pos": int(np.sum(eigenvalues > 0)),
        "n_neg": int(np.sum(eigenvalues < 0)),
        "min_eig": float(eigenvalues[0]),
        "psd": bool(eigenvalues[0] >= -1e-12),
    }


def main() -> None:
    records = json.loads((RESULTS_DIR / "discrete_hessian_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    print("=== inertia of I (diagonal zeroed) vs H (full discrete Hessian) ===")
    print(f"{'D':>4} {'regime':>14} {'m':>4} | {'I negE':>7} {'I n+':>5} {'I n-':>5} "
          f"| {'H negE':>7} {'H n+':>5} {'H n-':>5} {'H PSD':>7} | {'diag>0':>7} {'domin':>7}")

    report = {}
    for dim in sorted({r["dim"] for r in records}):
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in records if r["dim"] == dim and r["regime"] == regime]
            if not rows:
                continue
            i_stats, h_stats, diag_positive, dominance = [], [], [], []
            for record in rows:
                full = np.asarray(record["hessian"], dtype=float)
                offdiag = full - np.diag(np.diag(full))
                i_stats.append(inertia(offdiag))
                h_stats.append(inertia(full))
                diagonal = np.diag(full)
                diag_positive.append(float(np.mean(diagonal > 0)))
                offsum = np.abs(offdiag).sum(axis=1)
                dominance.append(float(np.mean(np.abs(diagonal) / np.maximum(offsum, 1e-30))))

            def mean(stats, key):
                return statistics.fmean([s[key] for s in stats])

            entry = {
                "I_neg_energy": mean(i_stats, "neg_energy"),
                "H_neg_energy": mean(h_stats, "neg_energy"),
                "H_psd_fraction": statistics.fmean([float(s["psd"]) for s in h_stats]),
                "diag_positive_fraction": statistics.fmean(diag_positive),
                "diagonal_dominance": statistics.fmean(dominance),
            }
            report[f"D{dim}_{regime}"] = entry
            print(f"{dim:4d} {regime:>14} {rows[0]['m']:4d} | "
                  f"{entry['I_neg_energy']:7.3f} {mean(i_stats,'n_pos'):5.1f} {mean(i_stats,'n_neg'):5.1f} | "
                  f"{entry['H_neg_energy']:7.3f} {mean(h_stats,'n_pos'):5.1f} {mean(h_stats,'n_neg'):5.1f} "
                  f"{100*entry['H_psd_fraction']:6.0f}% | "
                  f"{100*entry['diag_positive_fraction']:6.0f}% {entry['diagonal_dominance']:7.3f}")

    print("\ndiag>0  = fraction of nodes whose error is locally convex in its own rank")
    print("domin   = mean |H_vv| / sum_u |H_uv|; > 1 would mean diagonal dominance")
    print("H PSD   = fraction of configurations whose full Hessian is positive semidefinite")

    (RESULTS_DIR / "discrete_hessian_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/discrete_hessian_analysis.json")


if __name__ == "__main__":
    main()
