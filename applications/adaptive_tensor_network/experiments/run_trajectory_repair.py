"""M35: does re-measuring U repair local regret as m grows?

EXPLORATORY, NOT CONFIRMATORY.

M34 found that per single decision the pairwise surrogate recovers essentially
all the headroom (C_I ~ 1 at every m) and that first order's choices degrade
sharply with scale -- its pick falls from the 2nd-best bundle at m=8 to the
29th at m=31. M33 found that over a six-round trajectory at m=14 that advantage
mostly vanishes. The proposed explanation is that re-measuring U at each new
state repairs the damage, so per-step losses do not compound.

This tests that directly, and at scale. For each method, along ITS OWN
trajectory:

    R_t^inst  = E(method's pick at step t) - min over the pool at step t
    sum_t R_t^inst                                   if losses compounded fully
    R_T^term  = E_method(T) - E_step_oracle(T)       what actually survived
    A_T       = 1 - R_T^term / sum_t R_t^inst        the repair coefficient

A_T ~ 1 means marginal feedback substitutes for pairwise modelling: the loop
recovers almost everything it gave up step by step. A_T falling with m means
the interaction becomes operationally necessary, not merely informative.

A_T > 1 is possible and meaningful: the step-greedy oracle is not globally
optimal, so a method that makes locally worse choices can land in a better
basin.

At every step each method draws a fresh candidate pool from its current state,
evaluates all of it truly to obtain R_t^inst, then advances using its own rule.
The step oracle uses the same pool with the true objective.
"""

from __future__ import annotations

import itertools
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
from run_interaction_dimension import (  # noqa: E402
    EVAL_BATCH, FIT_BATCH, heterogeneous_network,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
SEEDS = [0, 1, 2]
M_VALUES = [8, 14, 23, 31]
BUNDLE = 3
ROUNDS = 6
POOL = 600
Q_MODES = 4
START_FRACTION = 0.25
METHODS = ("first_order", "full_pairwise", "lowrank_pairwise", "step_oracle")


def low_rank_matrix(interaction: np.ndarray, q: int) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    np.fill_diagonal(approx, 0.0)
    return approx


def sample_pool(m: int, b: int, rng) -> list[tuple[int, ...]]:
    total = 1
    for i in range(b):
        total = total * (m - i) // (i + 1)
    if total <= POOL:
        return list(itertools.combinations(range(m), b))
    seen = set()
    while len(seen) < POOL:
        seen.add(tuple(sorted(rng.choice(m, size=b, replace=False).tolist())))
    return sorted(seen)


def run_one_trial(m_target: int, seed: int) -> dict:
    topology = chain_topology(depth=m_target + 1, leaf_dim=DIM, ambient_dim=DIM)
    net = heterogeneous_network(topology, DIM, seed=seed)
    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [n.node_id for n in topology.nodes_postorder]

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    budget = max(len(node_ids), int(round(START_FRACTION * len(node_ids) * DIM)))
    start = uniform_allocation(net, budget)

    results = {}
    for method_index, method in enumerate(METHODS):
        ranks = dict(start)
        # A deterministic per-method offset: Python's string hash is salted per
        # process, so hash(method) would give a different pool on every run.
        rng = np.random.default_rng(seed * 4093 + method_index)
        trajectory, instant_regret, evaluations = [], [], 0

        for _ in range(ROUNDS):
            eligible = [nid for nid in node_ids
                        if nid != root_id and ranks[nid] < DIM]
            if len(eligible) < BUNDLE + 1:
                break
            m = len(eligible)
            e_base = root_error(ranks)
            evaluations += 1

            pool = sample_pool(m, BUNDLE, rng)
            truth = []
            for combo in pool:
                candidate = dict(ranks)
                for index in combo:
                    candidate[eligible[index]] += 1
                truth.append(root_error(candidate))
            truth = np.array(truth)
            evaluations += len(pool)

            if method == "step_oracle":
                pick = int(np.argmin(truth))
            else:
                singles = {nid: root_error({**ranks, nid: ranks[nid] + 1})
                           for nid in eligible}
                evaluations += m
                utility = np.array([e_base - singles[nid] for nid in eligible])
                if method == "first_order":
                    scores = np.array([
                        -float(utility[list(combo)].sum()) for combo in pool])
                else:
                    interaction = np.zeros((m, m))
                    for i in range(m):
                        for j in range(i + 1, m):
                            u, v = eligible[i], eligible[j]
                            value = (root_error({**ranks, u: ranks[u] + 1, v: ranks[v] + 1})
                                     - singles[u] - singles[v] + e_base)
                            interaction[i, j] = interaction[j, i] = value
                    evaluations += m * (m - 1) // 2
                    matrix = (interaction if method == "full_pairwise"
                              else low_rank_matrix(interaction, min(Q_MODES, m)))
                    scores = []
                    for combo in pool:
                        delta = np.zeros(m)
                        delta[list(combo)] = 1.0
                        scores.append(-float(utility @ delta)
                                      + 0.5 * float(delta @ matrix @ delta))
                    scores = np.array(scores)
                pick = int(np.argmin(scores))

            instant_regret.append(float(truth[pick] - truth.min()))
            for index in pool[pick]:
                ranks[eligible[index]] += 1
            trajectory.append(float(truth[pick]))

        results[method] = {
            "trajectory": trajectory,
            "instant_regret": instant_regret,
            "evaluations": evaluations,
        }

    return {"m_target": m_target, "seed": seed, "methods": results}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    start_time = time.time()
    for m_target in M_VALUES:
        for seed in SEEDS:
            records.append(run_one_trial(m_target, seed))
        print(f"m~{m_target}: {len(records)} trials, "
              f"elapsed={time.time() - start_time:.1f}s", flush=True)

    out_path = RESULTS_DIR / "trajectory_repair_raw.json"
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(records)} trials to {out_path}")
    print(f"Total wall time: {time.time() - start_time:.1f}s")


if __name__ == "__main__":
    main()
