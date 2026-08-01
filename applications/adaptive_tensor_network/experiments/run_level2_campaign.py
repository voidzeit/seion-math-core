"""Level 2 (mission AI3): standard tensor-learning task - hierarchical
tensor regression, teacher-student design (a standard, legitimate
synthetic regression benchmark for tensor-network methods).

A fixed "teacher" network (full-rank, random cores) defines the
regression target: teacher_root(leaf_batch) for a fresh random leaf
batch each trial. A "student" network of the SAME topology is fit to
approximate it: intermediate layers are fixed random multilinear
features truncated per the rank allocation under test (the "random-
feature hierarchical regression" scheme - see
network.py::fit_root_via_least_squares), and only the student's root
core tensor is trained via closed-form ridge least squares on a training
split. Evaluated on a held-out test split (never used for fitting the
root OR for fitting projectors).
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
from tree import chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

SEEDS = list(range(5))  # mission: "at least 5 seeds for larger tasks"
LEAF_DIM = 5
AMBIENT_DIM = 5
TRAIN_SIZE = 400
VAL_SIZE = 200  # used to fit projectors (not the root, not the test error)
TEST_SIZE = 400


def budget_grid(n_nodes: int) -> list[int]:
    lo = n_nodes
    hi = n_nodes * AMBIENT_DIM
    return sorted(set(int(round(x)) for x in np.linspace(lo, hi, 5)))


def run_one_trial(topology, seed: int) -> list[dict]:
    teacher = TensorNetwork.random(topology, seed=seed * 7919 + 1)  # large prime offset, independent stream
    student_template = TensorNetwork.random(topology, seed=seed)  # student's intermediate-layer cores

    root_id = topology.root.node_id

    train_leaf = teacher.sample_leaf_batch(TRAIN_SIZE, seed=seed * 1000 + 1)
    val_leaf = teacher.sample_leaf_batch(VAL_SIZE, seed=seed * 1000 + 2)
    test_leaf = teacher.sample_leaf_batch(TEST_SIZE, seed=seed * 1000 + 3)

    train_target = teacher.ambient_forward(train_leaf)[root_id]
    test_target = teacher.ambient_forward(test_leaf)[root_id]

    # fit projectors for the student's intermediate layers on the
    # validation split (never train or test data)
    val_ambient = student_template.ambient_forward(val_leaf)
    student_template.fit_projectors(val_ambient)

    n_nodes = topology.internal_node_count
    records = []
    for budget in budget_grid(n_nodes):
        for method_name, method_fn in ALLOCATION_METHODS.items():
            # allocate ranks for all nodes (root's rank is irrelevant -
            # root is never truncated - but the method still assigns one;
            # only non-root ranks are actually used by fit/predict)
            ranks = method_fn(
                student_template, budget,
                ambient_values=val_ambient, leaf_batch=val_leaf, seed=seed,
            )
            student_template.fit_root_via_least_squares(train_leaf, ranks, train_target)
            test_pred = student_template.predict_root(test_leaf, ranks)
            test_rmse = float(np.sqrt(np.mean(np.sum((test_pred - test_target) ** 2, axis=1))))
            train_pred = student_template.predict_root(train_leaf, ranks)
            train_rmse = float(np.sqrt(np.mean(np.sum((train_pred - train_target) ** 2, axis=1))))
            records.append({
                "seed": seed,
                "budget": budget,
                "method": method_name,
                "ranks": ranks,
                "rank_cost": sum(ranks.values()),
                "train_rmse": train_rmse,
                "test_rmse": test_rmse,
            })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    topology = chain_topology(depth=3, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    all_records = []
    start = time.time()
    for seed in SEEDS:
        records = run_one_trial(topology, seed)
        all_records.extend(records)
        print(f"seed={seed}: {len(records)} records, elapsed={time.time()-start:.1f}s")

    out_path = RESULTS_DIR / "level2_raw.json"
    out_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")


if __name__ == "__main__":
    main()
