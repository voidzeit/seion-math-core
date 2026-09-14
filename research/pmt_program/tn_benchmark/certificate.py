"""PMT-TN benchmark V1: certificate arithmetic.

All formulas refer to THEOREM_R_v2 (tag theorem-R-v2-review). With uniform law-norm budget M,
relative leakage eta = rho / M and leaf product L = prod ||z_l||, Theorem R gives

    E^P  <=  eta * C_k(eta) * M^k * L,      C_k(eta) = max_{0<=th<=asin eta} |1 - w(th)^(k-1)| / eta,

with w(th) = cos(th) e^{i th}. (Note M^k, not M^(k-1): C = E / (rho M^(k-1) L) and rho = eta M.)
The naive telescoping bound is (k-1) * eta * M^k * L.

G_k(eta) := eta * C_k(eta) = max_{th in [0, asin eta]} g_k(th),  g_k(th) = |1 - w(th)^(k-1)|.
It is computed from the exact critical points of g_k^2 (sign changes of the derivative on a fine
grid, refined by brentq) plus the endpoints; `G_k_mp` recomputes it in mpmath for replay.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
from scipy.optimize import brentq

import mpmath as mp


def g(theta: float, n: int) -> float:
    """g_k(th) = |1 - cos^n(th) e^{i n th}|, n = k - 1, evaluated stably as |expm1(X)| with
    X = n log cos(th) + i n th and log cos(th) = log1p(-sin^2 th) / 2 (no cancellation for small th)."""
    s = math.sin(theta)
    if s * s >= 1.0:
        return 1.0
    X = complex(0.5 * n * math.log1p(-s * s), n * theta)
    return float(abs(np.expm1(X)))


def g2(theta: float, n: int) -> float:
    """g_k(th)^2 with n = k - 1."""
    return g(theta, n) ** 2


def dg2(theta: float, n: int) -> float:
    """d/dth g_k(th)^2."""
    c, s = math.cos(theta), math.sin(theta)
    cn1 = c ** (n - 1) if n >= 1 else 0.0
    return (-2.0 * n * c ** (2 * n - 1) * s
            + 2.0 * n * cn1 * s * math.cos(n * theta)
            + 2.0 * n * c ** n * math.sin(n * theta))


def G_k(k: int, eta: float, grid: int = 20001) -> float:
    """eta * C_k(eta) = max over th in [0, asin eta] of |1 - w(th)^(k-1)| (float64)."""
    if k <= 1:
        return 0.0
    if not (0.0 < eta <= 1.0):
        raise ValueError(f"eta must lie in (0, 1], got {eta}")
    n = k - 1
    a = math.asin(eta)
    cands = [0.0, a]
    ts = np.linspace(0.0, a, grid)
    d = np.array([dg2(t, n) for t in ts])
    for i in range(grid - 1):
        if d[i] == 0.0:
            cands.append(float(ts[i]))
        elif d[i] * d[i + 1] < 0.0:
            cands.append(brentq(dg2, ts[i], ts[i + 1], args=(n,), xtol=1e-15, rtol=1e-15, maxiter=200))
    return max(g(t, n) for t in cands)


def C_k(k: int, eta: float) -> float:
    return G_k(k, eta) / eta if k > 1 else 0.0


def G_k_mp(k: int, eta: float, dps: int = 50, grid: int = 4001) -> mp.mpf:
    """High-precision replay of G_k (mpmath): grid + findroot refinement of critical points."""
    if k <= 1:
        return mp.mpf(0)
    with mp.workdps(dps):
        n = k - 1
        a = mp.asin(mp.mpf(eta))
        f = lambda t: 1 + mp.cos(t) ** (2 * n) - 2 * mp.cos(t) ** n * mp.cos(n * t)
        df = lambda t: mp.diff(f, t)
        cands = [mp.mpf(0), a]
        ts = [a * i / (grid - 1) for i in range(grid)]
        dv = [df(t) for t in ts]
        for i in range(grid - 1):
            if dv[i] * dv[i + 1] < 0:
                try:
                    cands.append(mp.findroot(df, (ts[i], ts[i + 1]), solver="anderson"))
                except (ValueError, ZeroDivisionError):
                    cands.append((ts[i] + ts[i + 1]) / 2)
        return mp.sqrt(max(f(t) for t in cands if 0 <= t <= a))


@dataclass
class Certificate:
    k: int
    eta_hat: float
    M_hat: float
    leaf_product: float
    E_obs: float
    F_norm: float
    B_naive: float
    B_R: float
    ratio_obs_to_BR: float
    gain_BR_over_naive: float
    deflation: float
    relative_certificate: float     # B_R / ||F_r||  (< 1 means informative)
    M_provenance: str

    def to_dict(self) -> dict:
        return asdict(self)


def certificate(k: int, eta_hat: float, M_hat: float, leaf_product: float, E_obs: float,
                F_norm: float, M_provenance: str) -> Certificate:
    eta_c = min(max(eta_hat, 1e-300), 1.0)
    scale = (M_hat ** k) * leaf_product
    B_naive = (k - 1) * eta_c * scale
    B_R = G_k(k, eta_c) * scale if k > 1 else 0.0
    ratio = E_obs / B_R if B_R > 0 else (math.inf if E_obs > 0 else 0.0)
    return Certificate(
        k=k, eta_hat=eta_hat, M_hat=M_hat, leaf_product=leaf_product, E_obs=E_obs, F_norm=F_norm,
        B_naive=B_naive, B_R=B_R, ratio_obs_to_BR=ratio,
        gain_BR_over_naive=(B_R / B_naive) if B_naive > 0 else float("nan"),
        deflation=(F_norm / scale) if scale > 0 else float("nan"),
        relative_certificate=(B_R / F_norm) if F_norm > 0 else float("inf"),
        M_provenance=M_provenance)


# ---------------------------------------------------------------- H1 replay protocol
TRIGGER = 1e-10


def classify(cert: Certificate, expected_violation: bool) -> str:
    """First-stage label. A float64 excess is only a replay trigger, never a conclusion."""
    if cert.ratio_obs_to_BR > 1.0 + TRIGGER:
        return "EXPECTED_VIOLATION_NEGATIVE_CONTROL" if expected_violation else "REPLAY_TRIGGERED"
    return "EXPECTED_VIOLATION_MISSING" if expected_violation else "WITHIN_CERTIFICATE"
