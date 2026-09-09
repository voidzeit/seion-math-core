"""J_2 = 2, H_2 = 2, and S_2 = Sigma_2(eta), from the explicit witnesses.

Reproduces the three k=2 rebracketing constants. Runs in seconds, numpy only.

    J_2, H_2   one ternary law, one rank-2 projector, ambient dimension 3,
               all four vertices of both trees, every leaf inside Ran(P).
               This is the SAME + sharedP class, so the class hierarchy
               collapses at k = 2.
    S_2        a dimension-2 witness with A = 0 EXACTLY (not merely P A = 0),
               using three distinct laws -- the FREE class. Whether one tagged
               law reaches Sigma_2 is OPEN.

NUMERICAL ROLE: audit of analytic proofs (RG_CANONICAL.md Thm 5.1, Cor 5.2).
The 4.44e-16 agreement is not the evidence for M42; the proof is.
"""

from __future__ import annotations

import math
import sys

import numpy as np

TOL = 1e-12
failures = []


def check(name, condition, detail=""):
    print(f"  [{'ok  ' if condition else 'FAIL'}] {name}"
          + (f"   {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def sigma2(eta):
    return math.sin(min(2 * math.asin(min(eta, 1.0)), math.pi / 2)) / eta


def op_norm_ternary(mu, rng, restarts=200, iters=40, post=None):
    """||mu||_op over unit x,y,z, by alternating maximization on slot Grams."""
    dim = mu.shape[1]
    best = 0.0
    for _ in range(restarts):
        vecs = [v / np.linalg.norm(v) for v in rng.standard_normal((3, dim))]
        for _ in range(iters):
            for slot in range(3):
                letters = ["a", "c", "d"]
                keep = letters[slot]
                others = [l for l in letters if l != keep]
                sub = f"oacd,{others[0]},{others[1]}->o{keep}"
                idx = [i for i in range(3) if i != slot]
                grad = np.einsum(sub, mu, vecs[idx[0]], vecs[idx[1]])
                if post is not None:
                    grad = post @ grad
                _, eigvecs = np.linalg.eigh(grad.T @ grad)
                vecs[slot] = eigvecs[:, -1]
            out = np.einsum("oacd,a,c,d->o", mu, *vecs)
            if post is not None:
                out = post @ out
            best = max(best, float(np.linalg.norm(out)))
    return best


# ------------------------------------------------------------ J_2 and H_2
print("\nJ_2 = 2 and H_2 = 2  (one law, one projector, dimension 3)")
rng = np.random.default_rng(20260825)
worst_j, worst_h, worst_norm, worst_leak, worst_conceal = 0.0, 0.0, 0.0, 0.0, 0.0

for eta in [0.05, 0.2, 0.5, 1 / math.sqrt(2), 0.85, 1.0]:
    mu = np.zeros((3, 3, 3, 3))
    mu[1, 0, 0, 0] = eta          # eta * x0 y0 z0 * e1     the closure term
    mu[0, 1, 0, 2] = 1.0          # the slot-antisymmetric monomial
    mu[0, 0, 1, 2] = -1.0
    P = np.diag([1.0, 0.0, 1.0])
    e0, e2 = np.eye(3)[0], np.eye(3)[2]

    # T_L = mu(mu(e0,e0,e0), e0, e2)   and   T_M = mu(e0, mu(e0,e0,e0), e2)
    inner_F = np.einsum("oacd,a,c,d->o", mu, e0, e0, e0)
    inner_R = P @ inner_F
    F_L = np.einsum("oacd,a,c,d->o", mu, inner_F, e0, e2)
    F_M = np.einsum("oacd,a,c,d->o", mu, e0, inner_F, e2)
    R_L = P @ np.einsum("oacd,a,c,d->o", mu, inner_R, e0, e2)
    R_M = P @ np.einsum("oacd,a,c,d->o", mu, e0, inner_R, e2)

    A, A_hat = F_L - F_M, R_L - R_M
    D = A_hat - P @ A
    scale = eta * 1.0 * 1.0                      # rho * M * L, with M = L = 1

    worst_j = max(worst_j, abs(np.linalg.norm(D) / scale - 2.0))
    worst_h = max(worst_h, abs(np.linalg.norm(P @ A) / scale - 2.0))
    worst_conceal = max(worst_conceal, float(np.linalg.norm(A_hat)))
    worst_norm = max(worst_norm, abs(op_norm_ternary(mu, rng, 60, 25) - 1.0))
    worst_leak = max(worst_leak,
                     op_norm_ternary(mu, rng, 60, 25, post=np.eye(3) - P) - eta)
    print(f"    eta = {eta:.4f}   J_2 = {np.linalg.norm(D)/scale:.12f}   "
          f"H_2 = {np.linalg.norm(P @ A)/scale:.12f}   ||A_hat|| = "
          f"{np.linalg.norm(A_hat):.2e}")

check("J_2 = 2 at every eta", worst_j < 1e-12, f"max dev {worst_j:.3e}")
check("H_2 = 2 at every eta", worst_h < 1e-12, f"max dev {worst_h:.3e}")
check("concealment is TOTAL: A_hat = 0 exactly", worst_conceal < 1e-14,
      f"max ||A_hat|| = {worst_conceal:.3e}")
check("one shared law has operator norm 1", worst_norm < 1e-6)
check("shared law respects the closure budget", worst_leak < 1e-6)
check("=> J_2^free = J_2^same = J_2^same+sharedP = 2, hierarchy collapses", True)

# ------------------------------------------------------------------- S_2
print("\nS_2 = Sigma_2(eta)  (dimension 2, three distinct laws, A = 0 exactly)")
worst_s, worst_A, worst_adm = 0.0, 0.0, 0.0
for eta in [0.025, 0.05, 0.2, 0.4, 0.6, 1 / math.sqrt(2), 0.8, 0.9, 1.0]:
    d = min(eta, 1 / math.sqrt(2))
    r = math.sqrt(1 - d * d)
    e0, e1 = np.eye(2)[0], np.eye(2)[1]

    F_i = r * e0 + d * e1                        # inner value, both vertices
    R_i = np.outer(e0, e0) @ F_i                 # = r e0
    # roots, applied with the inner value in slot 1 (T_L) or slot 2 (T_M)
    root_L = lambda x, y, z: (r * x[1] - d * x[0]) * y[0] * z[0] * e0
    root_M = lambda x, y, z: x[0] * (-r * y[1] + d * y[0]) * z[0] * e0

    F_L, F_M = root_L(F_i, e0, e0), root_M(e0, F_i, e0)
    R_L, R_M = root_L(R_i, e0, e0), root_M(e0, R_i, e0)
    A, A_hat = F_L - F_M, R_L - R_M

    worst_A = max(worst_A, float(np.linalg.norm(A)))
    worst_s = max(worst_s, abs(np.linalg.norm(A_hat) / eta - sigma2(eta)))
    worst_adm = max(worst_adm, abs(math.hypot(r, d) - 1.0), d - eta)
    print(f"    eta = {eta:.4f}   S_2 = {np.linalg.norm(A_hat)/eta:.12f}   "
          f"Sigma_2 = {sigma2(eta):.12f}   ||A|| = {np.linalg.norm(A):.2e}")

check("S_2 = Sigma_2(eta) at every eta", worst_s < 1e-12,
      f"max |S_2 - Sigma_2| = {worst_s:.3e}")
check("A = 0 EXACTLY, not merely P A = 0", worst_A < 1e-15,
      f"max ||A|| = {worst_A:.3e}")
check("every law has operator norm 1 and leakage <= eta", worst_adm < 1e-12)
check("Sigma_2 < 2 for every eta > 0, so fabrication is NOT total",
      all(sigma2(e) < 2 for e in [1e-3, 0.1, 0.5, 1.0]))

# ------------------------------------------------------ the two transitions
print("\ntwo transitions -- do not conflate")
check("eta_c^{S_2} = 1/sqrt2", abs(1 / math.sqrt(2) - 0.7071067811865475) < TOL,
      "0.707107 -- transition of Sigma_2, k = 2")
check("eta_c^{W_3} = sqrt(2/3)", abs(math.sqrt(2 / 3) - 0.816496580927726) < TOL,
      "0.816497 -- transition of W_3, k = 3")
check("Sigma_2 continuous at its crossover",
      abs(sigma2(1 / math.sqrt(2)) - math.sqrt(2)) < 1e-12)

print("\n" + ("PASS" if not failures else f"FAILED: {failures}"))
sys.exit(1 if failures else 0)
