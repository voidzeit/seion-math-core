"""Exploratory comparison for the exact fitted-majorant optimizer.

This is intentionally separate from the preregistered Level 1 campaign. It
reuses its topology, seed, fitting/evaluation split, and budget grid, but does
not rewrite historical raw data or make a superiority claim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import (  # noqa: E402
    pathwise_global_allocation,
    pathwise_majorant_optimal_allocation,
    pathwise_majorant_value,
)
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "majorant_optimizer_probe_2026-08-09.json"
SEEDS = list(range(10))
FIT_BATCH_SIZE = 300
EVAL_BATCH_SIZE = 300
LEAF_DIM = 6
AMBIENT_DIM = 6


def topologies():
    return {
        "chain_depth3": chain_topology(depth=3, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
        "balanced_binary_4leaf": balanced_binary_topology(4, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
    }


def budgets(n_nodes: int) -> list[int]:
    return sorted(set(int(round(x)) for x in np.linspace(n_nodes, n_nodes * AMBIENT_DIM, 6)))


def run_probe() -> dict:
    records = []
    for topology_name, topology in topologies().items():
        for seed in SEEDS:
            net = TensorNetwork.random(topology, seed=seed)
            fit_leaf_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
            eval_leaf_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)
            fit_ambient_values = net.ambient_forward(fit_leaf_batch)
            net.fit_projectors(fit_ambient_values)
            eval_ambient_values = net.ambient_forward(eval_leaf_batch)
            root_id = topology.root.node_id
            root_ambient = eval_ambient_values[root_id]

            for budget in budgets(topology.internal_node_count):
                methods = {
                    "pathwise_global": pathwise_global_allocation,
                    "pathwise_majorant_optimal": pathwise_majorant_optimal_allocation,
                }
                for method_name, method in methods.items():
                    ranks = method(
                        net,
                        budget,
                        ambient_values=fit_ambient_values,
                        leaf_batch=fit_leaf_batch,
                        seed=seed,
                    )
                    reduced = net.reduced_forward(eval_leaf_batch, ranks)
                    diff = root_ambient - reduced[root_id]
                    true_error = float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))
                    fitted_majorant = pathwise_majorant_value(
                        net,
                        ranks,
                        ambient_values=fit_ambient_values,
                        leaf_batch=fit_leaf_batch,
                    )
                    records.append({
                        "topology": topology_name,
                        "seed": seed,
                        "budget": budget,
                        "method": method_name,
                        "ranks": ranks,
                        "rank_cost": sum(ranks.values()),
                        "true_root_error": true_error,
                        "fitted_root_excluded_majorant": fitted_majorant,
                    })

    paired = {}
    by_key = {}
    for record in records:
        by_key.setdefault((record["topology"], record["seed"], record["budget"]), {})[record["method"]] = record
    for key, methods in by_key.items():
        if len(methods) != 2:
            continue
        baseline = methods["pathwise_global"]
        candidate = methods["pathwise_majorant_optimal"]
        paired.setdefault(key[0], []).append({
            "seed": key[1],
            "budget": key[2],
            "true_error_reduction_candidate_minus_baseline": baseline["true_root_error"] - candidate["true_root_error"],
            "majorant_reduction_candidate_minus_baseline": baseline["fitted_root_excluded_majorant"] - candidate["fitted_root_excluded_majorant"],
        })
    summary = {}
    for topology_name, values in paired.items():
        summary[topology_name] = {
            "n_pairs": len(values),
            "mean_true_error_reduction": float(np.mean([x["true_error_reduction_candidate_minus_baseline"] for x in values])),
            "candidate_true_error_better_fraction": float(np.mean([x["true_error_reduction_candidate_minus_baseline"] > 0 for x in values])),
            "mean_majorant_reduction": float(np.mean([x["majorant_reduction_candidate_minus_baseline"] for x in values])),
            "majorant_exactly_no_worse_fraction": float(np.mean([x["majorant_reduction_candidate_minus_baseline"] >= -1e-12 for x in values])),
        }
    return {
        "status": "EXPLORATORY_PROBE_NOT_PREREGISTERED",
        "design": {
            "topologies": list(topologies()),
            "seeds": SEEDS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "methods": ["pathwise_global", "pathwise_majorant_optimal"],
            "comparison": "same fitted data and held-out evaluation data within each paired trial",
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "The path factors are empirical directional-derivative estimates, not validated global operator norms.",
            "The probe does not establish superiority for true root error or a universal allocator theorem.",
            "Historical preregistered Level 1 records are unchanged.",
        ],
    }


if __name__ == "__main__":
    output = run_probe()
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['records'])} records to {RESULT_PATH}")
    for topology_name, summary in output["summary"].items():
        print(topology_name, json.dumps(summary, sort_keys=True))
