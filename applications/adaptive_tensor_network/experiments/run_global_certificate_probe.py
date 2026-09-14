"""Exploratory domain-certified allocation probe on normalized leaf inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import global_certificate_optimal_allocation, pathwise_global_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "global_certificate_probe_2026-08-09.json"
SEEDS = list(range(10))
FIT_BATCH_SIZE = 80
EVAL_BATCH_SIZE = 300
LEAF_DIM = 4
AMBIENT_DIM = 4


def normalize_batch(batch):
    return [values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0) for values in batch]


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
            fit_leaves = normalize_batch(net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 21))
            eval_leaves = normalize_batch(net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 22))
            fit_ambient = net.ambient_forward(fit_leaves)
            net.fit_projectors(fit_ambient)
            eval_ambient = net.ambient_forward(eval_leaves)
            root_id = topology.root.node_id
            root_ambient = eval_ambient[root_id]
            for budget in budgets(topology.internal_node_count):
                methods = {
                    "pathwise_global": pathwise_global_allocation(
                        net, budget, ambient_values=fit_ambient, leaf_batch=fit_leaves, seed=seed
                    ),
                    "global_certificate_optimal": global_certificate_optimal_allocation(
                        net, budget, leaf_norm_bounds=[1.0] * len(fit_leaves), seed=seed
                    ),
                }
                for method_name, ranks in methods.items():
                    reduced = net.reduced_forward(eval_leaves, ranks)
                    diff = root_ambient - reduced[root_id]
                    certificate = net.global_error_certificate([1.0] * len(fit_leaves), ranks)
                    held_out_sup = float(np.max(np.linalg.norm(diff, axis=1)))
                    records.append({
                        "topology": topology_name,
                        "seed": seed,
                        "budget": budget,
                        "method": method_name,
                        "ranks": ranks,
                        "rank_cost": sum(ranks.values()),
                        "held_out_root_error_rms": float(np.sqrt(np.mean(np.sum(diff**2, axis=1)))),
                        "held_out_root_error_sup": held_out_sup,
                        "domain_leaf_norm_bound": 1.0,
                        "global_certificate": certificate["root_bound"],
                        "global_certificate_holds_on_held_out": held_out_sup <= certificate["root_bound"] + 1e-10,
                    })
    by_key = {}
    for record in records:
        by_key.setdefault((record["topology"], record["seed"], record["budget"]), {})[record["method"]] = record
    summary = {}
    for topology_name in topologies():
        pairs = [value for key, value in by_key.items() if key[0] == topology_name]
        baseline = [pair["pathwise_global"] for pair in pairs]
        candidate = [pair["global_certificate_optimal"] for pair in pairs]
        summary[topology_name] = {
            "n_pairs": len(pairs),
            "candidate_mean_held_out_rms_reduction": float(np.mean([
                b["held_out_root_error_rms"] - c["held_out_root_error_rms"] for b, c in zip(baseline, candidate)
            ])),
            "candidate_held_out_better_fraction": float(np.mean([
                b["held_out_root_error_rms"] > c["held_out_root_error_rms"] for b, c in zip(baseline, candidate)
            ])),
            "candidate_certificate_holds_fraction": float(np.mean([
                c["global_certificate_holds_on_held_out"] for c in candidate
            ])),
        }
    return {
        "status": "EXPLORATORY_PROBE_NOT_PREREGISTERED",
        "design": {
            "topologies": list(topologies()),
            "seeds": SEEDS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "leaf_domain": "each normalized leaf row has norm <= 1",
            "methods": ["pathwise_global", "global_certificate_optimal"],
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "Frobenius operator enclosures are conservative.",
            "The probe does not establish universal allocator superiority.",
            "The comparison is not preregistered and does not alter Level 1.",
        ],
    }


if __name__ == "__main__":
    output = run_probe()
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['records'])} records to {RESULT_PATH}")
    for topology_name, summary in output["summary"].items():
        print(topology_name, json.dumps(summary, sort_keys=True))
