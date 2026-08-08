"""M10: proof that the M9 upper envelope U_3(eta) is not attained.

Core lemma (standard fact about operator-norm-attaining directions,
applied twice to derive a new consequence for this specific extremal
problem): if a linear map N has operator norm <= M and attains this bound
EXACTLY at a unit direction u-hat, then N(u-hat) is orthogonal to N(v-hat)
for any v-hat orthogonal to u-hat. Proof: f(psi):=||N(cos(psi)u-hat +
sin(psi)v-hat)||^2 has a maximum at psi=0 (since u-hat attains the global
max), so f'(0)=0, which expands to 2*<N(u-hat),N(v-hat)>=0.

Applying this at node 2 (with u-hat=D1/||D1||, v-hat=R1/||R1||, orthogonal
by the Pythagorean split of the k3_upper_bound.py derivation) shows: if T1
saturates exactly (mu2 attains M at D1's direction), then S1 and S2 are
forced orthogonal. Applying it again at node 3 (with u-hat=S1/||S1||,
v-hat=S2/||S2||) shows: if T1 *also* saturates at node 3 (mu3 attains M at
S1's direction), then mu3(S1,d) is forced orthogonal to mu3(S2,d) -- which
directly contradicts the triangle-inequality equality (parallel vectors)
needed for E_P to equal T1+T2. Hence h(q) -- and therefore U_3(eta) -- is
never exactly attained for q in (0,rho) (where both terms are active,
which is the generic/optimal case for every eta in (0,1)).

This proves C_3,ind^P(eta) < U_3(eta) strictly for every eta in (0,1). It
does NOT determine the exact tightened value -- that requires solving a
genuine joint trade-off optimization (how much of T1's saturation to give
up to reduce the forced-orthogonality penalty) not solved in this pass.
"""

from __future__ import annotations

import numpy as np


def forced_orthogonality_holds(
    N: np.ndarray, u_hat: np.ndarray, v_hat: np.ndarray, *, tol: float = 1e-9
) -> bool:
    """Check the lemma's conclusion for a linear map N (matrix) and an
    orthonormal pair (u_hat, v_hat), GIVEN u_hat attains N's operator norm.

    Returns True iff <N u_hat, N v_hat> ~ 0. Raises if the orthonormality
    precondition or the "u_hat attains the operator norm" precondition is
    violated (the lemma's hypothesis, not its conclusion).
    """

    if abs(float(np.dot(u_hat, v_hat))) > tol:
        raise ValueError("u_hat, v_hat must be orthonormal")
    Nu = N @ u_hat
    Nv = N @ v_hat
    # Verify the precondition: u_hat attains ||N||_op (checked via a fine
    # angular sweep in the (u_hat, v_hat) plane -- sufficient since the
    # lemma only concerns behaviour restricted to this 2D subspace).
    angles = np.linspace(0.0, 2 * np.pi, 4001)
    vals = [
        np.linalg.norm(np.cos(t) * Nu + np.sin(t) * Nv) for t in angles
    ]
    if max(vals) > np.linalg.norm(Nu) + tol:
        raise ValueError("u_hat does not attain the operator norm on span(u_hat, v_hat)")
    return abs(float(np.dot(Nu, Nv))) < tol * max(1.0, np.linalg.norm(Nu) * np.linalg.norm(Nv))


def pareto_frontier_two_direction_norm_budget(
    angle: float, ratio: float, *, M: float = 1.0
) -> float:
    """Maximum joint scale factor k such that P0=k, R0=k*ratio (two vectors
    at the given angle, magnitude ratio ``ratio``) can be realized as
    N(u_hat), N(v_hat) for some linear N with ||N||_op<=M.

    This is exactly the largest eigenvalue condition described in the
    module docstring's "genuine trade-off" discussion: the 2x2 Gram matrix
    [[P0^2, P0*R0*cos(angle)], [P0*R0*cos(angle), R0^2]] must have largest
    eigenvalue <= M^2. Returns the largest feasible k (P0=k caps the pair).
    Quantifies, but does not by itself solve, the joint (q, angle)
    trade-off left open by this session's non-sharpness proof.
    """

    if not 0.0 <= angle <= np.pi or ratio < 0.0 or M <= 0.0:
        raise ValueError("require 0<=angle<=pi, ratio>=0, M>0")
    c = np.cos(angle)
    # Gram matrix for (k, k*ratio) at this angle, per unit k^2:
    a11, a22, a12 = 1.0, ratio * ratio, ratio * c
    trace = a11 + a22
    det = a11 * a22 - a12 * a12
    lam_max_per_k2 = (trace + np.sqrt(max(0.0, trace * trace - 4.0 * det))) / 2.0
    if lam_max_per_k2 <= 0.0:
        return float("inf")
    return float(M / np.sqrt(lam_max_per_k2))
