from __future__ import annotations

from pathlib import Path

from seion_core.orchestration.roles import load_roles, roles_for_stage

EXPECTED_STAGE_BINDINGS = {
    "intake": set(),
    "context": {"graph-maintainer", "memory-curator"},
    "plan": {"research-mathematician", "prior-art-auditor"},
    "change": {"artifact-builder", "development-reviewer"},
    "verify": {"numerical-verifier", "verification-runner", "proof-auditor", "security-auditor"},
    "evidence": {"experiment-runner"},
    "postflight": {"memory-curator"},
    "release": {"release-auditor", "paper-editor", "research-editor", "visualization-auditor"},
}


def test_all_fifteen_roles_load(repo_root: Path):
    roles = load_roles(repo_root)
    assert len(roles) == 15


def test_every_role_has_the_upgraded_schema_fields(repo_root: Path):
    for role in load_roles(repo_root):
        assert role.agent_id, role.path
        assert role.authority, role.path
        assert role.must_not, role.path
        assert role.required_outputs, role.path


def test_stage_bindings_match_the_declared_mapping(repo_root: Path):
    for stage, expected in EXPECTED_STAGE_BINDINGS.items():
        actual = {r.agent_id for r in roles_for_stage(repo_root, stage)}
        assert actual == expected, f"stage {stage!r}: expected {expected}, got {actual}"


def test_every_bound_role_appears_in_exactly_the_stages_it_declares(repo_root: Path):
    roles = load_roles(repo_root)
    for role in roles:
        for stage in role.stages:
            assert role in roles_for_stage(repo_root, stage)
