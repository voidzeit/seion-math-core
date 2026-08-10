"""Exploratory shared-DAG study at matched validation-error tolerances.

The policy selection stage sees only a fitting batch (for projectors) and a
separate validation batch.  The test batch is used only after selection.  The
reported resource quantities are the exact compressed-coordinate proxy from
``DAGTensorNetwork.resource_proxy``; they are not hardware timing claims.
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

RESULT_PATH = Path(__file__).resolve().parents[1] / "results" / "DAG_MATCHED_TOLERANCE_PROBE_2026-08-09.json"
REPORT_PATH = Path(__file__).resolve().parents[1] / "results" / "DAG_MATCHED_TOLERANCE_PROBE_2026-08-09.md"
SEEDS = list(range(12))
LEAF_DIM = 4
AMBIENT_DIM = 4
FIT_BATCH_SIZE = 100
VALIDATION_BATCH_SIZE = 120
TEST_BATCH_SIZE = 240
BUDGETS = list(range(4, 13, 2))
TOLERANCES = (0.05, 0.10, 0.15)


def normalize(batch: list[np.ndarray]) -> list[np.ndarray]:
    return [
        values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0)
        for values in batch
    ]


def uniform_allocation(net: DAGTensorNetwork, budget: int) -> dict[str, int]:
    node_ids = [
        node_id
        for node_id in net.topology.topological_order
        if node_id != net.topology.root_id
    ]
    ranks = {net.topology.root_id: 1, **{node_id: 1 for node_id in node_ids}}
    while sum(ranks.values()) < budget:
        progressed = False
        for node_id in node_ids:
            if sum(ranks.values()) >= budget:
                break
            ambient = net.topology.nodes[node_id].ambient_dim
            if ranks[node_id] < ambient:
                ranks[node_id] += 1
                progressed = True
        if not progressed:
            break
    return ranks


def error_metrics(
    net: DAGTensorNetwork,
    leaf_batch: list[np.ndarray],
    ambient: dict[str, np.ndarray],
    ranks: dict[str, int],
) -> tuple[float, float]:
    root_id = net.topology.root_id
    reduced = net.reduced_forward(leaf_batch, ranks)
    diff = ambient[root_id] - reduced[root_id]
    return (
        float(np.max(np.linalg.norm(diff, axis=1))),
        float(np.sqrt(np.mean(np.sum(diff**2, axis=1)))),
    )


def _allocation(net: DAGTensorNetwork, method: str, budget: int) -> dict[str, int]:
    if method == "uniform":
        return uniform_allocation(net, budget)
    if method == "global_certificate_optimal":
        return net.optimal_certificate_allocation(
            budget, leaf_norm_bounds=[1.0] * len(net.topology.leaf_dims)
        )
    if method == "rank_aware_certificate_optimal":
        return net.optimal_rank_aware_certificate_allocation(
            budget, leaf_norm_bounds=[1.0] * len(net.topology.leaf_dims)
        )
    raise ValueError(f"unknown method {method!r}")


def _select(
    candidates: list[dict[str, object]], tolerance: float
) -> dict[str, object] | None:
    eligible = [
        item
        for item in candidates
        if float(item["validation_root_error_sup"]) <= tolerance + 1.0e-12
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda item: (
            int(item["contraction_units_per_sample"]),
            int(item["parameter_storage_bytes"]),
            int(item["rank_budget"]),
            int(item["budget"]),
        ),
    )


def _comparison(
    selected: dict[tuple[int, str, float], dict[str, object] | None],
    method: str,
    tolerance: float,
) -> dict[str, float | int | None]:
    pairs = [
        (selected[(seed, method, tolerance)], selected[(seed, "uniform", tolerance)])
        for seed in SEEDS
    ]
    pairs = [(candidate, baseline) for candidate, baseline in pairs if candidate and baseline]
    if not pairs:
        return {"matched_seed_count": 0}
    return {
        "matched_seed_count": len(pairs),
        "candidate_better_test_sup_fraction": float(np.mean([
            float(candidate["test_root_error_sup"]) < float(baseline["test_root_error_sup"])
            for candidate, baseline in pairs
        ])),
        "mean_test_sup_reduction_vs_uniform": float(np.mean([
            float(baseline["test_root_error_sup"]) - float(candidate["test_root_error_sup"])
            for candidate, baseline in pairs
        ])),
        "mean_contraction_unit_reduction_vs_uniform": float(np.mean([
            int(baseline["contraction_units_per_sample"])
            - int(candidate["contraction_units_per_sample"])
            for candidate, baseline in pairs
        ])),
        "mean_parameter_storage_byte_reduction_vs_uniform": float(np.mean([
            int(baseline["parameter_storage_bytes"])
            - int(candidate["parameter_storage_bytes"])
            for candidate, baseline in pairs
        ])),
    }


def run_probe() -> dict[str, object]:
    methods = (
        "global_certificate_optimal",
        "rank_aware_certificate_optimal",
        "uniform",
    )
    candidates: list[dict[str, object]] = []
    selected: dict[tuple[int, str, float], dict[str, object] | None] = {}

    for seed in SEEDS:
        topology = shared_diamond_topology(leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
        net = DAGTensorNetwork.random(topology, seed=seed)
        fit = normalize(net.sample_leaf_batch(FIT_BATCH_SIZE, seed=1000 + seed))
        validation = normalize(
            net.sample_leaf_batch(VALIDATION_BATCH_SIZE, seed=2000 + seed)
        )
        test = normalize(net.sample_leaf_batch(TEST_BATCH_SIZE, seed=3000 + seed))
        net.fit_projectors(net.ambient_forward(fit))
        validation_ambient = net.ambient_forward(validation)
        test_ambient = net.ambient_forward(test)

        by_method: dict[str, list[dict[str, object]]] = {method: [] for method in methods}
        for budget in BUDGETS:
            for method in methods:
                ranks = _allocation(net, method, budget)
                validation_sup, validation_rms = error_metrics(
                    net, validation, validation_ambient, ranks
                )
                test_sup, test_rms = error_metrics(net, test, test_ambient, ranks)
                certificate = net.global_error_certificate(
                    [1.0] * len(topology.leaf_dims), ranks
                )
                resources = net.resource_proxy(ranks)
                record: dict[str, object] = {
                    "seed": seed,
                    "budget": budget,
                    "method": method,
                    "ranks": ranks,
                    "validation_root_error_sup": validation_sup,
                    "validation_root_error_rms": validation_rms,
                    "test_root_error_sup": test_sup,
                    "test_root_error_rms": test_rms,
                    "global_certificate": float(certificate["root_bound"]),
                    "certificate_holds_on_test": test_sup <= float(certificate["root_bound"]) + 1.0e-10,
                    **resources,
                }
                by_method[method].append(record)
                candidates.append(record)

        for method in methods:
            for tolerance in TOLERANCES:
                selected[(seed, method, tolerance)] = _select(
                    by_method[method], tolerance
                )

    selected_records: list[dict[str, object]] = []
    for (seed, method, tolerance), record in selected.items():
        if record is not None:
            selected_records.append({
                "seed": seed,
                "method": method,
                "tolerance": tolerance,
                "selected_budget": record["budget"],
                "selected_ranks": record["ranks"],
                "validation_root_error_sup": record["validation_root_error_sup"],
                "test_root_error_sup": record["test_root_error_sup"],
                "test_root_error_rms": record["test_root_error_rms"],
                "test_meets_tolerance": float(record["test_root_error_sup"]) <= tolerance + 1.0e-12,
                "certificate_holds_on_test": record["certificate_holds_on_test"],
                "rank_budget": record["rank_budget"],
                "contraction_units_per_sample": record["contraction_units_per_sample"],
                "parameter_storage_bytes": record["parameter_storage_bytes"],
                "peak_activation_units_per_sample": record["peak_activation_units_per_sample"],
            })

    summary: dict[str, object] = {}
    for method in methods:
        summary[method] = {}
        for tolerance in TOLERANCES:
            values = [
                selected[(seed, method, tolerance)]
                for seed in SEEDS
                if selected[(seed, method, tolerance)] is not None
            ]
            summary[method][str(tolerance)] = {
                "available_fraction": len(values) / len(SEEDS),
                "test_meets_tolerance_fraction": float(np.mean([
                    float(value["test_root_error_sup"]) <= tolerance + 1.0e-12
                    for value in values
                ])) if values else None,
                "certificate_holds_on_test_fraction": float(np.mean([
                    bool(value["certificate_holds_on_test"]) for value in values
                ])) if values else None,
                "comparison_vs_uniform": _comparison(selected, method, tolerance)
                if method != "uniform" else None,
            }

    return {
        "status": "EXPLORATORY_MATCHED_TOLERANCE_PROBE_NOT_PREREGISTERED",
        "design": {
            "topology": "shared_diamond",
            "shared_node": "u feeds left and right and is materialized once",
            "seeds": SEEDS,
            "fit_batch_size": FIT_BATCH_SIZE,
            "validation_batch_size": VALIDATION_BATCH_SIZE,
            "test_batch_size": TEST_BATCH_SIZE,
            "leaf_domain": "each normalized leaf row has norm <= 1",
            "budgets": BUDGETS,
            "tolerances": TOLERANCES,
            "methods": methods,
            "selection_rule": "minimum contraction units, then parameter bytes, among validation sup-error <= tolerance",
            "resource_semantics": "exact compressed-coordinate proxy; not wall-clock or hardware FLOPs",
        },
        "summary": summary,
        "candidate_records": candidates,
        "selected_records": selected_records,
        "limitations": [
            "One finite synthetic shared-DAG topology and random cores only.",
            "Validation/test error is sampled rather than a continuum supremum.",
            "The compressed resource quantities are analytical proxies, not hardware measurements.",
            "The study is exploratory and does not establish industrial utility or universal allocator superiority.",
        ],
    }


def render_report(output: dict[str, object]) -> str:
    summary = output["summary"]
    lines = [
        "# Shared-DAG matched-tolerance probe — 2026-08-09",
        "",
        "Status: exploratory and not preregistered. The raw output is "
        "`DAG_MATCHED_TOLERANCE_PROBE_2026-08-09.json`; the executable design is "
        "`experiments/run_dag_matched_tolerance_probe.py`.",
        "",
        "Each method selected the least compressed-contraction proxy on a "
        "validation batch satisfying the stated sup-error tolerance. The test "
        "batch was held out until after selection. Resource values are the exact "
        "coordinate-transformed proxy, not timing measurements.",
        "",
        "| Method | Tolerance | Available | Test reaches tolerance | Certificate holds | Mean Δ test sup vs uniform | Mean Δ contraction units vs uniform | Mean Δ parameter bytes vs uniform |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, by_tolerance in summary.items():
        for tolerance, values in by_tolerance.items():
            comparison = values["comparison_vs_uniform"]
            lines.append(
                f"| {method} | {tolerance} | {values['available_fraction']:.3f} | "
                f"{values['test_meets_tolerance_fraction'] if values['test_meets_tolerance_fraction'] is not None else 'n/a'} | "
                f"{values['certificate_holds_on_test_fraction'] if values['certificate_holds_on_test_fraction'] is not None else 'n/a'} | "
                f"{comparison['mean_test_sup_reduction_vs_uniform'] if comparison else 'n/a'} | "
                f"{comparison['mean_contraction_unit_reduction_vs_uniform'] if comparison else 'n/a'} | "
                f"{comparison['mean_parameter_storage_byte_reduction_vs_uniform'] if comparison else 'n/a'} |"
            )
    lines += [
        "",
        "Interpretation: matching a validation error target turns the question "
        "into a resource/error tradeoff, but this finite probe is not a policy "
        "superiority result. Positive resource reduction with a negative test "
        "error reduction is a valid context-dependent outcome and must remain "
        "reported as such.",
        "",
        "Limitations: one synthetic topology, sampled domains, random cores, "
        "and analytical resource proxies. A technology claim would require the "
        "preregistered multi-topology train/validation/test study described in "
        "`APPLIED_VALIDATION_STATUS_2026-08-09.md`.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    output = run_probe()
    RESULT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(output), encoding="utf-8")
    print(f"Wrote {len(output['candidate_records'])} candidate records")
    print(f"Wrote {len(output['selected_records'])} selected records")
    print(json.dumps(output["summary"], sort_keys=True))
