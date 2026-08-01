from __future__ import annotations

from spectral.certification_v18.blocks.block_c_beals_proxy import (
    adversarial_projector,
    build_observables,
    localized_projector,
    nested_commutator_norms,
    random_projector,
    scaling_study,
    smooth_projector,
)


def test_all_reported_quantities_are_finite_matrix_norms_only():
    ops = build_observables(12, f_count=2, x_count=1)
    P = random_projector(12, 3, seed=0)
    entries = nested_commutator_norms(P, ops, max_order=2)
    for e in entries:
        assert e["norm"] == e["norm"]  # not NaN
        assert e["norm"] < float("inf")


def test_adversarial_projector_beats_or_matches_the_other_families():
    report = scaling_study(dims=[16], max_order=1, rank=3, seed=0)
    fam = report.projector_family_comparison
    assert fam["adversarial"] >= max(fam["random"], fam["smooth"], fam["localized"]) - 1e-6


def test_scaling_study_runs_across_dimensions_and_orders():
    report = scaling_study(dims=[8, 16, 24], max_order=2, rank=3, seed=0)
    assert set(report.dimension_scaling.keys()) == {8, 16, 24}
    assert set(report.order_scaling.keys()) == {0, 1, 2}
    # order-0 is just ||P||, should be sqrt(rank) exactly (idempotent projector trace)
    assert abs(report.order_scaling[0] - 3**0.5) < 1e-6
