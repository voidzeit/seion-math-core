from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw


def _quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a0, av = a[0], a[1:]
    b0, bv = b[0], b[1:]
    return np.concatenate(([a0 * b0 - np.dot(av, bv)], a0 * bv + b0 * av + np.cross(av, bv)))


def octonion_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cayley-Dickson product on H + H l with a fixed convention."""
    a = np.asarray(a); b = np.asarray(b)
    if a.shape != (8,) or b.shape != (8,):
        raise ValueError("octonions use eight real coordinates")
    ap, aq = a[:4], a[4:]
    bp, bq = b[:4], b[4:]
    # (p,q)(r,s)=(pr-s*conj(q), conj(p)s+rq)
    conj_q = aq.copy(); conj_q[1:] *= -1
    conj_p = ap.copy(); conj_p[1:] *= -1
    first = _quat_mul(ap, bp) - _quat_mul(bq, conj_q)
    second = _quat_mul(conj_p, bq) + _quat_mul(bp, aq)
    return np.concatenate((first, second))


def octonion_ternary_law(dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((8, 8, 8, 8), dtype=dtype)
    basis = np.eye(8, dtype=dtype)
    for i in range(8):
        for j in range(8):
            for k in range(8):
                tensor[:, i, j, k] = octonion_mul(octonion_mul(basis[:, i], basis[:, j]), basis[:, k])
    return TernaryLaw(tensor, "octonion_left_nested_ternary")

