"""Does a real tensor-train truncation produce the quantity M24 needs?

FIRST PRODUCT GATE. Everything downstream -- certified auditing, rank advice,
adaptive control -- rests on one correspondence that has never been checked:

    the residual a TT/TTN truncation already computes
                        ==?==
    gamma_v = ||(I - P_v) Rtilde_v||,  the REALIZED local leakage of M24

Note carefully which object that is. `rho_v^proj` of the canonical
formalization is an operator SUPREMUM over all admissible projected inputs; it
is what the extremal constants C_T^P, W_3 and Sigma_2 are stated in. M24's
`gamma_v` is the leakage that actually happened on this instance. They satisfy
`gamma_v <= rho_v^proj * prod ||R_c||` but are not equal, and it is the second
one -- not the first -- that a framework's truncation telemetry can supply. A
first bridge experiment aimed at `rho_v^proj` would be measuring the wrong
thing, and would be far harder for no gain: M24 deploys without it.

The tensor train is written out here rather than taken from a library on
purpose. "Discarded weight" is reported inconsistently in the wild -- the
Frobenius tail `sqrt(sum_{i>r} sigma_i^2)`, the spectral residual `sigma_{r+1}`,
and the unsquared sum `sum_{i>r} sigma_i^2` all appear under that name -- so the
test computes all three and reports which one, if any, is `gamma_v`.

FRAMING. A left-to-right TT contraction with truncation after each step IS a
PMT chain: each internal vertex is the bilinear law `mu_v(x, G) = x . G`
contracting the bond, the cores are unreduced leaves, and SVD truncation of the
bond is an orthogonal projector on the vertex output space. So the gates below
test PMT's hypotheses against an actual compressed pipeline, not an analogy.

GATES
  A  projector       P^2 = P and P^* = P for the truncation actually applied
  B  correspondence  gamma_v equals the Frobenius tail, and which telemetry
                     field it is NOT
  C  reconstruction  R_v = P_v Rtilde_v
  D  soundness       ||E|| <= B_r on every instance, E = F_r - Rtilde_r
  E  tightness       tau = B_r / ||E||, the number a product lives or dies on
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def random_tt(bond, physical, cores, rng):
    """Cores of a tensor train: G_1 (n x r), then (r x n x r), ..."""
    train = [rng.standard_normal((physical, bond))]
    for _ in range(cores - 2):
        train.append(rng.standard_normal((bond, physical, bond)))
    train.append(rng.standard_normal((bond, physical)))
    return train


def contract_step(partial, core):
    """mu_v(x, G): contract the bond index, then flatten the new physical leg.

    `partial` is (N, r_in); `core` is (r_in, n, r_out) or (r_in, n) at the end.
    Returns (N * n, r_out), or (N * n,) at the last core.
    """
    if core.ndim == 2:
        return (partial @ core).reshape(-1)
    out = np.einsum("Ni,inj->Nnj", partial, core)
    return out.reshape(-1, out.shape[2])


def truncate(matrix, rank):
    """Orthogonal SVD projection of the left index, plus its telemetry."""
    left, values, right = np.linalg.svd(matrix, full_matrices=False)
    keep = min(rank, values.size)
    basis = left[:, :keep]                       # P = basis @ basis.T
    projected = basis @ (basis.T @ matrix)
    tail = values[keep:]
    return {
        "projector_basis": basis,
        "projected": projected,
        "frobenius_tail": float(np.sqrt((tail ** 2).sum())),
        "spectral_residual": float(tail[0]) if tail.size else 0.0,
        "squared_tail_sum": float((tail ** 2).sum()),
        "singular_values": values,
    }


def run_instance(train, rank, rng):
    """One TT contraction, ambient and truncated, collecting M24's ingredients."""
    ambient = train[0].copy()                    # F path, never truncated
    reduced = train[0].copy()                    # R path, truncated each step
    bound, records = 0.0, []                     # B_leaf = 0

    for index, core in enumerate(train[1:], start=1):
        is_root = index == len(train) - 1
        ambient = contract_step(ambient, core)
        raw = contract_step(reduced, core)        # Rtilde_v

        # ||M_{v,1}||_op for the Frobenius norm: ||x G||_F <= ||x||_F ||G||_2.
        # Slot 2's child is a leaf, so it carries B = 0 and never propagates.
        flat_core = core.reshape(core.shape[0], -1)
        slot_norm = float(np.linalg.svd(flat_core, compute_uv=False)[0])
        propagated = slot_norm * bound            # p_v

        if is_root:
            # B_r = p_r: the root's own leakage cannot reach the projected root
            bound = propagated
            reduced = raw
            records.append({"vertex": index, "root": True,
                            "slot_norm": slot_norm, "propagated": propagated,
                            "gamma": 0.0})
            continue

        result = truncate(raw, rank)
        gamma = float(np.linalg.norm(raw - result["projected"]))
        basis = result["projector_basis"]

        records.append({
            "vertex": index, "root": False, "slot_norm": slot_norm,
            "propagated": propagated, "gamma": gamma,
            "frobenius_tail": result["frobenius_tail"],
            "spectral_residual": result["spectral_residual"],
            "squared_tail_sum": result["squared_tail_sum"],
            # gate A, on the projector actually applied
            "idempotent": float(np.abs(basis @ (basis.T @ basis) - basis).max()),
            "selfadjoint": float(np.abs(basis.T @ basis
                                        - np.eye(basis.shape[1])).max()),
            # gate C
            "reconstruction": float(np.abs(result["projected"]
                                           - basis @ (basis.T @ raw)).max()),
        })
        bound += 0.0
        bound = propagated + gamma
        reduced = result["projected"]

    error = float(np.linalg.norm(ambient - reduced))
    return {"error": error, "bound": bound, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond", type=int, default=8)
    parser.add_argument("--physical", type=int, default=3)
    parser.add_argument("--cores", type=int, default=6)
    parser.add_argument("--rank", type=int, default=5)
    parser.add_argument("--instances", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--json", type=str, default="rg_tt_bridge.json")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    print(f"tensor train: {args.cores} cores, bond {args.bond}, physical "
          f"{args.physical}, truncated to rank {args.rank}")
    print(f"{args.instances} instances\n")

    runs, gate = [], {"idempotent": 0.0, "selfadjoint": 0.0,
                      "reconstruction": 0.0, "gamma_vs_frobenius": 0.0,
                      "gamma_vs_spectral": 0.0, "gamma_vs_squared": 0.0,
                      "violations": 0}
    ratios = []
    for _ in range(args.instances):
        train = random_tt(args.bond, args.physical, args.cores, rng)
        result = run_instance(train, args.rank, rng)
        runs.append({"error": result["error"], "bound": result["bound"]})
        if result["error"] > result["bound"] * (1 + 1e-9):
            gate["violations"] += 1
        if result["error"] > 0:
            ratios.append(result["bound"] / result["error"])
        for row in result["records"]:
            if row["root"]:
                continue
            scale = max(row["gamma"], 1e-300)
            gate["idempotent"] = max(gate["idempotent"], row["idempotent"])
            gate["selfadjoint"] = max(gate["selfadjoint"], row["selfadjoint"])
            gate["reconstruction"] = max(gate["reconstruction"],
                                         row["reconstruction"])
            gate["gamma_vs_frobenius"] = max(
                gate["gamma_vs_frobenius"],
                abs(row["gamma"] - row["frobenius_tail"]) / scale)
            gate["gamma_vs_spectral"] = max(
                gate["gamma_vs_spectral"],
                abs(row["gamma"] - row["spectral_residual"]) / scale)
            gate["gamma_vs_squared"] = max(
                gate["gamma_vs_squared"],
                abs(row["gamma"] - row["squared_tail_sum"]) / scale)

    def verdict(value, tolerance=1e-10):
        return "PASS" if value <= tolerance else "FAIL"

    print("GATE A  the truncation really is an orthogonal projector")
    print(f"  max |P^2 - P|                  {gate['idempotent']:.3e}   "
          f"{verdict(gate['idempotent'])}")
    print(f"  max |basis^T basis - I|        {gate['selfadjoint']:.3e}   "
          f"{verdict(gate['selfadjoint'])}")
    print("\nGATE B  which telemetry field IS gamma_v")
    print(f"  vs Frobenius tail sqrt(sum s^2) {gate['gamma_vs_frobenius']:.3e}"
          f"   {verdict(gate['gamma_vs_frobenius'])}")
    print(f"  vs spectral residual s_(r+1)    {gate['gamma_vs_spectral']:.3e}"
          f"   {verdict(gate['gamma_vs_spectral'])}")
    print(f"  vs unsquared sum sum s^2        {gate['gamma_vs_squared']:.3e}"
          f"   {verdict(gate['gamma_vs_squared'])}")
    print("\nGATE C  reconstruction R_v = P_v Rtilde_v")
    print(f"  max deviation                  {gate['reconstruction']:.3e}   "
          f"{verdict(gate['reconstruction'])}")
    print("\nGATE D  M24 soundness  ||E|| <= B_r")
    print(f"  instances violating the bound  {gate['violations']} / "
          f"{args.instances}   "
          f"{'PASS' if gate['violations'] == 0 else 'FAIL'}")
    print("\nGATE E  tightness  tau = B_r / ||E||   (1.0 would be exact)")
    if ratios:
        ratios_array = np.array(ratios)
        for label, value in (("min", ratios_array.min()),
                             ("median", np.median(ratios_array)),
                             ("mean", ratios_array.mean()),
                             ("max", ratios_array.max())):
            print(f"  {label:>7}  {value:12.4f}")

    (HERE / args.json).write_text(json.dumps(
        {"config": vars(args), "gates": gate,
         "tau": {"median": float(np.median(ratios)) if ratios else None,
                 "max": float(max(ratios)) if ratios else None},
         "runs": runs}, indent=2), encoding="utf-8")
    print(f"\n-> {args.json}")


if __name__ == "__main__":
    main()
