"""Parallel driver for the M37 sweeps. Same numerics, 24 workers.

WHY CPU AND NOT GPU. The frozen pipeline is numpy float64 and Gate 0 reproduced
M31 to machine precision against it. Moving to torch/CUDA would change the
arithmetic (different reduction orders, and float64 throughput on this class of
card is heavily derated), so it would trade reproducibility for throughput --
which the campaign forbids. Every configuration (dim, seed, family) is an
independent deterministic computation, so process-level parallelism gives the
speedup with bit-identical results.

BLAS OVERSUBSCRIPTION. Each worker is pinned to a single BLAS thread. Without
this, 24 workers each spawning 24 OpenBLAS threads would contend for 24 cores
and run slower than serial. The variables must be set before numpy is imported
in the child, which happens here because Windows uses the spawn start method
and children inherit the parent environment set below.

Reproducibility is asserted, not assumed: --verify re-runs a sample serially
and compares bit-for-bit.
"""

from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_var] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor, as_completed  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_heterogeneity_mechanism_m37 import (  # noqa: E402
    INTERNAL_NODES, alpha_families, build_network, git_state, measure,
)
from run_heterogeneity_placement_m37 import placements  # noqa: E402
from tree import chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def run_task(task: dict) -> dict | None:
    """One (dim, seed, label) configuration. Must be importable for spawn."""
    dim, seed = task["dim"], task["seed"]
    alphas = np.asarray(task["alphas"], dtype=float)
    topology = chain_topology(depth=INTERNAL_NODES, leaf_dim=dim, ambient_dim=dim)
    net = build_network(topology, dim, alphas, structure_seed=seed)
    record = measure(topology, net, dim, seed)
    if not record:
        return None
    record.update({
        "dim": dim, "seed": seed,
        "alpha_mean": float(np.mean(alphas)), "alpha_std": float(np.std(alphas)),
        "alpha_min": float(np.min(alphas)), "alpha_max": float(np.max(alphas)),
        "n_distinct_alpha": int(len(np.unique(np.round(alphas, 6)))),
        **{k: v for k, v in task.items() if k in ("family", "placement", "multiset")},
    })
    if "placement" in task:
        record["alpha_sorted"] = sorted(float(a) for a in alphas)
    return record


def build_tasks(mode: str, dims, seeds) -> list[dict]:
    tasks = []
    for dim in dims:
        for seed in seeds:
            if mode == "distribution":
                for name, alphas in alpha_families(INTERNAL_NODES,
                                                   alpha_seed=500000 + seed).items():
                    tasks.append({"dim": dim, "seed": seed, "family": name,
                                  "alphas": alphas.tolist()})
            else:
                rng = np.random.default_rng(700000 + seed)
                multiset = rng.uniform(0.3, 2.0, size=INTERNAL_NODES)
                for name, alphas in placements(multiset, rng).items():
                    tasks.append({"dim": dim, "seed": seed, "placement": name,
                                  "multiset": "baseline", "alphas": alphas.tolist()})
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["distribution", "placement"],
                        default="distribution")
    parser.add_argument("--dims", type=int, nargs="+", default=[32])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--workers", type=int, default=min(24, os.cpu_count() or 1))
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--verify", type=int, default=0,
                        help="re-run this many tasks serially and compare bit-for-bit")
    args = parser.parse_args()

    tasks = build_tasks(args.mode, args.dims, args.seeds)
    print(f"{len(tasks)} tasks on {args.workers} workers "
          f"({os.cpu_count()} cores available)")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / args.out
    payload = {
        "config": {
            "mode": args.mode, "internal_nodes": INTERNAL_NODES,
            "dims": args.dims, "seeds": args.seeds, "workers": args.workers,
            "dtype": "float64", "backend": "numpy (BLAS pinned to 1 thread/worker)",
            "command": " ".join(sys.argv), "git": git_state(),
            "platform": platform.platform(), "numpy": np.__version__,
            "python": sys.version.split()[0],
        },
        "runs": [],
    }

    start = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_task, task): task for task in tasks}
        for future in as_completed(futures):
            record = future.result()
            done += 1
            if record:
                payload["runs"].append(record)
            if done % max(1, len(tasks) // 20) == 0 or done == len(tasks):
                out_path.write_text(json.dumps(payload), encoding="utf-8")
                rate = done / max(time.time() - start, 1e-9)
                print(f"  {done}/{len(tasks)} done, {time.time() - start:.0f}s, "
                      f"{rate:.2f} tasks/s, eta {(len(tasks) - done) / rate:.0f}s",
                      flush=True)

    out_path.write_text(json.dumps(payload), encoding="utf-8")
    elapsed = time.time() - start
    print(f"\nWrote {len(payload['runs'])} runs to {out_path} in {elapsed:.0f}s")

    if args.verify:
        print(f"\nreproducibility check: re-running {args.verify} tasks serially")
        key = "family" if args.mode == "distribution" else "placement"
        index = {(r["dim"], r["seed"], r[key]): r for r in payload["runs"]}
        worst = 0.0
        for task in tasks[: args.verify]:
            serial = run_task(task)
            if serial is None:
                continue
            parallel = index[(task["dim"], task["seed"], task[key])]
            for field in ("r_eff_participation", "R1", "R4", "stable_rank",
                          "base_error", "interaction_over_first_order"):
                worst = max(worst, abs(serial[field] - parallel[field]))
        verdict = "PASS" if worst == 0.0 else f"MISMATCH {worst:.3e}"
        print(f"  max |serial - parallel| over all compared fields = {worst:.3e}"
              f" -> {verdict}")


if __name__ == "__main__":
    main()
