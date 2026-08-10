"""Exploratory held-out probe for the finite-batch certificate allocator."""

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
    small_case_validated_certificate_allocation,
)
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "validated_certificate_probe_2026-08-09.json"
SEEDS = list(range(10))
FIT_BATCH_SIZE = 80
EVAL_BATCH_SIZE = 300
LEAF_DIM = 4
AMBIENT_DIM = 4


def topologies():
    return {
        "chain_depth3": chain_topology(depth=3, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
        "balanced_binary_4leaf": balanced_binary_topology(4, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM),
    }


def budgets(n_nodes: int) -> list[int]:
    return sorted(set(int(round(x)) for x in np.linspace(n_nodes, n_nodes * AMBIENT_DIM, 6)))


def run_probe() -> dict:
    records = []
    method_names = [
        "pathwise_global",
        "pathwise_majorant_optimal",
        "validated_certificate_small_case",
    ]
    for topology_name, topology in topologies().items():
        for seed in SEEDS:
            net = TensorNetwork.random(topology, seed=seed)
            fit_leaves = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 11)
            eval_leaves = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 12)
            fit_ambient = net.ambient_forward(fit_leaves)
            net.fit_projectors(fit_ambient)
            eval_ambient = net.ambient_forward(eval_leaves)
            root_id = topology.root.node_id
            root_ambient = eval_ambient[root_id]
            methods = {
                "pathwise_global": lambda budget: pathwise_global_allocation(
                    net, budget, ambient_values=fit_ambient, leaf_batch=fit_leaves, seed=seed
                ),
                "pathwise_majorant_optimal": lambda budget: pathwise_majorant_optimal_allocation(
                    net, budget, ambient_values=fit_ambient, leaf_batch=fit_leaves, seed=seed
                ),
                "validated_certificate_small_case": lambda budget: small_case_validated_certificate_allocation(
                    net, budget, leaf_batch=fit_leaves, max_combinations=500, seed=seed
                ),
            }
            for budget in budgets(topology.internal_node_count):
                for method_name, allocator in methods.items():
                    ranks = allocator(budget)
                    reduced = net.reduced_forward(eval_leaves, ranks)
                    diff = root_ambient - reduced[root_id]
                    certificate = net.validated_error_certificate(fit_leaves, ranks)
                    records.append({
                        "topology": topology_name,
                        "seed": seed,
                        "budget": budget,
                        "method": method_name,
                        "ranks": ranks,
                        "rank_cost": sum(ranks.values()),
                        "true_root_error_rms": float(np.sqrt(np.mean(np.sum(diff**2, axis=1)))),
                        "held_out_root_error_sup": float(np.max(np.linalg.norm(diff, axis=1))),
                        "fit_validated_root_bound": certificate["root_bound"],
                        "fit_validated_bound_holds": certificate["bound_holds"],
                        "fit_empirical_majorant": pathwise_majorant_value(
                            net, ranks, ambient_values=fit_ambient, leaf_batch=fit_leaves
                        ),
                    })

    by_key = {}
    for record in records:
        by_key.setdefault((record["topology"], record["seed"], record["budget"]), {})[record["method"]] = record
    summary = {}
    for topology_name in topologies():
        pairs = [value for key, value in by_key.items() if key[0] == topology_name]
        candidate = [pair["validated_certificate_small_case"] for pair in pairs]
        baseline = [pair["pathwise_global"] for pair in pairs]
        summary[topology_name] = {
            "n_pairs": len(pairs),
            "certificate_allocator_true_rms_reduction": float(np.mean([
                b["true_root_error_rms"] - c["true_root_error_rms"] for b, c in zip(baseline, candidate)
            ])),
            "certificate_allocator_better_fraction": float(np.mean([
                b["true_root_error_rms"] > c["true_root_error_rms"] for b, c in zip(baseline, candidate)
            ])),
            "validated_bound_reduction": float(np.mean([
                b["fit_validated_root_bound"] - c["fit_validated_root_bound"] for b, c in zip(baseline, candidate)
            ])),
            "validated_bound_no_worse_fraction": float(np.mean([
                b["fit_validated_root_bound"] >= c["fit_validated_root_bound"] - 1e-12 for b, c in zip(baseline, candidate)
            ])),
            "all_candidate_fit_certificates_hold": all(
                c["fit_validated_bound_holds"] for c in candidate
            ),
        }
    return {
        "status": "EXPLORATORY_PROBE_NOT_PREREGISTERED",
        "design": {
            "topologies": list(topologies()),
            "seeds": SEEDS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "methods": method_names,
            "certificate_allocator_uses_fit_batch_only": True,
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "The validated bound uses Frobenius enclosures and is conservative.",
            "The certificate allocator is combinatorial and only tested on small networks.",
            "No true-error superiority or technology claim is established.",
        ],
    }


if __name__ == "__main__":
    output = run_probe()
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['records'])} records to {RESULT_PATH}")
    for topology_name, summary in output["summary"].items():
        print(topology_name, json.dumps(summary, sort_keys=True))
