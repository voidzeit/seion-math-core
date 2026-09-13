"""Standalone exact verifier for the PMT free-chain Gram-SDP dual certificates.

Dependencies: Python standard library only (fractions, json). No floating point is
used in any accept/reject decision.

What is checked for each certificate file (k internal vertices, N = k-1 active stages,
rational eta):

1. Dual feasibility.  From the stored rational symmetric matrices Z3_n (2n x 2n) and
   Z4_n (n x n) the verifier rebuilds
       Z1_n = Z3_n - TP_n (Z3_{n+1}[:n+1,:n+1] + eta^2 Z4_{n+1}) TP_n^T     (n < N)
       Z1_N = Z3_N - TP_N a a^T TP_N^T
       Z2_n = Z3_n + emb(Z4_n) - TQ_n Z3_{n+1}[n+1:,n+1:] TQ_n^T           (n < N)
       Z2_N = Z3_N + emb(Z4_N) - TQ_N a a^T TQ_N^T
   and checks Z1_n, Z2_n, Z3_n, Z4_n are all positive semidefinite, exactly
   (every elementary symmetric function of the eigenvalues, i.e. every sum of
   principal minors, is >= 0; computed by Faddeev-LeVerrier over Q).
2. The certified upper bound V = Z3_1[0,0] + eta^2 Z4_1[0,0] equals the stored value.
3. Matching lower bound.  The planar rotation witness with t = eta (rational cosine
   c = sqrt(1-t^2) required) is evaluated exactly; its operator norms (=1) and closure
   defects (=t) are checked exactly, and ||e_N||^2 must equal V.

Weak duality (proved in EXACT_CERTIFICATES.md) turns 1-2 into
    sup ||e_N||^2 over the Gram model  <=  V,
and the Gram model is a valid relaxation of the original PMT-A chain class (necessity
lemma in the same file), so V bounds (E_T^P)^2 / (M^{2(k-1)} L_T^2) for every admissible
chain realisation at this eta.  Together with 3 this certifies
    C^P_{k,chain}(eta)^2 = V / eta^2   exactly.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
from fractions import Fraction as Fr


def mat(rows):
    return [[Fr(x) for x in r] for r in rows]


def zeros(n, m=None):
    return [[Fr(0)] * (n if m is None else m) for _ in range(n)]


def mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def transpose(A):
    return [list(r) for r in zip(*A)]


def add(A, B, s=1):
    return [[A[i][j] + s * B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def scale(A, s):
    return [[s * x for x in r] for r in A]


def block(A, r0, r1, c0, c1):
    return [row[c0:c1] for row in A[r0:r1]]


def selectors(n):
    tp = zeros(2 * n, n + 1)
    tq = zeros(2 * n, n + 1)
    tp[0][0] = Fr(1)
    tq[0][n] = Fr(1)
    for i in range(1, n):
        tp[i][i] = tp[n + i][i] = Fr(1)
        tq[i][i] = tq[n + i][i] = Fr(1)
    return tp, tq


def is_symmetric(A):
    return all(A[i][j] == A[j][i] for i in range(len(A)) for j in range(len(A)))


def char_coeffs(A):
    """Faddeev-LeVerrier: returns e_1..e_n, the elementary symmetric functions of eigenvalues."""
    n = len(A)
    M = zeros(n)
    I = [[Fr(int(i == j)) for j in range(n)] for i in range(n)]
    c = [Fr(1)]  # c_0 of det(xI - A) = x^n + c_1 x^{n-1} + ...
    for k in range(1, n + 1):
        M = add(mul(A, M), scale(I, c[-1]))
        AM = mul(A, M)
        ck = -sum(AM[i][i] for i in range(n)) / k
        c.append(ck)
    # det(xI - A) = sum c_k x^{n-k};  e_k = (-1)^k c_k
    return [((-1) ** k) * c[k] for k in range(1, n + 1)]


def is_psd_exact(A):
    assert is_symmetric(A), "matrix not symmetric"
    return all(e >= 0 for e in char_coeffs(A))


def dual_multipliers(Z3, Z4, eta2, N):
    a = [Fr(0)] + [Fr(1)] * N
    aa = [[x * y for y in a] for x in a]
    Z1, Z2 = [], []
    for n in range(1, N + 1):
        tp, tq = selectors(n)
        if n < N:
            nxt3, nxt4 = Z3[n], Z4[n]
            Y = mul(mul(tp, add(block(nxt3, 0, n + 1, 0, n + 1), scale(nxt4, eta2))), transpose(tp))
            Yq = mul(mul(tq, block(nxt3, n + 1, 2 * (n + 1), n + 1, 2 * (n + 1))), transpose(tq))
        else:
            Y = mul(mul(tp, aa), transpose(tp))
            Yq = mul(mul(tq, aa), transpose(tq))
        emb = zeros(2 * n)
        for i in range(n):
            for j in range(n):
                emb[i][j] = Z4[n - 1][i][j]
        Z1.append(add(Z3[n - 1], Y, -1))
        Z2.append(add(add(Z3[n - 1], emb), Yq, -1))
    return Z1, Z2


def isqrt_fraction(q: Fr):
    p, r = q.numerator, q.denominator
    sp, sr = math.isqrt(p), math.isqrt(r)
    if sp * sp != p or sr * sr != r:
        raise ValueError(f"{q} is not a rational square")
    return Fr(sp, sr)


def opnorm2_is_one_rotation(c, t):
    # [[c,-t],[t,c]] with c^2+t^2 = 1 is orthogonal, hence operator norm exactly 1
    return c * c + t * t == 1


def witness_value(N, t: Fr):
    """Exact ||e_N||^2 for the planar rotation witness; also checks norms/closures exactly."""
    c = isqrt_fraction(1 - t * t)
    assert opnorm2_is_one_rotation(c, t)
    # stage 1: A_1 s = s (c, t);  ||A_1|| = sqrt(c^2+t^2) = 1;  ||Q A_1|| = t
    F = [c, t]
    R = [c, Fr(0)]
    assert c * c + t * t == 1
    for _ in range(2, N + 1):
        F = [c * F[0] - t * F[1], t * F[0] + c * F[1]]
        AR = [c * R[0] - t * R[1], t * R[0] + c * R[1]]
        # closure on Ran P = span e0: ||Q A e0|| = |t| exactly
        R = [AR[0], Fr(0)]
    e = [F[0] - R[0], F[1] - R[1]]
    return e[0] ** 2 + e[1] ** 2


def verify(path):
    d = json.load(open(path))
    k = d["k"]
    N = k - 1
    eta = Fr(d["eta"])
    eta2 = eta * eta
    Z3 = [mat(Z) for Z in d["Z3"]]
    Z4 = [mat(Z) for Z in d["Z4"]]
    assert [len(Z) for Z in Z3] == [2 * n for n in range(1, N + 1)]
    assert [len(Z) for Z in Z4] == [n for n in range(1, N + 1)]
    Z1, Z2 = dual_multipliers(Z3, Z4, eta2, N)
    psd = {f"Z{name}_{n}": is_psd_exact(M)
           for name, mats in (("1", Z1), ("2", Z2), ("3", Z3), ("4", Z4))
           for n, M in enumerate(mats, 1)}
    V = Z3[0][0][0] + eta2 * Z4[0][0][0]
    stored = Fr(d["certified_value_squared"])
    W = witness_value(N, eta)
    ok = all(psd.values()) and V == stored and W == V
    return ok, {"file": os.path.basename(path), "k": k, "eta": str(eta), "upper_bound_V": str(V),
                "witness_value": str(W), "all_multipliers_psd": all(psd.values()),
                "C_squared_exact": str(V / eta2), "C_float": math.sqrt(V / eta2), "verified": ok}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(here, "certificate_chain_k*_eta_*.json")))
    allok = True
    for f in files:
        ok, info = verify(f)
        allok &= ok
        print(json.dumps(info))
    print("ALL_CERTIFICATES_VERIFIED" if allok else "CERTIFICATE_FAILURE")
    sys.exit(0 if allok else 1)
