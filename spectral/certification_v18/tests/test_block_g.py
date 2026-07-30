from __future__ import annotations

from spectral.certification_v18.blocks.block_g_closure import closure_report, exact_arity3_zero_case


def test_exact_zero_law_closes_exactly():
    defect = exact_arity3_zero_case()
    assert defect < 1e-20


def test_closure_report_has_consistent_statistics():
    report = closure_report(seed=0, n=16, rank=4, cp_rank=4, n_samples=500, adversarial_steps=30)
    assert report.quantiles[0.5] <= report.quantiles[0.9] <= report.quantiles[0.99] <= report.worst + 1e-9
    assert report.mean >= 0
    assert report.mean_upper_confidence_bound_95 >= report.mean


def test_adversarial_search_finds_at_least_as_bad_as_random_worst():
    report = closure_report(seed=1, n=16, rank=4, cp_rank=4, n_samples=200, adversarial_steps=100)
    assert report.adversarial_worst >= report.worst - 1e-9, (
        "adversarial gradient ascent should find a defect at least as large as the best random sample found"
    )
