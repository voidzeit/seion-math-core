"""Where does the certificate's factor of ~8 actually come from?

The TT bridge established that M24 is sound on a real truncation pipeline and
measured its tightness at `tau = B_r / ||E|| ~ 7.66` (median). Attributing that
slack to the triangle inequality is an INFERENCE, not a measurement -- M24 can
lose tightness in two structurally different places, and the repair differs:

  DIRECTIONAL   ||M_{v,j} delta|| <= ||M_{v,j}||_op ||delta||
                loose when the realized error direction is far from the
                dominant singular vector of the slot map
                -> needs subspace-restricted amplification, not Gram geometry

  ANGULAR       ||a_v + b_v|| <= ||a_v|| + ||b_v||
                loose when the propagated error and the closure residual are
                not aligned
                -> this is what M25's Gram refinement attacks

In a chain with unreduced leaves the decomposition is unambiguous, because each
vertex has exactly two contributions:

    delta_v = M_{v,1} delta_{v-1}  +  (I - P_v) Rtilde_v
              |___ a_v ___|           |___ b_v ___|

so the two slack factors separate cleanly, per vertex:

    s_op(v)    = ||M||_op ||delta_{v-1}||  /  ||M delta_{v-1}||     >= 1
    s_angle(v) = ( ||a_v|| + ||b_v|| )     /  ||a_v + b_v||         >= 1

Their product is the local inflation of one recursion step. `chi_v`, the cosine
between `a_v` and `b_v`, says whether M25 has room: near 0 or negative means the
triangle step is burning precision, near 1 means it is not and the bottleneck is
elsewhere.

This measures which repair is worth building before building either.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def random_tt(bond, physical, cores, rng):
    train = [rng.standard_normal((physical, bond))]
    for _ in range(cores - 2):
        train.append(rng.standard_normal((bond, physical, bond)))
    train.append(rng.standard_normal((bond, physical)))
    return train


def contract_step(partial, core):
    if core.ndim == 2:
        return (partial @ core).reshape(-1)
    out = np.einsum("Ni,inj->Nnj", partial, core)
    return out.reshape(-1, out.shape[2])


def slot_map(core):
    """M_{v,1}: x -> x . G, as a matrix acting on the bond index of x."""
    return core.reshape(core.shape[0], -1)


def run_instance(train, rank):
    """Two certificates side by side.

    `bound` is M24's: B_v = ||M||_op B_{v-1} + gamma_v, recursive and
    deployable. `oracle` replaces B_{v-1} by the TRUE ||delta_{v-1}||, which is
    not a certificate at all -- it needs the answer -- but it isolates how much
    of M24's slack is ACCUMULATION through the recursion rather than local
    looseness. The gap between the two is the ceiling on what any tightening
    that stays local could ever recover.
    """
    ambient = train[0].copy()
    reduced = train[0].copy()
    previous_delta = np.zeros_like(ambient)      # delta at the leaf-fed vertex
    bound, oracle, rows = 0.0, 0.0, []

    for index, core in enumerate(train[1:], start=1):
        is_root = index == len(train) - 1
        flat = slot_map(core)
        operator_norm = float(np.linalg.svd(flat, compute_uv=False)[0])

        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)

        # a_v = F_v - Rtilde_v = M_{v,1} delta_{v-1}, computed both ways
        propagated = contract_step(previous_delta, core)
        realized_a = float(np.linalg.norm(propagated))
        previous_norm = float(np.linalg.norm(previous_delta))
        operator_a = operator_norm * previous_norm

        if is_root:
            error = ambient - raw
            rows.append({
                "vertex": index, "root": True,
                "s_op": operator_a / realized_a if realized_a > 1e-300 else 1.0,
                "s_angle": 1.0, "chi": float("nan"),
                "realized_gain": (realized_a / previous_norm
                                  if previous_norm > 1e-300 else 0.0),
                "operator_norm": operator_norm,
            })
            return {"error": float(np.linalg.norm(error)),
                    "bound": operator_norm * bound,       # M24's B_r
                    "oracle": operator_a,                 # ||M|| ||delta_true||
                    "rows": rows}

        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        basis = left[:, :keep]
        projected = basis @ (basis.T @ raw)

        a_vector = ambient - raw                  # equals M delta_{v-1}
        b_vector = raw - projected                # (I - P_v) Rtilde_v
        delta = ambient - projected               # a + b

        norm_a = float(np.linalg.norm(a_vector))
        norm_b = float(np.linalg.norm(b_vector))
        norm_delta = float(np.linalg.norm(delta))
        denominator = max(norm_a * norm_b, 1e-300)

        rows.append({
            "vertex": index, "root": False,
            "s_op": operator_a / norm_a if norm_a > 1e-300 else 1.0,
            "s_angle": (norm_a + norm_b) / norm_delta if norm_delta > 1e-300
                       else 1.0,
            "chi": float((a_vector * b_vector).sum() / denominator),
            "realized_gain": (norm_a / previous_norm
                              if previous_norm > 1e-300 else 0.0),
            "operator_norm": operator_norm,
        })

        bound = operator_norm * bound + norm_b
        oracle = operator_norm * previous_norm + norm_b
        reduced = projected
        previous_delta = delta

    raise AssertionError("chain ended without a root")


def percentiles(values, points=(10, 25, 50, 75, 90, 95)):
    array = np.array(values, dtype=float)
    return {str(p): float(np.percentile(array, p)) for p in points}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--rank", type=int, default=5)
    parser.add_argument("--instances", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--json", type=str, default="rg_tt_slack_ledger.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    op_slack, angle_slack, cosines, taus, gain_ratio = [], [], [], [], []
    oracle_taus = []
    for _ in range(args.instances):
        train = random_tt(args.bond, args.physical, args.cores, rng)
        result = run_instance(train, args.rank)
        if result["error"] > 0:
            taus.append(result["bound"] / result["error"])
            oracle_taus.append(result["oracle"] / result["error"])
        for row in result["rows"]:
            op_slack.append(row["s_op"])
            if not row["root"]:
                angle_slack.append(row["s_angle"])
                cosines.append(row["chi"])
            if row["operator_norm"] > 0 and row["realized_gain"] > 0:
                gain_ratio.append(row["realized_gain"] / row["operator_norm"])

    print(f"{args.instances} instances, chain of {args.cores} cores, "
          f"rank {args.rank}\n")
    print(f"  tau_M24    = B_r / ||E||            median "
          f"{np.median(taus):8.4f}   deployable")
    print(f"  tau_oracle = ||M|| ||delta_true|| / ||E||  median "
          f"{np.median(oracle_taus):8.4f}   NOT a certificate")
    print(f"  -> accumulation through the recursion accounts for a factor "
          f"{np.median(taus) / np.median(oracle_taus):.2f}")
    print()
    print("WHERE THE SLACK IS  (per recursion step, 1.0 = no loss)")
    print(f"{'':>26} {'p10':>8} {'p50':>8} {'p90':>8} {'max':>9}")
    for label, values in (("s_op   directional", op_slack),
                          ("s_angle triangle", angle_slack)):
        stats = percentiles(values)
        print(f"{label:>26} {stats['10']:8.4f} {stats['50']:8.4f} "
              f"{stats['90']:8.4f} {max(values):9.4f}")

    print("\nDIRECTIONAL DETAIL   realized gain / ||M||_op   (1.0 = tight)")
    stats = percentiles(gain_ratio)
    print(f"{'':>26} {stats['10']:8.4f} {stats['50']:8.4f} "
          f"{stats['90']:8.4f} {max(gain_ratio):9.4f}")

    print("\nANGLE BETWEEN propagated error and closure residual")
    stats = percentiles(cosines)
    print(f"{'chi':>26} {stats['10']:8.4f} {stats['50']:8.4f} "
          f"{stats['90']:8.4f}")
    median_cos = float(np.median(cosines))

    print("\nREADING")
    op_median = float(np.median(op_slack))
    angle_median = float(np.median(angle_slack))
    if op_median > angle_median * 1.5:
        print("  The DIRECTIONAL step dominates. M25's Gram refinement attacks")
        print("  the angular step and therefore cannot recover most of the")
        print("  slack; subspace-restricted amplification is the lever.")
    elif angle_median > op_median * 1.5:
        print("  The ANGULAR step dominates. M25 has real room here.")
    else:
        print("  Both steps contribute comparably; neither repair alone")
        print("  gets tau near 1.")
    print(f"  median cos(a,b) = {median_cos:+.4f}"
          f"{'  (near-orthogonal: triangle is lossy)' if abs(median_cos) < 0.3 else ''}")

    (HERE / args.json).write_text(json.dumps({
        "config": vars(args),
        "tau_m24": percentiles(taus),
        "tau_oracle": percentiles(oracle_taus),
        "s_op": percentiles(op_slack),
        "s_angle": percentiles(angle_slack),
        "realized_gain_over_op_norm": percentiles(gain_ratio),
        "chi": percentiles(cosines),
    }, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
