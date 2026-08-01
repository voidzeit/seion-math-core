"""Level 3 (mission AI3): external scientific task - reduced surrogate
for the 1D viscous Burgers equation.

Real finite-difference PDE solves (burgers_solver.py) generate ground-
truth (parameters -> final-state-field) pairs. A small hierarchical
tensor network (one intermediate node with an allocatable rank, root
predicting the 32-point solution field) is fit via the same random-
feature + closed-form-least-squares scheme as Level 2, and evaluated on
a held-out test split of PDE parameters never used for fitting.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import ALLOCATION_METHODS  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import NodeSpec, TreeTopology  # noqa: E402

from burgers_solver import generate_dataset  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

SEEDS = list(range(5))
GRID_SIZE = 32
TRAIN_SIZE = 300
VAL_SIZE = 150
TEST_SIZE = 300
INTERMEDIATE_AMBIENT_DIM = 6


def build_topology() -> TreeTopology:
    # leaf0 = [nu, fc0, fc1] (dim 3), leaf1 = [fc2, fc3] (dim 2): node0's
    # ambient output is a linear combination of the outer-product basis
    # of leaf0 and leaf1, hence genuinely spans up to dim(leaf0)*dim(leaf1)
    # = 6 dimensions - matching INTERMEDIATE_AMBIENT_DIM exactly, so rank
    # allocation from 1 to 6 is a real, non-degenerate question (checked
    # directly before trusting this design - see the diagnostic that
    # caught the PREVIOUS 1-dim/1-dim split producing a mathematically
    # rank-1 node regardless of declared ambient_dim).
    # leaf2 = [fc4] (dim 1) feeds directly into the root alongside node0.
    node0 = NodeSpec(node_id="n0", children=(0, 1), ambient_dim=INTERMEDIATE_AMBIENT_DIM)
    root = NodeSpec(node_id="root", children=(node0, 2), ambient_dim=GRID_SIZE)
    return TreeTopology(root=root, leaf_dims=(3, 2, 1))


def leaves_from_params(nu: np.ndarray, fourier_coeffs: np.ndarray) -> list[np.ndarray]:
    leaf0 = np.concatenate([nu.reshape(-1, 1), fourier_coeffs[:, 0:2]], axis=1)
    leaf1 = fourier_coeffs[:, 2:4]
    leaf2 = fourier_coeffs[:, 4:5]
    return [leaf0, leaf1, leaf2]


def budget_grid() -> list[int]:
    # only n0 has an allocatable rank in this topology (root is not
    # truncated); sweep its rank from 1 to INTERMEDIATE_AMBIENT_DIM.
    # "budget" here = the intermediate node's rank directly + a constant
    # 1 for consistency with the allocation API's per-node minimum.
    return list(range(2, INTERMEDIATE_AMBIENT_DIM + 2))


def run_one_trial(seed: int) -> list[dict]:
    topology = build_topology()
    student = TensorNetwork.random(topology, seed=seed)

    nu_train, fc_train, states_train = generate_dataset(TRAIN_SIZE, seed=seed * 1000 + 1, grid_size=GRID_SIZE, n_fourier_modes=5)
    nu_val, fc_val, states_val = generate_dataset(VAL_SIZE, seed=seed * 1000 + 2, grid_size=GRID_SIZE, n_fourier_modes=5)
    nu_test, fc_test, states_test = generate_dataset(TEST_SIZE, seed=seed * 1000 + 3, grid_size=GRID_SIZE, n_fourier_modes=5)

    train_leaf = leaves_from_params(nu_train, fc_train)
    val_leaf = leaves_from_params(nu_val, fc_val)
    test_leaf = leaves_from_params(nu_test, fc_test)

    val_ambient = student.ambient_forward(val_leaf)
    student.fit_projectors(val_ambient)

    records = []
    for budget in budget_grid():
        for method_name, method_fn in ALLOCATION_METHODS.items():
            ranks = method_fn(
                student, budget + 1,  # +1 for the root's own (unused) minimum-rank slot in the allocation API
                ambient_values=val_ambient, leaf_batch=val_leaf, seed=seed,
            )
            student.fit_root_via_least_squares(train_leaf, ranks, states_train)
            test_pred = student.predict_root(test_leaf, ranks)
            test_rmse = float(np.sqrt(np.mean(np.sum((test_pred - states_test) ** 2, axis=1))))
            # baseline: predict the training-set mean field (sanity floor)
            mean_baseline_rmse = float(np.sqrt(np.mean(np.sum((states_test - states_train.mean(axis=0)) ** 2, axis=1))))
            records.append({
                "seed": seed,
                "budget": budget,
                "method": method_name,
                "ranks": ranks,
                "n0_rank": ranks.get("n0"),
                "test_rmse": test_rmse,
                "mean_baseline_rmse": mean_baseline_rmse,
            })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records = []
    start = time.time()
    for seed in SEEDS:
        records = run_one_trial(seed)
        all_records.extend(records)
        print(f"seed={seed}: {len(records)} records, elapsed={time.time()-start:.1f}s")

    out_path = RESULTS_DIR / "level3_raw.json"
    out_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")


if __name__ == "__main__":
    main()
