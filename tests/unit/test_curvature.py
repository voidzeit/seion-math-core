import numpy as np

from seion_core.geometry.induced_curvature import standard_curvature_residual


def test_standard_curvature_associator_expansion():
    # A non-associative bilinear product represented by a dense rank-3 tensor.
    tensor = np.zeros((2, 2, 2))
    tensor[0, 0, 1] = 1.0
    tensor[1, 1, 0] = -0.5

    def product(x, y):
        return np.einsum("aij,i,j->a", tensor, x, y)

    x = np.array([1.0, 0.2]); y = np.array([-0.3, 0.7]); z = np.array([0.4, -0.5])
    np.testing.assert_allclose(standard_curvature_residual(product, x, y, z), 0.0, atol=1e-12)

