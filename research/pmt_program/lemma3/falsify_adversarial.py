"""Adversarial (local optimization) falsification of Lemma 3 for O1 / O2.

Objective = signed domination margin of the output state against the best target w(theta) prod z_i:
  O1: margin = -min_theta max_{lam,phi} (D_s - D_z)
  O2: margin =  max_theta min(1-a^2, rho^2-r^2, (c+m) - rho cos chi, rho - (c-m))
Negative margin = counterexample. We MINIMIZE the margin over (child chain angles, child states, law).
Child states are parametrised inside the dominated set of the order under test.
usage: python falsify_adversarial.py ORDER m eta restarts seed
"""
import json, math, sys
import numpy as np
from scipy.optimize import minimize
from states import contract, opnorm, gram_state, o1_violation, enforce_closure

order, m, eta, restarts, seed = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rng = np.random.default_rng(seed)
TH = math.asin(eta)
d = 4
NF = 2  # chain factors per child
THETAS = np.linspace(0, TH, 61)


def sig(x):
    return 1 / (1 + np.exp(-x))


def unpack(p):
    i = 0
    kids, zs = [], []
    for _ in range(m):
        th = TH * sig(p[i:i + NF]); i += NF
        rho, chi = float(np.prod(np.cos(th))), float(np.sum(th))
        if order == "O2":
            psi = chi * sig(p[i]); i += 1
            B = p[i:i + 4].reshape(2, 2); i += 4
            sB = np.linalg.svd(B, compute_uv=False)[0]
            B = B / max(sB, 1.0)
            F = B @ np.array([math.cos(psi), math.sin(psi)]); R = B @ np.array([rho, 0.0])
        else:
            a = sig(p[i]); r = rho * sig(p[i + 1]); psi = math.pi * sig(p[i + 2]); i += 3
            F = np.array([a * math.cos(psi), a * math.sin(psi)]); R = np.array([r, 0.0])
        nr = np.linalg.norm(R)
        if nr > 1e-15:
            u = R / nr; Qm = np.array([[u[0], u[1]], [-u[1], u[0]]]); F, R = Qm @ F, Qm @ R
        kids.append((F, R)); zs.append((rho, chi))
    T = p[i:i + d * 2 ** m].reshape((d,) + (2,) * m); i += d * 2 ** m
    rank = 1 + int(sig(p[i]) * (d - 1) - 1e-9)
    return kids, zs, T, rank


def margin(p, fine=False):
    kids, zs, T, rank = unpack(p)
    P = np.diag([1.0] * rank + [0.0] * (d - rank))
    est, ub = opnorm(T, m, fine=fine)
    T = T / (ub if fine else est)
    T = enforce_closure(T, m, P, eta)
    est2, ub2 = opnorm(T, m, fine=fine)
    T = T / max(ub2 if fine else est2, 1.0)
    if order == "O1":
        # O1 domination of children is a hard constraint: penalise violations
        pen = sum(max(0.0, o1_violation(*(lambda s: (s[0], s[1], s[3]))(gram_state(F, R)), rho, chi)[0])
                  for (F, R), (rho, chi) in zip(kids, zs))
    else:
        pen = 0.0
    x = contract(T, [k[0] for k in kids]); y = contract(T, [k[1] for k in kids])
    a, r, c, psi = gram_state(x, P @ y)
    rho_in = float(np.prod([z[0] for z in zs])); chi_in = float(np.sum([z[1] for z in zs]))
    best = -np.inf
    qy0 = float(np.linalg.norm(y - P @ y))
    th_star = [math.asin(min(1.0, qy0 / rho_in))] if rho_in > 1e-15 and qy0 <= eta * rho_in + 1e-12 else []
    for th in list(THETAS) + th_star:
        rho_o, chi_o = rho_in * math.cos(th), min(chi_in + th, math.pi)
        if order == "O1":
            val = -o1_violation(a, r, psi, rho_o, chi_o)[0]
        else:
            mm = math.sqrt(max(0.0, 1 - a * a) * max(0.0, rho_o ** 2 - r * r))
            val = min(1 - a * a, rho_o ** 2 - r * r, (c + mm) - rho_o * math.cos(chi_o), rho_o - (c - mm))
        best = max(best, val)
    return best + 10.0 * pen, (a, r, c, psi, rho_in, chi_in, pen)


dim = m * (NF + (5 if order == "O2" else 3)) + d * 2 ** m + 1
results = []
for rs in range(restarts):
    p0 = rng.normal(size=dim)
    res = minimize(lambda q: margin(q)[0], p0, method="Powell", options={"maxiter": 4000, "xtol": 1e-6, "ftol": 1e-10})
    res = minimize(lambda q: margin(q)[0], res.x, method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-8, "fatol": 1e-12})
    val_fine, info = margin(res.x, fine=True)
    results.append((val_fine, res.x, info))
results.sort(key=lambda t: t[0])
best = results[0]
rec = {"order": order, "m": m, "eta": eta, "seed": seed, "restarts": restarts,
       "min_margin_certified_norm": best[0], "counterexample": bool(best[0] < -1e-7),
       "state_at_min_a_r_c_psi_rhoin_chiin_pen": best[2], "params": best[1].tolist(),
       "all_margins": [r[0] for r in results]}
with open(f"outputs/adversarial_{order}_m{m}_eta{eta}_s{seed}.json", "w") as fh:
    json.dump(rec, fh, indent=1)
print(json.dumps({k: rec[k] for k in ("order", "m", "eta", "min_margin_certified_norm", "counterexample")}), flush=True)
