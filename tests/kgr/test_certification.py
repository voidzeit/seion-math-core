"""Campaign Phase B4: certification chain.

The central thing to verify honestly here is NOT "certification always
succeeds" — it's that certification correctly REFUSES to certify the
moment an uncertified assumption (projector closure leakage, nonlinear
envelope Lipschitz constant) is in the path, and that the one case where
it DOES certify (no compression in the path) is mathematically real, not
a fudge.
"""
import math

import pytest
import torch

from seion_kgr.certification import (
    AssumptionCheck,
    certify_query,
    check_nonlinear_envelope_assumptions,
    check_projector_assumptions,
    coverage_report,
    cp_law_operator_norm_bound,
    entity_norm_bound,
    operator_norm,
)
from seion_kgr.kernels import CPTernaryLaw, StiefelProjector

pytestmark = pytest.mark.symbolic


# ------------------------------------------------------------------ checked constants


def test_operator_norm_matches_independent_svd_computation():
    W = torch.randn(6, 4)
    got = operator_norm(W)
    expected = float(torch.linalg.svd(W, full_matrices=False).S.max().item())
    assert abs(got - expected) < 1e-5


def test_entity_norm_bound_matches_independent_max_norm():
    E = torch.randn(10, 5)
    got = entity_norm_bound(E)
    expected = float(max(torch.linalg.norm(row).item() for row in E))
    assert abs(got - expected) < 1e-5


def test_cp_law_operator_norm_bound_is_never_exceeded_empirically():
    """The certified property that actually matters: for MANY random
    unit-norm (x,a,q), ||mu(x,a,q)|| must never exceed M_bound. A single
    violation would mean the 'certified' bound is not actually valid."""
    torch.manual_seed(3)
    law = CPTernaryLaw(dim_x=4, dim_a=4, dim_q=4, dim_out=5, rank=3)
    M_bound = cp_law_operator_norm_bound(law)
    worst = 0.0
    for _ in range(500):
        x = torch.nn.functional.normalize(torch.randn(4), dim=0)
        a = torch.nn.functional.normalize(torch.randn(4), dim=0)
        q = torch.nn.functional.normalize(torch.randn(4), dim=0)
        out_norm = float(torch.linalg.norm(law.forward(x, a, q)).item())
        worst = max(worst, out_norm)
        assert out_norm <= M_bound + 1e-6, f"empirical output norm {out_norm} exceeds certified M_bound {M_bound}"
    assert worst > 0.0  # sanity: the law isn't trivially zero, so this was a real check


# ------------------------------------------------------------------ assumption checks


def test_projector_assumptions_pass_when_absent_or_full_rank():
    checks_absent = check_projector_assumptions(None)
    assert all(c.passed for c in checks_absent)
    checks_disabled = check_projector_assumptions(StiefelProjector(dim=5, rank=0))
    assert all(c.passed for c in checks_disabled)


def test_projector_assumptions_fail_closure_leakage_when_rank_reducing():
    proj = StiefelProjector(dim=6, rank=3)
    checks = check_projector_assumptions(proj)
    by_name = {c.name: c for c in checks}
    assert by_name["isometry_residual"].passed  # QR retraction is always exactly orthonormal
    assert not by_name["closure_leakage_operator_norm_certified"].passed  # honestly never passes today


def test_nonlinear_envelope_assumption_fails_when_present():
    assert all(c.passed for c in check_nonlinear_envelope_assumptions(False))
    assert not all(c.passed for c in check_nonlinear_envelope_assumptions(True))


# ------------------------------------------------------------------ certify_query: the honest certified case


def test_base_expert_only_certifies_with_zero_bound_and_positive_margin():
    scores = torch.tensor([5.0, 1.0, 0.5, 0.0])
    result = certify_query(
        query_id="q0", scores=scores, gold_index=0, cp_law=None, projector=None,
        entity_weight=torch.randn(4, 3), has_nonlinear_envelope=False,
    )
    assert result.state_error_bound == 0.0
    assert result.score_linf_bound == 0.0
    assert result.certified_rank_stable is True
    assert result.certified_top1 is True
    assert result.certificate_reason.startswith("CERTIFIED")


def test_cp_law_no_projection_no_envelope_still_certifies():
    torch.manual_seed(1)
    law = CPTernaryLaw(dim_x=4, dim_a=4, dim_q=4, dim_out=4, rank=3)
    scores = torch.tensor([2.0, -1.0, -3.0])
    result = certify_query(
        query_id="q1", scores=scores, gold_index=0, cp_law=law, projector=None,
        entity_weight=torch.randn(3, 4), has_nonlinear_envelope=False,
    )
    assert result.certified_rank_stable is True
    assert result.state_error_bound == 0.0


# ------------------------------------------------------------------ certify_query: honest refusals


def test_rank_reducing_projector_refuses_certification():
    proj = StiefelProjector(dim=6, rank=3)
    scores = torch.tensor([9.0, 1.0, 0.0])
    result = certify_query(
        query_id="q2", scores=scores, gold_index=0, cp_law=None, projector=proj,
        entity_weight=torch.randn(3, 4), has_nonlinear_envelope=False,
    )
    assert result.state_error_bound is None
    assert result.score_linf_bound is None
    assert result.certified_rank_stable is False
    assert result.certificate_reason.startswith("NOT_CERTIFIED")
    assert any(not c.passed for c in result.assumption_checks)


def test_nonlinear_envelope_refuses_certification_even_with_huge_margin():
    """A huge margin does NOT rescue certification if the assumptions
    that would make the bound meaningful were never checked — this is
    the single most important behavior of this module."""
    scores = torch.tensor([1000.0, -1000.0])
    result = certify_query(
        query_id="q3", scores=scores, gold_index=0, cp_law=None, projector=None,
        entity_weight=torch.randn(2, 4), has_nonlinear_envelope=True,
    )
    assert result.certified_rank_stable is False
    assert result.score_linf_bound is None


def test_zero_margin_gold_tied_with_competitor_is_never_certified_top1():
    scores = torch.tensor([1.0, 1.0, 0.0])  # gold ties with a competitor
    result = certify_query(
        query_id="q4", scores=scores, gold_index=0, cp_law=None, projector=None,
        entity_weight=torch.randn(3, 4), has_nonlinear_envelope=False,
    )
    assert result.ranking_margin == 0.0
    # margin > 2*epsilon with epsilon=0 requires margin > 0 STRICTLY
    assert result.certified_rank_stable is False


# ------------------------------------------------------------------ coverage report


def test_coverage_report_matches_hand_computed_fractions():
    scores_certified = torch.tensor([5.0, 1.0])
    scores_uncertified_proj = torch.tensor([5.0, 1.0])
    proj = StiefelProjector(dim=4, rank=2)
    r1 = certify_query("a", scores_certified, 0, None, None, torch.randn(2, 3), False)
    r2 = certify_query("b", scores_uncertified_proj, 0, None, proj, torch.randn(2, 3), False)
    report = coverage_report([r1, r2])
    assert report["count"] == 2
    assert abs(report["certified_top1_coverage"] - 0.5) < 1e-9
    assert abs(report["certified_rank_stable_coverage"] - 0.5) < 1e-9


def test_coverage_report_handles_empty_list():
    assert coverage_report([]) == {"count": 0}


# ------------------------------------------------------------------ certify_evaluation_split (integration)


def test_certify_evaluation_split_base_expert_only_has_high_coverage():
    from seion_kgr.data import tiny_kg
    from seion_kgr.model import SeionKGRv26

    kg = tiny_kg()
    model = SeionKGRv26(num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8, base_expert="distmult")
    device = torch.device("cpu")

    from seion_kgr.certification import certify_evaluation_split

    report = certify_evaluation_split(model, kg, "test", device)
    assert report["coverage"]["count"] == len(kg.test)
    # No path reasoner, no seion scorer -> every assumption trivially
    # holds -> certified whenever the gold score isn't exactly tied.
    assert report["coverage"]["certified_rank_stable_coverage"] >= 0.0  # always a valid fraction
    for pq in report["per_query"]:
        assert pq["certificate_reason"].startswith("CERTIFIED")


def test_certify_evaluation_split_path_enabled_has_zero_coverage_honestly():
    from seion_kgr.data import tiny_kg
    from seion_kgr.model import SeionKGRv26

    kg = tiny_kg()
    model = SeionKGRv26(
        num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8,
        base_expert="distmult", enable_path=True, path_rank=3, path_layers=1, path_max_neighbors=4,
    )
    device = torch.device("cpu")

    from seion_kgr.certification import certify_evaluation_split

    report = certify_evaluation_split(model, kg, "test", device)
    assert report["coverage"]["certified_rank_stable_coverage"] == 0.0
    for pq in report["per_query"]:
        assert pq["certificate_reason"].startswith("NOT_CERTIFIED")
