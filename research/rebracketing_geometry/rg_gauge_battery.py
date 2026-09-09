"""Is projected amplification intrinsic, or a property of the representation?

The TT retraction of 2026-08-18 showed that `tau` collapsed from ~9.5 to exactly
1 under right-orthogonalization -- a change of gauge that leaves the represented
tensor bit-for-bit identical. That makes `tau` suspect as a geometric quantity.
This battery decides the question on chains, then asks whether BRANCHING can
escape the collapse.

A bond gauge is `A` invertible acting between neighbouring cores,

    core_v  ->  core_v . A            core_{v+1}  ->  A^{-1} . core_{v+1}

which is the identity on the represented tensor. So any quantity that is not
invariant under this group is a property of coordinates, not of the object.

GATE G0   orthogonal gauge on a canonical train
          `tau` must be unchanged (= 1). Anything else is a bug in this file.

GATE G1   ill-conditioned invertible gauge, same tensor
          If `tau` blows up, the old slack was gauge-dependent and therefore
          carried no intrinsic meaning. This is the formal statement of the
          retraction.

GATE G2   re-canonicalize after G1
          `tau` must return to 1, establishing for TT chains

              kappa_intrinsic := inf over admissible gauges of the
                                 non-isometric amplification    =    1

GATE BRANCH   the question G0-G2 cannot answer.
          At a branching node the parent-directed unfolding is
          `G : R^{r_1 r_2} -> R^{r_v}` with `r_v < r_1 r_2` generically, so
          canonicalization makes it a strict CO-isometry, not an isometry: it
          is norm-non-increasing but kills part of any generic error. The
          certificate still charges gain 1. If `tau > 1` survives every
          canonicalization there, the amplification is intrinsic and a
          non-trivial PMT certificate has a genuine domain.

FAIL CLOSED: every gauge is checked to preserve the represented tensor before
any conclusion is drawn from it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


# --------------------------------------------------------------- chain pieces

def shaped_core(rows, columns, rate, rng):
    left, _ = np.linalg.qr(rng.standard_normal((rows, max(rows, columns))))
    right, _ = np.linalg.qr(rng.standard_normal((columns, max(rows, columns))))
    size = min(rows, columns)
    values = np.arange(1, size + 1, dtype=float) ** (-rate)
    return (left[:, :size] * values) @ right[:, :size].T


def heterogeneous_tt(bond, physical, cores, rng, rate_low, rate_high):
    rates = rng.uniform(rate_low, rate_high, size=cores)
    train = [shaped_core(physical, bond, rates[0], rng)]
    for index in range(1, cores - 1):
        train.append(shaped_core(bond, physical * bond, rates[index], rng)
                     .reshape(bond, physical, bond))
    train.append(shaped_core(bond, physical, rates[-1], rng))
    return train


def contract_step(partial, core):
    if core.ndim == 2:
        return (partial @ core).reshape(-1)
    out = np.einsum("Ni,inj->Nnj", partial, core)
    return out.reshape(-1, out.shape[2])


def full_tensor(train):
    x = train[0].copy()
    for core in train[1:]:
        x = contract_step(x, core)
    return x


def right_orthogonalize(train):
    """Sweep right to left so every core but the first has orthonormal rows."""
    train = [core.copy() for core in train]
    for v in range(len(train) - 1, 0, -1):
        core = train[v]
        unfolding = core.reshape(core.shape[0], -1)
        basis, upper = np.linalg.qr(unfolding.T)
        train[v] = basis.T.reshape((basis.shape[1],) + core.shape[1:])
        previous = train[v - 1]
        train[v - 1] = (previous.reshape(-1, previous.shape[-1]) @ upper.T
                        ).reshape(previous.shape[:-1] + (upper.shape[0],))
    return train


def apply_gauge(train, bond_index, matrix):
    """core_v . A  and  A^{-1} . core_{v+1}: identity on the represented tensor."""
    train = [core.copy() for core in train]
    inverse = np.linalg.inv(matrix)
    left = train[bond_index]
    train[bond_index] = (left.reshape(-1, left.shape[-1]) @ matrix
                         ).reshape(left.shape[:-1] + (matrix.shape[1],))
    right = train[bond_index + 1]
    train[bond_index + 1] = (inverse @ right.reshape(right.shape[0], -1)
                             ).reshape((inverse.shape[0],) + right.shape[1:])
    return train


def orthogonal_gauge(size, rng):
    basis, _ = np.linalg.qr(rng.standard_normal((size, size)))
    return basis


def conditioned_gauge(size, condition, rng):
    """Invertible with prescribed condition number -- still a valid gauge."""
    left, _ = np.linalg.qr(rng.standard_normal((size, size)))
    right, _ = np.linalg.qr(rng.standard_normal((size, size)))
    values = np.logspace(0, np.log10(condition), size)
    return (left * values) @ right.T


def certificates(train, rank):
    """True error, M24 bound and Pythagorean bound at a uniform rank."""
    ambient = train[0].copy()
    reduced = train[0].copy()
    m24 = pythagorean = 0.0
    for index, core in enumerate(train[1:], start=1):
        gain = float(np.linalg.svd(core.reshape(core.shape[0], -1),
                                   compute_uv=False)[0])
        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)
        if index == len(train) - 1:
            return (float(np.linalg.norm(ambient - raw)),
                    gain * m24, gain * pythagorean)
        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        basis = left[:, :keep]
        projected = basis @ (basis.T @ raw)
        gamma = float(np.linalg.norm(raw - projected))
        m24 = gain * m24 + gamma
        pythagorean = float(np.sqrt((gain * pythagorean) ** 2 + gamma ** 2))
        reduced = projected
    raise AssertionError("chain ended without a root")


def gains(train):
    return [float(np.linalg.svd(core.reshape(core.shape[0], -1),
                                compute_uv=False)[0]) for core in train[1:]]


# ------------------------------------------------------------------- branching

def branching_tree(bond, child_dim, rng, rate):
    """A node with TWO children, each a truncatable leaf-to-bond map.

    children:  L1 : R^{child_dim} -> R^{bond},  L2 likewise
               child_dim must exceed the rank or nothing is truncated
    node:      G  : R^{bond} (x) R^{bond} -> R^{parent}
    The parent-directed unfolding of G is (bond*bond, parent) with
    parent < bond*bond, so canonicalization can make its COLUMNS orthonormal
    but it cannot be an isometry out of the full child product.
    """
    child_one = shaped_core(child_dim, bond, rate, rng)
    child_two = shaped_core(child_dim, bond, rate, rng)
    parent = bond
    node = rng.standard_normal((bond * bond, parent))
    node, _ = np.linalg.qr(node)              # columns orthonormal: canonical
    return child_one, child_two, node.reshape(bond, bond, parent)


def branching_certificate(child_one, child_two, node, rank):
    """Truncate BOTH children, then transport through the branching node."""
    def truncate(child):
        left, values, _ = np.linalg.svd(child, full_matrices=False)
        keep = min(rank, values.size)
        basis = left[:, :keep]
        projected = basis @ (basis.T @ child)
        return projected, float(np.linalg.norm(child - projected))

    reduced_one, gamma_one = truncate(child_one)
    reduced_two, gamma_two = truncate(child_two)

    exact = np.einsum("ai,bj,ijp->abp", child_one, child_two, node)
    approx = np.einsum("ai,bj,ijp->abp", reduced_one, reduced_two, node)
    error = float(np.linalg.norm(exact - approx))

    # the certificate charges the node's operator norm, which canonicalization
    # has already driven to its minimum of 1
    gain = float(np.linalg.svd(node.reshape(-1, node.shape[2]),
                               compute_uv=False)[0])
    pythagorean = gain * float(np.sqrt(gamma_one ** 2 + gamma_two ** 2))
    return error, pythagorean, gain


# ----------------------------------------------------------------------- main

def percentiles(values):
    array = np.array(values, dtype=float)
    return {"p10": float(np.percentile(array, 10)),
            "p50": float(np.median(array)),
            "p90": float(np.percentile(array, 90)),
            "max": float(array.max())}


def line(label, summary):
    print(f"{label:>34} {summary['p10']:11.4f} {summary['p50']:11.4f} "
          f"{summary['p90']:11.4f} {summary['max']:11.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=5)
    parser.add_argument("--rank", type=int, default=3)
    parser.add_argument("--child-dim", type=int, default=9,
                        help="left dimension of each branch child")
    parser.add_argument("--instances", type=int, default=200)
    parser.add_argument("--condition", type=float, default=1e3)
    parser.add_argument("--rate-low", type=float, default=0.6)
    parser.add_argument("--rate-high", type=float, default=2.6)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--json", type=str, default="rg_gauge_battery.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    buckets = {name: [] for name in
               ("canonical", "G0", "G1", "G2", "gain_G1", "gain_canonical")}
    drift = []

    for _ in range(args.instances):
        train = heterogeneous_tt(args.bond, args.physical, args.cores, rng,
                                 args.rate_low, args.rate_high)
        canonical = right_orthogonalize(train)
        reference = full_tensor(canonical)
        scale = float(np.linalg.norm(reference))

        bond_index = 1
        size = canonical[bond_index].shape[-1]
        g0 = apply_gauge(canonical, bond_index, orthogonal_gauge(size, rng))
        g1 = apply_gauge(canonical, bond_index,
                         conditioned_gauge(size, args.condition, rng))
        g2 = right_orthogonalize(g1)

        for candidate in (g0, g1, g2):
            drift.append(float(np.linalg.norm(full_tensor(candidate)
                                              - reference)) / scale)

        for name, candidate in (("canonical", canonical), ("G0", g0),
                                ("G1", g1), ("G2", g2)):
            error, _, pythagorean = certificates(candidate, args.rank)
            if error > 1e-9:
                buckets[name].append(pythagorean / error)
        buckets["gain_canonical"].extend(gains(canonical))
        buckets["gain_G1"].extend(gains(g1))

    worst_drift = max(drift)
    print(f"{args.instances} instances, chain of {args.cores} cores, "
          f"rank {args.rank}, gauge condition number {args.condition:.0e}")
    print(f"gauge fidelity: worst relative tensor drift {worst_drift:.3e}")
    if worst_drift > 1e-8:
        raise SystemExit("FAIL CLOSED: a gauge changed the represented tensor")
    print("  -> every gauge preserved the represented tensor\n")

    print(f"{'':>34} {'p10':>11} {'p50':>11} {'p90':>11} {'max':>11}")
    print("\nslot-map gains ||M_v||_op")
    line("canonical", percentiles(buckets["gain_canonical"]))
    line("after G1 (same tensor!)", percentiles(buckets["gain_G1"]))

    print("\ntau = Pythagorean certificate / true error")
    for name, label in (("canonical", "canonical (reference)"),
                        ("G0", "G0  orthogonal gauge"),
                        ("G1", "G1  ill-conditioned gauge"),
                        ("G2", "G2  re-canonicalized")):
        line(label, percentiles(buckets[name]))

    canonical_tau = np.median(buckets["canonical"])
    g0_tau = np.median(buckets["G0"])
    g1_tau = np.median(buckets["G1"])
    g2_tau = np.median(buckets["G2"])

    print("\nREADING")
    if abs(g0_tau - canonical_tau) < 1e-6:
        print("  G0: an orthogonal gauge leaves tau untouched, as it must.")
    else:
        print("  G0: FAILED -- an orthogonal gauge moved tau. Bug in this file.")
    if g1_tau > canonical_tau * 1.5:
        print(f"  G1: the SAME tensor shows tau {g1_tau:.3f} instead of "
              f"{canonical_tau:.3f}. The slack is GAUGE-DEPENDENT and")
        print("      therefore carries no intrinsic meaning.")
    if abs(g2_tau - canonical_tau) < 1e-6:
        print("  G2: re-canonicalization restores tau exactly. For TT chains")
        print("      kappa_intrinsic = 1: there is nothing to certify.")

    print("\nGATE BRANCH   canonical branching node, both children truncated")
    branch = []
    for _ in range(args.instances):
        one, two, node = branching_tree(args.bond, args.child_dim, rng, 1.6)
        error, pythagorean, gain = branching_certificate(one, two, node,
                                                         args.rank)
        if error > 1e-9:
            branch.append((pythagorean / error, gain))
    taus = percentiles([b[0] for b in branch])
    node_gains = percentiles([b[1] for b in branch])
    line("node gain ||G||_op", node_gains)
    line("tau at the branching node", taus)
    if taus["p10"] > 1 + 1e-6:
        print("\n  tau > 1 at EVERY percentile on a node already in canonical")
        print("  form, with node gain exactly 1. The parent-directed unfolding")
        print("  is a strict co-isometry, so it discards part of each child's")
        print("  error while the certificate still charges gain 1. Branching")
        print("  amplification survives canonicalization -- unlike the chain.")
    else:
        print("\n  tau collapses at the branching node too; the chain result")
        print("  was not special and the certificate line closes for good.")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "worst_gauge_drift": worst_drift,
         "tau": {name: percentiles(buckets[name])
                 for name in ("canonical", "G0", "G1", "G2")},
         "gains": {"canonical": percentiles(buckets["gain_canonical"]),
                   "after_G1": percentiles(buckets["gain_G1"])},
         "branching": {"tau": taus, "node_gain": node_gains}},
        indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
