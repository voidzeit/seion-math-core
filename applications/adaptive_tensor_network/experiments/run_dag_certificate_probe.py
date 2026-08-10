"""Exploratory shared-DAG certificate/allocation probe.

The candidate is selected from a domain certificate fit without held-out
values.  The probe only checks soundness and compares reconstruction error to a
uniform budget baseline; it is not preregistered evidence of universal
allocator superiority.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from dag import shared_diamond_topology  # noqa: E402
from dag_network import DAGTensorNetwork  # noqa: E402

RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "dag_certificate_probe_2026-08-09.json"
SEEDS = list(range(20))
LEAF_DIM = 4
AMBIENT_DIM = 4
FIT_BATCH_SIZE = 100
EVAL_BATCH_SIZE = 300


def normalize(batch: list[np.ndarray]) -> list[np.ndarray]:
    return [values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0) for values in batch]


def uniform_allocation(net: DAGTensorNetwork, budget: int) -> dict[str, int]:
    node_ids = [node_id for node_id in net.topology.topological_order if node_id != net.topology.root_id]
    ranks = {net.topology.root_id: 1, **{node_id: 1 for node_id in node_ids}}
    while sum(ranks.values()) < budget:
        progressed = False
        for node_id in node_ids:
            if sum(ranks.values()) >= budget:
                break
            if ranks[node_id] < AMBIENT_DIM:
                ranks[node_id] += 1
                progressed = True
        if not progressed:
            break
    return ranks


def budgets() -> list[int]:
    return list(range(4, 4 * 4 + 1, 2))


def run_probe() -> dict:
    records = []
    for seed in SEEDS:
        topology = shared_diamond_topology(leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
        net = DAGTensorNetwork.random(topology, seed=seed)
        fit = normalize(net.sample_leaf_batch(FIT_BATCH_SIZE, seed=1000 + seed))
        evaluation = normalize(net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=2000 + seed))
        net.fit_projectors(net.ambient_forward(fit))
        for budget in budgets():
            methods = {
                "global_certificate_optimal": net.optimal_certificate_allocation(
                    budget, leaf_norm_bounds=[1.0] * len(topology.leaf_dims)
                ),
                "rank_aware_certificate_optimal": net.optimal_rank_aware_certificate_allocation(
                    budget, leaf_norm_bounds=[1.0] * len(topology.leaf_dims)
                ),
                "uniform": uniform_allocation(net, budget),
            }
            eval_ambient = net.ambient_forward(evaluation)
            for method, ranks in methods.items():
                certificate = net.global_error_certificate([1.0] * len(topology.leaf_dims), ranks)
                reduced = net.reduced_forward(evaluation, ranks)
                diff = eval_ambient[topology.root_id] - reduced[topology.root_id]
                root_error_sup = float(np.max(np.linalg.norm(diff, axis=1)))
                root_error_rms = float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))
                records.append({
                    "seed": seed,
                    "budget": budget,
                    "method": method,
                    "ranks": ranks,
                    "rank_cost": sum(ranks.values()),
                    "held_out_root_error_sup": root_error_sup,
                    "held_out_root_error_rms": root_error_rms,
                    "global_certificate": certificate["root_bound"],
                    "certificate_holds": root_error_sup <= certificate["root_bound"] + 1.0e-10,
                })

    grouped: dict[tuple[int, int], dict[str, dict]] = {}
    for record in records:
        grouped.setdefault((record["seed"], record["budget"]), {})[record["method"]] = record
    pairs = list(grouped.values())
    baseline = [pair["uniform"] for pair in pairs]

    def compare(method: str) -> dict[str, float]:
        candidate = [pair[method] for pair in pairs]
        return {
            "certificate_holds_fraction": float(np.mean([item["certificate_holds"] for item in candidate])),
            "better_sup_fraction_vs_uniform": float(np.mean([
                item["held_out_root_error_sup"] < base["held_out_root_error_sup"]
                for item, base in zip(candidate, baseline)
            ])),
            "mean_sup_reduction_vs_uniform": float(np.mean([
                base["held_out_root_error_sup"] - item["held_out_root_error_sup"]
                for item, base in zip(candidate, baseline)
            ])),
            "better_rms_fraction_vs_uniform": float(np.mean([
                item["held_out_root_error_rms"] < base["held_out_root_error_rms"]
                for item, base in zip(candidate, baseline)
            ])),
        }

    summary = {
        "n_pairs": len(pairs),
        "global_certificate_optimal": compare("global_certificate_optimal"),
        "rank_aware_certificate_optimal": compare("rank_aware_certificate_optimal"),
    }
    return {
        "status": "EXPLORATORY_PROBE_NOT_PREREGISTERED",
        "design": {
            "topology": "shared_diamond",
            "shared_node": "u feeds left and right",
            "seeds": SEEDS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "leaf_domain": "each normalized leaf row has norm <= 1",
            "budgets": budgets(),
            "methods": [
                "global_certificate_optimal",
                "rank_aware_certificate_optimal",
                "uniform",
            ],
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "One finite topology and synthetic random cores only.",
            "Frobenius operator enclosures are conservative.",
            "The probe does not establish universal allocator superiority or industrial utility.",
            "The candidate is selected from a global domain certificate, not held-out errors.",
        ],
    }


if __name__ == "__main__":
    output = run_probe()
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['records'])} records to {RESULT_PATH}")
    print(json.dumps(output["summary"], sort_keys=True))
