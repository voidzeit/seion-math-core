from research.math_closure.k3.m21_same_law_tagged_exact_constant import (
    evaluate_tagged_same_law,
    exact_same_law_constant,
    shared_law_certificate,
    verify_tagged_same_law,
)


def test_m21_tagged_same_law_chain_and_branching_attain_w3() -> None:
    assert verify_tagged_same_law()
    for family in ("chain", "branch"):
        error, norm, defect = evaluate_tagged_same_law(0.5, family)
        assert norm == 1.0
        assert defect == min(0.5, (2.0 / 3.0) ** 0.5)
        assert abs(error / 0.5 - exact_same_law_constant(0.5)) < 2.0e-10


def test_m21_structural_direct_sum_certificate_is_computed() -> None:
    for family in ("chain", "branch"):
        norm, defect = shared_law_certificate(0.5, family)
        assert norm == 1.0
        assert defect == 0.5
