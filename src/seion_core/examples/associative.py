from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw


def coordinatewise_associative_law(dimension: int = 3, dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((dimension,) * 4, dtype=dtype)
    for i in range(dimension):
        tensor[i, i, i, i] = 1.0
    return TernaryLaw(tensor, "coordinatewise_associative_ternary")


def matrix_algebra_ternary_law(dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((4, 4, 4, 4), dtype=dtype)
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    for e in range(2):
                        for f in range(2):
                            out = 2 * a + f
                            i = 2 * a + b
                            j = 2 * c + d
                            k = 2 * e + f
                            if out < 4 and i < 4 and j < 4 and k < 4:
                                # (E_ab E_cd) E_ef = delta_bc delta_de E_af
                                if b == c and d == e:
                                    tensor[out, i, j, k] += 1.0
    return TernaryLaw(tensor, "matrix_algebra_ternary")


def lie_derived_law(dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((3, 3, 3, 3), dtype=dtype)
    basis = np.eye(3, dtype=dtype)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                tensor[:, i, j, k] = np.cross(np.cross(basis[:, i], basis[:, j]), basis[:, k])
    return TernaryLaw(tensor, "lie_derived_cross_product")

