"""Affine connections induced by finite-dimensional bilinear products.

For a square bilinear law ``star`` on ``V`` this module implements the
connection ``nabla_X Y = D_X Y + X star Y`` on the affine space ``A(V)``.
The geometric curvature of this connection is

    R_affine(x, y) = [L_x, L_y]

for constant vector fields.  This is intentionally separate from
``induced_curvature.curvature_operator``, whose ``R_standard`` convention
also subtracts ``L_[x,y]``.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np

from ..algebra.nary_law import NaryLaw
from ..algebra.ternary_law import TernaryLaw
from ..exceptions import ShapeError


BilinearInput: TypeAlias = NaryLaw | np.ndarray


def _as_bilinear_law(product: BilinearInput) -> NaryLaw:
    """Normalize an array or ``NaryLaw`` and require a square internal law."""
    law = product if isinstance(product, NaryLaw) else NaryLaw(np.asarray(product), arity=2)
    if law.arity != 2:
        raise ShapeError("affine connection requires a bilinear law")
    if law.input_dims != (law.output_dim, law.output_dim):
        raise ShapeError(
            "affine connection requires a product V x V -> V with equal dimensions; "
            f"got output_dim={law.output_dim}, input_dims={law.input_dims}"
        )
    return law


def _vector(value: np.ndarray, dimension: int, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or array.shape[0] != dimension:
        raise ShapeError(f"{name} must have shape ({dimension},), got {array.shape}")
    return array


def left_multiplication(product: BilinearInput, x: np.ndarray) -> np.ndarray:
    """Return the matrix of ``L_x(z) = x star z`` in the standard basis."""
    law = _as_bilinear_law(product)
    x = _vector(x, law.output_dim, "x")
    basis = np.eye(law.output_dim, dtype=np.result_type(law.tensor, x))
    return np.column_stack([law(x, basis[:, j]) for j in range(law.output_dim)])


def product_commutator(product: BilinearInput, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Return ``[x,y]_star = x star y - y star x``."""
    law = _as_bilinear_law(product)
    x = _vector(x, law.output_dim, "x")
    y = _vector(y, law.output_dim, "y")
    return law(x, y) - law(y, x)


def associator(
    product: BilinearInput, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> np.ndarray:
    """Return ``A(x,y,z) = (x star y) star z - x star (y star z)``."""
    law = _as_bilinear_law(product)
    x = _vector(x, law.output_dim, "x")
    y = _vector(y, law.output_dim, "y")
    z = _vector(z, law.output_dim, "z")
    return law(law(x, y), z) - law(x, law(y, z))


def antisymmetrized_associator(
    product: BilinearInput, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> np.ndarray:
    """Return ``A^-(x,y,z) = A(x,y,z) - A(y,x,z)``."""
    return associator(product, x, y, z) - associator(product, y, x, z)


def affine_torsion(product: BilinearInput, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Return the torsion of ``D + star`` on constant vectors."""
    return product_commutator(product, x, y)


def affine_curvature(product: BilinearInput, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Return the matrix ``R^nabla(x,y) = [L_x,L_y]``."""
    lx = left_multiplication(product, x)
    ly = left_multiplication(product, y)
    return lx @ ly - ly @ lx


def affine_curvature_on_vectors(
    product: BilinearInput, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> np.ndarray:
    """Apply the affine curvature operator to ``z``."""
    law = _as_bilinear_law(product)
    z = _vector(z, law.output_dim, "z")
    return affine_curvature(product, x, y) @ z


def curvature_torsion_associator_residual(
    product: BilinearInput, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> np.ndarray:
    """Return the exact identity residual ``R - (T star z - A^-)``."""
    law = _as_bilinear_law(product)
    lhs = affine_curvature_on_vectors(law, x, y, z)
    torsion_term = law(affine_torsion(law, x, y), z)
    return lhs - (torsion_term - antisymmetrized_associator(law, x, y, z))


def connection_coefficients(product: BilinearInput) -> np.ndarray:
    """Return ``Gamma[i,j,k] = K[i,j,k]`` for ``nabla_ej e_k``."""
    return _as_bilinear_law(product).tensor.copy()


def torsion_components(product: BilinearInput) -> np.ndarray:
    """Return ``T[m,j,k] = K[m,j,k] - K[m,k,j]``."""
    tensor = connection_coefficients(product)
    return tensor - tensor.swapaxes(1, 2)


def associator_components(product: BilinearInput) -> np.ndarray:
    """Return ``A[i,j,k,l]`` in the coordinate convention of the theorem."""
    law = _as_bilinear_law(product)
    return np.einsum("mjk,iml->ijkl", law.tensor, law.tensor) - np.einsum(
        "mkl,ijm->ijkl", law.tensor, law.tensor
    )


def curvature_components(product: BilinearInput) -> np.ndarray:
    """Return ``R[i,l,j,k]`` for ``R(e_j,e_k)e_l``."""
    law = _as_bilinear_law(product)
    return np.einsum("mkl,ijm->iljk", law.tensor, law.tensor) - np.einsum(
        "mjl,ikm->iljk", law.tensor, law.tensor
    )


def curvature_torsion_associator_components(product: BilinearInput) -> np.ndarray:
    """Return the coordinate residual of ``R = T star - A^-``."""
    curvature = curvature_components(product)
    torsion_term = np.einsum("mjk,iml->iljk", torsion_components(product), connection_coefficients(product))
    assoc = associator_components(product)
    assoc_minus = assoc - assoc.swapaxes(1, 2)
    return curvature - (torsion_term - assoc_minus.transpose(0, 3, 1, 2))


def metric_compatibility_residual(
    product: BilinearInput,
    metric: np.ndarray,
    metric_derivatives: np.ndarray | None = None,
    *,
    hermitian: bool = False,
) -> np.ndarray:
    """Return ``d_i G - (L_i^* G + G L_i)`` for a metric field.

    ``metric`` is the matrix ``G`` at a point.  If ``metric_derivatives`` is
    omitted, it is treated as zero, giving the constant-metric condition.
    The derivative array, when supplied, has shape ``(d,d,d)`` with
    ``metric_derivatives[i] = partial_i G``.  ``hermitian=True`` uses the
    conjugate transpose for complex forms.
    """
    law = _as_bilinear_law(product)
    dimension = law.output_dim
    metric = np.asarray(metric)
    if metric.shape != (dimension, dimension):
        raise ShapeError(f"metric must have shape ({dimension}, {dimension}), got {metric.shape}")
    derivatives = np.zeros((dimension, dimension, dimension), dtype=np.result_type(metric, law.tensor))
    if metric_derivatives is not None:
        supplied = np.asarray(metric_derivatives)
        if supplied.shape != derivatives.shape:
            raise ShapeError(
                f"metric_derivatives must have shape {derivatives.shape}, got {supplied.shape}"
            )
        derivatives = supplied
    result = np.empty_like(derivatives, dtype=np.result_type(derivatives, law.tensor))
    for i in range(dimension):
        left = left_multiplication(law, np.eye(dimension, dtype=result.dtype)[i])
        adjoint = left.conj().T if hermitian else left.T
        result[i] = derivatives[i] - (adjoint @ metric + metric @ left)
    return result


def curvature_metric_integrability_residual(
    product: BilinearInput, metric: np.ndarray, *, hermitian: bool = False
) -> np.ndarray:
    """Return ``R_jk^* G + G R_jk`` for the parallel-metric integrability test."""
    law = _as_bilinear_law(product)
    metric = np.asarray(metric)
    dimension = law.output_dim
    if metric.shape != (dimension, dimension):
        raise ShapeError(f"metric must have shape ({dimension}, {dimension}), got {metric.shape}")
    curvature = curvature_components(law)
    result = np.empty((dimension, dimension, dimension, dimension), dtype=np.result_type(metric, curvature))
    for j in range(dimension):
        for k in range(dimension):
            operator = curvature[:, :, j, k]
            adjoint = operator.conj().T if hermitian else operator.T
            result[j, k] = adjoint @ metric + metric @ operator
    return result


def anchored_bilinear_law(law: TernaryLaw, anchor: np.ndarray) -> NaryLaw:
    """Freeze the third input of ``mu_3`` to obtain ``x star_u y``."""
    if law.input_dims[:2] != (law.output_dim, law.output_dim):
        raise ShapeError("anchored product requires the first two ternary slots to be V -> V")
    anchor = _vector(anchor, law.input_dims[2], "anchor")
    tensor = np.tensordot(law.tensor, anchor, axes=([3], [0]))
    return NaryLaw(tensor, arity=2, name=f"{law.name}_anchored")

