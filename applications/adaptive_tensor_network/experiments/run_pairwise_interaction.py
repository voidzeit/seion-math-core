"""M29: the geometry of pairwise rank-decision interaction.

EXPLORATORY, NOT CONFIRMATORY. Same label as the sweep it reuses.

M27 established that marginal rank utility is non-monotone (42.7% of measured
marginals negative) and that no separable score tested predicts it at depth.
The object that was missing is the second difference

    I_uv(r) = E(r + e_u + e_v) - E(r + e_u) - E(r + e_v) + E(r),

the finite-difference analogue of d^2 E / dr_u dr_v. It is exactly the amount
by which one decision changes the value of another, since

    U_v(r + e_u) - U_v(r) = -I_uv(r).

I is symmetric in (u, v) by construction.

Establishing I != 0 is not the point -- M27 already implies that. The question
is what STRUCTURE I has: local (decaying with topological distance), low-rank
(few latent modes), sparse-but-nonlocal (a few strong couplings), or dense and
high-rank (allocation is genuinely global and no node-ordering allocator can
work).

Base states are exactly M27's: the same depths, regimes, seeds, budgets and
`uniform` base allocation, so the two campaigns are directly comparable and
U_v is reused rather than recomputed.

Also recorded, as the no-go sub-objective: how often bumping one node's rank
REVERSES the true utility ordering of two other nodes. A separable score
cannot represent such a reversal, since it assigns each node a value
independent of the others' ranks.

Raw records go to results/pairwise_interaction_raw.json; statistics are
computed afterward by analyze_pairwise_interaction.py.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_depth_sweep import (  # noqa: E402
    AMBIENT_DIM, EVAL_BATCH_SIZE, FIT_BATCH_SIZE, LEAF_DIM, SEEDS,
    budget_grid, heterogeneous_network,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DEPTHS = [6, 10, 16, 24]        # k=3 leaves <3 allocatable nodes, as in M27


def topological_distance(topology, a: str, b: str) -> int:
    """Edge distance through the lowest common ancestor."""
    path_a = topology.path_to_root(a)
    path_b = topology.path_to_root(b)
    index_b = {node_id: i for i, node_id in enumerate(path_b)}
    for i, node_id in enumerate(path_a):
        if node_id in index_b:
            return i + index_b[node_id]
    raise ValueError("nodes share no ancestor")


def run_one_trial(depth: int, regime: str, seed: int) -> list[dict]:
    topology = chain_topology(depth=depth, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, seed=seed))

    fit_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [node.node_id for node in topology.nodes_postorder]

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    records: list[dict] = []
    for budget in budget_grid(topology.internal_node_count):
        base = uniform_allocation(net, budget)
        eligible = [
            nid for nid in node_ids
            if nid != root_id and base.get(nid, AMBIENT_DIM) < AMBIENT_DIM
        ]
        if len(eligible) < 3:
            continue

        e_base = root_error(base)
        singles = {}
        for nid in eligible:
            bumped = dict(base)
            bumped[nid] += 1
            singles[nid] = root_error(bumped)
        utility = {nid: e_base - singles[nid] for nid in eligible}

        m = len(eligible)
        interaction = np.zeros((m, m))
        distance = np.zeros((m, m), dtype=int)
        for i in range(m):
            for j in range(i + 1, m):
                u, v = eligible[i], eligible[j]
                both = dict(base)
                both[u] += 1
                both[v] += 1
                value = root_error(both) - singles[u] - singles[v] + e_base
                interaction[i, j] = interaction[j, i] = value
                d = topological_distance(topology, u, v)
                distance[i, j] = distance[j, i] = d

        # No-go probe: bumping u turns U into U - I[u], so count how often the
        # ordering of two OTHER nodes reverses.
        u_vector = np.array([utility[nid] for nid in eligible])
        reversals, comparisons = 0, 0
        for i in range(m):
            shifted = u_vector - interaction[i]
            for a in range(m):
                if a == i:
                    continue
                for b in range(a + 1, m):
                    if b == i:
                        continue
                    comparisons += 1
                    if np.sign(u_vector[a] - u_vector[b]) != np.sign(shifted[a] - shifted[b]):
                        reversals += 1

        records.append({
            "depth": depth,
            "regime": regime,
            "seed": seed,
            "budget": budget,
            "eligible": eligible,
            "base_root_error": e_base,
            "utility": utility,
            "interaction": interaction.tolist(),
            "distance": distance.tolist(),
            "order_reversals": reversals,
            "order_comparisons": comparisons,
        })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    start = time.time()
    for regime in ("iid", "heterogeneous"):
        for depth in DEPTHS:
            for seed in SEEDS:
                all_records.extend(run_one_trial(depth, regime, seed))
            print(f"{regime} k={depth}: {len(all_records)} records so far, "
                  f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "pairwise_interaction_raw.json"
    out_path.write_text(json.dumps(all_records), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
