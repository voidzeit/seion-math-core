"""Analytic family and proof diagnostics; no automatic theorem approval.

Formula and dilation proof: CHAIN_GRAM_REPORT.md, advisory pending review.
"""

import math
import numpy as np


def chain4_formula(eta):
    if not 0 < eta <= 1:
        raise ValueError("require 0 < eta <= 1")
    t = min(eta, math.sqrt(3/7))
    return t*math.sqrt(9-15*t*t+7*t**4)/eta


def isometric_dilation(operators, projectors):
    """Finite dilation retaining original coordinates and full closure caps.

    B_j=A_j pi_(j-1), V_j=(B_j,sqrt(I-B_j*B_j)), P'_j=P_j direct-sum I.
    This is a numerical diagnostic of the analytic construction, not an
    interval certificate. Small negative eigenvalues are clipped only within
    the stated 1e-10 diagnostic tolerance.
    """
    if not operators or len(operators) != len(projectors):
        raise ValueError("equal nonempty stage lists required")
    dimension = operators[0].shape[1]
    vs, ps = [], []
    for a, p in zip(operators, projectors):
        b = np.zeros((a.shape[0], dimension), dtype=np.result_type(a, p))
        b[:, :a.shape[1]] = a
        eig, u = np.linalg.eigh(np.eye(dimension)-b.conj().T@b)
        if eig.min() < -1e-10:
            raise ValueError("dilation requires contractions")
        defect = (u*np.sqrt(np.maximum(0, eig)))@u.conj().T
        v = np.vstack((b, defect))
        pp = np.zeros((v.shape[0], v.shape[0]), dtype=v.dtype)
        pp[:len(p), :len(p)] = p
        pp[len(p):, len(p):] = np.eye(dimension)
        vs.append(v)
        ps.append(pp)
        dimension = len(pp)
    return vs, ps
