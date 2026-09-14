"""BBR (k=4: two singleton children -> bilinear parent -> root) adversarial search over R vs C.

Realization in dimension d (children and parent spaces C^d or R^d), P = e0 e0^* everywhere.
Children: unit F_a, F_b with ||Q F|| <= eta (parametrised by angle + unit normal direction).
Parent: bilinear mu: K^d x K^d -> K^d, normalised to operator norm 1 (estimated on a sample of
unit pairs + power iteration, then verified on a dense sample); closure ||Q mu(e0-sphere x e0-sphere)||
= |Q mu(e0,e0)| <= eta enforced by clipping. Root reads ||x - P y|| exactly (rank-one reader).
"""
import numpy as np, math, sys, json
field = sys.argv[1]; eta = float(sys.argv[2]); d = int(sys.argv[3]); seed = int(sys.argv[4])
rng = np.random.default_rng(seed)
cplx = field == "C"
TH = math.asin(eta)

def G4(eta, n=3):
    th = np.linspace(0, math.asin(eta), 200001)
    return float(np.max(np.abs(1 - (np.cos(th) * np.exp(1j * th)) ** n)))

def rand_unit(shape):
    z = rng.normal(size=shape + (d,)) + (1j * rng.normal(size=shape + (d,)) if cplx else 0)
    return z / np.linalg.norm(z, axis=-1, keepdims=True)

def opnorm(T, iters=60, starts=64):
    # T: (d,d,d) with mu(x,y)_k = sum T[k,i,j] x_i y_j ; alternating power iteration
    best = 0
    X = rand_unit((starts,)); Y = rand_unit((starts,))
    for _ in range(iters):
        V = np.einsum('kij,si,sj->sk', T, X, Y)
        W = V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-300)
        X = np.einsum('kij,sk,sj->si', T, W.conj(), Y).conj() if cplx else np.einsum('kij,sk,sj->si', T, W, Y)
        X /= np.linalg.norm(X, axis=1, keepdims=True)
        Y = np.einsum('kij,sk,si->sj', T, W.conj(), X).conj() if cplx else np.einsum('kij,sk,si->sj', T, W, X)
        Y /= np.linalg.norm(Y, axis=1, keepdims=True)
    V = np.einsum('kij,si,sj->sk', T, X, Y)
    return np.linalg.norm(V, axis=1).max()

def unpack(p):
    nT = d ** 3
    T = p[:nT].reshape(d, d, d) + (1j * p[nT:2 * nT].reshape(d, d, d) if cplx else 0)
    off = 2 * nT if cplx else nT
    def child(q):
        ang = TH / (1 + math.exp(-q[0]))
        nvec = q[1:d] + (1j * q[d:2 * d - 1] if cplx else 0)
        nvec = nvec / max(np.linalg.norm(nvec), 1e-12)
        F = np.zeros(d, dtype=complex if cplx else float); F[0] = math.cos(ang); F[1:] = math.sin(ang) * nvec
        return F
    L = 2 * d - 1 if cplx else d
    return T, child(p[off:off + L]), child(p[off + L:off + 2 * L])

def value(p, exact=False):
    T, Fa, Fb = unpack(p)
    T = T / opnorm(T, iters=(200 if exact else 25), starts=(4096 if exact else 32))
    q = T[1:, 0, 0]; nq = np.linalg.norm(q)
    if nq > eta:
        T = T.copy(); T[1:, 0, 0] *= eta / nq
        T = T / max(1.0, opnorm(T, iters=(200 if exact else 25), starts=(4096 if exact else 32)))
    Ra = np.zeros_like(Fa); Ra[0] = Fa[0]; Rb = np.zeros_like(Fb); Rb[0] = Fb[0]
    x = np.einsum('kij,i,j->k', T, Fa, Fb); y = np.einsum('kij,i,j->k', T, Ra, Rb)
    Py = np.zeros_like(y); Py[0] = y[0]
    return float(np.linalg.norm(x - Py))

dim = (2 * d ** 3 if cplx else d ** 3) + 2 * (2 * d - 1 if cplx else d)
best = (0, None)
for restart in range(int(sys.argv[5]) if len(sys.argv) > 5 else 6):
    p = rng.normal(size=dim); p[-1] = p[-(2 * d - 1 if cplx else d) - 1] = 3.0
    v = value(p); step = 0.3
    for it in range(4000):
        q = p + step * rng.normal(size=dim) * (rng.random(dim) < 0.3)
        vq = value(q)
        if vq > v:
            p, v = q, vq
        if it % 400 == 399:
            step *= 0.6
    ve = value(p, exact=True)
    if ve > best[0]:
        best = (ve, p)
print(json.dumps({"field": field, "eta": eta, "d": d, "seed": seed, "best_ratio": best[0] / eta,
                  "chain_ratio": G4(eta) / eta, "first_order_3": 3.0}), flush=True)
