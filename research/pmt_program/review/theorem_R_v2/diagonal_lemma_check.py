"""Numerical control of the Diagonal Lemma (THEOREM_R_v2.md, Lemma D):
   max_{theta in [0,alpha]^n} |1 - prod_j w(theta_j)| = max_{theta in [0,alpha]} |1 - w(theta)^n|,  w(t) = cos t e^{it}.
Random + boundary-heavy sampling and local maximisation (L-BFGS-B) for n = 1..12. Also records the
counterexample showing that R = prod cos theta_j >= cos Theta FAILS when Theta > pi (so the case split is needed).
"""
import json, math
import numpy as np
from scipy.optimize import minimize

rng = np.random.default_rng(7)


def obj(th):
    z = np.prod(np.cos(th) * np.exp(1j * th))
    return abs(1 - z)


def diag_max(n, alpha):
    t = np.linspace(0, alpha, 400001)
    return float(np.max(np.abs(1 - (np.cos(t) * np.exp(1j * t)) ** n)))


rows = []
worst = -np.inf
for n in range(1, 13):
    for alpha in (0.05, 0.3, math.asin(0.6), 1.0, math.pi / 2 - 1e-9, math.pi / 2):
        d = diag_max(n, alpha)
        best = 0.0
        for _ in range(3000):
            th = rng.uniform(0, alpha, n)
            mask = rng.random(n) < 0.3
            th[mask] = rng.choice([0.0, alpha], size=mask.sum())
            best = max(best, obj(th))
        for _ in range(40):
            x0 = rng.uniform(0, alpha, n)
            res = minimize(lambda x: -obj(x), x0, method="L-BFGS-B", bounds=[(0, alpha)] * n)
            best = max(best, obj(np.clip(res.x, 0, alpha)))
        rows.append({"n": n, "alpha": alpha, "diagonal_max": d, "best_found": best, "excess": best - d})
        worst = max(worst, best - d)
eps = 1e-3
th = np.full(4, math.pi / 2 - eps)
ce = {"theta_j": float(th[0]), "n": 4, "R": float(np.prod(np.cos(th))), "Theta": float(th.sum()),
      "cos_Theta": math.cos(th.sum()), "R_ge_cos_Theta": bool(np.prod(np.cos(th)) >= math.cos(th.sum()))}
out = {"max_excess_best_minus_diagonal": worst, "rows": rows, "counterexample_R_ge_cosTheta_for_Theta_gt_pi": ce}
json.dump(out, open("outputs/diagonal_lemma_check.json", "w", newline="\n"), indent=1)
print(json.dumps({"max_excess": worst, "cases": len(rows), "counterexample": ce}))
