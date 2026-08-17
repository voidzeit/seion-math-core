"""Random-sampling falsification of the k=2 ceilings, across all CPU cores.

EXPERIMENTAL. Companion to the GPU harness `rg_fused_search.py`, which does
gradient ascent. The two fail in different ways and are worth running together:
gradient ascent converges to whatever basin it starts in and can stall at a
saddle; uniform random sampling never finds the extremizer but covers the class
without bias, so it is the better detector of a bound that is simply WRONG
somewhere unexpected rather than merely not tight.

Both are tests of the same constraint-free ceilings, which need no penalty or
constraint handling:

    J:  ||D||                / (rho M L)  <= 2
    H:  (||PA|| - ||Ahat||)  / (rho M L)  <= 2
    S:  (||Ahat|| - ||PA||)  / (rho M L)  <= Sigma_2(eta)

Everything is vectorized over a batch of configurations and the batches are
spread over `--workers` processes, so the run is bounded by cores, not by
Python. On this machine (Intel Core Ultra 9 285HX, 24 cores) the default
saturates all of them.

Admissibility is enforced, not assumed: each law is scaled by its measured
operator norm and the inner laws have their normal component shrunk until the
closure budget holds. Operator norms are measured by alternating maximization
with multiple restarts, because a norm UNDERestimate would scale a law too
little and quietly push it outside the admissible class -- which would then
manufacture a false violation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sigma2(eta: float) -> float:
    return math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi)) / eta


def batched_op_norm(tensors: np.ndarray, restarts: int, iters: int,
                    rng: np.random.Generator) -> np.ndarray:
    """Operator norm of each tensor in a batch, over configurations at once.

    Shape (N, out, s1, s2, s3). Configurations and restarts are both folded
    into the leading axis of the SVD stack, so one call covers the batch.
    """
    count, dim = tensors.shape[0], tensors.shape[2]
    wide = np.repeat(tensors, restarts, axis=0)
    vectors = []
    for _ in range(3):
        block = rng.standard_normal((count * restarts, dim))
        vectors.append(block / np.linalg.norm(block, axis=1, keepdims=True))
    specs = ["noacd,nc,nd->noa", "noacd,na,nd->noc", "noacd,na,nc->nod"]
    for _ in range(iters):
        for slot in range(3):
            others = [s for s in range(3) if s != slot]
            mat = np.einsum(specs[slot], wide, vectors[others[0]],
                            vectors[others[1]], optimize=True)
            _, _, vh = np.linalg.svd(mat, full_matrices=False)
            vectors[slot] = vh[:, 0, :]
    values = np.einsum("noacd,na,nc,nd->no", wide, *vectors, optimize=True)
    norms = np.linalg.norm(values, axis=1).reshape(count, restarts)
    return norms.max(axis=1)


def coordinate_projectors(ranks: np.ndarray, dim: int) -> np.ndarray:
    index = np.arange(dim).reshape(1, dim)
    mask = (index < ranks.reshape(-1, 1)).astype(float)
    return mask[:, :, None] * np.eye(dim)[None, :, :]


def sample_and_score(job) -> dict:
    """One worker batch: sample admissible pairs, return the worst excesses."""
    seed, dim, eta, count, restarts, iters = job
    rng = np.random.default_rng(seed)

    ranks = rng.integers(1, dim, size=(3, count))
    P_iL, P_iM, P_root = (coordinate_projectors(r, dim) for r in ranks)
    identity = np.eye(dim)[None, :, :]

    def admissible_inner(projector):
        raw = rng.standard_normal((count, dim, dim, dim, dim))
        raw /= batched_op_norm(raw, restarts, iters, rng
                               ).reshape(-1, 1, 1, 1, 1)
        normal = identity - projector
        defect = batched_op_norm(np.einsum("nqo,noacd->nqacd", normal, raw),
                                 restarts, iters, rng)
        shrink = np.where(defect > eta, eta / np.maximum(defect, 1e-12), 1.0)
        return (np.einsum("nqo,noacd->nqacd", projector, raw)
                + shrink.reshape(-1, 1, 1, 1, 1)
                * np.einsum("nqo,noacd->nqacd", normal, raw))

    def admissible_root():
        """P-valued without loss of generality (Lemma 2.2)."""
        raw = np.einsum("nqo,noacd->nqacd", P_root,
                        rng.standard_normal((count, dim, dim, dim, dim)))
        return raw / batched_op_norm(raw, restarts, iters, rng
                                     ).reshape(-1, 1, 1, 1, 1)

    mu_iL, mu_iM = admissible_inner(P_iL), admissible_inner(P_iM)
    mu_rL, mu_rM = admissible_root(), admissible_root()

    leaves = rng.standard_normal((count, 5, dim))
    leaves /= np.linalg.norm(leaves, axis=2, keepdims=True)
    x1, x2, x3, x4, x5 = (leaves[:, i, :] for i in range(5))

    def contract(tensor, a, b, c):
        return np.einsum("noacd,na,nc,nd->no", tensor, a, b, c, optimize=True)

    def apply(projector, vector):
        return np.einsum("nij,nj->ni", projector, vector)

    F_iL = contract(mu_iL, x1, x2, x3)
    R_L = apply(P_root, contract(mu_rL, apply(P_iL, F_iL), x4, x5))
    F_L = contract(mu_rL, F_iL, x4, x5)
    F_iM = contract(mu_iM, x2, x3, x4)
    R_M = apply(P_root, contract(mu_rM, x1, apply(P_iM, F_iM), x5))
    F_M = contract(mu_rM, x1, F_iM, x5)

    A_hat = R_L - R_M
    PA = apply(P_root, F_L - F_M)
    D = A_hat - PA
    norm = lambda v: np.linalg.norm(v, axis=1)                # noqa: E731

    excess = {"J": norm(D) / eta - 2.0,
              "H": (norm(PA) - norm(A_hat)) / eta - 2.0,
              "S": (norm(A_hat) - norm(PA)) / eta - sigma2(eta)}
    return {"dim": dim, "eta": eta, "count": count,
            "max_excess": {key: float(value.max())
                           for key, value in excess.items()},
            "violations": {key: int((value > 1e-9).sum())
                           for key, value in excess.items()}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[2, 3, 4, 5, 6])
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.2, 0.4, 1 / math.sqrt(2), 0.9, 1.0])
    parser.add_argument("--samples", type=int, default=200_000,
                        help="configurations per (dim, eta) cell")
    parser.add_argument("--batch", type=int, default=2_000)
    parser.add_argument("--restarts", type=int, default=6)
    parser.add_argument("--iters", type=int, default=25)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--json", type=str, default="rg_cpu_falsify_raw.json")
    args = parser.parse_args()

    workers = args.workers or os.cpu_count() or 1
    jobs, seed = [], 20260816
    for dim in args.dims:
        for eta in args.etas:
            remaining = args.samples
            while remaining > 0:
                size = min(args.batch, remaining)
                jobs.append((seed, dim, eta, size, args.restarts, args.iters))
                seed += 1
                remaining -= size

    total = sum(job[3] for job in jobs)
    print(f"{total:,} random admissible pairs over {len(args.dims)} dims x "
          f"{len(args.etas)} etas, {len(jobs)} batches on {workers} cores")

    started = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(sample_and_score, jobs, chunksize=1))
    elapsed = time.time() - started

    summary = {}
    for row in results:
        key = (row["dim"], row["eta"])
        entry = summary.setdefault(key, {"count": 0, "max_excess": {},
                                         "violations": {}})
        entry["count"] += row["count"]
        for objective in ("J", "H", "S"):
            entry["max_excess"][objective] = max(
                entry["max_excess"].get(objective, -math.inf),
                row["max_excess"][objective])
            entry["violations"][objective] = (
                entry["violations"].get(objective, 0)
                + row["violations"][objective])

    print(f"\n{'D':>3} {'eta':>6} {'samples':>10} {'max excess J':>14} "
          f"{'max excess H':>14} {'max excess S':>14}")
    violations = 0
    for (dim, eta), entry in sorted(summary.items()):
        excess = entry["max_excess"]
        violations += sum(entry["violations"].values())
        print(f"{dim:3d} {eta:6.3f} {entry['count']:10,} "
              f"{excess['J']:+14.3e} {excess['H']:+14.3e} "
              f"{excess['S']:+14.3e}")

    (HERE / args.json).write_text(
        json.dumps({"config": vars(args),
                    "summary": [{"dim": k[0], "eta": k[1], **v}
                                for k, v in sorted(summary.items())]},
                   indent=2), encoding="utf-8")
    rate = total / max(elapsed, 1e-9)
    print(f"\n{total:,} pairs in {elapsed:.0f}s ({rate:,.0f}/s) on {workers} "
          f"cores -> {args.json}")
    print(f"  configurations above a ceiling: {violations} "
          f"(any is a refutation or an admissibility bug -- inspect)")


if __name__ == "__main__":
    main()
