"""Hostile edge-case checks for Theorem R, v2 (extends ../theorem_R_v1/edge_cases.py), real field.

Added in v2: eta in {1e-6, 1e-3} (eta = 0 is outside PMT-A since rho > 0), children with |F| < 1 made
explicit (uniformly shrunk contractions). Arity 0..3 (arity 4 is covered by the tensor-angle LP campaign).

Every case evaluates the O2 domination of the vertex output at the PROOF angle
sin(theta*) = |Q mu(R)| / prod(rho_i)  (theta* = 0 if prod rho = 0), and the root bound.
Edge families: projector rank 0 and full; eta = 1; rho_i = 0 (theta = pi/2); psi_i in {0, chi_i};
angle sums >= pi; zero / rank-one / isometric child contractions; m = 0 (leaf-only vertex); m up to 3.
"""
import itertools, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lemma3"))
from states import contract, opnorm, gram_state, o2_violation, enforce_closure, sample_law

rng = np.random.default_rng(2026)
d = 4
TOL = 1e-10


def child_pair(rho, psi, Bkind):
    Fh = np.array([math.cos(psi), math.sin(psi)]); Rt = np.array([rho, 0.0])
    if Bkind == "id":
        B = np.eye(2)
    elif Bkind == "zero":
        B = np.zeros((2, 2))
    elif Bkind == "rank1":
        v = rng.normal(size=2); v /= np.linalg.norm(v); B = np.outer(rng.normal(size=2), v); B /= max(1.0, np.linalg.norm(B, 2))
    elif Bkind == "shrink":
        U, _ = np.linalg.qr(rng.normal(size=(2, 2))); B = rng.uniform(0.0, 0.999) * U
    else:
        U, _ = np.linalg.qr(rng.normal(size=(2, 2))); B = U
    F, R = B @ Fh, B @ Rt
    r = np.linalg.norm(R)
    if r > 1e-15:
        u = R / r; Qm = np.array([[u[0], u[1]], [-u[1], u[0]]]); F, R = Qm @ F, Qm @ R
    return F, R


rows, worst = [], {"v": -1}
etas = [1.0, 0.9, 0.3, 1e-3, 1e-6]
for trial in range(8000):
    eta = float(rng.choice(etas)); TH = math.asin(eta)
    m = int(rng.integers(0, 4))
    rank = int(rng.choice([0, d, 1, 2]))
    P = np.diag([1.0] * rank + [0.0] * (d - rank)); Q = np.eye(d) - P
    kids, datums = [], []
    for i in range(m):
        n = int(rng.integers(1, 5))
        th = rng.choice([0.0, TH, rng.uniform(0, TH)], size=n)
        rho, chi = float(np.prod(np.cos(th))), float(np.sum(th))
        if rng.random() < 0.15 and eta == 1.0:
            rho, chi = 0.0, chi + math.pi / 2            # a theta = pi/2 factor
        psi = float(rng.choice([0.0, min(chi, math.pi), rng.uniform(0, min(chi, math.pi))]))
        kids.append(child_pair(rho, psi, str(rng.choice(["id", "zero", "rank1", "orth", "shrink"]))))
        datums.append((rho, chi))
    if m == 0:
        f = rng.normal(size=d); f /= max(np.linalg.norm(f), 1e-12)
        f *= float(rng.choice([1.0, rng.uniform(0, 1), 0.0]))
        q = Q @ f
        if np.linalg.norm(q) > eta:
            f = P @ f + q * eta / np.linalg.norm(q)
        x = f; y = f; rho_in, chi_in = 1.0, 0.0
    else:
        T = sample_law(rng, m, d, eta, str(rng.choice(["gauss", "phase", "rank1"])))
        # trajectory closure along the actual children R (unit-normalised)
        Rs = [k[1] for k in kids]
        yR = contract(T, Rs)
        bound = eta * float(np.prod([np.linalg.norm(r) for r in Rs]))
        if np.linalg.norm(Q @ yR) > bound + 1e-15:
            s = bound / np.linalg.norm(Q @ yR)
            T = np.tensordot(P, T, axes=([1], [0])) + s * np.tensordot(Q, T, axes=([1], [0]))
        _, ub = opnorm(T, m)
        T = T / max(ub, 1.0)
        x = contract(T, [k[0] for k in kids]); y = contract(T, Rs)
        rho_in = float(np.prod([dd[0] for dd in datums])); chi_in = float(np.sum([dd[1] for dd in datums]))
    a, r, c, psi_out = gram_state(x, P @ y)
    qy = float(np.linalg.norm(Q @ y))
    if rho_in > 1e-15:
        ths = math.asin(min(1.0, qy / rho_in))
    else:
        ths = 0.0
    v = o2_violation(a, r, c, rho_in * math.cos(ths), chi_in + ths)
    if m >= 1:
        root_err = float(np.linalg.norm(x - y))
        S = min(chi_in, math.pi)
        vroot = root_err - abs(1 - rho_in * complex(math.cos(S), math.sin(S)))
    else:
        vroot = -1.0
    rec = {"m": m, "eta": eta, "P_rank": rank, "rho_in": rho_in, "chi_in": chi_in, "theta_star": ths,
           "theta_star_within_budget": bool(ths <= TH + 1e-12), "v_O2": v, "v_root": vroot}
    rows.append(rec)
    if max(v, vroot) > worst["v"]:
        worst = dict(rec, v=max(v, vroot))
summary = {"cases": len(rows), "max_v_O2": max(r["v_O2"] for r in rows), "max_v_root": max(r["v_root"] for r in rows),
           "theta_star_out_of_budget": sum(not r["theta_star_within_budget"] for r in rows),
           "violations": sum((r["v_O2"] > TOL) or (r["v_root"] > TOL) for r in rows),
           "counts_by_m": {str(k): sum(r["m"] == k for r in rows) for k in range(4)},
           "counts_P_rank0": sum(r["P_rank"] == 0 for r in rows), "counts_P_full": sum(r["P_rank"] == d for r in rows),
           "counts_eta1": sum(r["eta"] == 1.0 for r in rows), "counts_eta_tiny": sum(r["eta"] <= 1e-3 for r in rows), "counts_rho_zero": sum(r["rho_in"] == 0 for r in rows),
           "counts_chi_ge_pi": sum(r["chi_in"] >= math.pi for r in rows), "worst": worst}
with open("outputs/edge_cases_v2.json", "w", newline="\n") as fh:
    json.dump(summary, fh, indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != "worst"}))
