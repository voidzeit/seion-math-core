"""Random falsification of Lemma 3 (non-root multilinear vertex) for orders O1 and O2, plus Lemma 2 (root).

usage: python falsify_random.py ORDER m eta n_cases seed      (ORDER in {O1, O2})
Writes JSON lines: one summary line, and one line per violation with all data needed to replay it.
"""
import json, math, sys
import numpy as np
from states import (chain_state, sample_thetas, sample_child_O1, sample_child_O2, sample_law,
                    enforce_closure, opnorm, contract, gram_state, o1_violation, o2_violation)

order, m, eta, n_cases, seed = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rng = np.random.default_rng(seed)
TH = math.asin(eta)
THETAS = np.linspace(0, TH, 41)
d = 4
TOL = 1e-9
stats = {"order": order, "m": m, "eta": eta, "cases": 0, "violations_lemma3": 0, "violations_root": 0,
         "max_v_lemma3": -1.0, "max_v_root": -1.0, "max_v_lemma3_proof_theta": -1.0}
out = open(f"outputs/random_{order}_m{m}_eta{eta}_s{seed}.jsonl", "w")
for case in range(n_cases):
    zs = [chain_state(sample_thetas(rng, eta, int(rng.integers(1, 4)))) for _ in range(m)]
    kids = [(sample_child_O2 if order == "O2" else sample_child_O1)(rng, rho, chi) for rho, chi in zs]
    rank = int(rng.integers(1, d))
    Pdiag = np.zeros(d); Pdiag[:rank] = 1; P = np.diag(Pdiag)
    kind = rng.choice(["gauss", "phase", "rank1", "tensor"] if m <= 2 else ["gauss", "phase", "rank1"])
    T = sample_law(rng, m, d, eta, kind)
    T = enforce_closure(T, m, P, eta)
    _, ub = opnorm(T, m)
    T = T / max(ub, 1.0) if ub > 1 else T
    F = [k[0] for k in kids]; R = [k[1] for k in kids]
    x = contract(T, F); y = contract(T, R)
    Rout = P @ y
    a, r, c, psi = gram_state(x, Rout)
    rho_in = float(np.prod([z[0] for z in zs])); chi_in = float(np.sum([z[1] for z in zs]))
    best1 = (np.inf, None); best2 = (np.inf, None)
    qy0 = float(np.linalg.norm(y - P @ y))
    th_star = [math.asin(min(1.0, qy0 / rho_in))] if rho_in > 1e-15 and qy0 <= eta * rho_in + 1e-12 else []
    for th in list(THETAS) + th_star:
        rho_o, chi_o = rho_in * math.cos(th), chi_in + th
        if order == "O1":
            v, lam, phi = o1_violation(a, r, psi, rho_o, chi_o)
            if v < best1[0]:
                best1 = (v, (float(th), lam, phi))
        else:
            v = o2_violation(a, r, c, rho_o, chi_o)
            if v < best2[0]:
                best2 = (v, (float(th),))
    v3, arg = best1 if order == "O1" else best2
    # proof-determined theta (O2 argument): sin theta = |Q y| / prod rho
    qy = np.linalg.norm(y - P @ y)
    thp = math.asin(min(1.0, qy / rho_in)) if rho_in > 1e-15 else TH
    vproof = (o2_violation(a, r, c, rho_in * math.cos(thp), chi_in + thp) if thp <= TH + 1e-12 else np.nan)
    # Lemma 2 (root): |P_r (x - y)| <= |1 - rho_in e^{i min(chi_in, pi)}|
    root_err = float(np.linalg.norm(x - y))           # P_r = I is the worst case of the reading
    root_bound = abs(1 - rho_in * complex(math.cos(min(chi_in, math.pi)), math.sin(min(chi_in, math.pi))))
    vroot = root_err - root_bound
    stats["cases"] += 1
    stats["max_v_lemma3"] = max(stats["max_v_lemma3"], v3)
    stats["max_v_root"] = max(stats["max_v_root"], vroot)
    if not np.isnan(vproof):
        stats["max_v_lemma3_proof_theta"] = max(stats["max_v_lemma3_proof_theta"], vproof)
    rec = None
    if v3 > TOL:
        stats["violations_lemma3"] += 1
        rec = "lemma3"
    if vroot > TOL:
        stats["violations_root"] += 1
        rec = (rec + "+root") if rec else "root"
    if rec:
        out.write(json.dumps({"type": rec, "v_lemma3": v3, "argmin_theta_lam_phi": arg, "v_root": vroot,
                              "v_proof_theta": vproof, "eta": eta, "m": m, "law_kind": str(kind),
                              "child_chain_states_rho_chi": zs,
                              "child_states_a_r_psi": [gram_state(F[i], R[i])[:2] + (gram_state(F[i], R[i])[3],) for i in range(m)],
                              "F": [f.tolist() for f in F], "R": [q.tolist() for q in R],
                              "mu": T.tolist(), "P_rank": rank, "out_state_a_r_c_psi": [a, r, c, psi]}) + "\n")
out.write(json.dumps({"summary": stats}) + "\n")
out.close()
print(json.dumps(stats), flush=True)
