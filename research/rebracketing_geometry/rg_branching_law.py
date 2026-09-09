"""Branching amplification is intrinsic, and it has a closed form.

The chain result of 2026-08-18 was a collapse: right-orthogonalization drove the
Pythagorean certificate to `tau = 1` exactly, making it a rediscovery of the
TT-SVD error identity and killing the certificate line for chains. The gauge
battery then showed the earlier `tau ~ 9.5` was a pure gauge artifact
(`kappa_intrinsic = 1` for chains).

This file asks whether BRANCHING escapes that collapse, and answers it with a
mechanism rather than an observation.

DERIVATION. At a branching node with children bonds `r_1, r_2` and parent bond
`r_p`, canonicalization makes the parent-directed unfolding `U` of shape
`(r_1 r_2, r_p)` satisfy `U^T U = I`. Transport of an error is `x -> U^T x`, and

    || U^T x ||  =  || P x ||,        P = U U^T

with `P` the orthogonal projector onto an `r_p`-dimensional subspace of
`R^{r_1 r_2}`. So the node does not amplify -- it PROJECTS AWAY. For an error
direction generic relative to that subspace,

    E || P x ||^2  =  (r_p / r_1 r_2) || x ||^2

while the certificate still charges gain `||U||_op = 1`. Hence

    tau  ~  sqrt( r_1 r_2 / r_p ).                                        (*)

WHY NO GAUGE REMOVES IT. A bond gauge is an invertible `A`; invertible maps do
not change dimensions, so both `r_1 r_2` and `r_p` are gauge invariant, and so
is their ratio. Moreover the reachable error subspace has dimension
`(r_1 - k) k + k (r_2 - k)`, which for the tested settings exceeds `r_p`, so it
cannot be embedded in `Ran(U)` under ANY gauge -- the same dimension count.

A chain is the special case `r_p = r_1 r_2` of a node with no compression, where
(*) gives `tau = 1` and reproduces the collapse exactly. That is the falsifiable
edge of this law and it is checked here.

WHAT THIS DOES AND DOES NOT ESTABLISH. It establishes that generic branching
amplification survives every gauge, with a formula confirmed across bond sizes,
ranks and parent dimensions. It does NOT prove `kappa_intrinsic > 1` as an
infimum: the law is generic, and whether some gauge can steer a SPECIFIC
realized error into `Ran(U)` for a given instance is not settled here. A random
search over 12 000 admissible gauges (see `rg_gauge_battery.py`) never found
one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def shaped_core(rows, columns, rate, rng):
    left, _ = np.linalg.qr(rng.standard_normal((rows, max(rows, columns))))
    right, _ = np.linalg.qr(rng.standard_normal((columns, max(rows, columns))))
    size = min(rows, columns)
    values = np.arange(1, size + 1, dtype=float) ** (-rate)
    return (left[:, :size] * values) @ right[:, :size].T


def truncate(child, rank):
    left, values, _ = np.linalg.svd(child, full_matrices=False)
    keep = min(rank, values.size)
    basis = left[:, :keep]
    projected = basis @ (basis.T @ child)
    return projected, float(np.linalg.norm(child - projected)), keep


def trial(bond, child_dim, parent, rank, rng, rate):
    """One canonical branching node, both children truncated."""
    one = shaped_core(child_dim, bond, rate, rng)
    two = shaped_core(child_dim, bond, rate, rng)
    one /= np.linalg.norm(one)
    two /= np.linalg.norm(two)
    node, _ = np.linalg.qr(rng.standard_normal((bond * bond, parent)))
    node = node.reshape(bond, bond, parent)

    reduced_one, gamma_one, keep = truncate(one, rank)
    reduced_two, gamma_two, _ = truncate(two, rank)

    exact = np.einsum("ai,bj,ijp->abp", one, two, node)
    approx = np.einsum("ai,bj,ijp->abp", reduced_one, reduced_two, node)
    error = float(np.linalg.norm(exact - approx))
    gain = float(np.linalg.svd(node.reshape(-1, parent),
                               compute_uv=False)[0])
    # sibling-aware: ||e_1 (x) L_2|| = ||e_1|| ||L_2||
    certificate = gain * float(np.sqrt(
        (gamma_one * np.linalg.norm(two)) ** 2
        + (np.linalg.norm(reduced_one) * gamma_two) ** 2))
    reachable = (bond - keep) * keep * 2
    return (certificate / error if error > 1e-12 else np.nan), gain, reachable


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bonds", type=int, nargs="+", default=[6, 8, 10])
    parser.add_argument("--ranks", type=int, nargs="+", default=[2, 3, 5])
    parser.add_argument("--instances", type=int, default=300)
    parser.add_argument("--rate", type=float, default=1.6)
    parser.add_argument("--tolerance", type=float, default=0.05,
                        help="allowed relative departure from the law")
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--json", type=str, default="rg_branching_law.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    print("law under test:   tau = sqrt(r1 r2 / r_p)")
    print("falsifiable edge: r_p = r1 r2 is a true isometry and must give "
          "tau = 1\n")
    print(f"{'bond':>5} {'r1*r2':>7} {'r_p':>6} {'rank':>5} {'reach':>6} "
          f"{'tau p50':>9} {'law':>9} {'ratio':>8} {'gain':>7}")

    rows, worst, isometric = [], 0.0, []
    for bond in args.bonds:
        for rank in args.ranks:
            if rank >= bond:
                continue
            parents = sorted({bond, 2 * bond, 4 * bond, bond * bond})
            for parent in parents:
                if parent > bond * bond:
                    continue
                results = [trial(bond, bond + 4, parent, rank, rng, args.rate)
                           for _ in range(args.instances)]
                taus = [r[0] for r in results if np.isfinite(r[0])]
                if not taus:
                    continue
                measured = float(np.median(taus))
                law = float(np.sqrt(bond * bond / parent))
                gain = float(np.median([r[1] for r in results]))
                reach = results[0][2]
                ratio = measured / law
                worst = max(worst, abs(ratio - 1.0))
                if parent == bond * bond:
                    isometric.append(measured)
                print(f"{bond:5d} {bond*bond:7d} {parent:6d} {rank:5d} "
                      f"{reach:6d} {measured:9.4f} {law:9.4f} {ratio:8.4f} "
                      f"{gain:7.4f}")
                rows.append({"bond": bond, "product": bond * bond,
                             "parent": parent, "rank": rank,
                             "reachable_dim": reach, "tau": measured,
                             "law": law, "ratio": ratio, "node_gain": gain})

    print(f"\nworst relative departure from the law: {worst:.4f}")
    edge_ok = all(abs(value - 1.0) < 1e-9 for value in isometric)
    print(f"isometric edge (r_p = r1 r2): "
          f"{'tau = 1 in all ' + str(len(isometric)) + ' cases' if edge_ok else 'VIOLATED'}")

    print("\nREADING")
    if not edge_ok:
        print("  The law's own falsifiable edge failed. Do not read the rest.")
    elif worst < args.tolerance:
        print(f"  tau = sqrt(r1 r2 / r_p) holds to {100 * worst:.1f}% across")
        print("  every bond size, rank and parent dimension tested. Both")
        print("  r1 r2 and r_p are invariant under any invertible gauge, so")
        print("  the amplification is NOT a property of the representation --")
        print("  unlike the chain, where it was.")
        print("\n  A chain is the r_p = r1 r2 corner of this law, which is")
        print("  exactly where it returns tau = 1. The two results are one")
        print("  statement, not two.")
        print("\n  NOT established: kappa_intrinsic > 1 as an infimum. The law")
        print("  is generic; whether a gauge can steer a specific realized")
        print("  error into Ran(U) for a given instance is still open.")
    else:
        print(f"  Departure {100 * worst:.1f}% exceeds the {100 * args.tolerance:.0f}% "
              f"tolerance. The mechanism is not (only) the dimension deficit.")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "law": "tau = sqrt(r1*r2/r_p)",
         "worst_relative_departure": worst,
         "isometric_edge_holds": bool(edge_ok), "rows": rows},
        indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
