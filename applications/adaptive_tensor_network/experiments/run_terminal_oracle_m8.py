"""M35b Phase A: a genuine finite-horizon terminal reference at m = 8.

EXPERIMENTAL. Nothing here is a theorem.

M35 showed the step-greedy policy is not a terminal oracle: policies making
locally worse choices ended with lower terminal error. Every trajectory-level
claim therefore lacks a valid reference. This computes a real one on the
smallest case.

With T rounds of b binary increments the terminal increment vector x = r_T - r_0
satisfies x_i in {0..T} and sum(x) = T*b. For m=8, T=6, b=3 there are exactly
235,348 such profiles -- verified by DP below -- against C(8,3)^6 = 3.08e10
action sequences, so enumerating terminal profiles is ~131,000x cheaper.

Every x with x_i <= T and sum(x) = T*b is reachable: distributing x into T
binary bundles of exactly b ones each is a bipartite degree-sequence problem
whose Gale-Ryser condition is exactly these constraints. A constructive
decomposition (repeatedly take the b largest remaining needs) is implemented
and used for the path-independence check.

PATH INDEPENDENCE. Enumerating terminal profiles is only valid if E depends on
the final rank vector alone. Here that is structural -- reduced_forward is a
pure function of (leaf_batch, ranks) and carries no history -- but M35 failed
precisely by assuming a property instead of testing it, so it is tested
explicitly against multiple distinct decompositions of the same profile.

PREFIX MEMOIZATION. In a chain, node n_j's value depends only on the ranks of
n_0..n_{j-1}, so a depth-first walk that projects one node per step and reuses
shared prefixes amortizes the cost. The DFS result is verified against direct
reduced_forward on a random sample; a mismatch aborts the run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import EVAL_BATCH, FIT_BATCH, heterogeneous_network  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
M = 8
BUNDLE = 3
ROUNDS = 6
START_FRACTION = 0.25
TOLERANCE = 1e-9


def count_profiles(m: int, rounds: int, bundle: int) -> int:
    total = rounds * bundle
    dp = [0] * (total + 1)
    dp[0] = 1
    for _ in range(m):
        nxt = [0] * (total + 1)
        for s, count in enumerate(dp):
            if count:
                for v in range(min(rounds, total - s) + 1):
                    nxt[s + v] += count
        dp = nxt
    return dp[total]


def decompose(profile: list[int], rounds: int, bundle: int, rng) -> list[tuple[int, ...]]:
    """Split a terminal profile into `rounds` binary bundles of size `bundle`.

    Take the `bundle` largest remaining needs each round, breaking ties at
    random so repeated calls give genuinely different action sequences.
    """
    remaining = list(profile)
    schedule = []
    for _ in range(rounds):
        keys = [(-remaining[i], float(rng.random()), i) for i in range(len(remaining))]
        keys.sort()
        chosen = tuple(sorted(k[2] for k in keys[:bundle]))
        if any(remaining[i] <= 0 for i in chosen):
            raise ValueError("profile is not decomposable")
        for i in chosen:
            remaining[i] -= 1
        schedule.append(chosen)
    if any(remaining):
        raise ValueError("profile not exhausted")
    return schedule


class ChainEvaluator:
    """Root error of a chain as a function of the allocatable rank vector."""

    def __init__(self, seed: int) -> None:
        self.topology = chain_topology(depth=M + 1, leaf_dim=DIM, ambient_dim=DIM)
        self.net = heterogeneous_network(self.topology, DIM, seed=seed)
        fit_batch = self.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
        self.eval_batch = self.net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
        self.net.fit_projectors(self.net.ambient_forward(fit_batch))
        self.nodes = [n.node_id for n in self.topology.nodes_postorder]
        self.root_id = self.topology.root.node_id
        self.allocatable = [n for n in self.nodes if n != self.root_id]
        self.root_ambient = self.net.ambient_forward(self.eval_batch)[self.root_id]
        budget = int(round(START_FRACTION * len(self.nodes) * DIM))
        self.base = uniform_allocation(self.net, max(len(self.nodes), budget))

    def direct(self, ranks: dict[str, int]) -> float:
        reduced = self.net.reduced_forward(self.eval_batch, ranks)
        diff = self.root_ambient - reduced[self.root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    def ranks_of(self, profile) -> dict[str, int]:
        ranks = dict(self.base)
        for node, increment in zip(self.allocatable, profile):
            ranks[node] = self.base[node] + int(increment)
        return ranks

    def enumerate_all(self, rounds: int, bundle: int, report=None):
        """Depth-first over allocatable ranks, reusing shared chain prefixes."""
        total = rounds * bundle
        m = len(self.allocatable)
        leaves = self.eval_batch
        cores = self.net.cores
        projectors = self.net.projectors
        root_ambient = self.root_ambient
        results: list[tuple[float, tuple[int, ...]]] = []
        counter = {"n": 0}

        def finish(prev_value):
            node = self.topology.root
            out = cores[node.node_id].apply([prev_value, leaves[M + 1]])
            diff = root_ambient - out
            return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

        def walk(index: int, used: int, prev_value, profile: list[int]):
            if index == m:
                if used != total:
                    return
                results.append((finish(prev_value), tuple(profile)))
                counter["n"] += 1
                if report and counter["n"] % 25000 == 0:
                    report(counter["n"])
                return
            remaining_slots = m - index - 1
            for increment in range(rounds + 1):
                if used + increment > total:
                    break
                if used + increment + remaining_slots * rounds < total:
                    continue
                node = self.topology.nodes_postorder[index]
                rank = self.base[node.node_id] + increment
                if rank > DIM:
                    break
                left = prev_value if index > 0 else leaves[0]
                out = cores[node.node_id].apply([left, leaves[index + 1]])
                projected = projectors[node.node_id].project(out, rank)
                profile.append(increment)
                walk(index + 1, used + increment, projected, profile)
                profile.pop()

        walk(0, 0, None, [])
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--verify-samples", type=int, default=200)
    args = parser.parse_args()

    expected = count_profiles(M, ROUNDS, BUNDLE)
    print(f"admissible terminal profiles (DP count): {expected}")

    # Merge into any existing payload rather than rebuilding it: this script is
    # run in several invocations (one per batch of seeds), and overwriting would
    # silently discard the seeds computed by an earlier call.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    existing_path = RESULTS_DIR / "terminal_oracle_m8_raw.json"
    payload = (json.loads(existing_path.read_text(encoding="utf-8"))
               if existing_path.exists() else {"config": {}, "seeds": {}})
    payload["config"] = {
        "m": M, "dim": DIM, "bundle": BUNDLE, "rounds": ROUNDS,
        "start_fraction": START_FRACTION, "eval_batch": EVAL_BATCH,
        "fit_batch": FIT_BATCH, "expected_profiles": expected,
        "regime": "heterogeneous", "dtype": "float64",
        "commands": payload.get("config", {}).get("commands", []) + [" ".join(sys.argv)],
    }

    for seed in args.seeds:
        start = time.time()
        evaluator = ChainEvaluator(seed)
        rng = np.random.default_rng(90210 + seed)

        # --- path independence -------------------------------------------------
        path_checks = []
        for _ in range(20):
            profile = [0] * M
            for _ in range(ROUNDS * BUNDLE):
                candidates = [i for i in range(M) if profile[i] < ROUNDS]
                profile[int(rng.choice(candidates))] += 1
            values = []
            for _ in range(4):
                schedule = decompose(profile, ROUNDS, BUNDLE, rng)
                ranks = dict(evaluator.base)
                for bundle in schedule:
                    for index in bundle:
                        ranks[evaluator.allocatable[index]] += 1
                values.append(evaluator.direct(ranks))
            path_checks.append(max(values) - min(values))
        path_spread = float(max(path_checks))
        path_independent = path_spread <= TOLERANCE
        print(f"seed {seed}: path-independence max spread = {path_spread:.3e} "
              f"-> {'PASS' if path_independent else 'FAIL'}")
        if not path_independent:
            payload["seeds"][str(seed)] = {
                "path_independent": False, "path_spread": path_spread,
                "note": "terminal-profile enumeration is invalid; stopping",
            }
            continue

        # --- enumeration -------------------------------------------------------
        def report(n):
            print(f"    seed {seed}: {n} profiles, {time.time() - start:.0f}s", flush=True)

        results = evaluator.enumerate_all(ROUNDS, BUNDLE, report=report)
        if len(results) != expected:
            raise RuntimeError(f"enumerated {len(results)}, expected {expected}")

        # --- verify the memoized DFS against direct evaluation -----------------
        sample = rng.choice(len(results), size=min(args.verify_samples, len(results)),
                            replace=False)
        worst = 0.0
        for index in sample:
            value, profile = results[int(index)]
            worst = max(worst, abs(value - evaluator.direct(evaluator.ranks_of(profile))))
        print(f"seed {seed}: DFS-vs-direct max abs error over {len(sample)} "
              f"samples = {worst:.3e} -> {'PASS' if worst <= 1e-9 else 'FAIL'}")
        if worst > 1e-9:
            raise RuntimeError("prefix-memoized enumeration disagrees with direct evaluation")

        values = np.array([r[0] for r in results])
        order = np.argsort(values)
        optimum = float(values[order[0]])
        ties = int(np.sum(values <= optimum + TOLERANCE))

        payload["seeds"][str(seed)] = {
            "path_independent": True,
            "path_spread": path_spread,
            "dfs_verification_max_error": worst,
            "n_profiles": len(results),
            "base_ranks": {k: int(v) for k, v in evaluator.base.items()},
            "base_error": evaluator.direct(evaluator.base),
            "E_terminal_star": optimum,
            "n_tied_optima": ties,
            "argmin_profile": list(results[int(order[0])][1]),
            "value_quantiles": {
                q: float(np.quantile(values, q / 100))
                for q in (0, 1, 5, 25, 50, 75, 95, 99, 100)
            },
            "top20_profiles": [
                {"profile": list(results[int(i)][1]), "value": float(values[i])}
                for i in order[:20]
            ],
            "wall_seconds": time.time() - start,
        }
        print(f"seed {seed}: E* = {optimum:.6f}, ties = {ties}, "
              f"{time.time() - start:.0f}s")

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / "terminal_oracle_m8_raw.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")

        np.save(RESULTS_DIR / f"terminal_oracle_m8_values_seed{seed}.npy", values)

    print("\nWrote results/terminal_oracle_m8_raw.json")


if __name__ == "__main__":
    main()
