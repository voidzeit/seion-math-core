"""State calculus for the Lemma 3 falsification campaign (PMT-A, real field).

A vertex state is the Gram data of (F_v, R_v): a = |F|, r = |R|, c = <F,R>, psi = angle(F,R).
A chain state is z = rho e^{i chi}: rho = prod cos(theta_j), chi = sum theta_j, theta_j in [0, asin eta].

Order O1 (proposed):  s <=_1 z  iff  for all lam in [0,1], phi in [0,pi]
      D_s(lam,phi) := a^2 + lam^2 r^2 - 2 lam a r cos(min(psi+phi,pi))
   <= D_z(lam,phi) := 1   + lam^2 rho^2 - 2 lam rho cos(min(chi+phi,pi)).
Order O2 (dilation):  s <=_2 z  iff  Gram(F,R) <= Gram(1, rho e^{i psi'}) (Loewner) for some psi' in [0, min(chi,pi)],
   i.e. (F,R) is the image of a unit chain pair under a contraction.
   Closed form: a <= 1, r <= rho, c + m >= rho cos(min(chi,pi)), c - m <= rho, m = sqrt((1-a^2)(rho^2-r^2)).
"""
from __future__ import annotations

import math

import numpy as np

PHI = np.linspace(0.0, np.pi, 181)


def gram_state(F, R):
    a = float(np.linalg.norm(F)); r = float(np.linalg.norm(R)); c = float(F @ R)
    psi = math.acos(max(-1.0, min(1.0, c / (a * r)))) if a > 1e-15 and r > 1e-15 else 0.0
    return a, r, c, psi


def o1_violation(a, r, psi, rho, chi):
    """max over (lam, phi) of D_s - D_z  (> 0 means O1 fails). lam maximised in closed form."""
    cs = np.cos(np.minimum(psi + PHI, np.pi)); cz = np.cos(np.minimum(chi + PHI, np.pi))
    A = r * r - rho * rho                     # coefficient of lam^2
    B = -2.0 * (a * r * cs - rho * cz)        # coefficient of lam
    C0 = a * a - 1.0
    vals = [C0 + 0 * PHI, C0 + A + B]         # lam = 0, lam = 1
    with np.errstate(divide="ignore", invalid="ignore"):
        lv = np.where(A < 0, -B / (2 * A), -1.0)
    inside = (lv > 0) & (lv < 1)
    vals.append(np.where(inside, C0 + A * lv ** 2 + B * lv, -np.inf))
    V = np.max(np.stack(vals), axis=0)
    i = int(np.argmax(V))
    lam_best = 0.0 if vals[0][i] == V[i] else (1.0 if vals[1][i] == V[i] else float(lv[i]))
    return float(V[i]), lam_best, float(PHI[i])


def o2_violation(a, r, c, rho, chi):
    """>0 means O2 fails; 0 means dominated."""
    chi = min(chi, math.pi)
    m = math.sqrt(max(0.0, (1 - a * a)) * max(0.0, (rho * rho - r * r)))
    return max(0.0, a * a - 1.0, r * r - rho * rho, rho * math.cos(chi) - (c + m), (c - m) - rho)


def chain_state(thetas):
    return float(np.prod(np.cos(thetas))), float(np.sum(thetas))


def sample_thetas(rng, eta, n):
    th = rng.uniform(0, math.asin(eta), n)
    mask = rng.random(n) < 0.4
    th[mask] = math.asin(eta)                  # put mass on the budget boundary
    return th


def rot_to_e0(F, R):
    """Rotate the plane so that R is along +e0 (closure direction); returns (F', R')."""
    r = np.linalg.norm(R)
    if r < 1e-15:
        return F.copy(), np.zeros(2)
    u = R / r
    Qm = np.array([[u[0], u[1]], [-u[1], u[0]]])
    return Qm @ F, Qm @ R


def sample_child_O2(rng, rho, chi):
    """Contraction image of a unit chain pair with angle psi <= chi: guaranteed s <=_2 z."""
    psi = chi if rng.random() < 0.5 else rng.uniform(0, chi)
    psi = min(psi, math.pi)
    Fh = np.array([math.cos(psi), math.sin(psi)]); Rt = np.array([rho, 0.0])
    kind = rng.integers(4)
    if kind == 0:
        B = np.eye(2)
    else:
        U, _ = np.linalg.qr(rng.normal(size=(2, 2))); V, _ = np.linalg.qr(rng.normal(size=(2, 2)))
        s = rng.uniform(0, 1, 2)
        if kind == 1:
            s[0] = 1.0
        if kind == 2:
            s = np.array([1.0, rng.uniform(0, 0.05)])
        B = U @ np.diag(s) @ V
    return rot_to_e0(B @ Fh, B @ Rt)


def sample_child_O1(rng, rho, chi, tries=400):
    """Uniform (a, r, psi) filtered by O1 (not necessarily O2)."""
    for _ in range(tries):
        a = rng.uniform(0, 1); r = rng.uniform(0, rho); psi = rng.uniform(0, math.pi)
        if o1_violation(a, r, psi, rho, chi)[0] <= 0:
            return np.array([a * math.cos(psi), a * math.sin(psi)]), np.array([r, 0.0])
    return sample_child_O2(rng, rho, chi)


# ----------------------------------------------------------------------------- multilinear maps
def contract(T, vecs):
    out = T
    for v in vecs:                       # T shape (d, 2, ..., 2); contract leading input slots
        out = np.tensordot(out, v, axes=([1], [0]))
    return out


def opnorm(T, m, fine=False):
    """Operator norm of T: (R^2)^m -> R^d. Returns (estimate, certified_upper)."""
    if m == 1:
        s = np.linalg.svd(T, compute_uv=False)[0]
        return s, s
    N = (8192 if fine else 2048) if m == 2 else (512 if fine else 256)
    ang = np.linspace(0, np.pi, N, endpoint=False)
    X = np.stack([np.cos(ang), np.sin(ang)], 1)
    h = np.pi / N
    if m == 2:
        M = np.einsum("kij,si->skj", T, X)
        g = np.linalg.svd(M, compute_uv=False)[:, 0].max()
        return g, g / (1 - h / 2)
    M = np.einsum("kijl,si,tj->stkl", T, X, X).reshape(N * N, T.shape[0], 2)
    g = np.linalg.svd(M, compute_uv=False)[:, 0].max()
    return g, g / (1 - h)


def sample_law(rng, m, d, eta, kind):
    shape = (d,) + (2,) * m
    if kind == "gauss":
        T = rng.normal(size=shape)
    elif kind == "phase":                  # complex multiplication with a random phase, embedded, + noise
        T = np.zeros(shape)
        th = rng.uniform(0, 2 * np.pi)
        idx = np.indices((2,) * m).reshape(m, -1).T
        for bits in idx:
            val = np.prod([1j if b else 1.0 for b in bits]) * np.exp(1j * th)
            T[(0,) + tuple(bits)] = val.real
            T[(2,) + tuple(bits)] = val.imag
        T += rng.normal(scale=rng.choice([0.0, 0.05, 0.3]), size=shape)
    elif kind == "rank1":
        T = np.einsum("k,i->ki", rng.normal(size=d), rng.normal(size=2))
        for _ in range(m - 1):
            T = np.multiply.outer(T, rng.normal(size=2))
    else:                                  # "tensor": Hilbert tensor embedding (m<=2 fits d=4)
        T = np.zeros(shape)
        idx = np.indices((2,) * m).reshape(m, -1).T
        for j, bits in enumerate(idx):
            T[(j % d,) + tuple(bits)] = 1.0
    est, _ = opnorm(T, m)
    return T / max(est, 1e-12)


def enforce_closure(T, m, P, eta):
    Q = np.eye(P.shape[0]) - P
    e0 = (0,) * m
    col = T[(slice(None),) + e0]
    q = Q @ col
    nq = np.linalg.norm(q)
    if nq > eta:
        T = T.copy()
        T[(slice(None),) + e0] = P @ col + q * (eta / nq)
    return T
