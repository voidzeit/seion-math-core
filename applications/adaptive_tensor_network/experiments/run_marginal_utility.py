"""M27: does any available score predict the causal marginal utility of rank?

EXPLORATORY, NOT CONFIRMATORY. Same label as the depth sweep it reuses.

The depth sweep established that `local_error_greedy` is never beaten by
`pathwise_global` at any depth or regime, but not why. This measures the
quantity an allocator is actually trying to rank on, directly:

    U_v = [ E_out(r) - E_out(r + e_v) ] / [ cost(r + e_v) - cost(r) ]

with cost = sum of ranks, so the denominator is 1 and U_v is the true drop in
root error from giving node v one more unit of rank. It is measured, not
predicted: both forward passes are run.

Four candidate scores are compared against it, all evaluated at the same base
allocation:

    s_local = eps_v                       local truncation error
    s_path  = w_v * eps_v                 pathwise score
    s_M24   = B_root(r) - B_root(r + e_v) marginal tightening of the M24 bound
    s_M25   = G_root(r) - G_root(r + e_v) same for the M25 bound

s_M24/s_M25 are defined as the certificate's OWN prediction of marginal
utility, which is the apples-to-apples comparison with U_v and is exactly what
a certificate-driven greedy step would rank on.

The base allocation is `uniform` at each budget: a neutral state that is not
itself produced by any of the scores under test, so no score is evaluated at a
point it chose.

Nodes already at full rank are excluded (no rank can be added), and configs
with fewer than three eligible nodes are skipped as unrankable.

Raw records go to results/marginal_utility_raw.json; all statistics are
computed afterward by analyze_marginal_utility.py.
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
from geometric_certificate import gram_aware_certificate, restricted_gain_certificate  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_depth_sweep import (  # noqa: E402
    AMBIENT_DIM, DEPTHS, EVAL_BATCH_SIZE, FIT_BATCH_SIZE, LEAF_DIM, SEEDS,
    budget_grid, heterogeneous_network, transport_weights,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def run_one_trial(depth: int, regime: str, seed: int) -> list[dict]:
    topology = chain_topology(depth=depth, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, seed=seed))

    fit_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)
    fit_ambient = net.ambient_forward(fit_batch)
    net.fit_projectors(fit_ambient)

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    amplifications = net.path_amplification(fit_ambient, fit_batch)
    weights = transport_weights(net, amplifications)
    node_ids = [node.node_id for node in topology.nodes_postorder]

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    records: list[dict] = []
    for budget in budget_grid(topology.internal_node_count):
        base = uniform_allocation(net, budget)
        # The root is excluded: `reduced_forward` does not project it, so its
        # rank is not a decision variable and would enter every ranking as a
        # guaranteed zero.
        eligible = [
            nid for nid in node_ids
            if nid != root_id and base.get(nid, AMBIENT_DIM) < AMBIENT_DIM
        ]
        if len(eligible) < 3:
            continue

        base_error = root_error(base)
        base_b = restricted_gain_certificate(net, eval_batch, base)["root_bound"]
        base_g = gram_aware_certificate(net, eval_batch, base)["root_bound"]
        local_errors = net.local_truncation_error(fit_ambient, base)
        path_scores = net.pathwise_score(local_errors, amplifications)

        utility, s_local, s_path, s_m24, s_m25 = {}, {}, {}, {}, {}
        for nid in eligible:
            bumped = dict(base)
            bumped[nid] = bumped[nid] + 1
            utility[nid] = base_error - root_error(bumped)
            s_local[nid] = local_errors[nid]
            s_path[nid] = path_scores[nid]
            s_m24[nid] = base_b - restricted_gain_certificate(net, eval_batch, bumped)["root_bound"]
            s_m25[nid] = base_g - gram_aware_certificate(net, eval_batch, bumped)["root_bound"]

        records.append({
            "depth": depth,
            "regime": regime,
            "seed": seed,
            "budget": budget,
            "n_eligible": len(eligible),
            "eligible": eligible,
            "base_root_error": base_error,
            "w_cv": float(np.std([weights[n] for n in node_ids])
                          / max(np.mean([weights[n] for n in node_ids]), 1e-30)),
            "utility": utility,
            "score_local": s_local,
            "score_path": s_path,
            "score_m24": s_m24,
            "score_m25": s_m25,
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

    out_path = RESULTS_DIR / "marginal_utility_raw.json"
    out_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
