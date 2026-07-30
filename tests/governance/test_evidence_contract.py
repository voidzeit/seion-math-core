"""Mutation/anti-gaming tests for the SEION V5 Phase 2 frozen evidence contract.

Each test proves the corresponding invariant in evidence_contract.py
actually rejects the specific violation it claims to catch, and does not
false-positive on the corresponding valid case.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from seion_core.governance import evidence_contract as ec

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bound_ordering_accepts_valid_bounds():
    assert ec.check_bound_ordering(1.0, 2.0) == []
    assert ec.check_bound_ordering(2.0, 2.0) == []
    assert ec.check_bound_ordering(1.99999, 2.0, tolerance=1e-6) == []


def test_bound_ordering_rejects_lower_exceeding_upper():
    violations = ec.check_bound_ordering(3.0, 2.0)
    assert violations
    assert "exceeds" in violations[0]


def test_bound_ordering_tolerance_does_not_mask_real_violation():
    violations = ec.check_bound_ordering(3.0, 2.0, tolerance=1e-6)
    assert violations


def test_exact_status_accepts_zero_gap():
    assert ec.check_exact_status_requires_zero_gap("EXACT_CERTIFICATE", 0.0) == []
    assert ec.check_exact_status_requires_zero_gap("EMPIRICAL_SCREENING_PASS", 0.37) == []


def test_exact_status_rejects_nonzero_gap():
    violations = ec.check_exact_status_requires_zero_gap("EXACT_CERTIFICATE", 0.01)
    assert violations
    assert "!= 0" in violations[0]


def test_exact_status_rejects_missing_gap():
    violations = ec.check_exact_status_requires_zero_gap("PROVED", None)
    assert violations
    assert "absent" in violations[0]


def test_empirical_evidence_cannot_promote_theorem_status():
    violations = ec.check_empirical_cannot_promote_theorem_status(
        "PROVED", ["empirical", "STATISTICALLY_VALIDATED"]
    )
    assert violations
    assert "empirical-only" in violations[0]


def test_proof_grade_evidence_can_support_theorem_status():
    assert ec.check_empirical_cannot_promote_theorem_status("PROVED", ["symbolically_verified"]) == []


def test_theorem_status_with_no_evidence_is_rejected():
    violations = ec.check_empirical_cannot_promote_theorem_status("proved", [])
    assert violations
    assert "no supporting evidence" in violations[0]


def test_non_theorem_status_is_exempt():
    assert ec.check_empirical_cannot_promote_theorem_status("open", []) == []


def test_screening_mode_cannot_emit_certificate():
    violations = ec.check_screening_cannot_emit_certificate("screening", "VALIDATED_NUMERICAL_CERTIFICATE")
    assert violations
    assert "cannot certify" in violations[0]


def test_certification_mode_can_emit_certificate():
    assert ec.check_screening_cannot_emit_certificate("certification", "VALIDATED_NUMERICAL_CERTIFICATE") == []


def test_screening_mode_can_emit_screening_status():
    assert ec.check_screening_cannot_emit_certificate("screening", "EMPIRICAL_SCREENING_PASS") == []


def test_resumed_run_with_restored_rng_is_not_independent_seed():
    violations = ec.check_resumed_run_is_not_independent_seed(
        is_resumed=True, restore_rng=True, claimed_as_independent_seed=True
    )
    assert violations


def test_resumed_run_not_claimed_as_independent_is_fine():
    assert ec.check_resumed_run_is_not_independent_seed(
        is_resumed=True, restore_rng=True, claimed_as_independent_seed=False
    ) == []


def test_fresh_run_can_be_claimed_as_independent_seed():
    assert ec.check_resumed_run_is_not_independent_seed(
        is_resumed=False, restore_rng=False, claimed_as_independent_seed=True
    ) == []


def test_figure_value_matching_source_is_accepted():
    assert ec.check_figure_values_exist_in_source({"gap": 0.01}, {"gap": 0.01}) == []


def test_figure_value_absent_from_source_is_rejected():
    violations = ec.check_figure_values_exist_in_source({"forged_metric": 99.9}, {"gap": 0.01})
    assert violations
    assert "forged_metric" in violations[0]


def test_figure_value_mismatching_source_is_rejected():
    violations = ec.check_figure_values_exist_in_source({"gap": 0.02}, {"gap": 0.01})
    assert violations
    assert "does not match" in violations[0]


def test_table_count_matching_is_accepted():
    assert ec.check_table_count_reconciles(table_row_count=80, declared_total=80) == []


def test_table_count_mismatch_is_rejected():
    violations = ec.check_table_count_reconciles(table_row_count=80, declared_total=105)
    assert violations
    assert "105" in violations[0] and "80" in violations[0]


def test_frozen_schema_manifest_matches_actual_file_hashes():
    """Schema drift detector: fails closed if any schemas/*.json file was edited
    without regenerating SCHEMA_FREEZE_MANIFEST.json (which itself must only be
    regenerated alongside a schemas/MIGRATIONS.md entry, per that file's own header)."""
    schema_dir = REPO_ROOT / "schemas"
    manifest_path = schema_dir / "SCHEMA_FREEZE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(schema_dir.glob("*.json"))
        if path.name != manifest_path.name
    }
    assert actual == manifest["hashes"], (
        "schemas/*.json drifted from schemas/SCHEMA_FREEZE_MANIFEST.json without a "
        "recorded migration — see schemas/MIGRATIONS.md"
    )


def test_migrations_log_exists_and_is_nonempty():
    migrations = REPO_ROOT / "schemas" / "MIGRATIONS.md"
    assert migrations.exists()
    assert "v1" in migrations.read_text(encoding="utf-8")
