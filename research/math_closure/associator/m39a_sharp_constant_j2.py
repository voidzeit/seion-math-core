"""M39-A: is the associator distortion constant J_2 equal to 2?

EXPERIMENTAL. Nothing here is a theorem.

For the elementary ternary associator

    T_L = mu(mu(x1,x2,x3), x4, x5)
    T_M = mu(x1, mu(x2,x3,x4), x5)

both trees have k = 2 internal vertices. With the same root projector P,

    D_A = Ahat - P A = -e_T + e_T'

and since C_2^P = 1 (M8), ||e_T||, ||e_T'|| <= rho M L, hence

    J_2 = sup ||D_A|| / (rho M L)  <=  2.

Saturation needs three things at once: both trees saturate their own projected
error, AND the two errors are antiparallel. The question is which law/projector
sharing classes still permit that.

CLASS LADDER, from loosest to tightest:

  free              independent laws at all four node slots, independent inner
                    projectors. This is NOT the associator problem -- with
                    independent root laws the two trees do not share mu, so
                    their difference is not an associator of anything. It is
                    included only as an upper control: if it does not reach 2,
                    the search is at fault, not the geometry.
  same_law          one mu at every node slot, inner projectors free.
                    This is the genuine associator.
  same_law_same_P   one mu and one projector everywhere.

The relevant coupling is that same_law forces D_1 = (I-P_1) mu(x1,x2,x3) and
D_1' = (I-P_1') mu(x2,x3,x4) to come from the same law on leaf triples that
SHARE x2 and x3. Section 28 of the canonical formalization notes that at k = 2
weight sharing alone does not prevent attaining the constant, because one map
can saturate on distinct input pairs; the overlap here is an extra constraint
that does not arise there.

FEASIBILITY IS PROJECTED, NOT PENALIZED. Every parameter vector is mapped onto
an admissible configuration before the objective is read -- operator norms
divided down to M, then the normal component shrunk until the projected
closure defect satisfies rho_v^proj <= eta at every internal vertex. A soft
penalty would let a configuration violating admissibility by 1e-6 manufacture
a spurious J > 2, which is the failure mode the k4 optimizer was written to
avoid.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

DTYPE = torch.float64
RESULTS = Path(__file__).resolve().parent


def coordinate_projector(dim: int, rank: int) -> torch.Tensor:
    diagonal = torch.zeros(dim, dtype=DTYPE)
    diagonal[:rank] = 1.0
    return torch.diag(diagonal)


def ternary_op_norm(tensor: torch.Tensor, *, post=None, restrict=None,
                    iters: int = 30, restarts: int = 3, generator=None):
    """sup ||post . mu(a,b,c)|| over unit a,b,c, optionally restricted.

    Envelope theorem: the maximizing vectors are located under no_grad and then
    held fixed, so the returned norm is differentiable in `tensor` alone.
    Backpropagating through the alternating maximization itself produces
    non-finite values within a few Adam steps -- the same failure the k4
    optimizer documents.
    """
    dim = tensor.shape[0]
    best_vectors, best_value = None, -1.0
    with torch.no_grad():
        frozen = tensor.detach()
        for _ in range(restarts):
            vectors = []
            for _ in range(3):
                v = torch.randn(dim, dtype=DTYPE, generator=generator)
                if restrict is not None:
                    v = restrict @ v
                vectors.append(v / v.norm().clamp_min(1e-12))
            for _ in range(iters):
                for i in range(3):
                    mat = frozen
                    for j in sorted((j for j in range(3) if j != i), reverse=True):
                        mat = torch.tensordot(vectors[j], mat, dims=([0], [j + 1]))
                    if post is not None:
                        mat = post @ mat
                    if restrict is not None:
                        mat = mat @ restrict
                    if not torch.isfinite(mat).all():
                        break
                    candidate = torch.linalg.svd(mat)[2][0]
                    if restrict is not None:
                        candidate = restrict @ candidate
                        if candidate.norm() < 1e-12:
                            continue
                        candidate = candidate / candidate.norm()
                    vectors[i] = candidate
            value = contract3(frozen, vectors)
            if post is not None:
                value = post @ value
            if float(value.norm()) > best_value:
                best_value, best_vectors = float(value.norm()), [v.clone() for v in vectors]

    value = contract3(tensor, best_vectors)
    if post is not None:
        value = post @ value
    return value.norm()


def contract3(tensor: torch.Tensor, args) -> torch.Tensor:
    out = tensor
    for v in reversed(args):
        out = torch.tensordot(out, v, dims=([out.ndim - 1], [0]))
    return out


def make_feasible(raw: torch.Tensor, projector: torch.Tensor, eta: float,
                  restrict=None, generator=None) -> torch.Tensor:
    """Unit operator norm, then projected closure defect <= eta."""
    dim = raw.shape[0]
    norm = ternary_op_norm(raw, generator=generator)
    tensor = raw / norm.clamp_min(1e-12)
    normal = torch.eye(dim, dtype=DTYPE) - projector
    closure = ternary_op_norm(tensor, post=normal, restrict=restrict,
                              generator=generator)
    if float(closure) > eta:
        scale = eta / closure.clamp_min(1e-12)
        tang = torch.tensordot(tensor, projector, dims=([0], [1])).permute(3, 0, 1, 2)
        norm_part = torch.tensordot(tensor, normal, dims=([0], [1])).permute(3, 0, 1, 2)
        tensor = tang + scale * norm_part
    return tensor


def objective(params, klass: str, dim: int, rank: int, eta: float, generator):
    """Return ||D_A|| / eta for one admissible configuration."""
    identity = torch.eye(dim, dtype=DTYPE)
    P = coordinate_projector(dim, rank)

    if klass == "free":
        raw_inner_L, raw_root_L, raw_inner_M, raw_root_M = params[:4]
        P_inner_L = coordinate_projector(dim, params[4])
        P_inner_M = coordinate_projector(dim, params[5])
    elif klass == "same_law":
        raw = params[0]
        raw_inner_L = raw_root_L = raw_inner_M = raw_root_M = raw
        P_inner_L = coordinate_projector(dim, params[1])
        P_inner_M = coordinate_projector(dim, params[2])
    else:  # same_law_same_P
        raw = params[0]
        raw_inner_L = raw_root_L = raw_inner_M = raw_root_M = raw
        P_inner_L = P_inner_M = P

    leaves = [v / v.norm().clamp_min(1e-12) for v in params[-1]]
    x1, x2, x3, x4, x5 = leaves

    # Inner vertices: children are leaves, so closure is unrestricted.
    mu_inner_L = make_feasible(raw_inner_L, P_inner_L, eta, generator=generator)
    mu_inner_M = make_feasible(raw_inner_M, P_inner_M, eta, generator=generator)
    # Root vertices: the internal child is restricted to Ran(P_inner).
    mu_root_L = make_feasible(raw_root_L, P, eta, restrict=P_inner_L, generator=generator)
    mu_root_M = make_feasible(raw_root_M, P, eta, restrict=P_inner_M, generator=generator)

    inner_L = contract3(mu_inner_L, [x1, x2, x3])
    inner_M = contract3(mu_inner_M, [x2, x3, x4])
    D_L = (identity - P_inner_L) @ inner_L
    D_M = (identity - P_inner_M) @ inner_M

    # e_T = P mu_root(D, ...) : the exact k=2 identity, Lemma 11.1
    e_T = P @ contract3(mu_root_L, [D_L, x4, x5])
    e_TM = P @ contract3(mu_root_M, [x1, D_M, x5])
    D_A = -e_T + e_TM
    return D_A.norm() / eta, e_T, e_TM


def search(klass: str, dim: int, rank: int, eta: float, *, restarts: int,
           steps: int, seed: int) -> dict:
    generator = torch.Generator().manual_seed(seed)
    best = {"value": -1.0}
    for _ in range(restarts):
        if klass == "free":
            tensors = [torch.randn((dim,) * 4, dtype=DTYPE, generator=generator,
                                   requires_grad=True) for _ in range(4)]
            ranks = [int(torch.randint(1, dim, (1,), generator=generator).item())
                     for _ in range(2)]
            extra = ranks
        elif klass == "same_law":
            tensors = [torch.randn((dim,) * 4, dtype=DTYPE, generator=generator,
                                   requires_grad=True)]
            extra = [int(torch.randint(1, dim, (1,), generator=generator).item())
                     for _ in range(2)]
        else:
            tensors = [torch.randn((dim,) * 4, dtype=DTYPE, generator=generator,
                                   requires_grad=True)]
            extra = []
        leaves = [torch.randn(dim, dtype=DTYPE, generator=generator,
                              requires_grad=True) for _ in range(5)]
        variables = tensors + leaves
        optimizer = torch.optim.Adam(variables, lr=0.05)
        params = tensors + extra + [leaves]
        for _ in range(steps):
            optimizer.zero_grad(set_to_none=True)
            value, _, _ = objective(params, klass, dim, rank, eta, generator)
            (-value).backward()
            optimizer.step()
        with torch.no_grad():
            value, e_T, e_TM = objective(params, klass, dim, rank, eta, generator)
        if float(value) > best["value"]:
            denominator = float(e_T.norm() * e_TM.norm())
            best = {
                "value": float(value),
                "chi": (float(torch.dot(e_T, e_TM)) / denominator
                        if denominator > 1e-14 else float("nan")),
                "eT": float(e_T.norm() / eta),
                "eTM": float(e_TM.norm() / eta),
            }
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[2, 3, 4])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.2, 0.5, 0.8, 1.0])
    parser.add_argument("--classes", type=str, nargs="+",
                        default=["free", "same_law", "same_law_same_P"])
    parser.add_argument("--restarts", type=int, default=8)
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print(f"{'class':>18} {'D':>3} {'r':>3} {'eta':>6} {'J2':>8} "
          f"{'chi':>7} {'|eT|/eta':>9} {'|eT\'|/eta':>9}")
    records = []
    start = time.time()
    for klass in args.classes:
        for dim in args.dims:
            for rank in range(1, dim):
                for eta in args.etas:
                    result = search(klass, dim, rank, eta,
                                    restarts=args.restarts, steps=args.steps,
                                    seed=args.seed + 1000 * dim + 10 * rank)
                    result.update({"class": klass, "dim": dim, "rank": rank,
                                   "eta": eta})
                    records.append(result)
                    print(f"{klass:>18} {dim:3d} {rank:3d} {eta:6.2f} "
                          f"{result['value']:8.4f} {result['chi']:+7.3f} "
                          f"{result['eT']:9.4f} {result['eTM']:9.4f}", flush=True)

    (RESULTS / "m39a_j2_raw.json").write_text(
        json.dumps({"config": vars(args), "runs": records}, indent=2),
        encoding="utf-8")
    print(f"\n{len(records)} configurations in {time.time() - start:.0f}s")
    for klass in args.classes:
        values = [r["value"] for r in records if r["class"] == klass]
        if values:
            print(f"  {klass:>18}: max J2 = {max(values):.5f}")
    print("\nUpper bound from C_2^P = 1 is 2. Values above 2 + 1e-6 would "
          "indicate a feasibility bug, not a discovery.")


if __name__ == "__main__":
    main()
