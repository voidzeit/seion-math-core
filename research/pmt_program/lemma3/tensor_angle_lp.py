"""Near-global test of the tensor angle inequality (TA_m), the analytic core of Lemma 3 in order O2:

    || u_1 (x) ... (x) u_m  -  t v_1 (x) ... (x) v_m ||_proj  <=  | 1 - t e^{i min(S,pi)} |,
    u_i, v_i unit in R^2, angle(u_i, v_i) = psi_i, S = sum psi_i, t >= 0.

The real projective norm is computed by a cutting-plane LP over m-linear forms W with ||W|| <= 1
(dual characterisation). The LP value is an UPPER estimate until the oracle certifies ||W|| <= 1;
dividing by the verified norm gives an admissible LOWER value. A counterexample needs lower > bound.
usage: python tensor_angle_lp.py m n_cases seed
"""
import itertools, json, math, sys
import numpy as np
from scipy.optimize import linprog

m, n_cases, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
rng = np.random.default_rng(seed)
G = {2: 2048, 3: 192, 4: 48}[m]
ang = np.linspace(0, np.pi, G, endpoint=False)
X = np.stack([np.cos(ang), np.sin(ang)], 1)


def unit(t):
    return np.array([math.cos(t), math.sin(t)])


def rank1(vecs):
    out = vecs[0]
    for v in vecs[1:]:
        out = np.multiply.outer(out, v)
    return out.ravel()


def form_norm(W):
    """max over unit x_1..x_{m-1} of |W(x_1,..,x_{m-1},.)| with local refinement; returns value and argmax vectors."""
    Wt = W.reshape((2,) * m)
    grids = [X] * (m - 1)
    if m == 2:
        V = np.einsum("ij,pi->pj", Wt, X)
    elif m == 3:
        V = np.einsum("ijk,pi,qj->pqk", Wt, X, X)
    else:
        V = np.einsum("ijkl,pi,qj,rk->pqrl", Wt, X, X, X)
    nrm = np.sqrt((V ** 2).sum(-1))
    idx = np.unravel_index(int(np.argmax(nrm)), nrm.shape)
    angs = [ang[i] for i in idx]
    best = nrm[idx]
    for h in (2e-3, 5e-4, 1e-4, 2e-5, 4e-6, 1e-6):
        improved = True
        while improved:
            improved = False
            for j in range(m - 1):
                for s in (h, -h):
                    trial = list(angs); trial[j] += s
                    v = Wt
                    for tt in trial:
                        v = np.tensordot(v, unit(tt), axes=([0], [0]))
                    val = np.linalg.norm(v)
                    if val > best:
                        best, angs, improved = val, trial, True
    v = Wt
    for tt in angs:
        v = np.tensordot(v, unit(tt), axes=([0], [0]))
    last = v / max(np.linalg.norm(v), 1e-300)
    # grid-spacing margin for a certified upper bound of the norm (Lipschitz <= (m-1)*norm*h/2 per grid)
    hgrid = np.pi / G
    ub = best / max(1e-9, 1 - (m - 1) * hgrid / 2)
    return best, ub, [unit(t) for t in angs] + [last]


def proj_norm_bracket(T, iters=300):
    cons = [rank1(list(vs)) for vs in itertools.product([unit(a) for a in np.linspace(0, np.pi, 5, endpoint=False)], repeat=m)]
    cons += [-c for c in cons]
    for it in range(iters):
        res = linprog(-T, A_ub=np.array(cons), b_ub=np.ones(len(cons)), bounds=[(-4, 4)] * (2 ** m), method="highs")
        W = res.x
        est, ub, vecs = form_norm(W)
        if est <= 1 + 1e-10:
            break
        c = rank1(vecs)
        cons.append(c); cons.append(-c)
    upper_lp = -res.fun
    lower = upper_lp / max(ub, 1.0)
    return upper_lp, lower


worst = {"excess_lower_minus_bound": -np.inf}
rows = []
for case in range(n_cases):
    psi = rng.uniform(0, math.pi / m, m) * rng.choice([1.0, rng.uniform(0.2, 1.0)])
    if rng.random() < 0.3:
        psi = np.full(m, rng.uniform(0, math.pi / m))
    t = float(rng.choice([rng.uniform(0, 1), rng.uniform(1, 2), float(np.prod(np.cos(psi)))]))
    phase = rng.uniform(0, 2 * np.pi, m)                   # random common orientation per factor
    us = [unit(phase[i] + psi[i]) for i in range(m)]
    vs = [unit(phase[i]) for i in range(m)]
    T = rank1(us) - t * rank1(vs)
    S = float(psi.sum())
    bound = abs(1 - t * complex(math.cos(min(S, math.pi)), math.sin(min(S, math.pi))))
    up, lo = proj_norm_bracket(T)
    row = {"psi": psi.tolist(), "t": t, "S": S, "bound": bound, "lp_upper": up, "admissible_lower": lo,
           "excess_lower_minus_bound": lo - bound, "excess_upper_minus_bound": up - bound}
    rows.append(row)
    if row["excess_lower_minus_bound"] > worst["excess_lower_minus_bound"]:
        worst = row
summary = {"m": m, "cases": n_cases, "seed": seed,
           "max_excess_lower_minus_bound": worst["excess_lower_minus_bound"],
           "max_excess_upper_minus_bound": max(r["excess_upper_minus_bound"] for r in rows),
           "counterexample": bool(worst["excess_lower_minus_bound"] > 1e-7), "worst_case": worst}
json.dump({"summary": summary, "rows": rows}, open(f"outputs/tensor_angle_lp_m{m}_s{seed}.json", "w"), indent=1)
print(json.dumps({k: summary[k] for k in ("m", "cases", "max_excess_lower_minus_bound", "max_excess_upper_minus_bound", "counterexample")}), flush=True)
