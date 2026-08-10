from __future__ import annotations

import json

from seion_kgr.train_spectral_mixture import build_parser, run


def test_spectral_mixture_tiny_trainer_completes_and_checkpoints(tmp_path):
    args = build_parser().parse_args([
        "--tiny", "--cpu", "--out-dir", str(tmp_path / "run"),
        "--dim", "8", "--relation-dim", "8", "--experts", "2",
        "--active-experts", "1", "--expert-rank", "4", "--core-basis", "2",
        "--batch-size", "4", "--candidate-block", "3", "--hard-k", "2",
        "--max-steps", "2", "--allow-existing",
    ])
    result = run(args)
    assert result["status"] == "COMPLETE"
    assert result["steps"] == 2
    assert (tmp_path / "run" / "checkpoint_last.pt").exists()
    saved = json.loads((tmp_path / "run" / "discovery_result.json").read_text())
    assert saved["steps"] == 2


def test_spectral_mixture_tiny_trainer_writes_best_validation_checkpoint(tmp_path):
    out_dir = tmp_path / "best"
    args = build_parser().parse_args([
        "--tiny", "--cpu", "--out-dir", str(out_dir),
        "--dim", "8", "--relation-dim", "8", "--experts", "2",
        "--active-experts", "1", "--expert-rank", "4", "--core-basis", "2",
        "--batch-size", "4", "--candidate-block", "3", "--hard-k", "2",
        "--max-steps", "2", "--eval-every", "1", "--eval-queries", "2",
        "--allow-existing",
    ])
    result = run(args)
    assert result["best_valid_step"] is not None
    assert (out_dir / "checkpoint_best.pt").exists()


def test_spectral_mixture_resume_normalizes_rng_and_optimizer_state(tmp_path):
    first = build_parser().parse_args([
        "--tiny", "--cpu", "--out-dir", str(tmp_path / "first"),
        "--dim", "8", "--relation-dim", "8", "--experts", "2",
        "--active-experts", "1", "--expert-rank", "4", "--core-basis", "2",
        "--batch-size", "4", "--candidate-block", "3", "--hard-k", "2",
        "--max-steps", "2", "--allow-existing",
    ])
    run(first)
    resumed = build_parser().parse_args([
        "--tiny", "--cpu", "--out-dir", str(tmp_path / "second"),
        "--dim", "8", "--relation-dim", "8", "--experts", "2",
        "--active-experts", "1", "--expert-rank", "4", "--core-basis", "2",
        "--batch-size", "4", "--candidate-block", "3", "--hard-k", "2",
        "--epochs", "2", "--max-steps", "3", "--resume",
        str(tmp_path / "first" / "checkpoint_last.pt"), "--allow-existing",
    ])
    result = run(resumed)
    assert result["steps"] == 3
