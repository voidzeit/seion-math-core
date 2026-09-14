"""Closed-form constants of the free chain (CHAIN_ALL_K.md), k = 2..12.

G_k(theta) := |1 - (cos th e^{i th})^{k-1}|,   E_k^2(s) polynomial in s = sin^2 th,
C_{k,chain}(eta) = max_{0<=th<=asin eta} G_k(th) / eta.

Reports: E_k^2(s) factored, small-eta series of C, a_k vs n(n-1)(n+7)/24 and the
refuted (k-2)(2k-3)/4, the critical leakage s_c (global max of E_k^2 on [0, sin^2(pi/n)]),
saturated absolute error G_k^max, and a unimodality check on [0, pi/n].
Requires sympy (exact algebra) and mpmath (high precision roots).
"""
import json
import sympy as sp
import mpmath as mp

mp.mp.dps = 40
s, eta = sp.symbols("s eta", positive=True)
rows = []
for k in range(2, 13):
    n = k - 1
    z = (1 + sp.cos(2 * sp.Symbol("x")) + sp.I * sp.sin(2 * sp.Symbol("x"))) / 2
    th = sp.Symbol("th", real=True)
    c = sp.cos(th)
    E2_trig = 1 + c ** (2 * n) - 2 * c ** n * sp.cos(n * th)
    E2 = sp.expand(sp.expand_trig(E2_trig).subs(sp.cos(th), sp.sqrt(1 - s)).subs(sp.sin(th), sp.sqrt(s)))
    E2 = sp.nsimplify(sp.expand(E2))
    assert E2.is_polynomial(s), (k, E2)
    C = sp.sqrt(E2.subs(s, eta ** 2)) / eta
    ser = sp.series(C, eta, 0, 6).removeO()
    a_k = -ser.coeff(eta, 2)
    b_k = ser.coeff(eta, 4)
    # critical point: global max of E2 on [0, sin^2(pi/n)]  (n>=2); for n=1, s in [0,1]
    s_hi = sp.Float(sp.N(sp.sin(sp.pi / n) ** 2, 40), 40) if n >= 2 else sp.Float(1, 40)
    dE = sp.Poly(sp.diff(E2, s), s)
    # exact real roots of E2'(s) (isolating intervals, no floating root finder)
    roots = [r for r in sp.real_roots(dE) if 0 < r.evalf(40) < s_hi]
    cands = [(sp.Integer(0), sp.Float(0)), (None, s_hi)] + [(r, r.evalf(40)) for r in roots]
    vals = [(E2.subs(s, v).evalf(40), ex, v) for ex, v in cands]
    Gmax2, exact_root, s_c = max(vals, key=lambda t: t[0])
    # number of interior critical points of E2 on (0, sin^2(pi/n)) = unimodality witness
    changes = len(roots)
    exact_sc = None
    if exact_root is not None:
        exact_sc = sp.radsimp(exact_root) if dE.degree() > 4 else sp.nsimplify(
            [r for r in sp.solve(dE.as_expr(), s) if abs(complex(r.evalf()) - complex(s_c)) < 1e-25][0])
    rows.append({
        "k": k, "E2_poly": str(sp.factor(E2)), "series_C": str(sp.expand(ser)),
        "a_k": str(a_k), "a_k_formula_(k-1)(k-2)(k+6)/24": str(sp.Rational((k - 1) * (k - 2) * (k + 6), 24)),
        "refuted_(k-2)(2k-3)/4": str(sp.Rational((k - 2) * (2 * k - 3), 4)), "b_k": str(b_k),
        "s_c": str(exact_sc) if exact_sc is not None else str(sp.N(s_c, 20)),
        "eta_c": str(sp.N(sp.sqrt(s_c), 20)), "G_max": str(sp.N(sp.sqrt(Gmax2), 20)),
        "G_max_squared_exact": str(sp.nsimplify(sp.simplify(E2.subs(s, exact_sc)))) if exact_sc is not None else None,
        "interior_critical_points_on_(0,sin^2(pi/n))": changes,
    })
    assert a_k == sp.Rational((k - 1) * (k - 2) * (k + 6), 24)
print(json.dumps(rows, indent=1))
