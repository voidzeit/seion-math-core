import numpy as np
import pytest

from seion_core.algebra.nary_law import NaryLaw
from seion_core.algebra.ternary_law import TernaryLaw
from seion_core.exceptions import ShapeError
from seion_core.geometry.affine_connection import (
    affine_curvature,
    affine_curvature_on_vectors,
    anchored_bilinear_law,
    curvature_components,
    curvature_metric_integrability_residual,
    curvature_torsion_associator_components,
    curvature_torsion_associator_residual,
    metric_compatibility_residual,
    torsion_components,
)
from seion_core.geometry.induced_curvature import curvature_operator


def test_affine_curvature_identity_holds_in_vectors_and_coordinates():
    rng = np.random.default_rng(20260909)
    product = NaryLaw(rng.normal(size=(3, 3, 3)), arity=2)
    x, y, z = (rng.normal(size=3) for _ in range(3))

    np.testing.assert_allclose(
        curvature_torsion_associator_residual(product, x, y, z), 0.0, atol=1e-12
    )
    np.testing.assert_allclose(
        curvature_torsion_associator_components(product), 0.0, atol=1e-12
    )

    coordinates = np.einsum("iljk,l,j,k->i", curvature_components(product), z, x, y)
    np.testing.assert_allclose(coordinates, affine_curvature_on_vectors(product, x, y, z))


def test_affine_and_standard_curvature_are_distinct_conventions():
    # Associative, non-commutative 2x2 matrix algebra represented on R^4.
    tensor = np.zeros((4, 4, 4))
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for ell in range(2):
                    left = 2 * i + j
                    right = 2 * k + ell
                    output = 2 * i + ell
                    if j == k:
                        tensor[output, left, right] = 1.0
    product = NaryLaw(tensor, arity=2)
    x = np.array([1.0, 2.0, -1.0, 0.5])
    y = np.array([0.0, 1.0, 2.0, -0.5])
    bracket = product(x, y) - product(y, x)
    left_bracket = np.column_stack(
        [product(bracket, np.eye(4)[:, j]) for j in range(4)]
    )
    np.testing.assert_allclose(
        affine_curvature(product, x, y), curvature_operator(
            np.column_stack([product(x, np.eye(4)[:, j]) for j in range(4)]),
            np.column_stack([product(y, np.eye(4)[:, j]) for j in range(4)]),
            left_bracket,
        ) + left_bracket
    )


def test_constant_metric_and_variable_metric_conditions():
    a = 2.5
    product = NaryLaw(np.array([[[a]]]), arity=2)
    metric = np.array([[np.exp(2.0 * a)]])
    derivative = np.array([[[2.0 * a * metric[0, 0]]]])

    np.testing.assert_allclose(
        metric_compatibility_residual(product, metric, derivative), 0.0, atol=1e-12
    )
    np.testing.assert_allclose(
        curvature_metric_integrability_residual(product, metric), 0.0, atol=1e-12
    )


def test_anchored_ternary_law_matches_direct_contraction():
    rng = np.random.default_rng(7)
    tensor = rng.normal(size=(2, 2, 2, 2))
    ternary = TernaryLaw(tensor)
    anchor = np.array([0.25, -0.75])
    anchored = anchored_bilinear_law(ternary, anchor)
    expected = np.tensordot(tensor, anchor, axes=([3], [0]))

    np.testing.assert_allclose(anchored.tensor, expected)
    x, y, z = (rng.normal(size=2) for _ in range(3))
    np.testing.assert_allclose(
        curvature_torsion_associator_residual(anchored, x, y, z), 0.0, atol=1e-12
    )


def test_bilinear_contract_rejects_non_square_laws():
    with pytest.raises(ShapeError):
        affine_curvature(NaryLaw(np.zeros((2, 3, 3)), arity=2), np.ones(2), np.ones(2))


def test_commutative_nonassociative_product_can_still_be_curved():
    tensor = np.zeros((2, 2, 2))
    tensor[0, 0, 0] = 1.0  # e0 star e0 = e0
    tensor[0, 1, 1] = 1.0  # e1 star e1 = e0
    product = NaryLaw(tensor, arity=2)
    x = np.array([1.0, 0.0])
    y = np.array([0.0, 1.0])

    np.testing.assert_allclose(torsion_components(product), 0.0)
    assert np.linalg.norm(affine_curvature(product, x, y)) > 0.0
