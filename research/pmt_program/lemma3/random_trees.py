"""End-to-end sanity check of Theorem R on random trees (k <= 6, arities <= 3), real PMT-A laws.

Each internal vertex: state space R^d (d=3), law (R^d)^m -> R^d built as a small perturbation of the
Theorem-U phase witness (embedded in the first two coordinates) plus Gaussian noise; normalized by a heuristic
operator-norm estimate (alternating maximisation x 1.02); full-subspace closure is NOT enforced, only trajectory closure
(the larger class in which the upper bound is claimed). Reports max E^P/eta vs C_k(eta).
usage: python random_trees.py n_trees seed
"""
import json, math, sys
import numpy as np

n_trees, seed = int(sys.argv[1]), int(sys.argv[2])
rng = np.random.default_rng(seed)
d = 3


def Ck(k, eta):
    th = np.linspace(0, math.asin(eta), 20001)
    return float(np.max(np.abs(1 - (np.cos(th) * np.exp(1j * th)) ** (k - 1)))) / eta


def random_skeleton(k):
    parent = [None] + [int(rng.integers(0, i)) for i in range(1, k)]   # vertex 0 = root
    kids = [[] for _ in range(k)]
    for v in range(1, k):
        kids[parent[v]].append(v)
    return kids if max(len(c) for c in kids) <= 3 else random_skeleton(k)


def unit_sphere(n, dim):
    x = rng.normal(size=(n, dim)); return x / np.linalg.norm(x, axis=1, keepdims=True)


def norm_upper(T, m):
    """Operator norm estimate: exact for m <= 1; alternating maximisation from 256 starts for m >= 2,
    inflated by 2% (heuristic safety factor, NOT a certificate)."""
    if m == 0:
        return float(np.linalg.norm(T))
    if m == 1:
        return float(np.linalg.svd(T, compute_uv=False)[0])
    xs = [unit_sphere(256, d) for _ in range(m)]
    for _ in range(80):
        for j in range(m):
            out = contract_batch(T, xs)
            w = out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-300)
            g = grad_slot(T, xs, w, j)
            xs[j] = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-300)
    return float(np.linalg.norm(contract_batch(T, xs), axis=1).max()) * 1.02


def contract_batch(T, xs):
    letters = "abcdefg"
    m = len(xs)
    expr = "o" + letters[:m] + "," + ",".join("N" + letters[i] for i in range(m)) + "->No"
    return np.einsum(expr, T, *xs)


def grad_slot(T, xs, w, j):
    letters = "abcdefg"; m = len(xs)
    ins = ["N" + letters[i] for i in range(m) if i != j]
    expr = "o" + letters[:m] + ",No," + ",".join(ins) + ("->N" + letters[j])
    args = [T, w] + [xs[i] for i in range(m) if i != j]
    if not ins:
        expr = "o" + letters[:m] + ",No->N" + letters[j]; args = [T, w]
    return np.einsum(expr, *args)


def phase_law(m, th, noise):
    T = np.zeros((d,) + (d,) * m)
    for bits in np.ndindex(*(2,) * m):
        val = np.exp(1j * th) * np.prod([1j if b else 1.0 for b in bits])
        T[(0,) + bits] = val.real; T[(1,) + bits] = val.imag
    return T + noise * rng.normal(size=T.shape)


worst = {"ratio_to_Ck": -1}
records = []
for t in range(n_trees):
    k = int(rng.integers(2, 7)); eta = float(rng.choice([0.1, 0.3, 0.5, 0.7, 0.9]))
    kids = random_skeleton(k)
    TH = math.asin(eta)
    th = TH * rng.choice([1.0, rng.uniform(0.3, 1.0)])
    noise = float(rng.choice([0.0, 0.02, 0.1, 0.5]))
    P = np.diag([1.0, 0.0, 0.0]) if rng.random() < 0.7 else np.diag([1.0, 1.0, 0.0])
    Q = np.eye(d) - P
    F = [None] * k; R = [None] * k
    for v in reversed(range(k)):          # children have larger indices
        m = len(kids[v])
        if m == 0:
            f = np.zeros(d); f[0] = math.cos(th); f[1] = math.sin(th)
            f = f + noise * rng.normal(size=d); f /= max(1.0, np.linalg.norm(f))
            q = Q @ f
            if np.linalg.norm(q) > eta:
                f = P @ f + q * eta / np.linalg.norm(q)
            F[v] = f; R[v] = P @ f
            continue
        T = phase_law(m, th if v != 0 else rng.uniform(0, 2 * np.pi), noise)
        T = T / norm_upper(T, m)
        Fin = [F[c] for c in kids[v]]; Rin = [R[c] for c in kids[v]]
        yR = contract_batch(T, [r[None, :] for r in Rin])[0]
        # trajectory closure: |Q mu(R)| <= eta prod |R|
        bound = eta * float(np.prod([np.linalg.norm(r) for r in Rin]))
        if v != 0 and np.linalg.norm(Q @ yR) > bound + 1e-15:
            scale = bound / np.linalg.norm(Q @ yR)
            T = np.einsum("pq,q...->p...", P, T) + scale * np.einsum("pq,q...->p...", Q, T)
        F[v] = contract_batch(T, [f[None, :] for f in Fin])[0]
        y = contract_batch(T, [r[None, :] for r in Rin])[0]
        R[v] = P @ y if v != 0 else y
    EP = float(np.linalg.norm(P @ (F[0] - R[0])))
    ratio = (EP / eta) / Ck(k, eta)
    rec = {"k": k, "eta": eta, "kids": kids, "noise": noise, "EP_over_eta": EP / eta, "Ck": Ck(k, eta), "ratio_to_Ck": ratio}
    records.append(rec)
    if ratio > worst["ratio_to_Ck"]:
        worst = rec
json.dump({"worst": worst, "n": n_trees, "count_ratio_gt_1": sum(r["ratio_to_Ck"] > 1 + 1e-9 for r in records)},
          open(f"outputs/random_trees_s{seed}.json", "w"), indent=1)
print(json.dumps({"n": n_trees, "max_ratio_to_Ck": worst["ratio_to_Ck"], "worst_k": worst["k"], "worst_eta": worst["eta"],
                  "worst_noise": worst["noise"], "count_ratio_gt_1": sum(r["ratio_to_Ck"] > 1 + 1e-9 for r in records)}))
