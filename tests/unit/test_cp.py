import numpy as np

from seion_core.algebra.cp_law import CPLaw
from seion_core.examples.rank_one import rank_one_law


def test_rank_one_cp_dense_parity():
    cp = rank_one_law(3)
    dense = cp.to_dense()
    rng = np.random.default_rng(8)
    vectors = tuple(rng.normal(size=3) for _ in range(3))
    np.testing.assert_allclose(cp(*vectors), dense(*vectors), rtol=1e-12, atol=1e-12)


def test_gauge_transform_preserves_law():
    cp = rank_one_law(3)
    transformed = cp.gauge_transform([np.array([2.0]), np.array([0.5]), np.array([1.0]), np.array([1.0])])
    np.testing.assert_allclose(cp.to_dense().tensor, transformed.to_dense().tensor)

