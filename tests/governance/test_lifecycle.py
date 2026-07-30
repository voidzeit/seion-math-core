from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from seion_core.orchestration.lifecycle import load_lifecycle
from seion_core.orchestration.loop import advance, record_verify_result, start_session
from seion_core.orchestration.session import load_session


def _repo(tmp_path: Path, repo_root: Path) -> Path:
    shutil.copytree(repo_root / "governance", tmp_path / "governance")
    (tmp_path / ".ai" / "runtime" / "sessions").mkdir(parents=True)
    (tmp_path / ".ai" / "evidence").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=False)
    return tmp_path


def test_lifecycle_loads_all_eight_stages(repo_root: Path):
    lifecycle = load_lifecycle(repo_root)
    assert set(lifecycle.stages) == {"intake", "context", "plan", "change", "verify", "evidence", "postflight", "release"}


def test_only_the_next_forward_stage_is_a_legal_transition(repo_root: Path):
    lifecycle = load_lifecycle(repo_root)
    assert lifecycle.validate_transition("INTAKE", "CONTEXT") == []
    assert lifecycle.validate_transition("INTAKE", "PLANNED") != []
    assert lifecycle.validate_transition("INTAKE", "RELEASE") != []


def test_verify_to_change_is_the_only_legal_backward_edge(repo_root: Path):
    lifecycle = load_lifecycle(repo_root)
    assert lifecycle.validate_transition("VERIFYING", "IN_PROGRESS") == []
    assert lifecycle.validate_transition("EVIDENCE", "VERIFYING") != []
    assert lifecycle.validate_transition("PLANNED", "INTAKE") != []


def test_blocked_and_superseded_reachable_from_any_nonterminal_state(repo_root: Path):
    lifecycle = load_lifecycle(repo_root)
    for state in ("INTAKE", "CONTEXT", "PLANNED", "IN_PROGRESS", "VERIFYING", "EVIDENCE", "POSTFLIGHT", "RELEASE"):
        assert lifecycle.validate_transition(state, "BLOCKED") == []
        assert lifecycle.validate_transition(state, "SUPERSEDED") == []


def test_terminal_states_have_no_outgoing_transitions(repo_root: Path):
    lifecycle = load_lifecycle(repo_root)
    for terminal in ("COMPLETED", "BLOCKED", "SUPERSEDED"):
        assert lifecycle.validate_transition(terminal, "CONTEXT") != []


def test_start_session_blocks_on_missing_intake_evidence(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    result = start_session(root, task="demo", workstream="spectral", risk_level="low", evidence={})
    assert result.ok is False
    assert result.session.current_stage == "BLOCKED"


def test_full_forward_walk_intake_to_release(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    assert r.ok
    sid = r.session.session_id

    r = advance(
        root,
        session_id=sid,
        target="context",
        evidence={"AGENTS.md": True, ".ai/CURRENT_STATE.md": True, ".ai/TASKS.md": True, "relevant registries": True},
        gate_confirmations={"intake": True},
    )
    assert r.ok and r.session.current_stage == "CONTEXT"

    r = advance(
        root,
        session_id=sid,
        target="plan",
        evidence={"plan": "x", "claim_impact": "x", "test_plan": "x", "rollback_or_preservation_note": "x"},
        gate_confirmations={"context": True},
    )
    assert r.ok and r.session.current_stage == "PLANNED"

    r = advance(
        root,
        session_id=sid,
        target="change",
        evidence={"changed_files": ["a.py"], "no_secrets": True, "preserved_user_changes": True},
    )
    assert r.ok and r.session.current_stage == "IN_PROGRESS"

    r = advance(
        root,
        session_id=sid,
        target="verify",
        evidence={"command": "pytest", "exit_code": 0, "environment": "ci", "branch": "x", "commit": "x", "limitations": []},
        gate_confirmations={"change": True},
    )
    assert r.ok and r.session.current_stage == "VERIFYING"

    r = record_verify_result(
        root,
        session_id=sid,
        passed=True,
        evidence={"run_id_or_proof_location": "x", "artifact_hashes": "x", "provenance": "x"},
        gate_confirmations={"verify": True},
    )
    assert r.ok and r.session.current_stage == "EVIDENCE"

    r = advance(
        root,
        session_id=sid,
        target="postflight",
        evidence={"summary": "x", "outcome": "x", "validation": "x", "changed_files": ["a.py"], "limitations": []},
        gate_confirmations={"evidence": True},
    )
    assert r.ok and r.session.current_stage == "POSTFLIGHT"

    r = advance(
        root,
        session_id=sid,
        target="release",
        evidence={
            "strict_governance_audit": True,
            "tests": True,
            "paper_build": True,
            "render_report": True,
            "blocker_report": True,
            "human_approval": True,
        },
        gate_confirmations={"postflight": True},
    )
    assert r.ok and r.session.current_stage == "RELEASE"


def test_verify_failure_routes_back_to_change_with_counted_retry(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    sid = r.session.session_id
    advance(root, session_id=sid, target="context", evidence={"AGENTS.md": True, ".ai/CURRENT_STATE.md": True, ".ai/TASKS.md": True, "relevant registries": True}, gate_confirmations={"intake": True})
    advance(root, session_id=sid, target="plan", evidence={"plan": "x", "claim_impact": "x", "test_plan": "x", "rollback_or_preservation_note": "x"}, gate_confirmations={"context": True})
    advance(root, session_id=sid, target="change", evidence={"changed_files": ["a.py"], "no_secrets": True, "preserved_user_changes": True})
    advance(root, session_id=sid, target="verify", evidence={"command": "pytest", "exit_code": 0, "environment": "ci", "branch": "x", "commit": "x", "limitations": []}, gate_confirmations={"change": True})

    change_evidence = {"changed_files": ["a.py"], "no_secrets": True, "preserved_user_changes": True}
    r = record_verify_result(root, session_id=sid, passed=False, evidence=change_evidence, gate_confirmations={"verify": True})
    assert r.ok
    assert r.session.current_stage == "IN_PROGRESS"
    assert r.session.retry_counts["verify"] == 1


def test_verify_retry_cap_hard_blocks_and_is_logged(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    sid = r.session.session_id
    advance(root, session_id=sid, target="context", evidence={"AGENTS.md": True, ".ai/CURRENT_STATE.md": True, ".ai/TASKS.md": True, "relevant registries": True}, gate_confirmations={"intake": True})
    advance(root, session_id=sid, target="plan", evidence={"plan": "x", "claim_impact": "x", "test_plan": "x", "rollback_or_preservation_note": "x"}, gate_confirmations={"context": True})
    advance(root, session_id=sid, target="change", evidence={"changed_files": ["a.py"], "no_secrets": True, "preserved_user_changes": True})
    advance(root, session_id=sid, target="verify", evidence={"command": "pytest", "exit_code": 0, "environment": "ci", "branch": "x", "commit": "x", "limitations": []}, gate_confirmations={"change": True})

    change_evidence = {"changed_files": ["a.py"], "no_secrets": True, "preserved_user_changes": True}
    for _ in range(2):
        record_verify_result(root, session_id=sid, passed=False, evidence=change_evidence, gate_confirmations={"verify": True}, max_retries=2)
        advance(root, session_id=sid, target="verify", evidence={"command": "pytest", "exit_code": 0, "environment": "ci", "branch": "x", "commit": "x", "limitations": []}, gate_confirmations={"change": True})

    final = record_verify_result(root, session_id=sid, passed=False, evidence=change_evidence, gate_confirmations={"verify": True}, max_retries=2)
    assert final.ok is False
    assert final.session.current_stage == "BLOCKED"
    assert final.session.blocked_reason is not None

    ledger = (root / ".ai" / "evidence" / "ledger.jsonl").read_text(encoding="utf-8")
    assert "lifecycle_blocked" in ledger


def test_gate_confirmation_is_required_and_never_assumed(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    sid = r.session.session_id
    result = advance(
        root,
        session_id=sid,
        target="context",
        evidence={"AGENTS.md": True, ".ai/CURRENT_STATE.md": True, ".ai/TASKS.md": True, "relevant registries": True},
        gate_confirmations={},  # no confirmation supplied
    )
    assert result.ok is False
    assert any("gate" in p for p in result.problems)


def test_missing_required_evidence_blocks_the_transition(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    sid = r.session.session_id
    result = advance(root, session_id=sid, target="context", evidence={}, gate_confirmations={"intake": True})
    assert result.ok is False
    assert any("missing required evidence" in p for p in result.problems)


def test_session_history_is_append_only_and_survives_multiple_transitions(tmp_path: Path, repo_root: Path):
    root = _repo(tmp_path, repo_root)
    r = start_session(
        root,
        task="demo",
        workstream="spectral",
        risk_level="low",
        evidence={"task_id": "T1", "affected_workstream": "spectral", "risk_level": "low", "expected_outputs": "x"},
    )
    sid = r.session.session_id
    advance(root, session_id=sid, target="context", evidence={"AGENTS.md": True, ".ai/CURRENT_STATE.md": True, ".ai/TASKS.md": True, "relevant registries": True}, gate_confirmations={"intake": True})
    history_path = root / ".ai" / "runtime" / "sessions" / f"{sid}.history.jsonl"
    lines_before = history_path.read_text(encoding="utf-8").splitlines()
    advance(root, session_id=sid, target="plan", evidence={"plan": "x", "claim_impact": "x", "test_plan": "x", "rollback_or_preservation_note": "x"}, gate_confirmations={"context": True})
    lines_after = history_path.read_text(encoding="utf-8").splitlines()
    assert lines_after[: len(lines_before)] == lines_before  # prior lines untouched
    assert len(lines_after) > len(lines_before)

    session = load_session(root, sid)
    assert session.current_stage == "PLANNED"
