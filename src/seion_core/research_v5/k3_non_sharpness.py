"""M10: proof that the M9 upper envelope U_3(eta) is not attained.

REVISED after review found two errors in the first version (see
research/math_closure/k3/m10_non_sharpness_of_m9.tex for the full
corrected proof and V5_CLOSURE_REPORT.md for the record):

1. The original Step 1 claimed S1 is orthogonal to S2 =(I-P2)mu2(R1,c).
   That does not follow from the base lemma alone: the lemma only gives
   S1 perp B, where B:=mu2(R1,c) is the UNPROJECTED precursor: projecting
   an orthogonal-to-S1 vector does not preserve orthogonality to S1 in
   general. The repaired argument (`precursor_never_parallel_after_
   projection` below) proves the weaker but sufficient fact that S2 is
   never a nonzero scalar multiple of S1 -- via a self-adjointness
   argument that works for ANY projector, not a specifically constructed
   one.
2. The original conclusion overclaimed C_3,ind^P(eta) < U_3(eta) (a
   strict SUPREMUM inequality) from a NON-ATTAINMENT fact (no single
   configuration reaches U_3(eta)) alone. These are logically different:
   a supremum can be approached without being attained (sup_{0<x<1} x = 1
   even though no x<1 equals 1). Only PROVED_NON_ATTAINMENT is
   established here; the strict inequality remains OPEN pending either a
   compactness argument or an explicit quantitative gap (see
   `pareto_frontier_two_direction_norm_budget` below, and the tex proof's
   "Route A / Route B" discussion).

Core lemma (standard fact about operator-norm-attaining directions): if a
linear map N has operator norm <= M and attains this bound EXACTLY at a
unit direction u-hat, then N(u-hat) is orthogonal to N(v-hat) for any
v-hat orthogonal to u-hat. Proof: f(psi):=||N(cos(psi)u-hat +
sin(psi)v-hat)||^2 has a maximum at psi=0 (since u-hat attains the global
max), so f'(0)=0, which expands to 2*<N(u-hat),N(v-hat)>=0.
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


def precursor_never_parallel_after_projection(
    N: np.ndarray,
    u_hat: np.ndarray,
    v_hat: np.ndarray,
    Q: np.ndarray,
    *,
    tol: float = 1e-9,
) -> bool:
    """Repaired Step-1 check (M10, node 2): given N attains ||N||_op=M
    exactly at u_hat (so S1:=N(u_hat) perp B:=N(v_hat) by the base lemma),
    and Q is ANY orthogonal projector, verify S2:=Q@B is never a nonzero
    scalar multiple of S1.

    Proof (see the .tex file for the full writeup): if S2=lambda*S1 with
    lambda!=0, then S1 in Range(Q) (since S2 is and Range(Q) is a
    subspace), so Q@S1=S1; using Q self-adjoint, <S2,S1> = <QB,S1> =
    <B,Q@S1> = <B,S1> = 0 (S1 perp B from the base lemma) -- but also
    <S2,S1> = lambda*||S1||^2 != 0, a contradiction. Works for ANY Q, not
    a specifically constructed one -- this is the fix for the original
    version's unjustified "S1 perp S2" claim.

    Returns True (the claim holds) or raises if S1==0 (degenerate,
    nothing to check) or if the "u_hat attains the operator norm"
    precondition fails.
    """

    if abs(float(np.dot(u_hat, v_hat))) > tol:
        raise ValueError("u_hat, v_hat must be orthonormal")
    S1 = N @ u_hat
    if np.linalg.norm(S1) < tol:
        raise ValueError("S1 is (numerically) zero; nothing to check")
    B = N @ v_hat
    angles = np.linspace(0.0, 2 * np.pi, 4001)
    vals = [np.linalg.norm(np.cos(t) * S1 + np.sin(t) * B) for t in angles]
    if max(vals) > np.linalg.norm(S1) + tol:
        raise ValueError("u_hat does not attain the operator norm on span(u_hat, v_hat)")
    S2 = Q @ B
    if np.linalg.norm(S2) < tol:
        return True  # S2 is zero: trivially "not a nonzero multiple" of S1
    cos_angle = abs(float(np.dot(S1, S2))) / (np.linalg.norm(S1) * np.linalg.norm(S2))
    return cos_angle < 1.0 - tol


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
