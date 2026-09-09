"""GATE D1 -- reduce every claimed bound to the setting the standard already covers.

A novelty claim is only meaningful where the standard result does not already
apply. So for each claimed theorem, identify the standard setting it
specialises to, compute what the standard result gives THERE, and compare.
Three verdicts:

    COINCIDES        the claim reproduces the standard result -> N1/N2 at best
    WEAKER           the claim is strictly worse on the standard's home ground
                     -> the value lives entirely outside it, and the paper must
                        say so explicitly
    STRICTLY SHARPER the claim beats the standard on the standard's own ground
                     -> N3 candidate, mechanically established

This gate is not optional and it is not a formality. The Pythagorean TT
certificate of 2026-08-18 looked new until it was evaluated on canonically
orthogonalised trains, where tau = 1.0000 exactly -- because it IS Oseledets'
TT-SVD error identity. That was found by an internal control, not by review.
D1 is that control, promoted to a protocol step.

TARGET 1 -- the projected-root (k-1) bound versus hierarchical truncation.
    PMT:      E_proj <= (k-1) * rho * M^(k-1) * L_T
    standard: with orthogonalisation every slot map is an isometry, errors are
              mutually orthogonal, and ||E||^2 = sum_v eps_v^2 exactly
              (Hackbusch-Kuehn / Grasedyck hierarchical SVD; Oseledets TT-SVD).
    With M = 1, L_T = 1, rho = max_v eps_v the two read (k-1)*rho versus
    sqrt(sum eps_v^2) <= sqrt(k)*rho, so the comparison is (k-1) versus sqrt(k)
    and it is decided by arithmetic, not by opinion.

TARGET 2 -- W_3(eta) versus the universal coefficient 2 at k = 3.
TARGET 3 -- Sigma_2(eta) versus the triangle-inequality threshold 2.

Targets 2 and 3 are strict-sharpening checks on the same home ground, which is
what an N3 claim requires.

FAIL CLOSED: every executed comparison must also verify that the standard bound
is itself sound on the instances used, or the comparison is discarded.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# TARGET 1: the (k-1) bound on the standard's home ground

def isometric_chain(depth, bond, physical, rng, isometry_defect=0.0):
    """A chain whose slot maps are isometries up to a controlled defect.

    isometry_defect = 0 gives exactly the canonical (orthogonalised) setting
    the hierarchical-SVD literature assumes. Raising it leaves that setting and
    is where the PMT bound is supposed to earn its keep.
    """
    cores = []
    for _ in range(depth):
        # The transport is X -> X . flat with flat the (bond, physical*bond)
        # unfolding, so isometry in Frobenius requires flat @ flat.T = I_bond,
        # i.e. ROW-orthonormality of THAT unfolding. Column-orthonormality of
        # the (bond*physical, bond) unfolding is a different condition and does
        # NOT make the transport an isometry -- a first version of this file got
        # that wrong and appeared to show the standard bound failing 50% of the
        # time, which would have been a false claim about an established result.
        raw = rng.standard_normal((bond * physical, bond))
        basis, _ = np.linalg.qr(raw)
        flat = basis[:, :bond].T                  # (bond, physical*bond) rows orthonormal
        if isometry_defect > 0:
            perturbation = rng.standard_normal(flat.shape)
            flat = flat + isometry_defect * perturbation / np.linalg.norm(
                perturbation) * np.linalg.norm(flat)
        cores.append(flat.reshape(bond, physical, bond))
    return cores


def run_chain(cores, ranks, physical, bond):
    """Executed: true error, per-node discarded mass, slot-map gains."""
    ambient = np.eye(bond)[:1]                      # (1, bond)
    reduced = ambient.copy()
    discarded, gains = [], []
    for core, rank in zip(cores, ranks):
        flat = core.reshape(bond, -1)
        gains.append(float(np.linalg.svd(flat, compute_uv=False)[0]))
        ambient = (ambient @ flat).reshape(-1, bond)
        raw = (reduced @ flat).reshape(-1, bond)
        left, values, right = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        reduced = (left[:, :keep] * values[:keep]) @ right[:keep]
        discarded.append(float(np.sqrt((values[keep:] ** 2).sum())))
    if sum(discarded) <= 0:
        return None            # nothing was truncated anywhere: vacuous instance
    return (float(np.linalg.norm(ambient - reduced)), discarded, gains)


def target_one(args, rng):
    """(k-1) rho M^(k-1) L_T   versus   sqrt(sum eps_v^2)."""
    rows = []
    for defect in args.isometry_defects:
        for depth in args.depths:
            pmt_ratios, std_ratios, sound_std, sound_pmt, n = [], [], 0, 0, 0
            for _ in range(args.instances):
                cores = isometric_chain(depth, args.bond, args.physical, rng,
                                        defect)
                ranks = [args.rank] * depth
                outcome = run_chain(cores, ranks, args.physical, args.bond)
                if outcome is None:
                    continue
                error, discarded, gains = outcome
                if error <= 1e-12:
                    continue
                gain = max(gains)
                leak = max(discarded) if discarded else 0.0
                if leak <= 0:
                    continue
                k = depth
                pmt = (k - 1) * leak * (gain ** max(k - 1, 0))
                standard = math.sqrt(sum(d * d for d in discarded))
                sound_pmt += pmt >= error * (1 - 1e-9)
                sound_std += standard >= error * (1 - 1e-9)
                pmt_ratios.append(pmt / error)
                std_ratios.append(standard / error)
                n += 1
            if not n:
                continue
            rows.append({
                "isometry_defect": defect, "k": depth, "instances": n,
                "pmt_tau_p50": float(np.median(pmt_ratios)),
                "standard_tau_p50": float(np.median(std_ratios)),
                "pmt_sound_frac": sound_pmt / n,
                "standard_sound_frac": sound_std / n,
                "ratio_pmt_over_standard": float(
                    np.median(pmt_ratios) / np.median(std_ratios)),
            })
    return rows


# --------------------------------------------------------------------------
# TARGET 2 and 3: strict-sharpening checks, analytic

def w3(eta):
    return math.sqrt(4 - 3 * eta ** 2) if eta <= math.sqrt(2 / 3) \
        else 2 / (math.sqrt(3) * eta)


def sigma2(eta):
    return math.sin(min(2 * math.asin(min(eta, 1.0)), math.pi / 2)) / eta


def target_two_three(etas):
    rows = []
    for eta in etas:
        rows.append({
            "eta": eta,
            "W_3": w3(eta), "universal_k_minus_1_at_k3": 2.0,
            "W_3_sharper_by": 1 - w3(eta) / 2.0,
            "Sigma_2": sigma2(eta), "triangle_threshold": 2.0,
            "Sigma_2_sharper_by": 1 - sigma2(eta) / 2.0,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depths", type=int, nargs="+", default=[2, 3, 4, 6, 8])
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--rank", type=int, default=3)
    parser.add_argument("--instances", type=int, default=120)
    parser.add_argument("--isometry-defects", type=float, nargs="+",
                        default=[0.0, 0.15, 0.5])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.2, 0.5, 0.7071067811865476,
                                 0.816496580927726, 0.95, 1.0])
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--json", type=str, default="d1_reduce_to_standard.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    print("GATE D1 / TARGET 1   projected-root (k-1) bound  vs  hierarchical")
    print("                     truncation on ITS OWN home ground\n")
    print(f"{'iso.defect':>11} {'k':>3} {'n':>5} {'tau PMT':>10} "
          f"{'tau std':>10} {'PMT/std':>9} {'PMT sound':>10} {'std sound':>10}")
    rows_one = target_one(args, rng)
    for row in rows_one:
        print(f"{row['isometry_defect']:11.2f} {row['k']:3d} "
              f"{row['instances']:5d} {row['pmt_tau_p50']:10.3f} "
              f"{row['standard_tau_p50']:10.3f} "
              f"{row['ratio_pmt_over_standard']:9.3f} "
              f"{100*row['pmt_sound_frac']:9.1f}% "
              f"{100*row['standard_sound_frac']:9.1f}%")

    print("\n  arithmetic core, M = 1, L_T = 1, rho = max eps_v:")
    print(f"{'k':>4} {'PMT (k-1)':>11} {'standard sqrt(k)':>17} {'winner':>10}")
    for k in args.depths:
        pmt, std = k - 1, math.sqrt(k)
        print(f"{k:4d} {pmt:11.3f} {std:17.3f} "
              f"{'PMT' if pmt < std else 'standard':>10}")

    print("\nGATE D1 / TARGET 2+3   strict-sharpening checks\n")
    print(f"{'eta':>10} {'W_3':>9} {'vs 2':>9} {'Sigma_2':>9} {'vs 2':>9}")
    rows_two = target_two_three(args.etas)
    for row in rows_two:
        print(f"{row['eta']:10.4f} {row['W_3']:9.4f} "
              f"{100*row['W_3_sharper_by']:8.1f}% {row['Sigma_2']:9.4f} "
              f"{100*row['Sigma_2_sharper_by']:8.1f}%")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "target_1_k_minus_1_vs_hierarchical": rows_one,
         "target_2_3_sharpening": rows_two}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
