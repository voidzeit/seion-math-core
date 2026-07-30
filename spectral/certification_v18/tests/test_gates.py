from __future__ import annotations

import pytest

from spectral.certification_v18.gates import (
    CRITICAL_GATES,
    ScreeningCertificateViolation,
    TypedStatus,
    assign_block_status,
    combine_gate_status,
    evaluate_global_certificate,
)


def test_screening_run_cannot_be_assigned_certificate_status():
    with pytest.raises(ScreeningCertificateViolation):
        assign_block_status(
            eval_mode="screening",
            status=TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE,
            block_name="A_projector",
        )


def test_certification_run_may_be_assigned_certificate_status():
    result = assign_block_status(
        eval_mode="certification",
        status=TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE,
        block_name="A_projector",
    )
    assert result == TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE


def test_screening_run_may_be_assigned_screening_pass():
    result = assign_block_status(
        eval_mode="screening",
        status=TypedStatus.EMPIRICAL_SCREENING_PASS,
        block_name="A_projector",
    )
    assert result == TypedStatus.EMPIRICAL_SCREENING_PASS


def test_gate_status_is_minimum_not_average():
    statuses = {
        "A_projector": TypedStatus.EXACT_CERTIFICATE,
        "D_snapping": TypedStatus.WARN,
    }
    assert combine_gate_status(statuses) == TypedStatus.WARN


def test_gate_status_all_not_applicable_is_not_applicable():
    statuses = {
        "E_interscale": TypedStatus.NOT_APPLICABLE,
        "J_tensor_interscale": TypedStatus.NOT_APPLICABLE,
    }
    assert combine_gate_status(statuses) == TypedStatus.NOT_APPLICABLE


def test_gate_status_mixed_not_applicable_ignores_it():
    statuses = {
        "E_interscale": TypedStatus.NOT_APPLICABLE,
        "J_tensor_interscale": TypedStatus.EMPIRICAL_SCREENING_PASS,
    }
    assert combine_gate_status(statuses) == TypedStatus.EMPIRICAL_SCREENING_PASS


def test_global_certificate_fails_closed_on_any_failing_gate():
    gate_statuses = {gate: TypedStatus.EMPIRICAL_SCREENING_PASS for gate in CRITICAL_GATES}
    gate_statuses["dynamic_explanation_gate"] = TypedStatus.WARN
    result = evaluate_global_certificate(gate_statuses, eval_mode="screening")
    assert result.final_state.startswith("FAIL_CLOSED_")
    assert "dynamic_explanation_gate" in result.failing_gates


def test_global_certificate_excludes_not_applicable_without_failing():
    gate_statuses = {gate: TypedStatus.EMPIRICAL_SCREENING_PASS for gate in CRITICAL_GATES}
    gate_statuses["interscale_gate"] = TypedStatus.NOT_APPLICABLE
    gate_statuses["persistence_gate"] = TypedStatus.NOT_APPLICABLE
    result = evaluate_global_certificate(gate_statuses, eval_mode="screening")
    assert result.final_state == "PASS_A_TO_N_SCREENING_ONLY_NOT_A_CERTIFICATE"
    assert "interscale_gate" in result.excluded_gates
    assert "persistence_gate" in result.excluded_gates


def test_global_certificate_screening_run_never_yields_full_certification():
    gate_statuses = {gate: TypedStatus.EXACT_CERTIFICATE for gate in CRITICAL_GATES}
    result = evaluate_global_certificate(gate_statuses, eval_mode="screening")
    assert "FULL_CERTIFICATION" not in result.final_state


def test_no_final_state_is_ever_full_certification():
    # No code path in evaluate_global_certificate may produce
    # PASS_A_TO_N_FULL_CERTIFICATION: that requires human review this
    # process cannot self-issue (mission section 10, rule 10).
    gate_statuses = {gate: TypedStatus.EXACT_CERTIFICATE for gate in CRITICAL_GATES}
    result = evaluate_global_certificate(gate_statuses, eval_mode="certification")
    assert result.final_state == "PASS_A_TO_N_PARTIAL_CERTIFICATION"
