"""M35b Phase A (policies) and Phase B: policy benchmark, with a true terminal
reference at m = 8.

EXPERIMENTAL. Nothing here is a theorem.

At m = 8 the exact finite-horizon optimum E* over all 235,348 admissible
terminal profiles is available from run_terminal_oracle_m8.py, so a genuine
terminal regret

    R_T^pi = E(r_T^pi) - E*

is defined, along with the rank of each policy's terminal state among all
feasible terminal states. At larger m no terminal oracle exists and only
within-m policy comparisons are reported; the one-step greedy policy is named
STEP_GREEDY throughout and is never called an oracle.

Policies:
    uniform                 round-robin, no measurement
    local_greedy            top-b by local truncation error
    measured_first_order    top-b by measured U_v
    full_pairwise           exhaustive on -U^T D + sum_{u<v} I_uv D_u D_v
    lowrank_pairwise_q4     same with I truncated to rank 4, truncation
                            diagonal removed
    step_greedy             exhaustive on the true immediate objective

All measurement-based policies draw from the SAME candidate pool at each state,
generated from a deterministic integer seed. Python's process-salted string
hash is never used for seeding.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import subprocess
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
BUNDLE = 3
ROUNDS = 6
START_FRACTION = 0.25
POOL = 600
Q_MODES = 4
POLICIES = ("uniform", "local_greedy", "measured_first_order",
            "full_pairwise", "lowrank_pairwise_q4", "step_greedy")


def git_state() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True,
            cwd=str(Path(__file__).resolve().parents[3]),
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def low_rank_matrix(interaction: np.ndarray, q: int) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    np.fill_diagonal(approx, 0.0)
    return approx


def build_pool(m: int, b: int, pool_seed: int) -> list[tuple[int, ...]]:
    total = 1
    for i in range(b):
        total = total * (m - i) // (i + 1)
    if total <= POOL:
        return list(itertools.combinations(range(m), b))
    rng = np.random.default_rng(pool_seed)
    seen = set()
    while len(seen) < POOL:
        seen.add(tuple(sorted(rng.choice(m, size=b, replace=False).tolist())))
    return sorted(seen)


class Instance:
    def __init__(self, m: int, seed: int) -> None:
        self.topology = chain_topology(depth=m + 1, leaf_dim=DIM, ambient_dim=DIM)
        self.net = heterogeneous_network(self.topology, DIM, seed=seed)
        fit_batch = self.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
        self.eval_batch = self.net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
        self.fit_ambient = self.net.ambient_forward(fit_batch)
        self.net.fit_projectors(self.fit_ambient)
        self.nodes = [n.node_id for n in self.topology.nodes_postorder]
        self.root_id = self.topology.root.node_id
        self.root_ambient = self.net.ambient_forward(self.eval_batch)[self.root_id]
        budget = int(round(START_FRACTION * len(self.nodes) * DIM))
        self.base = uniform_allocation(self.net, max(len(self.nodes), budget))
        self.allocatable = [n for n in self.nodes if n != self.root_id]
        self.evaluations = 0

    def error(self, ranks: dict[str, int]) -> float:
        self.evaluations += 1
        reduced = self.net.reduced_forward(self.eval_batch, ranks)
        diff = self.root_ambient - reduced[self.root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))


def run_policy(instance: Instance, policy: str, seed: int) -> dict:
    ranks = dict(instance.base)
    instance.evaluations = 0
    trajectory = []
    start = time.time()

    for step in range(ROUNDS):
        eligible = [n for n in instance.allocatable if ranks[n] < DIM]
        if len(eligible) < BUNDLE:
            break
        m = len(eligible)
        pool = build_pool(m, BUNDLE, pool_seed=seed * 100003 + step * 97 + 17)

        if policy == "uniform":
            order = sorted(range(m), key=lambda i: (ranks[eligible[i]], i))
            pick = tuple(sorted(order[:BUNDLE]))
        elif policy == "local_greedy":
            local = instance.net.local_truncation_error(instance.fit_ambient, ranks)
            order = sorted(range(m), key=lambda i: -local[eligible[i]])
            pick = tuple(sorted(order[:BUNDLE]))
        elif policy == "step_greedy":
            best, best_value = None, float("inf")
            for combo in pool:
                candidate = dict(ranks)
                for index in combo:
                    candidate[eligible[index]] += 1
                value = instance.error(candidate)
                if value < best_value:
                    best, best_value = combo, value
            pick = best
        else:
            e_base = instance.error(ranks)
            singles = {n: instance.error({**ranks, n: ranks[n] + 1}) for n in eligible}
            utility = np.array([e_base - singles[n] for n in eligible])
            if policy == "measured_first_order":
                scores = [-float(utility[list(combo)].sum()) for combo in pool]
            else:
                interaction = np.zeros((m, m))
                for i in range(m):
                    for j in range(i + 1, m):
                        u, v = eligible[i], eligible[j]
                        value = (instance.error({**ranks, u: ranks[u] + 1, v: ranks[v] + 1})
                                 - singles[u] - singles[v] + e_base)
                        interaction[i, j] = interaction[j, i] = value
                matrix = (interaction if policy == "full_pairwise"
                          else low_rank_matrix(interaction, min(Q_MODES, m)))
                scores = []
                for combo in pool:
                    delta = np.zeros(m)
                    delta[list(combo)] = 1.0
                    scores.append(-float(utility @ delta)
                                  + 0.5 * float(delta @ matrix @ delta))
            pick = pool[int(np.argmin(scores))]

        for index in pick:
            ranks[eligible[index]] += 1
        trajectory.append(instance.error(ranks))

    profile = [ranks[n] - instance.base[n] for n in instance.allocatable]
    return {
        "policy": policy,
        "trajectory": trajectory,
        "terminal_error": trajectory[-1],
        "terminal_profile": profile,
        "evaluations": instance.evaluations,
        "wall_seconds": time.time() - start,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, nargs="+", default=[8])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--out", type=str, default="policy_scaling_raw.json")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / args.out
    payload = {
        "config": {
            "dim": DIM, "bundle": BUNDLE, "rounds": ROUNDS, "pool": POOL,
            "start_fraction": START_FRACTION, "q_modes": Q_MODES,
            "eval_batch": EVAL_BATCH, "fit_batch": FIT_BATCH,
            "regime": "heterogeneous", "dtype": "float64",
            "m_values": args.m, "seeds": args.seeds,
            "command": " ".join(sys.argv), "git": git_state(),
            "platform": platform.platform(), "numpy": np.__version__,
        },
        "runs": [],
    }

    start = time.time()
    for m in args.m:
        for seed in args.seeds:
            instance = Instance(m, seed)
            base_error = instance.error(instance.base)
            for policy in POLICIES:
                result = run_policy(instance, policy, seed)
                result.update({"m": m, "seed": seed, "base_error": base_error})
                payload["runs"].append(result)
            # checkpoint after every instance so a crash cannot destroy the run
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"m={m} seed={seed} done, elapsed={time.time() - start:.0f}s",
                  flush=True)

    print(f"\nWrote {len(payload['runs'])} policy runs to {out_path}")


if __name__ == "__main__":
    main()
