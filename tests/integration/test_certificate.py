import json
from pathlib import Path

from seion_core.certification.runner import certify_config


def test_vertical_slice_certificate(tmp_path):
    root = Path(__file__).resolve().parents[2]
    run_dir = certify_config(root / "experiments" / "configs" / "finite_ternary_v1.yaml", root)
    required = ["config.yaml", "resolved_config.yaml", "command.txt", "stdout.log", "stderr.log", "environment.json", "hardware.json", "run_manifest.json", "metrics.jsonl", "final_metrics.json", "certificate.json", "summary.md", "artifact_hashes.json"]
    assert all((run_dir / name).exists() for name in required)
    assert json.loads((run_dir / "certificate.json").read_text())["status"].startswith("COMPLETE")

