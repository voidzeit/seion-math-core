"""Analysis for M31, computed entirely from results/interaction_dimension_raw.json.

M31A  r_eff against ambient dimension D. The diagnostic is r_eff/D: constant
      means the apparent low rank was an artifact of a small ambient space,
      falling means there is a latent interaction dimension below D.
M31B  stability of the leading subspace, via the chordal overlap
      S_q(A,B) = ||Q_A^T Q_B||_F^2 / q, compared across budgets (same instance)
      and across seeds (same architecture, different instance). The reference
      value for unrelated q-dimensional subspaces of R^m is q/m.
M31C  R2_Q(x) = ||Q Q^T x||^2 / ||x||^2 for node-indexed features, against the
      same q/m baseline and an explicit random-vector control.

Signed inertia: I is symmetric, so what matters for the quadratic surrogate is
the eigenvalue sign pattern, not the singular values reported so far.
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
Q_MODES = 4
FEATURES = ("constant", "depth", "local_error", "path_weight", "rank", "abs_utility")


def decompose(record: dict) -> dict:
    interaction = np.asarray(record["interaction"], dtype=float)
    m = interaction.shape[0]
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    energy = float(np.sum(eigenvalues**2))
    if energy <= 0:
        return {}

    q = min(Q_MODES, m)
    basis = eigenvectors[:, :q]

    explained = {}
    for name in FEATURES:
        x = np.asarray(record["features"][name], dtype=float)
        norm = float(np.dot(x, x))
        explained[name] = (float(np.dot(basis.T @ x, basis.T @ x) / norm)
                           if norm > 0 else float("nan"))
    rng = np.random.default_rng(0)
    controls = []
    for _ in range(20):
        x = rng.standard_normal(m)
        controls.append(float(np.dot(basis.T @ x, basis.T @ x) / np.dot(x, x)))
    explained["random_control"] = statistics.fmean(controls)

    return {
        "m": m,
        "R1": float(eigenvalues[0] ** 2 / energy),
        "R2": float(np.sum(eigenvalues[:2] ** 2) / energy),
        "R4": float(np.sum(eigenvalues[:4] ** 2) / energy),
        "R8": float(np.sum(eigenvalues[:8] ** 2) / energy) if m >= 8 else None,
        "r_eff": float(np.sum(np.abs(eigenvalues)) ** 2 / energy),
        "negative_energy_fraction": float(
            np.sum(eigenvalues[eigenvalues < 0] ** 2) / energy),
        "n_positive": int(np.sum(eigenvalues > 0)),
        "n_negative": int(np.sum(eigenvalues < 0)),
        "leading_sign_pattern": "".join(
            "+" if value > 0 else "-" for value in eigenvalues[:q]),
        "basis": basis,
        "explained": explained,
    }


def overlap(a: np.ndarray, b: np.ndarray) -> float:
    q = a.shape[1]
    return float(np.linalg.norm(a.T @ b) ** 2 / q)


def main() -> None:
    records = json.loads((RESULTS_DIR / "interaction_dimension_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    analysed = []
    for record in records:
        result = decompose(record)
        if result:
            result.update({k: record[k] for k in
                           ("family", "dim", "regime", "seed", "budget_fraction")})
            analysed.append(result)

    print("=== M31A: does the low rank survive growing ambient dimension? ===")
    print(f"{'D':>4} {'regime':>14} {'m':>4} {'R1':>6} {'R2':>6} {'R4':>6} {'R8':>6} "
          f"{'r_eff':>7} {'r_eff/D':>8} {'r_eff/m':>8}")
    scaling = {}
    for dim in sorted({r["dim"] for r in analysed}):
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in analysed if r["dim"] == dim and r["regime"] == regime]
            if not rows:
                continue

            def mean(field):
                values = [r[field] for r in rows if r[field] is not None]
                return statistics.fmean(values) if values else float("nan")

            entry = {k: mean(k) for k in ("R1", "R2", "R4", "R8", "r_eff", "m")}
            entry["r_eff_over_D"] = entry["r_eff"] / dim
            entry["r_eff_over_m"] = entry["r_eff"] / entry["m"]
            scaling[f"D{dim}_{regime}"] = entry
            print(f"{dim:4d} {regime:>14} {entry['m']:4.0f} {entry['R1']:6.3f} "
                  f"{entry['R2']:6.3f} {entry['R4']:6.3f} {entry['R8']:6.3f} "
                  f"{entry['r_eff']:7.2f} {entry['r_eff_over_D']:8.3f} "
                  f"{entry['r_eff_over_m']:8.3f}")

    print("\n=== signed inertia of I (symmetric; sign pattern drives convexity) ===")
    print(f"{'D':>4} {'regime':>14} {'neg energy':>11} {'n_pos':>6} {'n_neg':>6} "
          f"{'leading signs':>15}")
    for dim in sorted({r["dim"] for r in analysed}):
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in analysed if r["dim"] == dim and r["regime"] == regime]
            if not rows:
                continue
            patterns = defaultdict(int)
            for r in rows:
                patterns[r["leading_sign_pattern"]] += 1
            common = max(patterns.items(), key=lambda kv: kv[1])
            print(f"{dim:4d} {regime:>14} "
                  f"{statistics.fmean([r['negative_energy_fraction'] for r in rows]):11.3f} "
                  f"{statistics.fmean([r['n_positive'] for r in rows]):6.1f} "
                  f"{statistics.fmean([r['n_negative'] for r in rows]):6.1f} "
                  f"{common[0]:>10} ({100*common[1]//len(rows):2d}%)")

    print("\n=== M31B: stability of the leading subspace (S_q; q/m is the null) ===")
    print(f"{'D':>4} {'regime':>14} {'across budgets':>16} {'across seeds':>14} {'null q/m':>10}")
    for dim in sorted({r["dim"] for r in analysed}):
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in analysed if r["dim"] == dim and r["regime"] == regime]
            if not rows:
                continue
            by_instance = defaultdict(list)
            by_state = defaultdict(list)
            for r in rows:
                by_instance[(r["family"], r["seed"])].append(r)
                by_state[(r["family"], r["budget_fraction"])].append(r)
            budget_scores, seed_scores = [], []
            for group in by_instance.values():
                for a in range(len(group)):
                    for b in range(a + 1, len(group)):
                        if group[a]["m"] == group[b]["m"]:
                            budget_scores.append(overlap(group[a]["basis"], group[b]["basis"]))
            for group in by_state.values():
                for a in range(len(group)):
                    for b in range(a + 1, len(group)):
                        if group[a]["m"] == group[b]["m"]:
                            seed_scores.append(overlap(group[a]["basis"], group[b]["basis"]))
            null = Q_MODES / statistics.fmean([r["m"] for r in rows])
            print(f"{dim:4d} {regime:>14} "
                  f"{statistics.fmean(budget_scores) if budget_scores else float('nan'):16.3f} "
                  f"{statistics.fmean(seed_scores) if seed_scores else float('nan'):14.3f} "
                  f"{null:10.3f}")

    print("\n=== M31C: how much of each node feature lies in the leading subspace ===")
    header = " ".join(f"{name[:11]:>12}" for name in FEATURES) + f"{'random':>12}"
    print(f"{'D':>4} {'regime':>14} {header}")
    for dim in sorted({r["dim"] for r in analysed}):
        for regime in ("iid", "heterogeneous"):
            rows = [r for r in analysed if r["dim"] == dim and r["regime"] == regime]
            if not rows:
                continue
            values = []
            for name in list(FEATURES) + ["random_control"]:
                items = [r["explained"][name] for r in rows
                         if r["explained"][name] == r["explained"][name]]
                values.append(statistics.fmean(items) if items else float("nan"))
            print(f"{dim:4d} {regime:>14} " + " ".join(f"{v:12.3f}" for v in values))

    (RESULTS_DIR / "interaction_dimension_analysis.json").write_text(
        json.dumps(scaling, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/interaction_dimension_analysis.json")


if __name__ == "__main__":
    main()
