from __future__ import annotations

import json
from pathlib import Path

from seion_core.governance.actions import evaluate_action
from seion_core.governance.audit import REQUIRED_FILES, audit_governance
from seion_core.governance.context import build_context_pack
from seion_core.governance.runs import deduplicate_runs
from seion_core.cli.main import build_parser


def _write_run(run_dir: Path, *, run_id: str, seed: int = 42) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = "experiment_id: demo\nseed: 42\nprecision: float64\nbackend: numpy\ndevice: cpu\n"
    (run_dir / "config.yaml").write_text(config, encoding="utf-8")
    (run_dir / "resolved_config.yaml").write_text(config, encoding="utf-8")
    (run_dir / "final_metrics.json").write_text(
        json.dumps({"experiment_id": "demo", "status": "COMPLETE", "seed": seed, "precision": "float64"}),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"run_id": run_id, "status": "COMPLETE", "config": {"experiment_id": "demo", "seed": seed}}),
        encoding="utf-8",
    )


def test_deduplicator_collapses_same_scientific_identity(tmp_path: Path) -> None:
    _write_run(tmp_path / "artifacts" / "runs" / "demo" / "a", run_id="a")
    _write_run(tmp_path / "artifacts" / "runs" / "demo" / "b", run_id="b")
    report = deduplicate_runs(tmp_path)
    assert report["historical_run_count"] == 2
    assert report["unique_scientific_instance_count"] == 1
    assert report["duplicate_record_count"] == 1
    rows = (tmp_path / "artifacts" / "index" / "run_index_deduplicated.csv").read_text(encoding="utf-8")
    assert "duplicate_count" in rows
    assert "a;b" in rows or "b;a" in rows


def test_action_gate_rejects_numerical_proof_claim(repo_root: Path) -> None:
    result = evaluate_action(
        repo_root,
        action="claim_numerical_proof",
        risk="critical",
        evidence_authority="verified",
        human_approval=True,
    )
    assert result["allowed"] is False
    assert any("numerical" in reason for reason in result["reasons"])


def test_context_pack_is_derived_and_bounded(repo_root: Path, tmp_path: Path) -> None:
    target = tmp_path / "context.md"
    path = build_context_pack(repo_root, task="recover evidence", output=target)
    assert path == target
    text = target.read_text(encoding="utf-8")
    assert "SEION context pack" in text
    assert "CURRENT_STATE.md" in text
    assert "derived; rebuildable" in text


def test_audit_reports_missing_paper_as_warning_but_not_error(tmp_path: Path) -> None:
    for relative in REQUIRED_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "claims/claims_registry.yaml":
            path.write_text("claims:\n  - id: C1\n    title: demo\n    status: definition\n    statement: demo\n", encoding="utf-8")
        elif relative == "claims/theorem_registry.yaml":
            path.write_text("theorems: []\n", encoding="utf-8")
        elif path.suffix == ".csv":
            headers = {
                "artifacts/index/claim_evidence_matrix.csv": "claim_id,status,statement,evidence\n",
                "artifacts/index/theorem_dependency_matrix.csv": "identifier,epistemic_status\n",
                "artifacts/index/run_index.csv": "run_path,experiment_id,status\n",
                "artifacts/index/figure_provenance.csv": "figure_id,source,status\n",
                "artifacts/index/table_provenance.csv": "table_id,source,status\n",
            }
            path.write_text(headers[relative], encoding="utf-8")
        elif path.suffix == ".json":
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("version: 1\n", encoding="utf-8") if path.suffix == ".yaml" else path.write_text("# test\n", encoding="utf-8")
    result = audit_governance(tmp_path, write_outputs=False)
    assert result["status"] == "yellow"
    assert result["passed"] is True
    assert not any(item["severity"] == "error" for item in result["issues"])


def test_postflight_command_argument_does_not_shadow_subcommand() -> None:
    args = build_parser().parse_args(
        [
            "governance",
            "postflight",
            "--task",
            "cli regression",
            "--summary",
            "parser regression",
            "--validation",
            "targeted test",
            "--command",
            "python -m pytest -q tests/governance",
        ]
    )
    assert args.command == "governance"
    assert args.governance_command == "postflight"
    assert args.run_command == "python -m pytest -q tests/governance"
