"""Exact rational dual certificate for the free-chain Gram SDP.

Primal (necessity-valid relaxation of the original PMT chain class):
  stage n = 1..N, HP_n, HQ_n in S^{2n}
    HP_n >= 0, HQ_n >= 0
    diag(GP_{n-1}, GQ_{n-1}) - HP_n - HQ_n >= 0          (contraction)      mult Z3_n
    eta^2 GP_{n-1} - HQ_n[:n,:n] >= 0                    (closure)          mult Z4_n
    GP_n = TP' HP_n TP,  GQ_n = TQ' HQ_n TQ,  GP_0 = [1], GQ_0 = [0]
  maximize a'(GP_N + GQ_N)a,  a = (0,1,...,1).

Dual (weak duality, exact): for any PSD Z3_n, Z4_n put
  Y_n  := TP (Z3_{n+1}[:n+1,:n+1] + eta^2 Z4_{n+1}) TP'     (n<N),  Y_N  := TP aa' TP'
  Yq_n := TQ  Z3_{n+1}[n+1:,n+1:] TQ'                        (n<N),  Yq_N := TQ aa' TQ'
  Z1_n := Z3_n - Y_n,   Z2_n := Z3_n + emb(Z4_n) - Yq_n.
If Z1_n, Z2_n >= 0 then  value <= V := Z3_1[0,0] + eta^2 Z4_1[0,0].
(Proof: obj = sum <Z3,K3> + <Z4,K4> - sum <Z_i, slack_i> - sum <Z1,HP> - <Z2,HQ>.)
"""
from __future__ import annotations
import json, sys
from fractions import Fraction as Fr
import numpy as np
import sympy as sp


def selectors(n):
    tp = np.zeros((2 * n, n + 1), dtype=int); tq = np.zeros_like(tp)
    tp[0, 0] = 1; tq[0, n] = 1
    for i in range(1, n):
        tp[i, i] = tp[n + i, i] = 1
        tq[i, i] = tq[n + i, i] = 1
    return tp, tq


def dual_expressions(Z3, Z4, eta2, N, lib):
    """Return lists Z1, Z2 built from Z3, Z4 (works for cvxpy and sympy)."""
    a = np.ones(N + 1, dtype=int); a[0] = 0
    aa = np.outer(a, a)
    Z1, Z2 = [], []
    for n in range(1, N + 1):
        tp, tq = selectors(n)
        if n < N:
            nxt3, nxt4 = Z3[n], Z4[n]              # stage n+1 (0-based index n)
            if lib == "cvx":
                Y = tp @ (nxt3[: n + 1, : n + 1] + eta2 * nxt4) @ tp.T
                Yq = tq @ nxt3[n + 1:, n + 1:] @ tq.T
            else:
                TP, TQ = sp.Matrix(tp), sp.Matrix(tq)
                Y = TP * (nxt3[: n + 1, : n + 1] + eta2 * nxt4) * TP.T
                Yq = TQ * nxt3[n + 1:, n + 1:] * TQ.T
        else:
            if lib == "cvx":
                Y = tp @ aa @ tp.T; Yq = tq @ aa @ tq.T
            else:
                TP, TQ, AA = sp.Matrix(tp), sp.Matrix(tq), sp.Matrix(aa)
                Y = TP * AA * TP.T; Yq = TQ * AA * TQ.T
        if lib == "cvx":
            import cvxpy as cp
            emb = cp.bmat([[Z4[n - 1], np.zeros((n, n))], [np.zeros((n, n)), np.zeros((n, n))]])
        else:
            emb = sp.zeros(2 * n, 2 * n); emb[:n, :n] = Z4[n - 1]
        Z1.append(Z3[n - 1] - Y)
        Z2.append(Z3[n - 1] + emb - Yq)
    return Z1, Z2


def witness_primal(N, t: Fr):
    """Rational primal point from the planar rotation witness (c = sqrt(1-t^2) must be rational)."""
    c2 = 1 - t * t
    c = sp.sqrt(sp.Rational(c2.numerator, c2.denominator))
    assert c.is_Rational, "choose a Pythagorean t"
    t = sp.Rational(t.numerator, t.denominator)
    A1 = sp.Matrix([[c], [t]])
    Rot = sp.Matrix([[c, -t], [t, c]])
    P = sp.Matrix([[1, 0], [0, 0]]); Q = sp.eye(2) - P
    X = [sp.Matrix([[1]])]                # X_0 = (R_0) in K = R^1
    PX_prev, QX_prev = [sp.Matrix([[1]])], [sp.Matrix([[0]])]
    HP, HQ = [], []
    for n in range(1, N + 1):
        A = A1 if n == 1 else Rot
        L = PX_prev + QX_prev             # list of length 2n
        imgs = [A * v for v in L]
        pl = [P * w for w in imgs]; ql = [Q * w for w in imgs]
        HP.append(sp.Matrix(2 * n, 2 * n, lambda i, j: (pl[i].T * pl[j])[0]))
        HQ.append(sp.Matrix(2 * n, 2 * n, lambda i, j: (ql[i].T * ql[j])[0]))
        tp, tq = selectors(n)
        newX = [sum((int(tp[i, m]) * pl[i] + int(tq[i, m]) * ql[i] for i in range(2 * n)), sp.zeros(2, 1))
                for m in range(n + 1)]
        PX_prev = [P * v for v in newX]; QX_prev = [Q * v for v in newX]
        X = newX
    e = sum(X[1:], sp.zeros(2, 1))
    return HP, HQ, (e.T * e)[0]


def solve_dual_numeric(N, eta2, extra=None):
    import cvxpy as cp
    Z3 = [cp.Variable((2 * n, 2 * n), symmetric=True) for n in range(1, N + 1)]
    Z4 = [cp.Variable((n, n), symmetric=True) for n in range(1, N + 1)]
    Z1, Z2 = dual_expressions(Z3, Z4, eta2, N, "cvx")
    cons = [z >> 0 for z in Z3 + Z4] + [z >> 0 for z in Z1 + Z2]
    if extra:
        cons += extra(Z1, Z2, Z3, Z4)
    V = Z3[0][0, 0] + eta2 * Z4[0][0, 0]
    prob = cp.Problem(cp.Minimize(V), cons)
    prob.solve(solver="CLARABEL", tol_gap_abs=1e-12, tol_gap_rel=1e-12, tol_feas=1e-12, max_iter=500)
    return prob.value, [z.value for z in Z3], [z.value for z in Z4], prob.status


def is_psd_exact(M: sp.Matrix) -> bool:
    """PSD iff all coefficients of det(x I + M) are >= 0 (principal-minor sums)."""
    x = sp.Symbol('x')
    p = sp.Poly((M + x * sp.eye(M.shape[0])).det(method="berkowitz"), x)
    return all(cf >= 0 for cf in p.all_coeffs())


def rationalize(A, den):
    return sp.Matrix(A.shape[0], A.shape[1], lambda i, j: sp.Rational(Fr(float(A[i, j])).limit_denominator(den)))


def symmetric_vars(prefix, n):
    syms, M = [], sp.zeros(n, n)
    for i in range(n):
        for j in range(i, n):
            s = sp.Symbol(f"{prefix}_{i}_{j}"); syms.append(s); M[i, j] = M[j, i] = s
    return syms, M


def certify(N, t_frac: Fr, den=10**6):
    t = sp.Rational(t_frac.numerator, t_frac.denominator); eta2 = t * t
    HP, HQ, target = witness_primal(N, t_frac)
    target = sp.nsimplify(target)
    print(f"N={N} (k={N+1}), eta={t}, witness value ||e||^2 = {target} = {float(target):.12f}")
    val, Z3n, Z4n, st = solve_dual_numeric(N, float(eta2))
    print(f"  numeric dual value {val:.12f} [{st}]  gap to witness {val-float(target):+.2e}")
    # symbolic parametrisation
    allsyms, Z3s, Z4s = [], [], []
    for n in range(1, N + 1):
        s3, M3 = symmetric_vars(f"z3n{n}", 2 * n); s4, M4 = symmetric_vars(f"z4n{n}", n)
        allsyms += s3 + s4; Z3s.append(M3); Z4s.append(M4)
    Z1s, Z2s = dual_expressions(Z3s, Z4s, eta2, N, "sym")
    # exact complementarity with the rational witness: Z1_n HP_n = 0, Z2_n HQ_n = 0, Z3/Z4 * slack = 0
    eqs = []
    for n in range(N):
        eqs += list(Z1s[n] * HP[n]) + list(Z2s[n] * HQ[n])
    eqs.append(Z3s[0][0, 0] + eta2 * Z4s[0][0, 0] - target)
    eqs = [sp.expand(e) for e in eqs if sp.expand(e) != 0]
    # numeric point
    numeric = {}
    for n in range(1, N + 1):
        for i in range(2 * n):
            for j in range(i, 2 * n):
                numeric[sp.Symbol(f"z3n{n}_{i}_{j}")] = Z3n[n - 1][i, j]
        for i in range(n):
            for j in range(i, n):
                numeric[sp.Symbol(f"z4n{n}_{i}_{j}")] = Z4n[n - 1][i, j]
    # linear system  A z = b ; project rounded numeric point onto it exactly (min-norm correction)
    A, b = sp.linear_eq_to_matrix(eqs, allsyms)
    z0 = sp.Matrix([sp.Rational(Fr(float(numeric[s])).limit_denominator(den)) for s in allsyms])
    r = A * z0 - b
    AAt = A * A.T
    # A may be rank deficient: solve AAt y = r in least-norm sense via row-reduced basis
    rref, piv = A.T.rref()  # not used directly; use pinv via independent rows
    rows = list(sp.Matrix(A.T).rref()[1])
    Ai = A.extract(list(range(A.shape[0])), list(range(A.shape[1])))
    indep = []
    M = sp.zeros(0, A.shape[1])
    for i in range(A.shape[0]):
        cand = M.col_join(A[i, :])
        if cand.rank() > M.rank():
            M = cand; indep.append(i)
    Ar, rr = A[indep, :], r[indep, :]
    y = (Ar * Ar.T).LUsolve(rr)
    z = z0 - Ar.T * y
    assert A * z == b, "exact projection failed (inconsistent system?)"
    sub = dict(zip(allsyms, z))
    ok = True
    report = {}
    for name, mats in (("Z1", Z1s), ("Z2", Z2s), ("Z3", Z3s), ("Z4", Z4s)):
        for n, Ms in enumerate(mats, 1):
            Mv = Ms.subs(sub)
            psd = is_psd_exact(Mv)
            ev = np.linalg.eigvalsh(np.array(Mv.evalf(), dtype=float))
            report[f"{name}_{n}"] = {"psd_exact": bool(psd), "min_eig_float": float(ev[0])}
            ok &= psd
    V = (Z3s[0][0, 0] + eta2 * Z4s[0][0, 0]).subs(sub)
    print(f"  exact bound V = {V}  (== witness: {V == target});  all PSD exactly: {ok}")
    for k_, v in report.items():
        if not v["psd_exact"]:
            print("   FAIL", k_, v)
    return ok, V, target, sub, Z3s, Z4s, report


if __name__ == "__main__":
    N = int(sys.argv[1]); p, q = map(int, sys.argv[2].split("/"))
    den = int(sys.argv[3]) if len(sys.argv) > 3 else 10**6
    ok, V, target, sub, Z3s, Z4s, report = certify(N, Fr(p, q), den)
    if ok:
        out = {"topology": "chain", "k": N + 1, "eta": f"{p}/{q}", "certified_value_squared": str(V),
               "Z3": [[[str(x) for x in Z.subs(sub).row(i)] for i in range(Z.shape[0])] for Z in Z3s],
               "Z4": [[[str(x) for x in Z.subs(sub).row(i)] for i in range(Z.shape[0])] for Z in Z4s],
               "psd_checks": report}
        fn = f"certificate_chain_k{N+1}_eta_{p}_{q}.json"
        json.dump(out, open(fn, "w"), indent=1)
        print("  wrote", fn)
