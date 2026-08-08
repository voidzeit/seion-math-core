import math

import pytest

from seion_core.research_v5.k2_sharpness import construct_k2_independent_map_saturation


@pytest.mark.parametrize("eta", [0.1, 0.5, math.sqrt(0.5), 1.0])
def test_general_k2_independent_law_class_saturates_projected_bound(eta):
    result = construct_k2_independent_map_saturation(eta)
    assert result.inner_operator_norm == 1.0
    assert result.outer_operator_norm == 1.0
    assert result.inner_closure_norm == eta
    assert result.outer_closure_norm == 0.0
    assert result.projected_error == pytest.approx(eta)
    assert result.universal_projected_bound == pytest.approx(eta)
    assert result.normalized_ratio == pytest.approx(1.0)


def test_k2_saturation_scales_homogeneously_with_M():
    result = construct_k2_independent_map_saturation(0.3, M=4.0)
    assert result.rho == pytest.approx(1.2)
    assert result.projected_error == pytest.approx(4.8)
    assert result.normalized_ratio == pytest.approx(1.0)


def test_k2_saturation_rejects_out_of_domain_parameters():
    with pytest.raises(ValueError):
        construct_k2_independent_map_saturation(0.0)
    with pytest.raises(ValueError):
        construct_k2_independent_map_saturation(1.1)
    with pytest.raises(ValueError):
        construct_k2_independent_map_saturation(0.5, M=0.0)
