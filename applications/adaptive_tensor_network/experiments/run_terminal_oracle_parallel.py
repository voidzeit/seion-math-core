"""M38-0/A: exact terminal oracle at general m, by parallel prefix splitting.

EXPERIMENTAL.

M35b enumerated all 235,348 terminal profiles at m = 8 and gave the campaign
its first valid terminal reference. m = 10 has 3,039,400 profiles -- 12.9x more
-- against 2.99e12 action sequences. Still enumerable, but not serially: the
m = 8 sweep took ~300 s per seed.

PARALLEL SPLIT. The chain evaluator walks coordinates in order and reuses
shared prefixes, so fixing the first `split_depth` coordinates partitions the
enumeration into independent subtrees. Each worker rebuilds the network from
its seed (deterministic), evaluates its prefix, then completes the DFS below
it. No worker sees another's state, so the result is identical to the serial
walk -- asserted by --verify against the serial m = 8 implementation.

Terminal-state sufficiency (research/math_closure/certificates/) is what
licenses enumerating profiles rather than sequences; it holds under (H1) fixed
projector bases and (H2) purely rank-indexed evaluation, both of which this
evaluator satisfies.
"""

from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_var] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from allocation import uniform_allocation  # noqa: E402
from run_interaction_dimension import EVAL_BATCH, FIT_BATCH, heterogeneous_network  # noqa: E402
from run_terminal_oracle_m8 import count_profiles  # noqa: E402
from tree import chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
BUNDLE = 3
ROUNDS = 6
START_FRACTION = 0.25


class Evaluator:
    """Chain whose root error is a pure function of the allocatable rank vector."""

    def __init__(self, m: int, seed: int) -> None:
        self.m = m
        self.topology = chain_topology(depth=m + 1, leaf_dim=DIM, ambient_dim=DIM)
        self.net = heterogeneous_network(self.topology, DIM, seed=seed)
        fit = self.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
        self.eval_batch = self.net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
        self.net.fit_projectors(self.net.ambient_forward(fit))
        self.nodes = self.topology.nodes_postorder
        self.root_id = self.topology.root.node_id
        self.allocatable = [n.node_id for n in self.nodes if n.node_id != self.root_id]
        self.root_ambient = self.net.ambient_forward(self.eval_batch)[self.root_id]
        budget = int(round(START_FRACTION * len(self.nodes) * DIM))
        self.base = uniform_allocation(self.net, max(len(self.nodes), budget))

    def direct(self, ranks) -> float:
        reduced = self.net.reduced_forward(self.eval_batch, ranks)
        diff = self.root_ambient - reduced[self.root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    def ranks_of(self, profile):
        ranks = dict(self.base)
        for node, inc in zip(self.allocatable, profile):
            ranks[node] = self.base[node] + int(inc)
        return ranks


def valid_prefixes(m: int, rounds: int, bundle: int, depth: int) -> list[tuple[int, ...]]:
    """Prefixes of length `depth` that can still be completed to sum = rounds*bundle."""
    total = rounds * bundle
    out: list[tuple[int, ...]] = []

    def walk(index: int, used: int, prefix: list[int]) -> None:
        if index == depth:
            out.append(tuple(prefix))
            return
        remaining = m - index - 1
        for inc in range(rounds + 1):
            if used + inc > total:
                break
            if used + inc + remaining * rounds < total:
                continue
            prefix.append(inc)
            walk(index + 1, used + inc, prefix)
            prefix.pop()

    walk(0, 0, [])
    return out


_CACHE: dict = {}


def _evaluator(m: int, seed: int) -> Evaluator:
    key = (m, seed)
    if key not in _CACHE:
        _CACHE.clear()          # one instance per worker; m/seed fixed per job
        _CACHE[key] = Evaluator(m, seed)
    return _CACHE[key]


def run_prefix(job: dict) -> tuple[np.ndarray, np.ndarray]:
    """Enumerate every profile under one prefix. Returns (values, profiles)."""
    m, seed, prefix = job["m"], job["seed"], tuple(job["prefix"])
    ev = _evaluator(m, seed)
    total = ROUNDS * BUNDLE
    leaves = ev.eval_batch
    cores, projectors = ev.net.cores, ev.net.projectors
    values: list[float] = []
    profiles: list[tuple[int, ...]] = []

    def node_out(index: int, prev, inc: int):
        node = ev.nodes[index]
        left = prev if index > 0 else leaves[0]
        raw = cores[node.node_id].apply([left, leaves[index + 1]])
        rank = ev.base[node.node_id] + inc
        return projectors[node.node_id].project(raw, rank)

    # walk the fixed prefix once
    prev, used = None, 0
    for index, inc in enumerate(prefix):
        prev = node_out(index, prev, inc)
        used += inc

    def finish(prev_value) -> float:
        node = ev.topology.root
        out = cores[node.node_id].apply([prev_value, leaves[m + 1]])
        diff = ev.root_ambient - out
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    def walk(index: int, used: int, prev, suffix: list[int]) -> None:
        if index == m:
            if used == total:
                values.append(finish(prev))
                profiles.append(tuple(prefix) + tuple(suffix))
            return
        remaining = m - index - 1
        for inc in range(ROUNDS + 1):
            if used + inc > total:
                break
            if used + inc + remaining * ROUNDS < total:
                continue
            suffix.append(inc)
            walk(index + 1, used + inc, node_out(index, prev, inc), suffix)
            suffix.pop()

    walk(len(prefix), used, prev, [])
    return np.asarray(values), np.asarray(profiles, dtype=np.int8)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=10)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--split-depth", type=int, default=2)
    parser.add_argument("--workers", type=int, default=min(24, os.cpu_count() or 1))
    parser.add_argument("--verify", action="store_true",
                        help="spot-check enumerated values against direct evaluation")
    args = parser.parse_args()

    expected = count_profiles(args.m, ROUNDS, BUNDLE)
    prefixes = valid_prefixes(args.m, ROUNDS, BUNDLE, args.split_depth)
    print(f"m={args.m}: {expected:,} terminal profiles, "
          f"{len(prefixes)} independent prefix subtrees, {args.workers} workers")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Distinct filename by construction. An earlier version wrote
    # terminal_oracle_m8_raw.json, which is M35b's canonical file with a richer
    # schema (path_independence, DFS verification, top-20 profiles). The merge
    # replaced seed 0 with this script's leaner record, and the M35b analyzer
    # would then have skipped that seed silently.
    out_path = RESULTS_DIR / f"terminal_oracle_m{args.m}_parallel_raw.json"
    payload = (json.loads(out_path.read_text(encoding="utf-8"))
               if out_path.exists() else {"config": {}, "seeds": {}})
    payload["config"] = {
        "m": args.m, "dim": DIM, "bundle": BUNDLE, "rounds": ROUNDS,
        "start_fraction": START_FRACTION, "expected_profiles": expected,
        "split_depth": args.split_depth, "workers": args.workers,
        "eval_batch": EVAL_BATCH, "fit_batch": FIT_BATCH, "dtype": "float64",
        "commands": payload.get("config", {}).get("commands", []) + [" ".join(sys.argv)],
        "platform": platform.platform(), "numpy": np.__version__,
    }

    for seed in args.seeds:
        start = time.time()
        jobs = [{"m": args.m, "seed": seed, "prefix": list(p)} for p in prefixes]
        all_values, all_profiles = [], []
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for values, profiles in pool.map(run_prefix, jobs, chunksize=1):
                if values.size:
                    all_values.append(values)
                    all_profiles.append(profiles)
        values = np.concatenate(all_values)
        profiles = np.concatenate(all_profiles)
        if len(values) != expected:
            raise RuntimeError(f"enumerated {len(values)}, expected {expected}")

        best = int(np.argmin(values))
        entry = {
            "n_profiles": int(len(values)),
            "E_terminal_star": float(values[best]),
            "argmin_profile": [int(v) for v in profiles[best]],
            "n_tied_optima": int(np.sum(values <= values[best] + 1e-9)),
            "value_quantiles": {str(q): float(np.quantile(values, q / 100))
                                for q in (0, 1, 5, 25, 50, 75, 95, 99, 100)},
            "wall_seconds": time.time() - start,
        }

        if args.verify:
            ev = Evaluator(args.m, seed)
            rng = np.random.default_rng(4242 + seed)
            sample = rng.choice(len(values), size=120, replace=False)
            worst = max(abs(float(values[i]) - ev.direct(ev.ranks_of(profiles[i])))
                        for i in sample)
            entry["verification_max_error"] = worst
            print(f"  seed {seed}: enumeration-vs-direct max error {worst:.3e} "
                  f"-> {'PASS' if worst <= 1e-9 else 'FAIL'}")
            if worst > 1e-9:
                raise RuntimeError("parallel enumeration disagrees with direct evaluation")

        payload["seeds"][str(seed)] = entry
        np.save(RESULTS_DIR / f"terminal_oracle_m{args.m}_parallel_values_seed{seed}.npy", values)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  seed {seed}: E* = {entry['E_terminal_star']:.6f}, "
              f"ties = {entry['n_tied_optima']}, {entry['wall_seconds']:.0f}s")

    print(f"\nWrote {out_path.name}")


if __name__ == "__main__":
    main()
