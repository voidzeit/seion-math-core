"""Gate 13.3b acceptance test (``campaigns/gate13/``): PASS_ATTRIBUTION_REAL_RUN.

Trains a small real model on a real WN18RR subsample (via the actual
``train.py`` entrypoint), then runs the real attribution pipeline
(``run_attribution.py``) over the resulting checkpoint — not a bespoke
script, the same two CLI tools a real campaign would invoke in sequence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from seion_kgr.run_attribution import build_parser as build_attribution_parser
from seion_kgr.run_attribution import run_attribution
from seion_kgr.train import build_parser as build_train_parser
from seion_kgr.train import train

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "WN18RR"
FP32_TOLERANCE = 1e-5

pytestmark = pytest.mark.slow


def _write_subsample(tmp_path: Path) -> Path:
    sub = tmp_path / "wn18rr_sub"
    sub.mkdir()
    for split, n in (("train", 20000), ("valid", 300), ("test", 300)):
        lines = (DATA_ROOT / f"{split}.txt").read_text(encoding="utf-8").splitlines()[:n]
        (sub / f"{split}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sub


def _train_checkpoint(data_dir: Path, out_dir: Path) -> Path:
    args = build_train_parser().parse_args([
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(out_dir), "--dim", "16", "--enable_path", "--path_layers", "2", "--path_max_neighbors", "8",
        "--path_backend", "batched", "--path_selector_mode", "budgeted_bfs",
        "--epochs", "2", "--batch_size", "64", "--eval_max_queries", "100", "--seed", "0", "--cpu",
    ])
    train(args)
    return out_dir / "best.pt"


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_attribution_real_run_over_a_trained_checkpoint(tmp_path):
    data_dir = _write_subsample(tmp_path)
    checkpoint = _train_checkpoint(data_dir, tmp_path / "train_run")

    def _run(out_dir_name: str, attribution_mode: str):
        out_dir = tmp_path / out_dir_name
        args = build_attribution_parser().parse_args([
            "--checkpoint", str(checkpoint),
            "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
            "--out_dir", str(out_dir), "--attribution_split", "valid", "--attribution_max_queries", "100",
            "--attribution_seed", "13", "--attribution_mode", attribution_mode, "--cpu",
        ])
        return run_attribution(args), out_dir / "attribution"

    result, attr_dir = _run("attribution_end_to_end", "end_to_end")

    # --- files present ---
    for filename in (
        "module_error_attribution.jsonl", "shapley_attribution.jsonl", "rank_flip_attribution.jsonl",
        "module_interactions.json", "attribution_summary.json", "attribution_manifest.json",
    ):
        assert (attr_dir / filename).is_file(), f"missing artifact: {filename}"

    assert result["num_failures"] == 0

    # --- conservation, within the FP32 tolerance frozen in campaigns/gate13/preregistration.md §2 ---
    path_internal = result["module_interactions"]["path_internal"]
    assert path_internal["max_reconstruction_error_forward"] < FP32_TOLERANCE
    assert path_internal["max_reconstruction_error_backward"] < FP32_TOLERANCE
    assert path_internal["shapley_efficiency_error"] < FP32_TOLERANCE
    assert result["module_interactions"]["branch_level"]["max_reconstruction_error"] < FP32_TOLERANCE

    # --- manifest completeness ---
    manifest = json.loads((attr_dir / "attribution_manifest.json").read_text())
    for field in (
        "model_commit", "checkpoint_sha256", "dataset_hashes", "path_backend", "selector_mode",
        "attribution_mode", "coalition_semantics_version", "coalition_semantics", "shapley_samples",
        "seed", "modules", "numeric_tolerances",
    ):
        assert field in manifest, f"manifest missing field: {field}"
    assert manifest["coalition_semantics_version"] == "gate13-v1"

    # --- raw vs effective never conflated: for any record with a nonzero gate != 1, effective != raw ---
    records = [json.loads(line) for line in (attr_dir / "module_error_attribution.jsonl").read_text().splitlines()]
    path_records = [r for r in records if r["module_id"].startswith("path.") and r["raw_contribution"] not in (0.0, None)]
    assert path_records, "no nonzero path-internal attribution record found — fixture too degenerate to test raw-vs-effective distinction"
    for rec in path_records:
        gate = rec["gate_value"]
        if abs(gate - 1.0) > 1e-6:  # gate==1 would make raw==effective trivially, not a conflation bug
            assert rec["effective_contribution"] != rec["raw_contribution"], (
                f"raw and effective contribution are identical despite gate={gate} != 1: {rec}"
            )
        assert abs(rec["effective_contribution"] - gate * rec["raw_contribution"]) < FP32_TOLERANCE

    # --- deterministic re-execution: same checkpoint, same seed -> identical numbers ---
    result2, attr_dir2 = _run("attribution_end_to_end_rerun", "end_to_end")
    assert result2["module_interactions"] == result["module_interactions"]
    shapley1 = (attr_dir / "shapley_attribution.jsonl").read_text()
    shapley2 = (attr_dir2 / "shapley_attribution.jsonl").read_text()
    assert shapley1 == shapley2, "re-running attribution with the same checkpoint/seed did not reproduce byte-identical shapley_attribution.jsonl"

    # --- fixed_trace and end_to_end coincide for the currently-supported selector modes (see
    # run_attribution.py's module docstring for why: edge selection never depends on which
    # message components are ablated for full_neighborhood/budgeted_bfs) ---
    result_fixed, _ = _run("attribution_fixed_trace", "fixed_trace")
    assert result_fixed["module_interactions"] == result["module_interactions"], (
        "fixed_trace and end_to_end produced different numbers for a selector mode where they "
        "are expected to provably coincide"
    )
    assert result_fixed["manifest"]["attribution_mode"] == "fixed_trace"
    assert result["manifest"]["attribution_mode"] == "end_to_end"


@pytest.mark.skipif(not DATA_ROOT.is_dir(), reason="data/WN18RR not present in this checkout")
def test_attribution_rejects_learned_topk_explicitly(tmp_path):
    data_dir = _write_subsample(tmp_path)
    checkpoint = _train_checkpoint(data_dir, tmp_path / "train_run")
    # Simulate a checkpoint whose saved args used learned_topk (rather than
    # re-training with it, which is legacy-only and slow): monkeypatch is
    # avoided here in favor of directly asserting the guard exists in
    # run_attribution.py by constructing args that would hit it if the
    # checkpoint claimed learned_topk. Since load_checkpoint reads the
    # checkpoint's OWN saved selector mode, we verify the guard via the
    # checkpoint's args dict directly instead of retraining.
    import torch
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
    ckpt["args"]["path_selector_mode"] = "learned_topk"
    tampered_path = tmp_path / "tampered.pt"
    torch.save(ckpt, tampered_path)

    args = build_attribution_parser().parse_args([
        "--checkpoint", str(tampered_path),
        "--train", str(data_dir / "train.txt"), "--valid", str(data_dir / "valid.txt"), "--test", str(data_dir / "test.txt"),
        "--out_dir", str(tmp_path / "attribution_rejected"), "--attribution_max_queries", "10", "--cpu",
    ])
    with pytest.raises(NotImplementedError, match="learned_topk"):
        run_attribution(args)
