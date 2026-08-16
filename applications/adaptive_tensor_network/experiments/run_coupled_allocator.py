"""M33: does the low-rank coupled surrogate actually allocate better?

EXPLORATORY, NOT CONFIRMATORY.

M32A established that the second-order surrogate predicts held-out binary
bundles well (R^2 = 0.962, regret 0.002 in the structured regime) and that a
rank-4 compression of the interaction loses almost nothing. M32B established
that multi-unit steps from a single expansion are not supported. The algorithm
the data licenses is therefore incremental BINARY rounds with re-estimation,
and this tests whether it produces a better compression trajectory.

Protocol. Every method starts from the same low base allocation and runs the
same number of rounds, adding at most one unit to each of b nodes per round.
Each method follows its own trajectory from its own state, which is the
realistic comparison. True root error is recorded after every round.

Surrogate optimization is EXHAUSTIVE. With m = 14 and b = 3 there are
C(14,3) = 364 candidate bundles, so each surrogate is maximized exactly. Any
difference between methods is therefore attributable to the model, not to a
heuristic solver -- and the exact oracle evaluates the true error on the same
364 bundles, so it is the same search over a different objective.

Methods:
    uniform         round-robin, ignores everything
    local_greedy    top-b by local truncation error eps_v
    pathwise        top-b by w_v * eps_v
    first_order     top-b by measured U_v -- a first-order ORACLE, since U is
                    measured exactly rather than predicted
    full_pairwise   exhaustive on -U^T D + sum_{u<v} I_uv D_u D_v
    lowrank_pairwise same with I compressed to rank q, spurious truncation
                    diagonal removed
    oracle          exhaustive on the measured true error

Acquisition cost is recorded per method per round in units of forward
evaluations, because the coupled methods pay O(m^2) to build I and that cost is
the honest obstacle to scaling.
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

from network import TensorNetwork  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import (  # noqa: E402
    EVAL_BATCH, FIT_BATCH, heterogeneous_network, topology_for,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
FAMILIES = ("chain", "balanced")
SEEDS = [0, 1, 2]
START_RANK = 2
ROUNDS = 6
PER_ROUND = 3
Q_MODES = 4
METHODS = ("uniform", "local_greedy", "pathwise", "first_order",
           "full_pairwise", "lowrank_pairwise", "oracle")


def low_rank_matrix(interaction: np.ndarray, q: int) -> np.ndarray:
    """Rank-q approximation of I with the truncation-induced diagonal removed.

    Truncating a zero-diagonal matrix generally produces a nonzero diagonal,
    which would silently reintroduce a self-interaction term that the exact I
    does not have.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    np.fill_diagonal(approx, 0.0)
    return approx


def best_bundle(scores, m: int, b: int, objective) -> tuple[int, ...]:
    best, best_value = None, float("inf")
    for combo in itertools.combinations(range(m), b):
        value = objective(combo)
        if value < best_value:
            best, best_value = combo, value
    return best


def run_trajectory(net, topology, base: dict, method: str, eval_batch,
                   root_ambient, fit_ambient, amplifications) -> dict:
    root_id = topology.root.node_id
    node_ids = [n.node_id for n in topology.nodes_postorder]
    ranks = dict(base)
    trajectory, costs = [], []
    evaluations = 0

    def root_error(candidate: dict) -> float:
        reduced = net.reduced_forward(eval_batch, candidate)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    for _ in range(ROUNDS):
        eligible = [nid for nid in node_ids
                    if nid != root_id and ranks[nid] < DIM]
        if len(eligible) < PER_ROUND:
            break
        m = len(eligible)

        if method == "uniform":
            order = sorted(eligible, key=lambda nid: (ranks[nid], nid))
            chosen = tuple(eligible.index(nid) for nid in order[:PER_ROUND])
        elif method in ("local_greedy", "pathwise"):
            local = net.local_truncation_error(fit_ambient, ranks)
            if method == "local_greedy":
                score = {nid: local[nid] for nid in eligible}
            else:
                score = {
                    nid: local[nid] * float(np.prod([
                        amplifications.get(s, 1.0)
                        for s in topology.path_to_root(nid)[:-1]]))
                    for nid in eligible
                }
            order = sorted(eligible, key=lambda nid: -score[nid])
            chosen = tuple(eligible.index(nid) for nid in order[:PER_ROUND])
        else:
            e_base = root_error(ranks)
            evaluations += 1
            singles = {}
            for nid in eligible:
                singles[nid] = root_error({**ranks, nid: ranks[nid] + 1})
            evaluations += m
            utility = np.array([e_base - singles[nid] for nid in eligible])

            if method == "first_order":
                chosen = tuple(np.argsort(-utility)[:PER_ROUND])
            elif method == "oracle":
                def true_objective(combo):
                    candidate = dict(ranks)
                    for index in combo:
                        candidate[eligible[index]] += 1
                    return root_error(candidate)
                chosen = best_bundle(None, m, PER_ROUND, true_objective)
                evaluations += sum(1 for _ in itertools.combinations(range(m), PER_ROUND))
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

                def surrogate(combo):
                    delta = np.zeros(m)
                    delta[list(combo)] = 1.0
                    return -float(utility @ delta) + 0.5 * float(delta @ matrix @ delta)
                chosen = best_bundle(None, m, PER_ROUND, surrogate)

        for index in chosen:
            ranks[eligible[index]] += 1
        trajectory.append(root_error(ranks))
        costs.append(evaluations)

    return {"trajectory": trajectory, "evaluations": costs,
            "final_ranks": dict(ranks)}


def run_one_trial(family: str, regime: str, seed: int) -> dict:
    topology = topology_for(family, DIM)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, DIM, seed=seed))
    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    fit_ambient = net.ambient_forward(fit_batch)
    net.fit_projectors(fit_ambient)
    root_ambient = net.ambient_forward(eval_batch)[topology.root.node_id]
    amplifications = net.path_amplification(fit_ambient, fit_batch)

    base = {n.node_id: START_RANK for n in topology.nodes_postorder}
    results = {}
    for method in METHODS:
        results[method] = run_trajectory(
            net, topology, base, method, eval_batch, root_ambient,
            fit_ambient, amplifications,
        )
    return {"family": family, "regime": regime, "seed": seed, "methods": results}


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    start = time.time()
    for regime in ("iid", "heterogeneous"):
        for family in FAMILIES:
            for seed in SEEDS:
                records.append(run_one_trial(family, regime, seed))
                print(f"{regime}/{family}/seed{seed} done, "
                      f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "coupled_allocator_raw.json"
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
