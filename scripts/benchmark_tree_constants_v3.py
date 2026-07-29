"""Registered reference/NumPy/CUDA scaling benchmark for research-v3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import time
import tracemalloc

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from seion_core.research_v3.exact_evaluation import (  # noqa: E402
    evaluate_ambient_numpy,
    evaluate_ambient_reference,
)
from seion_core.research_v3.extremizers import rotation_tensor  # noqa: E402
from seion_core.research_v3.local_constants import TypedLaw  # noqa: E402
from seion_core.research_v3.projected_evaluation import evaluate_projected_torch  # noqa: E402
from seion_core.research_v3.run_schema import (  # noqa: E402
    V3RunConfig,
    canonical_hash,
    write_run_artifacts,
)
from seion_core.research_v3.tree_enumeration import (  # noqa: E402
    label_shape,
    topology_family_shape,
)
from seion_core.research_v3.typed_tree import Tree, iter_internal  # noqa: E402
from seion_core.research_v3.types import TypeSystem, TypedSpace  # noqa: E402


OUT = ROOT / "artifacts" / "research_v3"
RUNS = ROOT / "artifacts" / "runs_v3"


def problem(internal_nodes: int):
    tree = label_shape(topology_family_shape(internal_nodes, 2, "left_comb"))
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    tensor = rotation_tensor(2, 0.0)
    laws = {
        node.law_id: TypedLaw(node.law_id, ("tau", "tau"), "tau", tensor)
        for node in iter_internal(tree)
    }
    leaf_count = internal_nodes + 1
    leaves = {index: np.array([1.0]) for index in range(leaf_count)}
    return tree, types, laws, leaves, tensor


def _invoke(backend: str, tree: Tree, laws, types, leaves):
    if backend == "reference_python":
        return evaluate_ambient_reference(tree, laws, types, leaves).root
    if backend == "numpy_cpu":
        return evaluate_ambient_numpy(tree, laws, types, leaves).root
    if backend == "torch_cuda":
        value = evaluate_projected_torch(tree, laws, types, leaves, device="cuda")
        return value
    raise ValueError(backend)


def _synchronize(backend: str) -> None:
    if backend == "torch_cuda":
        import torch

        torch.cuda.synchronize()


def benchmark() -> pd.DataFrame:
    try:
        import torch

        cuda = bool(torch.cuda.is_available())
    except Exception:
        cuda = False
    backends = ["reference_python", "numpy_cpu"] + (["torch_cuda"] if cuda else [])
    rows: list[dict[str, object]] = []
    for k in (1, 2, 4, 8, 12):
        tree, types, laws, leaves, _ = problem(k)
        numpy_reference = evaluate_ambient_numpy(tree, laws, types, leaves).root
        calls = 30 if k <= 4 else 15
        for backend in backends:
            _invoke(backend, tree, laws, types, leaves)
            _synchronize(backend)
            durations = []
            peak_ram = 0
            peak_vram = 0
            result = None
            for repeat in range(5):
                if backend == "torch_cuda":
                    torch.cuda.reset_peak_memory_stats()
                tracemalloc.start()
                start = time.perf_counter()
                for _ in range(calls):
                    result = _invoke(backend, tree, laws, types, leaves)
                _synchronize(backend)
                elapsed = time.perf_counter() - start
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                durations.append(elapsed / calls)
                peak_ram = max(peak_ram, int(peak))
                if backend == "torch_cuda":
                    peak_vram = max(peak_vram, int(torch.cuda.max_memory_allocated()))
            if backend == "torch_cuda":
                value = result.detach().cpu().numpy()
            else:
                value = np.asarray(result)
            difference = float(np.max(np.abs(value - numpy_reference)))
            median = statistics.median(durations)
            rows.append(
                {
                    "backend": backend,
                    "internal_nodes": k,
                    "arity": 2,
                    "dimension": 2,
                    "calls_per_repeat": calls,
                    "repeats": 5,
                    "median_seconds_per_tree": median,
                    "minimum_seconds_per_tree": min(durations),
                    "maximum_seconds_per_tree": max(durations),
                    "throughput_internal_nodes_per_second": k / median,
                    "peak_traced_ram_bytes": peak_ram,
                    "peak_vram_bytes": peak_vram,
                    "max_abs_difference_to_numpy": difference,
                    "scientific_instance_hash": canonical_hash(
                        {"block": "SCALING", "backend": backend, "k": k, "arity": 2, "dimension": 2}
                    ),
                    "status": "COMPLETE",
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = benchmark()
    csv_path = OUT / "computational_scaling.csv"
    parquet_path = OUT / "computational_scaling.parquet"
    frame.to_csv(csv_path, index=False)
    frame.to_parquet(parquet_path, index=False)
    tree, types, laws, leaves, tensor = problem(12)
    config = V3RunConfig(
        block="SCALING",
        instance_id="reference_numpy_cuda_scaling",
        method="wall_clock_median_five_repeats",
        seed=None,
        precision="float64",
        device="cpu+cuda" if (frame["backend"] == "torch_cuda").any() else "cpu",
        parameters={"internal_nodes": [1, 2, 4, 8, 12], "calls": "15--30", "repeats": 5},
        stage="full",
    )
    run_id = f"v3_scaling_{config.resolved_hash[:16]}"
    run_dir = RUNS / run_id
    metrics = {
        "rows": len(frame),
        "backends": sorted(frame["backend"].unique().tolist()),
        "maximum_parity_error": float(frame["max_abs_difference_to_numpy"].max()),
        "maximum_peak_vram_bytes": int(frame["peak_vram_bytes"].max()),
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    write_run_artifacts(
        run_dir,
        repo_root=ROOT,
        config=config,
        tree=tree,
        type_signature={"tau": {"ambient_dimension": 2, "reduced_dimension": 1}},
        law_tensors={"mu2": tensor},
        local_constants={"operator_norm": 1.0, "closure_norm": 0.0},
        reference_metrics=metrics,
        optimization_history=[],
        node_contributions=frame.to_dict("records"),
        final_metrics=metrics,
        certificate={"status": "NUMERICAL_BENCHMARK", "timing_claim": "environment-specific"},
        command="python scripts/benchmark_tree_constants_v3.py",
        stdout=json.dumps(metrics, indent=2) + "\n",
    )
    summary = {**metrics, "run_dir": str(run_dir), "status": "COMPLETE"}
    (OUT / "computational_scaling_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
