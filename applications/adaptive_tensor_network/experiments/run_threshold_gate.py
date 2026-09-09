"""Decisive cutoff gate for measured downstream allocation at m=8 and m=10.

The experiment preserves the frozen projector bases and terminal-state oracle
used by M35b/M38.  It adds two local discarded-energy baselines:

* threshold_static: one common cutoff, selected once for the exact final rank;
* threshold_adaptive: re-estimate fixed-basis tail energies on the propagated
  calibration state and reselect a common cutoff every round.

All policies start from the same rank vector and add b=3 ranks for T=6 rounds.
Forward evaluations, a deterministic compressed-coordinate memory proxy, and
wall time are recorded separately.  This is synthetic evidence, not a hardware
benchmark or a theorem.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


APP = Path(__file__).resolve().parents[1]
SRC = APP / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from allocation import (  # noqa: E402
    threshold_adaptive_allocation,
    threshold_static_allocation,
)
from run_horizon_aware_allocation import (  # noqa: E402
    BUNDLE,
    DIM,
    ROUNDS,
    Instance,
    run_policy,
)
from run_interaction_dimension import EVAL_BATCH, FIT_BATCH  # noqa: E402


RESULTS = APP / "results"
POLICIES = (
    "uniform",
    "threshold_static",
    "threshold_adaptive",
    "measured_first_order",
    "full_pairwise",
    "rollout_first_order_h6",
)


def git_state() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            cwd=str(Path(__file__).resolve().parents[3]),
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unavailable"


def ranks_from_profile(instance: Instance, profile: list[int]) -> dict[str, int]:
    ranks = dict(instance.base)
    for node_id, increment in zip(instance.allocatable, profile, strict=True):
        ranks[node_id] += int(increment)
    return ranks


def tree_resource_proxy(instance: Instance, ranks: dict[str, int]) -> dict[str, int]:
    """Analytical storage/activation proxy for compressed tree execution."""

    topology = instance.topology

    def output_dim(node) -> int:
        return node.ambient_dim if node.node_id == instance.root_id else int(ranks[node.node_id])

    core_storage = 0
    basis_storage = 0
    contraction_units = 0
    node_units = {}
    for node in topology.nodes_postorder:
        input_dims = [
            topology.leaf_dims[child]
            if isinstance(child, int)
            else output_dim(child)
            for child in node.children
        ]
        units = output_dim(node) * int(np.prod(input_dims, dtype=int))
        node_units[node.node_id] = units
        core_storage += units
        contraction_units += units
        if node.node_id != instance.root_id:
            basis_storage += node.ambient_dim * output_dim(node)

    remaining: dict[tuple[str, int | str], int] = {
        ("leaf", index): 0 for index in range(len(topology.leaf_dims))
    }
    remaining.update({("node", node.node_id): 0 for node in topology.nodes_postorder})
    for node in topology.nodes_postorder:
        for child in node.children:
            key = ("leaf", child) if isinstance(child, int) else ("node", child.node_id)
            remaining[key] += 1

    live: dict[tuple[str, int | str], int] = {
        ("leaf", index): dim
        for index, dim in enumerate(topology.leaf_dims)
        if remaining[("leaf", index)] > 0
    }
    peak = sum(live.values())
    for node in topology.nodes_postorder:
        live[("node", node.node_id)] = output_dim(node)
        peak = max(peak, sum(live.values()))
        for child in node.children:
            key = ("leaf", child) if isinstance(child, int) else ("node", child.node_id)
            remaining[key] -= 1
            if remaining[key] == 0:
                live.pop(key, None)

    dtype_bytes = 8
    parameter_bytes = (core_storage + basis_storage) * dtype_bytes
    activation_bytes = peak * EVAL_BATCH * dtype_bytes
    return {
        "rank_budget": int(sum(ranks.values())),
        "allocatable_rank_budget": int(sum(ranks[n] for n in instance.allocatable)),
        "core_storage_units": int(core_storage),
        "basis_storage_units": int(basis_storage),
        "parameter_storage_bytes": int(parameter_bytes),
        "contraction_units_per_sample": int(contraction_units),
        "peak_activation_units_per_sample": int(peak),
        "peak_activation_bytes": int(activation_bytes),
        "memory_proxy_bytes": int(parameter_bytes + activation_bytes),
        "node_contraction_units": {key: int(value) for key, value in node_units.items()},
    }


def _first_order_action(instance: Instance, ranks: dict[str, int]) -> tuple[str, ...] | None:
    eligible = [node for node in instance.allocatable if ranks[node] < DIM]
    if len(eligible) < BUNDLE:
        return None
    e_base = instance.error(ranks)
    utility = {
        node: e_base - instance.error({**ranks, node: ranks[node] + 1})
        for node in eligible
    }
    return tuple(sorted(eligible, key=lambda node: -utility[node])[:BUNDLE])


def _continue_first_order(instance: Instance, ranks: dict[str, int], steps: int) -> dict[str, int]:
    current = dict(ranks)
    for _ in range(steps):
        action = _first_order_action(instance, current)
        if action is None:
            break
        for node in action:
            current[node] += 1
    return current


def run_rollout_h6(instance: Instance) -> dict:
    ranks = dict(instance.base)
    instance.evaluations = 0
    start = time.perf_counter()
    for step in range(ROUNDS):
        eligible = [node for node in instance.allocatable if ranks[node] < DIM]
        if len(eligible) < BUNDLE:
            break
        depth = ROUNDS - step
        best_combo = None
        best_value = float("inf")
        for combo in itertools.combinations(range(len(eligible)), BUNDLE):
            candidate = dict(ranks)
            for index in combo:
                candidate[eligible[index]] += 1
            final = _continue_first_order(instance, candidate, depth - 1)
            value = instance.error(final)
            if value < best_value:
                best_combo, best_value = combo, value
        if best_combo is None:
            raise RuntimeError("rollout found no feasible action")
        for index in best_combo:
            ranks[eligible[index]] += 1
    terminal_error = instance.error(ranks)
    return {
        "policy": "rollout_first_order_h6",
        "trajectory": [],
        "terminal_error": terminal_error,
        "terminal_profile": [ranks[node] - instance.base[node] for node in instance.allocatable],
        "objective_forward_evaluations": int(instance.evaluations),
        "calibration_forward_evaluations": 0,
        "forward_evaluations": int(instance.evaluations),
        "wall_seconds": time.perf_counter() - start,
        "thresholds": [],
    }


def run_threshold(instance: Instance, seed: int, *, adaptive: bool) -> dict:
    ranks = dict(instance.base)
    instance.evaluations = 0
    thresholds = []
    trajectory = []
    calibration_evaluations = 0
    fit_batch = instance.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    start = time.perf_counter()

    if not adaptive:
        final_allocatable_budget = (
            sum(ranks[node] for node in instance.allocatable) + BUNDLE * ROUNDS
        )
        selected, tau = threshold_static_allocation(
            instance.net,
            final_allocatable_budget,
            node_ids=instance.allocatable,
            minimum_ranks={node: ranks[node] for node in instance.allocatable},
        )
        ranks.update(selected)
        thresholds.append(tau)
        trajectory.append(instance.error(ranks))
    else:
        for _ in range(ROUNDS):
            current_values = instance.net.reduced_forward(fit_batch, ranks)
            calibration_evaluations += 1
            next_budget = sum(ranks[node] for node in instance.allocatable) + BUNDLE
            selected, tau = threshold_adaptive_allocation(
                instance.net,
                next_budget,
                node_ids=instance.allocatable,
                minimum_ranks={node: ranks[node] for node in instance.allocatable},
                current_values=current_values,
            )
            ranks.update(selected)
            thresholds.append(tau)
            trajectory.append(instance.error(ranks))

    return {
        "policy": "threshold_adaptive" if adaptive else "threshold_static",
        "trajectory": trajectory,
        "terminal_error": trajectory[-1],
        "terminal_profile": [ranks[node] - instance.base[node] for node in instance.allocatable],
        "objective_forward_evaluations": int(instance.evaluations),
        "calibration_forward_evaluations": int(calibration_evaluations),
        "forward_evaluations": int(instance.evaluations + calibration_evaluations),
        "wall_seconds": time.perf_counter() - start,
        "thresholds": thresholds,
    }


def run_named_policy(instance: Instance, policy: str, seed: int) -> dict:
    if policy == "threshold_static":
        return run_threshold(instance, seed, adaptive=False)
    if policy == "threshold_adaptive":
        return run_threshold(instance, seed, adaptive=True)
    if policy == "rollout_first_order_h6":
        return run_rollout_h6(instance)
    result = run_policy(instance, policy, seed)
    result["objective_forward_evaluations"] = int(result.pop("evaluations"))
    result["calibration_forward_evaluations"] = 0
    result["forward_evaluations"] = result["objective_forward_evaluations"]
    result["thresholds"] = []
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, nargs="+", default=[8, 10])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--policies", nargs="+", choices=POLICIES, default=list(POLICIES))
    parser.add_argument("--out", default="threshold_gate_m8_m10_raw.json")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / args.out
    payload = {
        "status": "EXPERIMENTAL_FIXED_BASIS_EXACT_ORACLE_GATE",
        "config": {
            "m_values": args.m,
            "seeds": args.seeds,
            "policies": args.policies,
            "dim": DIM,
            "bundle": BUNDLE,
            "rounds": ROUNDS,
            "fit_batch": FIT_BATCH,
            "eval_batch": EVAL_BATCH,
            "rank_additions": BUNDLE * ROUNDS,
            "threshold_rule": "min r with sum(sigma[r:]^2) <= tau; common tau; exact budget",
            "adaptive_semantics": "recompute fixed-basis tail energy on propagated calibration values; bases frozen",
            "forward_evaluation_semantics": "objective plus explicit adaptive calibration forwards; common instance setup excluded",
            "memory_proxy_semantics": "compressed-coordinate parameters plus peak batched activations; analytical, not measured RSS/VRAM",
            "command": " ".join(sys.argv),
            "git": git_state(),
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "runs": [],
        "limitations": [
            "five exact-oracle seeds per size in a synthetic heterogeneous D=16 chain",
            "projector bases are frozen so the exact terminal oracle remains valid",
            "memory is an analytical compressed-coordinate proxy, not measured RSS or VRAM",
            "wall time is single-run CPU timing and is not a robust hardware benchmark",
        ],
    }

    campaign_start = time.perf_counter()
    for m in args.m:
        for seed in args.seeds:
            for policy in args.policies:
                instance = Instance(m, seed)
                base_error = instance.error(instance.base)
                result = run_named_policy(instance, policy, seed)
                ranks = ranks_from_profile(instance, result["terminal_profile"])
                result.update(tree_resource_proxy(instance, ranks))
                result.update({"m": m, "seed": seed, "base_error": base_error})
                payload["runs"].append(result)
                out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                print(
                    f"m={m} seed={seed} {policy}: E={result['terminal_error']:.6f} "
                    f"evals={result['forward_evaluations']} "
                    f"memory={result['memory_proxy_bytes']} "
                    f"elapsed={time.perf_counter() - campaign_start:.1f}s",
                    flush=True,
                )

    print(f"wrote {len(payload['runs'])} runs to {out_path}")


if __name__ == "__main__":
    main()
