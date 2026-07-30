from __future__ import annotations

from spectral.certification_v18.blocks.block_k_hosvd import hosvd_compactness_report


def test_reconstruction_at_rank_needed_is_within_energy_threshold():
    report = hosvd_compactness_report(seed=0, n=16, rank=4, cp_rank=4, energy_threshold=0.99)
    assert report.reconstruction_error_at_rank_needed < 0.2


def test_perturbation_stability_is_small_for_small_perturbation():
    report = hosvd_compactness_report(seed=0, n=16, rank=4, cp_rank=4, perturbation_eps=1e-4)
    assert report.perturbation_max_principal_angle < 0.5


def test_report_includes_random_tensor_control_and_a_verdict():
    report = hosvd_compactness_report(seed=0, n=16, rank=4, cp_rank=4)
    assert len(report.random_tensor_rank_needed_per_mode) == len(report.rank_needed_per_mode)
    assert isinstance(report.real_tensor_more_compact_than_random, bool)
