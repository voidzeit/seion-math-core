from __future__ import annotations

from spectral.certification_v18.blocks.block_i_reduced_tensor import (
    exact_rational_small_case,
    extraction_parity_report,
)


def test_loop_and_einsum_extraction_agree_float64():
    report = extraction_parity_report(seed=0, n=12, rank=3, cp_rank=4)
    assert report.max_rel_diff_float64 < 1e-10


def test_loop_and_einsum_extraction_agree_float32():
    report = extraction_parity_report(seed=0, n=12, rank=3, cp_rank=4)
    assert report.max_rel_diff_float32 < 1e-4


def test_exact_rational_small_case_matches_hand_computation():
    result = exact_rational_small_case()
    assert result["exact_match"], result
