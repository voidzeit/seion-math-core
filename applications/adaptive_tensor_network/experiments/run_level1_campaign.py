"""Level 1 (mission AI3): exact synthetic validation campaign.

Runs the preregistered design in PREREGISTRATION.md: 2 topologies x 10
seeds x >=5 budgets x (6 allocation methods + oracle + 5 ablations),
computing true root reconstruction error and the predicted pathwise
majorant for each, on a held-out evaluation batch never used for
projector fitting (verified separately in tests/test_no_leakage.py).

Writes raw, unaggregated results to results/level1_raw.json. All
statistical analysis happens afterward, in analyze_level1.py, from this
raw file - never computed inline here, so the raw record is always
independently re-analyzable.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import ABLATION_METHODS, ALLOCATION_METHODS, small_case_oracle_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

SEEDS = list(range(10))
LEAF_DIM = 6
AMBIENT_DIM = 6
FIT_BATCH_SIZE = 300
EVAL_BATCH_SIZE = 300


def topologies():
    return {
        "chain_depth3": chain_topology(depth=3, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
        "balanced_binary_4leaf": balanced_binary_topology(4, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
    }


def budget_grid(n_nodes: int) -> list[int]:
    lo = n_nodes  # minimum: rank 1 everywhere
    hi = n_nodes * AMBIENT_DIM  # maximum: full rank everywhere
    return sorted(set(int(round(x)) for x in np.linspace(lo, hi, 6)))


def predicted_majorant(net, local_errors, amplifications) -> float:
    scores = net.pathwise_score(local_errors, amplifications)
    return float(sum(scores.values()))


def run_one_trial(topology_name: str, topology, seed: int) -> list[dict]:
    net = TensorNetwork.random(topology, seed=seed)

    # Fitting batch (used only to fit projectors) and a SEPARATE held-out
    # evaluation batch (different seed offset -> independent RNG stream)
    fit_leaf_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
    eval_leaf_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)

    fit_ambient_values = net.ambient_forward(fit_leaf_batch)
    net.fit_projectors(fit_ambient_values)

    eval_ambient_values = net.ambient_forward(eval_leaf_batch)
    root_id = net.topology.root.node_id
    root_ambient = eval_ambient_values[root_id]

    n_nodes = net.topology.internal_node_count
    records = []

    for budget in budget_grid(n_nodes):

        def evaluate_true_error(ranks: dict[str, int]) -> float:
            reduced = net.reduced_forward(eval_leaf_batch, ranks)
            diff = root_ambient - reduced[root_id]
            return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

        all_methods = dict(ALLOCATION_METHODS)
        all_methods.update({f"ablation_{k}": v for k, v in ABLATION_METHODS.items()})

        for method_name, method_fn in all_methods.items():
            ranks = method_fn(
                net, budget,
                ambient_values=fit_ambient_values,
                leaf_batch=fit_leaf_batch,
                seed=seed,
            )
            local_errors = net.local_truncation_error(fit_ambient_values, ranks)
            amplifications = net.path_amplification(fit_ambient_values, fit_leaf_batch)
            majorant = predicted_majorant(net, local_errors, amplifications)
            true_error = evaluate_true_error(ranks)
            records.append({
                "topology": topology_name,
                "seed": seed,
                "budget": budget,
                "method": method_name,
                "ranks": ranks,
                "rank_cost": sum(ranks.values()),
                "true_root_error": true_error,
                "predicted_majorant": majorant,
            })

        # oracle: only run once per (topology, seed, budget) - exhaustive,
        # evaluated on the SAME held-out eval batch's true error (the
        # oracle is allowed to use the true objective, per the mission's
        # own definition of a "small-case oracle obtained by exhaustive
        # search" - it is a ground-truth upper bound on achievable
        # performance, not a leakage-free method to be compared to the
        # others' fairness claims)
        oracle_ranks = small_case_oracle_allocation(
            net, budget, evaluate_fn=evaluate_true_error, max_combinations=1500,
        )
        oracle_true_error = evaluate_true_error(oracle_ranks)
        records.append({
            "topology": topology_name,
            "seed": seed,
            "budget": budget,
            "method": "oracle",
            "ranks": oracle_ranks,
            "rank_cost": sum(oracle_ranks.values()),
            "true_root_error": oracle_true_error,
            "predicted_majorant": None,
        })

    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records = []
    start = time.time()
    for topology_name, topology in topologies().items():
        for seed in SEEDS:
            records = run_one_trial(topology_name, topology, seed)
            all_records.extend(records)
            print(f"{topology_name} seed={seed}: {len(records)} records, "
                  f"elapsed={time.time()-start:.1f}s")

    out_path = RESULTS_DIR / "level1_raw.json"
    out_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time()-start:.1f}s")


if __name__ == "__main__":
    main()
