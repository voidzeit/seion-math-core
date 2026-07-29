import numpy as np
import pytest

from seion_core.algebra.nary_law import NaryLaw, SparseNaryLaw
from seion_core.exceptions import ShapeError


def test_strict_shapes_and_multilinearity():
    rng = np.random.default_rng(1)
    law = NaryLaw(rng.normal(size=(3, 3, 3, 3)), 3)
    vectors = tuple(rng.normal(size=3) for _ in range(3))
    assert law(*vectors).shape == (3,)
    assert law.multilinearity_residual(vectors, 1) < 1e-12
    with pytest.raises(ShapeError):
        law(np.ones(2), vectors[1], vectors[2])


def test_sparse_dense_parity():
    entries = {(0, 0, 1, 2): 2.0, (2, 1, 0, 1): -1.0}
    sparse = SparseNaryLaw(3, (3, 3, 3), entries)
    dense = sparse.to_dense()
    vectors = (np.array([1.0, 2.0, 3.0]),) * 3
    np.testing.assert_allclose(sparse(*vectors), dense(*vectors))

