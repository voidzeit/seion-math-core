"""Gate 13.2b acceptance run (``campaigns/gate13/``): drives the REAL
``seion_kgr.train.train()`` entrypoint — not a bespoke script, the actual
CLI path a real campaign would invoke — with ``--path_backend batched``
through one full epoch on real, hash-verified WN18RR, then FB15K-237.

This is an ENGINEERING acceptance check (does the production integration
work end-to-end, does it complete, how fast is it), not a confirmatory MRR
comparison — ``--eval_max_queries`` caps evaluation cost. No causal or MRR
claim is made or implied here; that is explicitly Gate 13.5+, gated behind
this test passing (per ``campaigns/gate13/stopping_rules.md``).
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from seion_kgr.train import build_parser, train

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
WALL_CLOCK_CEILING_SEC = 300.0

pytestmark = pytest.mark.slow


def _run(tmp_path, dataset: str, epochs: int = 1) -> dict:
    data_dir = DATA_ROOT / dataset
    args = build_parser().parse_args([
        "--train", str(data_dir / "train.txt"),
        "--valid", str(data_dir / "valid.txt"),
        "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / dataset),
        "--dim", "64",
        "--enable_path", "--path_layers", "2", "--path_max_neighbors", "32",
        "--path_backend", "batched", "--path_selector_mode", "budgeted_bfs",
        "--epochs", str(epochs), "--batch_size", "256",
        "--eval_max_queries", "200",  # engineering completion check, not a confirmatory MRR run
        "--seed", "0",
    ])
    start = time.time()
    result = train(args)
    wall_sec = time.time() - start
    return {"result": result, "wall_sec": wall_sec}


@pytest.mark.skipif(not (DATA_ROOT / "WN18RR").is_dir(), reason="data/WN18RR not present in this checkout")
def test_batched_backend_completes_a_full_wn18rr_training_epoch(tmp_path):
    outcome = _run(tmp_path, "WN18RR")
    print(f"\n[Gate 13.2b] WN18RR full epoch (path_backend=batched): {outcome['wall_sec']:.1f}s")
    assert outcome["result"]["status"] == "COMPLETED"
    assert outcome["wall_sec"] < WALL_CLOCK_CEILING_SEC
    perf = (tmp_path / "WN18RR" / "path_reasoner_perf.jsonl")
    assert perf.is_file(), "path_reasoner_perf.jsonl was not produced"


@pytest.mark.skipif(not (DATA_ROOT / "FB15K-237").is_dir(), reason="data/FB15K-237 not present in this checkout")
def test_batched_backend_completes_a_full_fb15k237_training_epoch(tmp_path):
    outcome = _run(tmp_path, "FB15K-237")
    print(f"\n[Gate 13.2b] FB15K-237 full epoch (path_backend=batched): {outcome['wall_sec']:.1f}s")
    assert outcome["result"]["status"] == "COMPLETED"
    assert outcome["wall_sec"] < WALL_CLOCK_CEILING_SEC
    perf = (tmp_path / "FB15K-237" / "path_reasoner_perf.jsonl")
    assert perf.is_file(), "path_reasoner_perf.jsonl was not produced"
