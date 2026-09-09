"""Is the observed a_v _|_ b_v structural, reachable-subspace, or trajectory-only?

The slack ledger measured cos(a_v, b_v) = 0 to displayed precision, where

    a_v = M_v delta_{v-1}      propagated error
    b_v = Q_v Rtilde_v         closure residual,  Q_v = I - P_v

PMT does NOT predict this. M25 only ever controls the NORMAL part `Q_v a_v`,
precisely because the general theory cannot assume the whole of `a_v` is
orthogonal to `b_v`. So if the zero is real it is an extra property of TT-SVD,
and it matters a great deal which of three things it is:

  LEVEL 3  structural       ||Q_v M_v||_op = 0, i.e. Ran(M_v) subset Ran(P_v)
                            -> Pythagoras holds for ANY error; the triangle
                               inequality can be deleted from the recursion
  LEVEL 2  reachable        Q_v M_v vanishes on the subspace errors can occupy
                            -> still certifiable, since it needs only the
                               reachable set, not the realized vector
  LEVEL 1  trajectory       it merely happened for this delta_{v-1}
                            -> diagnostic only; using it would need the answer

Only levels 3 and 2 can enter a certificate. Level 1 cannot: a bound that needs
the realized error is not a bound.

TWO ARTIFACTS ARE CHECKED FIRST, because either would fake a zero:
  * at the first internal vertex the leaves are unreduced, so delta_0 = 0 and
    a_1 = 0 exactly -- its cosine is 0 by construction and must be excluded;
  * a cosine computed as (a.b)/max(||a|| ||b||, tiny) returns 0 when a = 0.

NEGATIVE CONTROLS on the projector, to tell an SVD-specific effect from
anything that follows merely from P being orthogonal:
  random    an unrelated orthogonal projector of the same rank
  rotated   the same subspace, a different basis inside it -- must change nothing
  perturbed the SVD subspace tilted slightly -- if the zero dies immediately,
            the property belongs to the optimal subspace, not to orthogonality
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


def left_basis(matrix, rank, mode, rng):
    """Rank-`rank` orthonormal basis of the left index, per control mode."""
    left, _, _ = np.linalg.svd(matrix, full_matrices=False)
    keep = min(rank, left.shape[1])
    basis = left[:, :keep]
    if mode == "svd":
        return basis
    if mode == "rotated":                        # same subspace, new basis
        rotation, _ = np.linalg.qr(rng.standard_normal((keep, keep)))
        return basis @ rotation
    if mode == "random":                         # unrelated subspace
        candidate, _ = np.linalg.qr(
            rng.standard_normal((matrix.shape[0], keep)))
        return candidate
    if mode == "perturbed":                      # tilted slightly off the SVD
        tilt = basis + 1e-3 * rng.standard_normal(basis.shape)
        tilted, _ = np.linalg.qr(tilt)
        return tilted
    raise ValueError(mode)


def operator_norm_restricted(flat_core, normal, shape_left, restriction=None):
    """||Q M||_op, optionally with M restricted to a subspace of its domain.

    M_v: x -> x . G acts on the bond index of x, and Q acts on the flattened
    left index of the OUTPUT. The composition is not a plain matrix product, so
    it is materialized on a basis of the domain.
    """
    rows, bond = shape_left
    if restriction is None:
        directions = np.eye(rows * bond).reshape(rows * bond, rows, bond)
    else:
        directions = restriction
    images = []
    for direction in directions:
        image = direction @ flat_core
        image = image.reshape(rows * (flat_core.shape[1] // normal.shape[0]
                                      if False else 1), -1) \
            if False else image
        images.append(image)
    stacked = np.stack(images)
    return stacked


def probe_instance(train, rank, mode, rng):
    ambient = train[0].copy()
    reduced = train[0].copy()
    previous_delta = np.zeros_like(ambient)
    rows = []

    for index, core in enumerate(train[1:], start=1):
        if index == len(train) - 1:
            break                                # root carries no projector
        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)

        basis = left_basis(raw, rank, mode, rng)
        projected = basis @ (basis.T @ raw)

        a_vector = ambient - raw
        b_vector = raw - projected
        delta = ambient - projected

        norm_a = float(np.linalg.norm(a_vector))
        norm_b = float(np.linalg.norm(b_vector))

        # LEVEL 1: is the REALIZED propagated error normal-free?
        normal_a = a_vector - basis @ (basis.T @ a_vector)
        epsilon_realized = (float(np.linalg.norm(normal_a)) / norm_a
                            if norm_a > 1e-300 else float("nan"))
        cosine = (float((a_vector * b_vector).sum() / (norm_a * norm_b))
                  if norm_a > 1e-300 and norm_b > 1e-300 else float("nan"))

        # LEVEL 3: is the whole slot map normal-free? Materialize Q M on a
        # basis of M's domain -- the bond index of the incoming partial.
        rows_left, bond_in = raw.shape[0] // core.shape[1], core.shape[0]
        flat = core.reshape(core.shape[0], -1)
        gains, normal_gains = [], []
        for column in range(bond_in):
            probe = np.zeros((raw.shape[0] // core.shape[1], bond_in))
            probe[:, column] = 1.0 / np.sqrt(probe.shape[0])
            image = contract_step(probe, core)
            normal_image = image - basis @ (basis.T @ image)
            gains.append(float(np.linalg.norm(image)))
            normal_gains.append(float(np.linalg.norm(normal_image)))
        epsilon_op = (max(normal_gains) / max(gains)
                      if max(gains) > 1e-300 else float("nan"))

        rows.append({"vertex": index, "a_is_zero": norm_a <= 1e-300,
                     "cosine": cosine,
                     "epsilon_realized": epsilon_realized,
                     "epsilon_op": epsilon_op})
        reduced = projected
        previous_delta = delta
    return rows


def summarize(values, label):
    finite = np.array([v for v in values if np.isfinite(v)], dtype=float)
    if finite.size == 0:
        return f"{label:>26}   no finite samples"
    return (f"{label:>26} {np.percentile(finite, 10):11.3e} "
            f"{np.median(finite):11.3e} {np.percentile(finite, 90):11.3e} "
            f"{finite.max():11.3e}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--rank", type=int, default=5)
    parser.add_argument("--instances", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--json", type=str,
                        default="rg_tt_orthogonality_probe.json")
    args = parser.parse_args()

    report = {}
    print(f"{args.instances} instances, chain of {args.cores} cores, "
          f"rank {args.rank}\n")
    print(f"{'':>26} {'p10':>11} {'p50':>11} {'p90':>11} {'max':>11}")

    for mode in ("svd", "rotated", "perturbed", "random"):
        rng = np.random.default_rng(args.seed)
        cosines, realized, operator, excluded = [], [], [], 0
        for _ in range(args.instances):
            train = random_tt(args.bond, args.physical, args.cores, rng)
            for row in probe_instance(train, args.rank, mode, rng):
                if row["a_is_zero"]:
                    excluded += 1        # delta_0 = 0: cosine is 0 by fiat
                    continue
                cosines.append(abs(row["cosine"]))
                realized.append(row["epsilon_realized"])
                operator.append(row["epsilon_op"])
        print(f"--- projector: {mode}   ({excluded} vertices excluded for "
              f"a_v = 0) ---")
        print(summarize(cosines, "|cos(a,b)|"))
        print(summarize(realized, "eps_realized ||Qa||/||a||"))
        print(summarize(operator, "eps_op  ||QM||/||M||"))
        report[mode] = {
            "cosine_median": float(np.median(cosines)) if cosines else None,
            "eps_realized_median": float(np.median(realized)) if realized
                                   else None,
            "eps_op_median": float(np.median(operator)) if operator else None,
            "excluded_a_zero": excluded}
        print()

    svd = report["svd"]
    print("READING")
    if svd["eps_op_median"] is not None and svd["eps_op_median"] < 1e-10:
        print("  LEVEL 3: the slot map itself is normal-free. Pythagoras is")
        print("  structural and the triangle step can be removed outright.")
    elif svd["eps_realized_median"] is not None and \
            svd["eps_realized_median"] < 1e-10:
        print("  LEVEL 1 or 2: the REALIZED error is normal-free while the")
        print("  operator is not. Whether this is certifiable depends on the")
        print("  reachable-error subspace, which is the next thing to pin.")
    else:
        print("  The zero does not survive an honest measurement: the earlier")
        print("  cos = 0 was an artifact of the a_v = 0 vertices.")

    (HERE / args.json).write_text(json.dumps(report, indent=2),
                                  encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
