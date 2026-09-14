"""QUARANTINED 2026-08-18 -- DO NOT USE FOR EVIDENCE.

This harness computes its feasibility factors under `torch.no_grad()` (see
`feasibility_factors`, and the `no_grad` blocks below). That is exactly the
frozen-normalization bug fixed in commit `8843022`: the forward pass is scale
invariant but the backward pass is not, so the optimizer climbs a radial
direction the constraint should have removed. Numbers produced here are NOT
valid landscape evidence for any same-law question.

Use `rg_fused_search.py --differentiable` instead. Kept only so the historical
runs remain reproducible as a record of the bug.
"""

"""Adversarial search against the k=2 rebracketing ceilings J_2, H_2, S_2.

EXPERIMENTAL. Nothing here is a theorem; this is a falsification harness for
RG_CANONICAL.md, Theorems 3.1, 4.1 and 5.1.

All three constants have a CONSTRAINT-FREE surrogate, which is what makes an
unconstrained gradient search a fair test of them:

    J:  ||D||             / (rho M L)                        <= 2
    H:  (||PA|| - ||Ahat||) / (rho M L)                       <= 2
    S:  (||Ahat|| - ||PA||) / (rho M L)                       <= Sigma_2(eta)

The first two follow from ||D|| <= 2 rho M L together with Ahat = PA + D; the
third is Theorem 5.1. Each is attained by the corresponding witness in
rg_witnesses.py, so a value materially above the ceiling refutes the theorem
and a value materially below it at the maximum means the search is weak, not
that the constant is smaller.

Root laws are taken P-valued without loss of generality (Lemma 2.2 of
RG_CANONICAL.md): every quantity above is P-composed, so replacing mu_root by
P mu_root changes nothing, cannot increase the operator norm, and makes the
root closure defect vanish. Inner laws carry the closure budget and are
projected onto the admissible class with the canonical unrestricted
supremum, since an inner vertex's children are leaves.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_kernels import (  # noqa: E402
    DTYPE, contract3, coordinate_projectors, op_norms,
)


def batched_op_norm(tensor, *, post=None, seed=0, iters=40, restarts=8):
    """Signature-compatible shim over the restart-batched kernel."""
    return op_norms(tensor, post=post, seed=seed, iters=iters,
                    restarts=restarts), None

OBJECTIVES = ("J", "H", "S")


def sigma2(eta: float) -> float:
    return math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi)) / eta


def ceiling(objective: str, eta: float) -> float:
    return sigma2(eta) if objective == "S" else 2.0


# Projecting onto the admissible class is the expensive part: each call runs an
# alternating maximization, which at these tensor sizes is pure kernel-launch
# overhead. The scale factors move slowly under Adam, so they are recomputed
# every REFRESH steps and held fixed in between, exactly as in the sibling
# m39a_j2_fused.py. The reported value is ALWAYS recomputed with fresh
# high-quality factors, so a stale cache can only make the search less
# effective -- never inflate the number reported.
def feasibility_factors(raws, projectors, quality: int) -> dict:
    """Operator-norm and closure scalars per law, detached from the graph."""
    P_iL, P_iM, P_root = projectors
    identity = torch.eye(P_root.shape[-1], dtype=DTYPE,
                         device=P_root.device).expand_as(P_root)
    factors = {}
    with torch.no_grad():
        for key, projector, seed in (("inner_L", P_iL, 11),
                                     ("inner_M", P_iM, 23)):
            norms, _ = batched_op_norm(raws[key], seed=seed,
                                       iters=20 * quality,
                                       restarts=3 * quality)
            scaled = raws[key] / norms.clamp_min(1e-12).view(-1, 1, 1, 1, 1)
            closure, _ = batched_op_norm(scaled, post=identity - projector,
                                         seed=seed + 1, iters=20 * quality,
                                         restarts=3 * quality)
            factors[key] = (norms, closure)
        for key, seed in (("root_L", 37), ("root_M", 53)):
            tensor = torch.einsum("nqo,noacd->nqacd", P_root, raws[key])
            norms, _ = batched_op_norm(tensor, seed=seed, iters=20 * quality,
                                       restarts=3 * quality)
            factors[key] = (norms, None)
    return factors


def apply_factors(raw, projector, normal, eta, factors):
    """Admissible law rebuilt from cached scalars."""
    norms, closure = factors
    tensor = raw / norms.clamp_min(1e-12).view(-1, 1, 1, 1, 1)
    if closure is None:                                # P-valued root law
        return tensor
    scale = torch.where(closure > eta, eta / closure.clamp_min(1e-12),
                        torch.ones_like(closure)).view(-1, 1, 1, 1, 1)
    return (torch.einsum("nqo,noacd->nqacd", projector, tensor)
            + scale * torch.einsum("nqo,noacd->nqacd", normal, tensor))


def evaluate(raws, projectors, leaves, eta, factors):
    """Batched (Ahat, PA, D) for the rebracketing pair, laws made admissible."""
    P_iL, P_iM, P_root = projectors
    identity = torch.eye(P_root.shape[-1], dtype=DTYPE,
                         device=P_root.device).expand_as(P_root)

    mu_iL = apply_factors(raws["inner_L"], P_iL, identity - P_iL, eta,
                          factors["inner_L"])
    mu_iM = apply_factors(raws["inner_M"], P_iM, identity - P_iM, eta,
                          factors["inner_M"])
    mu_rL = apply_factors(
        torch.einsum("nqo,noacd->nqacd", P_root, raws["root_L"]),
        P_root, None, eta, factors["root_L"])
    mu_rM = apply_factors(
        torch.einsum("nqo,noacd->nqacd", P_root, raws["root_M"]),
        P_root, None, eta, factors["root_M"])

    unit = leaves / leaves.norm(dim=2, keepdim=True).clamp_min(1e-12)
    x1, x2, x3, x4, x5 = (unit[:, i, :] for i in range(5))

    F_iL = contract3(mu_iL, x1, x2, x3)
    R_iL = torch.einsum("nij,nj->ni", P_iL, F_iL)
    F_L = contract3(mu_rL, F_iL, x4, x5)
    R_L = torch.einsum("nij,nj->ni", P_root, contract3(mu_rL, R_iL, x4, x5))

    F_iM = contract3(mu_iM, x2, x3, x4)
    R_iM = torch.einsum("nij,nj->ni", P_iM, F_iM)
    F_M = contract3(mu_rM, x1, F_iM, x5)
    R_M = torch.einsum("nij,nj->ni", P_root, contract3(mu_rM, x1, R_iM, x5))

    A_hat = R_L - R_M
    PA = torch.einsum("nij,nj->ni", P_root, F_L - F_M)
    return A_hat, PA, A_hat - PA


def score(objective: str, A_hat, PA, D, eta):
    if objective == "J":
        return D.norm(dim=1) / eta
    if objective == "H":
        return (PA.norm(dim=1) - A_hat.norm(dim=1)) / eta
    return (A_hat.norm(dim=1) - PA.norm(dim=1)) / eta


def run_cell(objective, klass, dim, rank, eta, batch, steps, device, seed,
             quality, refresh):
    generator = torch.Generator(device=device).manual_seed(seed)
    rank_vec = torch.full((batch,), rank, device=device)
    eta_vec = torch.full((batch,), eta, dtype=DTYPE, device=device)
    P_root = coordinate_projectors(rank_vec, dim, device)
    if klass == "same_law_same_P":
        P_iL = P_iM = P_root
    else:
        inner = torch.randint(1, dim, (2, batch), device=device,
                              generator=generator)
        P_iL = coordinate_projectors(inner[0], dim, device)
        P_iM = coordinate_projectors(inner[1], dim, device)

    shape = (batch, dim, dim, dim, dim)
    keys = ("inner_L", "inner_M", "root_L", "root_M")
    if klass == "free":
        raws = {key: torch.randn(shape, dtype=DTYPE, device=device,
                                 generator=generator, requires_grad=True)
                for key in keys}
        parameters = list(raws.values())
    else:                                   # one law at every vertex
        shared = torch.randn(shape, dtype=DTYPE, device=device,
                             generator=generator, requires_grad=True)
        raws = dict.fromkeys(keys, shared)
        parameters = [shared]
    leaves = torch.randn(batch, 5, dim, dtype=DTYPE, device=device,
                         generator=generator, requires_grad=True)
    parameters.append(leaves)

    projectors = (P_iL, P_iM, P_root)
    optimizer = torch.optim.Adam(parameters, lr=0.05)
    factors = None
    for step in range(steps):
        if step % refresh == 0:
            factors = feasibility_factors(raws, projectors, 1)
        optimizer.zero_grad(set_to_none=True)
        values = score(objective, *evaluate(raws, projectors, leaves, eta_vec,
                                            factors), eta_vec)
        (-values.sum()).backward()
        torch.nn.utils.clip_grad_norm_(parameters, 10.0)
        optimizer.step()

    with torch.no_grad():
        factors = feasibility_factors(raws, projectors, quality)
        A_hat, PA, D = evaluate(raws, projectors, leaves, eta_vec, factors)
        values = torch.nan_to_num(score(objective, A_hat, PA, D, eta_vec),
                                  nan=-1.0)
        best = int(torch.argmax(values))
    return {"objective": objective, "class": klass, "dim": dim, "rank": rank,
            "eta": eta, "best": float(values[best]),
            "ceiling": ceiling(objective, eta),
            "A_hat_over_eta": float(A_hat[best].norm() / eta),
            "PA_over_eta": float(PA[best].norm() / eta),
            "restarts": batch}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objectives", nargs="+", default=list(OBJECTIVES))
    parser.add_argument("--classes", nargs="+",
                        default=["free", "same_law", "same_law_same_P"])
    parser.add_argument("--dims", type=int, nargs="+", default=[2, 3, 4])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.1, 0.3, 0.5, 1 / math.sqrt(2), 0.9, 1.0])
    parser.add_argument("--batch", type=int, default=2048)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--quality", type=int, default=4)
    parser.add_argument("--refresh", type=int, default=15,
                        help="steps between feasibility-factor refreshes")
    parser.add_argument("--json", type=str, default="rg4_s2_search_raw.json")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device} dtype=float64 restarts/cell={args.batch} "
          f"steps={args.steps}")

    records, start = [], time.time()
    print(f"\n{'obj':>4} {'class':>16} {'D':>3} {'r':>3} {'eta':>6} "
          f"{'best':>10} {'ceiling':>10} {'excess':>11}")
    for objective in args.objectives:
        for klass in args.classes:
            for dim in args.dims:
                for rank in range(1, dim):
                    for eta in args.etas:
                        row = run_cell(objective, klass, dim, rank, eta,
                                       args.batch, args.steps, device,
                                       seed=911 + 37 * dim + 7 * rank,
                                       quality=args.quality,
                                       refresh=args.refresh)
                        records.append(row)
                        excess = row["best"] - row["ceiling"]
                        print(f"{objective:>4} {klass:>16} {dim:3d} {rank:3d} "
                              f"{eta:6.3f} {row['best']:10.6f} "
                              f"{row['ceiling']:10.6f} {excess:+11.2e}",
                              flush=True)

    (HERE / args.json).write_text(
        json.dumps({"config": vars(args), "device": str(device),
                    "runs": records}, indent=2), encoding="utf-8")

    print(f"\n{len(records)} cells in {time.time() - start:.0f}s")
    for objective in args.objectives:
        rows = [r for r in records if r["objective"] == objective]
        for klass in args.classes:
            subset = [r for r in rows if r["class"] == klass]
            if not subset:
                continue
            worst = max(subset, key=lambda r: r["best"] - r["ceiling"])
            print(f"  {objective} / {klass:>16}: largest excess over ceiling "
                  f"{worst['best'] - worst['ceiling']:+.3e} at eta="
                  f"{worst['eta']:.3f} D={worst['dim']} r={worst['rank']}")
    violations = [r for r in records if r["best"] > r["ceiling"] + 1e-6]
    print(f"  cells above the proved ceiling: {len(violations)} "
          f"(any is a refutation or a feasibility bug -- inspect, do not ignore)")


if __name__ == "__main__":
    main()
