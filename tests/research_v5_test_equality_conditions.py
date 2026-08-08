import pytest

from seion_core.research_v5.equality_conditions import audit_k2_equality_conditions


def test_k2_equality_conditions_are_compatible_for_independent_laws():
    audit = audit_k2_equality_conditions(0.5, independent_laws=True)
    assert audit.conclusion == "SATURATED_BY_EXPLICIT_CONSTRUCTION"
    assert all(condition.status in {"COMPATIBLE", "NOT_REQUIRED"} for condition in audit.conditions)


def test_repeated_law_requirement_remains_open():
    audit = audit_k2_equality_conditions(0.5, independent_laws=False)
    assert audit.conclusion == "OPEN_REPEATED_LAW_COMPATIBILITY"
    assert any(condition.status == "OPEN_IF_REPEATED" for condition in audit.conditions)


def test_equality_audit_rejects_eta_boundary_outside_declared_domain():
    with pytest.raises(ValueError):
        audit_k2_equality_conditions(0.0)
