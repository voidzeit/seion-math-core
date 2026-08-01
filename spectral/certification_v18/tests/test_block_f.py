from __future__ import annotations

from spectral.certification_v18.blocks.block_f_rigidity import small_case_curvature_report


def test_finite_difference_matches_exact_hessian():
    report = small_case_curvature_report(seed=0, n=6, rank=2, cp_rank=2)
    assert report.finite_diff_vs_exact_rel_error < 1e-2


def test_ggn_eigenvalues_are_nonnegative_unlike_exact_hessian_which_need_not_be():
    report = small_case_curvature_report(seed=0, n=6, rank=2, cp_rank=2)
    assert all(v >= -1e-8 for v in report.ggn_eigvals), "GGN = J^T J (scaled) must be PSD by construction"


def test_gauge_rotation_leaves_loss_invariant():
    report = small_case_curvature_report(seed=1, n=6, rank=2, cp_rank=2)
    assert report.gauge_direction_loss_invariance < 1e-10


def test_gauge_direction_has_small_hessian_curvature():
    """The direction corresponding to an infinitesimal gauge rotation
    should show near-zero curvature in the exact Hessian — a flat
    direction, consistent with identifiability only modulo gauge."""
    report = small_case_curvature_report(seed=1, n=6, rank=2, cp_rank=2)
    scale = max(abs(v) for v in report.exact_hessian_eigvals) + 1e-12
    assert abs(report.gauge_direction_hessian_eigval) < 0.1 * scale


def test_basin_stability_reports_multiple_seeds():
    report = small_case_curvature_report(seed=0, n=6, rank=2, cp_rank=2)
    assert len(report.basin_final_losses) == 3
    assert report.basin_pairwise_max_principal_angle >= 0.0
