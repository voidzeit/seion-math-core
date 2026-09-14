"""W_3: the SOS inequality, the equality geometry, and the attaining witness.

Reproduces every step of CANONICAL_W3_PROOF.md that is checkable by machine.
Runs in seconds and depends only on numpy.

    Step 3   the SOS identity  4(1+u^2)(1+v^2) - 3[(u+v)^2+u^2v^2]
                                 = (uv-2)^2 + (u-v)^2
    Step 4   W_3 is an upper bound for f on the feasible square
    Step 5   equality iff u = v = sqrt2, i.e. q = s = sqrt(2/3)
    Step 6   the witness attains W_3 in both regimes

NUMERICAL ROLE: this file AUDITS an analytic proof. It is not the evidence for
W_3. The proof is in CANONICAL_W3_PROOF.md; these numbers only fail loudly if
that proof was transcribed wrong.
"""

from __future__ import annotations

import math
import sys

import numpy as np

ETA_C = math.sqrt(2 / 3)
TOL = 1e-12
failures = []


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {name}" + (f"   {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def w3(eta):
    return math.sqrt(4 - 3 * eta ** 2) if eta <= ETA_C else 2 / (math.sqrt(3) * eta)


def f_uv(u, v):
    return ((u + v) ** 2 + u ** 2 * v ** 2) / ((1 + u ** 2) * (1 + v ** 2))


# --------------------------------------------------------------- Step 3
print("\nStep 3 -- the SOS identity that produces 4 - 3 eta^2")
rng = np.random.default_rng(20260825)
worst = 0.0
for _ in range(200_000):
    u, v = rng.uniform(-6, 6, 2)
    lhs = 4 * (1 + u ** 2) * (1 + v ** 2) - 3 * ((u + v) ** 2 + u ** 2 * v ** 2)
    rhs = (u * v - 2) ** 2 + (u - v) ** 2
    worst = max(worst, abs(lhs - rhs))
check("identity holds as an exact polynomial identity", worst < 1e-9,
      f"max |lhs - rhs| = {worst:.3e} over 200k random (u,v)")
check("hence f <= 4/3 unconditionally",
      max(f_uv(*rng.uniform(-6, 6, 2)) for _ in range(200_000)) <= 4 / 3 + 1e-12)

# --------------------------------------------------------------- Step 4
print("\nStep 4 -- W_3 bounds f on the feasible square")
worst_ratio = 0.0
for eta in np.linspace(0.02, 1.0, 99):
    top = math.tan(math.asin(min(eta, 1.0))) if eta < 1 else 1e9
    grid = np.linspace(0, top, 400)
    best = max(f_uv(u, v) for u in grid for v in grid[::8])
    # f is the SQUARE of E/(M^3 L_T); the constant divides by eta
    achieved = math.sqrt(best) / eta
    worst_ratio = max(worst_ratio, achieved / w3(eta))
check("no feasible (u,v) exceeds W_3", worst_ratio <= 1 + 1e-6,
      f"max achieved/W_3 = {worst_ratio:.9f}")

# --------------------------------------------------------------- Step 5
print("\nStep 5 -- equality geometry")
u_star = math.sqrt(2)
check("f(sqrt2, sqrt2) = 4/3 exactly", abs(f_uv(u_star, u_star) - 4 / 3) < TOL,
      f"f = {f_uv(u_star, u_star):.15f}")
q_star = math.sin(math.atan(u_star))
check("u = v = sqrt2  <=>  q = s = sqrt(2/3)", abs(q_star - ETA_C) < TOL,
      f"q* = {q_star:.15f},  sqrt(2/3) = {ETA_C:.15f}")
# the interior optimum becomes feasible exactly at eta_c
feasible_below = math.tan(math.asin(ETA_C - 1e-6)) < u_star
feasible_above = math.tan(math.asin(min(ETA_C + 1e-6, 1.0))) >= u_star
check("interior optimum infeasible below eta_c, feasible above",
      feasible_below and feasible_above)
angle = math.degrees(math.asin(ETA_C))
check("frozen extremizer angle above eta_c", abs(angle - 54.7356103) < 1e-5,
      f"arcsin sqrt(2/3) = {angle:.7f} deg")

# --------------------------------------------------------------- Step 6
print("\nStep 6 -- the witness attains W_3 in both regimes")


def witness_error(eta):
    """The M14 construction, evaluated exactly as in CANONICAL_W3_PROOF.md."""
    t = min(eta, ETA_C)
    p = math.sqrt(1 - t * t)
    c = math.sqrt(1 - t * t)
    e0, e1 = np.array([1.0, 0.0]), np.array([0.0, 1.0])
    P = np.outer(e0, e0)

    mu1 = lambda x, y: (x @ e0) * (y @ e0) * (t * e1 + p * e0)
    N_t = np.column_stack([t * e1 - c * e0, c * e1 + t * e0])   # N_t e0, N_t e1
    mu2 = lambda x, y: (y @ e0) * (N_t @ x)

    D1, R1 = (np.eye(2) - P) @ mu1(e0, e0), P @ mu1(e0, e0)
    # exact second-node error split
    err2 = t * (N_t @ e1) + p * ((np.eye(2) - P) @ (N_t @ e0))
    return float(np.linalg.norm(err2)), t, N_t


worst_gap, worst_norm, worst_leak = 0.0, 0.0, 0.0
for eta in [0.05, 0.2, 0.5, ETA_C, 0.85, 0.95, 1.0]:
    err, t, N_t = witness_error(eta)
    predicted = t * math.sqrt(4 - 3 * t * t)
    worst_gap = max(worst_gap, abs(err / eta - w3(eta)))
    worst_norm = max(worst_norm, abs(np.linalg.norm(N_t, 2) - 1.0))
    worst_leak = max(worst_leak, t - eta)          # must be <= 0: within budget
    print(f"    eta = {eta:.4f}   E/eta = {err/eta:.12f}   "
          f"W_3 = {w3(eta):.12f}   active leakage t = {t:.6f}")
check("witness attains W_3 at every tested eta", worst_gap < 1e-12,
      f"max |E/eta - W_3| = {worst_gap:.3e}")
check("witness law N_t is orthogonal (operator norm 1)", worst_norm < 1e-12)
check("witness never exceeds its closure budget", worst_leak <= 1e-15,
      "and deliberately underuses it above eta_c -- V5 freeze defect C1")

print("\n" + ("PASS" if not failures else f"FAILED: {failures}"))
sys.exit(1 if failures else 0)
