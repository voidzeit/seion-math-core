"""Three gates on the inherited orthogonality of TT-SVD error, paired.

The block lemma, now proved rather than observed. Write

    A_v = Ran(P_{v-1}) (x) R^{n_v}        the block the truncated path lives in
    D_v = Ran(Q_{v-1}) (x) R^{n_v}        the block the inherited error lives in

so R^{N_v} = A_v (+)_perp D_v. Left-to-right contraction with left-index SVD
truncation gives `Rtilde_v in A_v`, hence `Ran(P_v) subset A_v` and
`b_v = Q_v Rtilde_v in A_v`, while `a_v = M_v delta_{v-1} in D_v`. Therefore

    a_v _|_ b_v

not because `P_v a_v = 0` on its own -- `b_v` also lies in `ker P_v` -- but
because the two live in complementary BLOCKS.

GATE ORTH-2   the Pythagorean certificate this licenses,
                  H_v = sqrt( m_v^2 H_{v-1}^2 + gamma_v^2 ),   H_r = m_r H_{r-1}
              recomputed, not extrapolated: the recursion is nonlinear, so
              tau_H is NOT tau_M24 / 1.38.

GATE ORTH-3   do errors born at DIFFERENT levels stay orthogonal after
              transport? Track birth layers e_{i->v} and measure the relative
              off-diagonal mass of their Gram matrix. If that vanishes too,
              ||delta_v||^2 = sum_i ||e_{i->v}||^2 and a layered certificate
              replaces the scalar one.

GATE REACH-1  is the directional slack s_op ~ 1.44 attackable by restricting
              M_v to the subspace the error can occupy? Note delta_{v-1} always
              lies in Ran(Q_{v-1}) -- both of its parts are orthogonal to
              Ran(P_{v-1}) -- so that subspace is known without knowing the
              error. The question is whether the restriction actually lowers the
              gain.
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


def restricted_gain(core, left_normal_basis, samples, rng):
    """||M_v|| restricted to matrices whose LEFT support is in a given subspace.

    M_v: X -> X . G contracts the bond index and leaves the left index alone, so
    a constraint on the left support may or may not bind. Estimated by power
    iteration inside the restricted set rather than assumed either way.
    """
    rows = left_normal_basis.shape[1]
    bond = core.shape[0]
    if rows == 0:
        return 0.0
    coefficients = rng.standard_normal((rows, bond))
    best = 0.0
    for _ in range(samples):
        matrix = left_normal_basis @ coefficients
        matrix /= max(np.linalg.norm(matrix), 1e-300)
        image = contract_step(matrix, core)
        best = max(best, float(np.linalg.norm(image)))
        # gradient of ||X G||_F^2 in X is 2 X G G^T; stay inside the subspace
        gradient = matrix @ core.reshape(bond, -1) @ core.reshape(bond, -1).T
        coefficients = left_normal_basis.T @ gradient
        if np.linalg.norm(coefficients) < 1e-300:
            break
    return best


def run_instance(train, rank, rng, reach_samples):
    ambient = train[0].copy()
    reduced = train[0].copy()
    layers = []                      # birth layers e_{i->v}, transported
    m24, pythagorean = 0.0, 0.0
    rows = []

    for index, core in enumerate(train[1:], start=1):
        is_root = index == len(train) - 1
        flat = core.reshape(core.shape[0], -1)
        operator_norm = float(np.linalg.svd(flat, compute_uv=False)[0])

        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)
        layers = [contract_step(layer, core) for layer in layers]

        if is_root:
            m24 = operator_norm * m24
            pythagorean = operator_norm * pythagorean
            error = float(np.linalg.norm(ambient - raw))
            total = sum(layers) if layers else np.zeros_like(ambient)
            rows.append({"vertex": index, "root": True})
            return {"error": error, "m24": m24, "pythagorean": pythagorean,
                    "layer_identity": float(np.abs(
                        (ambient - raw) - total).max()),
                    "rows": rows}

        left, values, _ = np.linalg.svd(raw, full_matrices=False)
        keep = min(rank, values.size)
        basis = left[:, :keep]
        normal_basis = left[:, keep:]
        projected = basis @ (basis.T @ raw)
        residual = raw - projected                       # b_v, the new layer
        gamma = float(np.linalg.norm(residual))

        # GATE REACH-1: delta_{v-1} always lies in Ran(Q_{v-1}); does
        # restricting M_v to that subspace lower the gain?
        reach = restricted_gain(core, normal_basis, reach_samples, rng) \
            if normal_basis.shape[1] else 0.0

        m24 = operator_norm * m24 + gamma
        pythagorean = float(np.sqrt((operator_norm * pythagorean) ** 2
                                    + gamma ** 2))

        layers.append(residual)
        # GATE ORTH-3: Gram of the transported birth layers
        stack = np.stack([layer.ravel() for layer in layers])
        gram = stack @ stack.T
        off = gram - np.diag(np.diag(gram))
        rows.append({
            "vertex": index, "root": False, "gamma": gamma,
            "operator_norm": operator_norm, "reach_gain": reach,
            "reach_ratio": reach / operator_norm if operator_norm > 0 else 1.0,
            "gram_off_diagonal": (float(np.linalg.norm(off)
                                        / max(np.linalg.norm(gram), 1e-300))
                                  if len(layers) > 1 else 0.0),
            "layers": len(layers),
        })
        reduced = projected

    raise AssertionError("chain ended without a root")


def stats(values):
    array = np.array([v for v in values if np.isfinite(v)], dtype=float)
    if array.size == 0:
        return None
    return {"p10": float(np.percentile(array, 10)),
            "p50": float(np.median(array)),
            "p90": float(np.percentile(array, 90)),
            "max": float(array.max())}


def show(label, summary, fmt="{:11.4f}"):
    if summary is None:
        print(f"{label:>30}   no samples")
        return
    print(f"{label:>30} " + " ".join(fmt.format(summary[k])
                                     for k in ("p10", "p50", "p90", "max")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--rank", type=int, default=5)
    parser.add_argument("--instances", type=int, default=200)
    parser.add_argument("--reach-samples", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--json", type=str,
                        default="rg_tt_layered_certificate.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    tau_m24, tau_pyth, gain, gram, identity = [], [], [], [], []
    for _ in range(args.instances):
        train = random_tt(args.bond, args.physical, args.cores, rng)
        result = run_instance(train, args.rank, rng, args.reach_samples)
        identity.append(result["layer_identity"])
        if result["error"] > 0:
            tau_m24.append(result["m24"] / result["error"])
            tau_pyth.append(result["pythagorean"] / result["error"])
        for row in result["rows"]:
            if row["root"]:
                continue
            gain.append(row["reach_ratio"])
            if row["layers"] > 1:
                gram.append(row["gram_off_diagonal"])

    print(f"{args.instances} instances, chain of {args.cores} cores, "
          f"rank {args.rank}\n")
    print(f"{'':>30} {'p10':>11} {'p50':>11} {'p90':>11} {'max':>11}")

    print("\nGATE ORTH-3  birth-layer decomposition")
    show("layer identity residual", stats(identity), "{:11.3e}")
    show("Gram off-diagonal / total", stats(gram), "{:11.3e}")

    print("\nGATE ORTH-2  certificate tightness, paired")
    show("tau  M24  (triangle)", stats(tau_m24))
    show("tau  Pythagorean", stats(tau_pyth))
    m24_median = np.median(tau_m24)
    pyth_median = np.median(tau_pyth)
    print(f"{'reduction at the median':>30} "
          f"{100 * (1 - pyth_median / m24_median):10.2f}%")

    print("\nGATE REACH-1  m_v restricted to Ran(Q_{v-1}) / ||M_v||_op")
    show("reach ratio", stats(gain))

    gram_summary = stats(gram)
    print("\nREADING")
    if gram_summary and gram_summary["p90"] < 1e-10:
        print("  Birth layers stay MUTUALLY orthogonal through transport, so")
        print("  ||delta||^2 = sum of layer norms^2 and a layered certificate")
        print("  replaces the scalar one outright.")
    elif gram_summary:
        print(f"  Birth layers are NOT mutually orthogonal (median "
              f"{gram_summary['p50']:.2e}); only the adjacent split a_v _|_ b_v")
        print("  holds, which is what the Pythagorean recursion already uses.")
    gain_summary = stats(gain)
    if gain_summary and gain_summary["p50"] > 0.999:
        print("  The reachable-subspace restriction does NOT lower the gain:")
        print("  M_v contracts the BOND index while the constraint sits on the")
        print("  LEFT index, so it does not bind. s_op is not attackable this")
        print("  way; the directional slack lives in the bond index.")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "tau_m24": stats(tau_m24),
         "tau_pythagorean": stats(tau_pyth), "reach_ratio": stats(gain),
         "gram_off_diagonal": stats(gram),
         "layer_identity": stats(identity)}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
