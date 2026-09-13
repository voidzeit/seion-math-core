"""Exact check of the Universal Sharp Witness (THEOREM_R_v2.md, Theorem W) on random trees.

Construction (all spaces R^2 = C, leaves e_0 = 1):
  non-root internal v:  mu_v(x) = e^{i theta_v} * prod_{internal slots} x_i * prod_{leaf slots} Re(x_j),  P_v = Re
  root (variant I):     mu_r(x) = prod_{internal slots} x_i * prod_{leaf slots} Re(x_j),  P_r = I
  root (variant II):    mu_r(x) = Re(lambda prod ...) e_0, P_r = Re
Checks: (1) E^P = |1 - prod_{v != r} w(theta_v)| for random per-vertex angles; (2) with theta_v = theta* for all v,
E^P / eta = C_k(eta); (3) full-subspace closure on random admissible inputs (projected internal slots are real,
leaf slots arbitrary): |Q_v mu_v(x)| <= sin(theta_v) prod |x|, root defect 0 (variant I).
"""
import json, math, cmath
import numpy as np

rng = np.random.default_rng(11)


def Ck(k, eta):
    t = np.linspace(0, math.asin(eta), 400001)
    g = np.abs(1 - (np.cos(t) * np.exp(1j * t)) ** (k - 1))
    i = int(np.argmax(g))
    return float(g[i]) / eta, float(t[i])


def random_tree(k, max_arity=4):
    while True:
        parent = [None] + [int(rng.integers(0, i)) for i in range(1, k)]
        kids = [[] for _ in range(k)]
        for v in range(1, k):
            kids[parent[v]].append(v)
        if all(len(c) <= max_arity for c in kids):
            leaves = [int(rng.integers(0 if kids[v] else 1, 3)) for v in range(k)]   # leaf-slot counts
            return kids, leaves


def evaluate(kids, leaves, theta, variant):
    k = len(kids)
    F = [None] * k; R = [None] * k
    for v in reversed(range(k)):
        pf = np.prod([F[c] for c in kids[v]]) if kids[v] else 1.0 + 0j
        pr = np.prod([R[c] for c in kids[v]]) if kids[v] else 1.0 + 0j
        # leaf slots receive e_0 = 1: Re(1) = 1 in both evaluations
        if v != 0:
            F[v] = cmath.exp(1j * theta[v]) * pf
            R[v] = (cmath.exp(1j * theta[v]) * pr).real + 0j
        else:
            if variant == "I":
                F[v] = pf; R[v] = pr                   # P_r = I
            else:
                F[v] = pf; R[v] = pr                   # reader Re(lambda .) applied below
    if variant == "I":
        return abs(F[0] - R[0])                       # E^P = |P_r F_r - R_r| with P_r = I
    diff = F[0] - R[0]
    return abs(diff)                                  # best lambda gives |Re(lambda diff)| = |diff|


def closure_defect_sample(m_int, m_leaf, theta, trials=200):
    worst = 0.0
    for _ in range(trials):
        xs = [complex(rng.normal(), 0.0) for _ in range(m_int)]                   # projected internal inputs (real)
        ls = [complex(rng.normal(), rng.normal()) for _ in range(m_leaf)]          # arbitrary leaf vectors
        val = cmath.exp(1j * theta) * np.prod(xs + [complex(l.real, 0) for l in ls]) if (xs or ls) else cmath.exp(1j * theta)
        norms = np.prod([abs(x) for x in xs + ls]) if (xs or ls) else 1.0
        if norms > 0:
            worst = max(worst, abs(val.imag) / norms - math.sin(theta))
    return worst


rows, max_err_random, max_err_sharp, max_closure_excess = [], 0.0, 0.0, -np.inf
for trial in range(4000):
    k = int(rng.integers(1, 11)); eta = float(rng.choice([1e-6, 1e-3, 0.1, 0.5, math.sqrt(3 / 7), 0.9, 1.0]))
    kids, leaves = random_tree(k)
    TH = math.asin(eta)
    theta = [0.0] + list(rng.uniform(0, TH, k - 1))
    variant = str(rng.choice(["I", "II"]))
    E = evaluate(kids, leaves, theta, variant)
    pred = abs(1 - np.prod([math.cos(t) * cmath.exp(1j * t) for t in theta[1:]])) if k > 1 else 0.0
    max_err_random = max(max_err_random, abs(E - pred))
    ck, tstar = Ck(k, eta) if k > 1 else (0.0, 0.0)
    E2 = evaluate(kids, leaves, [0.0] + [tstar] * (k - 1), variant)
    max_err_sharp = max(max_err_sharp, abs(E2 / eta - ck))
    for v in range(1, k):
        max_closure_excess = max(max_closure_excess, closure_defect_sample(len(kids[v]), leaves[v], theta[v], 20))
summary = {"trees": 4000, "max_abs_error_random_angles": max_err_random,
           "max_abs_error_sharp_ratio_vs_Ck": max_err_sharp,
           "max_closure_excess_over_sin_theta": max_closure_excess}
json.dump(summary, open("outputs/sharp_witness_check.json", "w", newline="\n"), indent=1)
print(json.dumps(summary))
