from __future__ import annotations

import json

from seion_kgr.train_sota_discovery import build_parser, run


def test_sota_discovery_tiny_canary_writes_recoverable_artifacts(tmp_path):
    args = build_parser().parse_args([
        "--tiny",
        "--cpu",
        "--out-dir", str(tmp_path / "run"),
        "--dim", "8",
        "--base-expert", "distmult",
        "--batch-size", "4",
        "--epochs", "1",
        "--max-steps", "2",
        "--candidate-pool", "5",
        "--hard-k", "2",
        "--allow-existing",
    ])
    result = run(args)
    assert result["status"] == "COMPLETE"
    assert result["global_step"] == 2
    assert (tmp_path / "run" / "checkpoint_last.pt").exists()
    saved = json.loads((tmp_path / "run" / "discovery_result.json").read_text())
    assert saved["global_step"] == 2
