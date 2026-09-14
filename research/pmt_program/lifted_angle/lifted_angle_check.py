"""Numerical checks for the lifted-angle proof of the tensor angle lemma and Lemma 3.

phi(f, g) := arccos(<f,g> + sqrt(1-|f|^2) sqrt(1-|g|^2))   for |f|, |g| <= 1
(the spherical distance between the hemisphere lifts (f, sqrt(1-|f|^2)) in G (+) R).

Checked (random + adversarial search, CPU, seeded):
  T1  triangle inequality     phi(f,h) <= phi(f,g) + phi(g,h)
  T2  contraction             ||lam|| <= 1  =>  phi(lam x, lam y) <= phi(x, y)
  T3  multilinear             ||mu|| <= 1   =>  phi(mu(x), mu(y)) <= sum_i phi(x_i, y_i)
  T4  projection identity     |g| <= 1, q = |Qg|, c = sqrt(1-q^2) > 0  =>  phi(g, Pg/c) = arcsin q
  T5  (N-) consequence        phi(f,g) <= S <= pi, t >= 0  =>  |f - t g|^2 <= 1 + t^2 - 2 t cos S
  T6  O2 equivalence          Gram(f,g) <= K(1,psi) for some psi <= S  <=>  phi(f,g) <= S

Run:  python research/pmt_program/lifted_angle/lifted_angle_check.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "outputs" / "lifted_angle_check.json"
rng = np.random.default_rng(20260914)


def phi(f, g):
    a = np.sqrt(max(0.0, 1 - f @ f))
    b = np.sqrt(max(0.0, 1 - g @ g))
    return float(np.arccos(np.clip(f @ g + a * b, -1.0, 1.0)))


def cphi(f, g):
    """cos(phi) without arccos (avoids the sqrt-amplification of rounding near cos = 1)."""
    return float(f @ g + np.sqrt(max(0.0, 1 - f @ f)) * np.sqrt(max(0.0, 1 - g @ g)))


def rand_ball(d, boundary_prob=0.3):
    v = rng.standard_normal(d)
    v /= np.linalg.norm(v)
    r = 1.0 if rng.random() < boundary_prob else rng.random() ** (1 / d)
    return r * v


def rand_contraction(dout, din):
    A = rng.standard_normal((dout, din))
    return A / np.linalg.norm(A, 2) * rng.uniform(0.2, 1.0)


def multilinear_apply(A, xs):
    """mu(x_1..x_m) = A (x_1 kron ... kron x_m); ||A||_op <= 1 gives ||mu|| <= 1."""
    t = xs[0]
    for x in xs[1:]:
        t = np.kron(t, x)
    return A @ t


worst = {"T1": -np.inf, "T2": -np.inf, "T3": -np.inf, "T4": 0.0, "T5": -np.inf, "T6_mismatch": 0}

# T1
for _ in range(20000):
    d = rng.integers(1, 6)
    f, g, h = rand_ball(d), rand_ball(d), rand_ball(d)
    worst["T1"] = max(worst["T1"], phi(f, h) - phi(f, g) - phi(g, h))

# T2
for _ in range(20000):
    din, dout = rng.integers(1, 6), rng.integers(1, 6)
    lam = rand_contraction(dout, din)
    x, y = rand_ball(din), rand_ball(din)
    worst["T2"] = max(worst["T2"], phi(lam @ x, lam @ y) - phi(x, y))
    # cosine form of T2: cos phi(lam x, lam y) >= cos phi(x, y)
    worst["T2_cos"] = max(worst.get("T2_cos", -np.inf), cphi(x, y) - cphi(lam @ x, lam @ y))

# T3 random
for _ in range(6000):
    m = rng.integers(1, 4)
    d = rng.integers(1, 4)
    dout = rng.integers(1, 5)
    A = rand_contraction(dout, d ** m)
    xs = [rand_ball(d) for _ in range(m)]
    ys = [rand_ball(d) for _ in range(m)]
    lhs = phi(multilinear_apply(A, xs), multilinear_apply(A, ys))
    rhs = sum(phi(x, y) for x, y in zip(xs, ys))
    worst["T3"] = max(worst["T3"], lhs - min(rhs, np.pi))

# T3 adversarial: random-restart hill climbing on the violation
adv_best = -np.inf
for _ in range(300):
    m = rng.integers(2, 4)
    d = 2
    dout = 2
    A = rand_contraction(dout, d ** m)
    xs = [rand_ball(d) for _ in range(m)]
    ys = [rand_ball(d) for _ in range(m)]

    def viol(A, xs, ys):
        return phi(multilinear_apply(A, xs), multilinear_apply(A, ys)) - sum(
            phi(x, y) for x, y in zip(xs, ys))

    cur = viol(A, xs, ys)
    step = 0.3
    for it in range(400):
        A2 = A + step * rng.standard_normal(A.shape)
        A2 /= max(1.0, np.linalg.norm(A2, 2))
        xs2 = [x + step * rng.standard_normal(d) for x in xs]
        ys2 = [y + step * rng.standard_normal(d) for y in ys]
        xs2 = [x / max(1.0, np.linalg.norm(x)) for x in xs2]
        ys2 = [y / max(1.0, np.linalg.norm(y)) for y in ys2]
        v = viol(A2, xs2, ys2)
        if v > cur:
            A, xs, ys, cur = A2, xs2, ys2, v
        else:
            step *= 0.995
    adv_best = max(adv_best, cur)
worst["T3_adversarial"] = adv_best

# T4
for _ in range(20000):
    d = rng.integers(2, 6)
    k = rng.integers(0, d + 1)
    U, _ = np.linalg.qr(rng.standard_normal((d, d)))
    P = U[:, :k] @ U[:, :k].T
    g = rand_ball(d)
    q = np.linalg.norm(g - P @ g)
    c = np.sqrt(max(0.0, 1 - q * q))
    if c < 1e-6:
        continue
    worst["T4"] = max(worst["T4"], abs(phi(g, P @ g / c) - np.arcsin(min(q, 1.0))))

# T5 and T6
for _ in range(20000):
    d = rng.integers(1, 5)
    f, g = rand_ball(d), rand_ball(d)
    p = phi(f, g)
    S = rng.uniform(p, np.pi)
    t = rng.uniform(0, 3)
    worst["T5"] = max(worst["T5"], (f - t * g) @ (f - t * g) - (1 + t * t - 2 * t * np.cos(S)))
    # T6: search psi on a grid in [0, S] for Gram <= K(1, psi)
    # T6: dense grid on [0, S2]; tolerance absorbs grid spacing (the feasible psi-set can be a point).
    S2 = rng.uniform(0, np.pi)
    if abs(p - S2) < 5e-3:
        continue
    G = np.array([[f @ f, f @ g], [f @ g, g @ g]])
    # det(K(c) - G) is concave in c = cos(psi) with maximum at c = G12, so over c in [cos S2, 1]
    # the best candidate is the clipped value; test it with a numerical eigen-solver.
    c_star = min(max(G[0, 1], np.cos(S2)), 1.0)
    K = np.array([[1.0, c_star], [c_star, 1.0]])
    ok = bool(np.linalg.eigvalsh(K - G).min() >= -1e-12)
    if ok != (p <= S2):
        worst["T6_mismatch"] += 1

report = {k: (float(v) if not isinstance(v, int) else v) for k, v in worst.items()}
report["note"] = "T1-T3,T5: max violation (<= ~1e-12 expected). T4: max abs error. T6: mismatches away from the boundary."
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
