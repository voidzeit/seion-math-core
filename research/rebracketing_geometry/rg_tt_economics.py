"""LAYER-GAIN falsifier, then the certification tax the new certificate buys.

GATE LAYER-GAIN
    ORTH-3 gave finer subspaces than the aggregate reachable set: each birth
    layer has its own, E_{i->v} = M_v ... M_{i+1}(L_i). A layered certificate
    would pay a per-layer gain

        m_{v,i} = || M_v restricted to E_{i->v-1} ||_op

    and would only be worth its much larger state if m_{v,i} < m_v. The
    prediction is that it is NOT: each layer's bond content is unconstrained, and
    M_v contracts the bond, so the restriction cannot bind. If confirmed,
    generation 3 collapses onto generation 2 exactly and the line closes.

GATE ECON
    With tau roughly halved, the economic question is now worth measuring rather
    than modelled. For each tolerance, find the cheapest rank that each notion
    of "error" can certify:

        r_oracle  min { r : E(r)      <= eps }   knows the true error
        r_M24     min { r : B_24(r)   <= eps }
        r_Pyth    min { r : H_P(r)    <= eps }

    and report the tax over the oracle in TT STORAGE, not rank, because storage
    goes as sum_k n_k r_{k-1} r_k and a 1.7x rank is more than 1.7x memory. Then

        recovered = (Tax_M24 - Tax_Pyth) / (Tax_M24 - 1)

    answers the only question an engineering director asks: what fraction of the
    cost that certification imposes did the new mathematics give back?
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


def gain_on_subspace(core, basis_vectors, iterations=60):
    """||M_v|| restricted to the span of given matrices, by power iteration."""
    if not basis_vectors:
        return 0.0
    stack = np.stack([vector.ravel() for vector in basis_vectors])
    orthonormal, _ = np.linalg.qr(stack.T)
    shape = basis_vectors[0].shape
    coefficients = np.ones(orthonormal.shape[1])
    best = 0.0
    for _ in range(iterations):
        vector = orthonormal @ coefficients
        vector /= max(np.linalg.norm(vector), 1e-300)
        image = contract_step(vector.reshape(shape), core)
        best = max(best, float(np.linalg.norm(image)))
        # one step of the power method on the restricted Gram operator
        back = np.einsum("Nnj,inj->Ni", image.reshape(
            shape[0], core.shape[1], core.shape[2]), core) \
            if core.ndim == 3 else None
        if back is None:
            break
        coefficients = orthonormal.T @ back.ravel()
        if np.linalg.norm(coefficients) < 1e-300:
            break
    return best


def sweep_instance(train, ranks, rng, layer_probe):
    """Run the chain at every rank in `ranks`, collecting E, B_24, H_Pyth."""
    results = {}
    layer_ratios = []
    for rank in ranks:
        ambient = train[0].copy()
        reduced = train[0].copy()
        layers, m24, pyth = [], 0.0, 0.0
        bond_ranks = []
        for index, core in enumerate(train[1:], start=1):
            is_root = index == len(train) - 1
            flat = core.reshape(core.shape[0], -1)
            operator_norm = float(np.linalg.svd(flat, compute_uv=False)[0])
            ambient = contract_step(ambient, core)
            raw = contract_step(reduced, core)

            if layer_probe and layers and not is_root:
                # LAYER-GAIN: each layer separately, versus the unrestricted norm
                for layer in layers:
                    restricted = gain_on_subspace(core, [layer])
                    if operator_norm > 0:
                        layer_ratios.append(restricted / operator_norm)
            layers = [contract_step(layer, core) for layer in layers]

            if is_root:
                m24 *= operator_norm
                pyth *= operator_norm
                results[rank] = {
                    "error": float(np.linalg.norm(ambient - raw)),
                    "m24": m24, "pyth": pyth,
                    "bond_ranks": bond_ranks}
                break

            left, values, _ = np.linalg.svd(raw, full_matrices=False)
            keep = min(rank, values.size)
            basis = left[:, :keep]
            projected = basis @ (basis.T @ raw)
            residual = raw - projected
            gamma = float(np.linalg.norm(residual))
            m24 = operator_norm * m24 + gamma
            pyth = float(np.sqrt((operator_norm * pyth) ** 2 + gamma ** 2))
            layers.append(residual)
            bond_ranks.append(keep)
            reduced = projected
    return results, layer_ratios


def storage_cost(bond_ranks, physical):
    """TT storage ~ sum_k n_k r_{k-1} r_k, with the kept left ranks."""
    total, previous = 0, 1
    for rank in bond_ranks:
        total += physical * previous * rank
        previous = rank
    return total + physical * previous


def cheapest(results, ranks, key, tolerance, physical):
    for rank in ranks:
        row = results.get(rank)
        if row is None:
            continue
        if row[key] <= tolerance:
            return storage_cost(row["bond_ranks"], physical)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--ranks", type=int, nargs="+",
                        default=[2, 3, 4, 5, 6, 7, 8])
    parser.add_argument("--instances", type=int, default=60)
    parser.add_argument("--layer-instances", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--json", type=str, default="rg_tt_economics.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    ranks = sorted(args.ranks)
    all_layer_ratios, sweeps = [], []
    for instance in range(args.instances):
        train = random_tt(args.bond, args.physical, args.cores, rng)
        probe = instance < args.layer_instances
        results, ratios = sweep_instance(train, ranks, rng, probe)
        sweeps.append(results)
        all_layer_ratios.extend(ratios)

    print("GATE LAYER-GAIN   m_{v,i} / ||M_v||_op  per birth layer")
    if all_layer_ratios:
        array = np.array(all_layer_ratios)
        print(f"  samples {array.size}   p10 {np.percentile(array, 10):.6f}   "
              f"p50 {np.median(array):.6f}   p90 "
              f"{np.percentile(array, 90):.6f}   max {array.max():.6f}")
        if np.median(array) > 0.999:
            print("  -> the per-layer restriction does NOT bind. Generation 3")
            print("     collapses onto the Pythagorean certificate exactly;")
            print("     storing a layer vector buys nothing. LINE CLOSED.")
        else:
            print("  -> per-layer gains ARE smaller: a layered certificate")
            print("     could beat the Pythagorean one.")

    print("\nGATE ECON   certification tax in TT STORAGE, over the oracle")
    errors = np.array([row["error"] for sweep in sweeps
                       for row in sweep.values() if row["error"] > 0])
    tolerances = [float(np.percentile(errors, p)) for p in (25, 50, 75, 90)]
    print(f"{'tolerance':>12} {'Tax M24':>10} {'Tax Pyth':>10} "
          f"{'recovered':>11} {'n':>5}")
    economics = []
    for tolerance in tolerances:
        taxes_24, taxes_p = [], []
        for results in sweeps:
            oracle = cheapest(results, ranks, "error", tolerance,
                              args.physical)
            certified_24 = cheapest(results, ranks, "m24", tolerance,
                                    args.physical)
            certified_p = cheapest(results, ranks, "pyth", tolerance,
                                   args.physical)
            if oracle and certified_24 and certified_p:
                taxes_24.append(certified_24 / oracle)
                taxes_p.append(certified_p / oracle)
        if not taxes_24:
            print(f"{tolerance:12.3e}   no instance certifiable at any rank")
            continue
        tax_24 = float(np.median(taxes_24))
        tax_p = float(np.median(taxes_p))
        recovered = ((tax_24 - tax_p) / (tax_24 - 1)
                     if tax_24 > 1 + 1e-12 else float("nan"))
        print(f"{tolerance:12.3e} {tax_24:10.4f} {tax_p:10.4f} "
              f"{recovered * 100 if np.isfinite(recovered) else float('nan'):10.1f}% "
              f"{len(taxes_24):5d}")
        economics.append({"tolerance": tolerance, "tax_m24": tax_24,
                          "tax_pyth": tax_p, "recovered": recovered,
                          "instances": len(taxes_24)})

    (HERE / args.json).write_text(json.dumps({
        "config": vars(args),
        "layer_gain": {"p50": float(np.median(all_layer_ratios))
                       if all_layer_ratios else None,
                       "samples": len(all_layer_ratios)},
        "economics": economics}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
