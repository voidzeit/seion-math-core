from __future__ import annotations

from spectral.certification_v18.blocks.block_n_cyclic_gji import cyclic_and_gji_report


def test_raw_defect_is_much_larger_than_symmetrized_defect():
    """The core finding this block must report: near-zero cyclic defect
    after explicit averaging is a construction identity, not evidence of a
    learned symmetry. The RAW (pre-averaging) defect must be substantially
    larger."""
    report = cyclic_and_gji_report(seed=0, n=12, rank=3, cp_rank=3, trials=50, adversarial_steps=30)
    assert report.raw_defect_mean > 1e-3
    assert report.symmetrized_defect_mean < 1e-10
    assert report.raw_defect_mean > 1e6 * report.symmetrized_defect_mean


def test_two_independent_gji_implementations_agree():
    report = cyclic_and_gji_report(seed=1, n=12, rank=3, cp_rank=3, trials=50, adversarial_steps=30)
    assert report.gji_cross_check_max_rel_diff < 1e-9


def test_mutation_test_detects_a_wrong_sign_convention():
    report = cyclic_and_gji_report(seed=2, n=12, rank=3, cp_rank=3, trials=20, adversarial_steps=10)
    assert report.mutation_test_detects_wrong_sign


def test_adversarial_gji_ratio_at_least_as_large_as_random_mean():
    report = cyclic_and_gji_report(seed=3, n=12, rank=3, cp_rank=3, trials=50, adversarial_steps=60)
    assert report.gji_ratio_adversarial_max >= report.gji_ratio_mean - 1e-9
