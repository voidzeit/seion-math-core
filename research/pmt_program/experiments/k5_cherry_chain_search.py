"""k=5 skeleton  1,2 -> 3 -> 4 -> r  (cherry, one linear stage, root), real field (PMT-A).

Outer: children angles alpha, beta <= asin(eta) (unit children, R1) and the vertex-3 bilinear law
T: R^2 x R^2 -> R^4 with P_3 = diag(1,1,0,0); normalised to norm 1 on a fine grid, closure
||Q_3 T(e0,e0)|| <= eta by clipping.
Inner: the Gram SDP of EXACT_CERTIFICATES.md §1 started from the state list X_0 = (R_3, e_3)
(one active linear stage, then the lossless root reader). By Lemma V it is an UPPER bound on the
continuation value, so  max_outer SDP  >=  true sup  >= chain witness value.
If max_outer SDP never exceeds G_5(eta) the skeleton shows no topology dependence at that eta.
"""
import numpy as np, math, sys, json
import cvxpy as cp

eta = float(sys.argv[1]); seed = int(sys.argv[2]); iters = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
rng = np.random.default_rng(seed)
TH = math.asin(eta)
D = 4
P3 = np.diag([1.0, 1.0, 0.0, 0.0]); Q3 = np.eye(D) - P3

def G_chain(n, eta):
    th = np.linspace(0, math.asin(eta), 200001)
    return float(np.max(np.abs(1 - (np.cos(th) * np.exp(1j * th)) ** n)))

# ---- inner SDP, parametrised by the initial Gram data (n = 2 list: (R, e))
def selectors(n):
    tp = np.zeros((2 * n, n + 1)); tq = np.zeros_like(tp)
    tp[0, 0] = 1; tq[0, n] = 1
    for i in range(1, n):
        tp[i, i] = tp[n + i, i] = 1; tq[i, i] = tq[n + i, i] = 1
    return tp, tq

GP0 = cp.Parameter((2, 2), symmetric=True); GQ0 = cp.Parameter((2, 2), symmetric=True)
HP = cp.Variable((4, 4), symmetric=True); HQ = cp.Variable((4, 4), symmetric=True)
Z = np.zeros((2, 2))
gin = cp.bmat([[GP0, Z], [Z, GQ0]])
tp, tq = selectors(2)
a = np.array([0.0, 1.0, 1.0])
obj = cp.quad_form(a, tp.T @ HP @ tp + tq.T @ HQ @ tq, assume_PSD=False) if False else \
    cp.sum(cp.multiply(np.outer(a, a), tp.T @ HP @ tp + tq.T @ HQ @ tq))
prob = cp.Problem(cp.Maximize(obj), [HP >> 0, HQ >> 0, gin - HP - HQ >> 0, eta ** 2 * GP0 - HQ[:2, :2] >> 0])

def inner(R, e):
    gp = np.array([[P3 @ R @ P3 @ R, P3 @ R @ P3 @ e], [P3 @ e @ P3 @ R, P3 @ e @ P3 @ e]])
    gq = np.array([[0.0, 0.0], [0.0, Q3 @ e @ Q3 @ e]])
    GP0.value = (gp + gp.T) / 2; GQ0.value = gq
    try:
        v = prob.solve(solver="CLARABEL")
    except Exception:
        return 0.0
    return math.sqrt(max(v, 0.0)) if v is not None else 0.0

S = np.linspace(0, np.pi, 1024, endpoint=False)
Xg = np.stack([np.cos(S), np.sin(S)], 1)

def norm_bil(T):
    M = np.einsum('kij,si->skj', T, Xg)          # (m, D, 2)
    return np.linalg.svd(M, compute_uv=False)[:, 0].max()

def evaluate(p):
    al = TH * min(max(p[0], 0.0), 1.0); be = TH * min(max(p[1], 0.0), 1.0)
    T = p[2:].reshape(D, 2, 2).copy()
    T /= norm_bil(T)
    q = Q3 @ T[:, 0, 0]; nq = np.linalg.norm(q)
    if nq > eta:
        T[:, 0, 0] = P3 @ T[:, 0, 0] + q * (eta / nq)
        T /= max(1.0, norm_bil(T))
    Fa = np.array([math.cos(al), math.sin(al)]); Fb = np.array([math.cos(be), math.sin(be)])
    f = np.einsum('kij,i,j->k', T, Fa, Fb)
    g = T[:, 0, 0] * math.cos(al) * math.cos(be)
    R = P3 @ g; e = f - R
    return inner(R, e), (al, be, T)

gref = G_chain(4, eta)
# start near the Theorem-U witness: complex multiplication with phase, embedded in R^4
def witness_params(th):
    T = np.zeros((D, 2, 2))
    c, s = math.cos(th), math.sin(th)
    # x~ y~ e^{i th}: real part -> coord 0, imaginary part -> coord 2 (a Q-direction)
    base = np.zeros((2, 2, 2)); base[0, 0, 0] = 1; base[0, 1, 1] = -1; base[1, 0, 1] = 1; base[1, 1, 0] = 1
    rot = np.array([[c, -s], [s, c]])
    Tm = np.einsum('ab,bij->aij', rot, base)
    T[0] = Tm[0]; T[2] = Tm[1]
    return np.concatenate([[th / TH, th / TH], T.ravel()])

best = (0.0, None)
th_star = float(np.linspace(0, TH, 200001)[np.argmax(np.abs(1 - (np.cos(np.linspace(0, TH, 200001)) * np.exp(1j * np.linspace(0, TH, 200001))) ** 4))])
w0 = witness_params(th_star)
v_w0, _ = evaluate(w0)
starts = [w0, w0, w0] + [np.concatenate([rng.uniform(0.3, 1.0, 2), rng.normal(size=D * 4)]) for _ in range(3)]
for p0 in starts:
    p = p0.copy(); v, _ = evaluate(p); step = 0.05 if p0 is w0 else 0.2
    for it in range(iters // len(starts)):
        q = p + step * rng.normal(size=p.size) * (rng.random(p.size) < 0.35)
        vq, _ = evaluate(q)
        if vq > v:
            p, v = q, vq
        if it % 150 == 149:
            step = max(step * 0.7, 1e-4)
    if v > best[0]:
        best = (v, p)
print(json.dumps({"skeleton": "1,2->3->4->r", "eta": eta, "seed": seed, "chain_G5": gref,
                  "witness_at_theta_star_sdp_value": v_w0, "best_sdp_upper_value": best[0], "excess": best[0] - gref}), flush=True)
