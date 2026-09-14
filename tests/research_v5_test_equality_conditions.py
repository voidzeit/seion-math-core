import pytest

from seion_core.research_v5.equality_conditions import audit_k2_equality_conditions


def test_k2_equality_conditions_are_compatible_for_independent_laws():
    audit = audit_k2_equality_conditions(0.5, independent_laws=True)
    assert audit.conclusion == "SATURATED_BY_EXPLICIT_CONSTRUCTION"
    assert all(condition.status in {"COMPATIBLE", "NOT_REQUIRED"} for condition in audit.conditions)


def test_repeated_law_requirement_is_resolved_by_the_v5b_witness():
    # Superseded 2026-08-08: construct_k2_repeated_map_saturation (V5-B)
    # exhibits a single law satisfying every equality condition at once, so
    # this is no longer an open compatibility question for the declared
    # same-map class (narrower restricted subclasses, e.g. gated-planar
    # rotation, are a separate, still-open question not audited here).
    audit = audit_k2_equality_conditions(0.5, independent_laws=False)
    assert audit.conclusion == "SATURATED_BY_EXPLICIT_CONSTRUCTION"
    assert all(condition.status in {"COMPATIBLE", "NOT_REQUIRED"} for condition in audit.conditions)


def test_equality_audit_rejects_eta_boundary_outside_declared_domain():
    with pytest.raises(ValueError):
        audit_k2_equality_conditions(0.0)
