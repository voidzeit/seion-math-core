from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw


def curried_operator(law: TernaryLaw, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Return the matrix of ``z -> mu(x,y,z)`` in the standard basis."""
    x = np.asarray(x)
    y = np.asarray(y)
    if law.input_dims != (law.output_dim,) * 3:
        raise ValueError("curried operator requires a common internal space")
    basis = np.eye(law.output_dim, dtype=np.result_type(law.tensor, x, y))
    return np.column_stack([law(x, y, basis[:, j]) for j in range(law.output_dim)])


def anchored_left_operator(law: TernaryLaw, anchor: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Matrix of ``z -> x circ_anchor z = mu(x,z,anchor)``."""
    basis = np.eye(law.output_dim, dtype=np.result_type(law.tensor, anchor, x))
    return np.column_stack([law(x, basis[:, j], anchor) for j in range(law.output_dim)])

