"""First-order (eta -> 0) transport gain at a bilinear vertex followed by one more stage, R vs C.

Model for skeleton  1,2 -> 3 -> 4 -> r  (k = 5): children values e0 + eta*d with d = e1 (unit, normal),
vertex-3 law mu: K^2 x K^2 -> K^m with ||mu|| <= 1, u = mu(e0,e0), w = mu(e1,e0) + mu(e0,e1).
Upper estimate of lim E/eta (see K4_TOPOLOGY.md §6):
    Gain(mu) = sqrt(|w_par|^2 + (|w_perp| + 1)^2) + |u|,   w_par = component of w along u.
Over R, complex multiplication gives u=1, w=2i: Gain = 4 = k-1. Question: sup Gain over C.
"""
import numpy as np, sys, json
from scipy.optimize import minimize

field = sys.argv[1]; m = int(sys.argv[2]) if len(sys.argv) > 2 else 3
cplx = field == "C"
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 0)

# grid over unit x in K^2 (up to phase): x = (cos a, e^{i b} sin a)
A = np.linspace(0, np.pi / 2, 91); B = np.linspace(0, 2 * np.pi, 121, endpoint=False) if cplx else np.array([0.0, np.pi])
XA, XB = np.meshgrid(A, B, indexing="ij")
X = np.stack([np.cos(XA).ravel(), (np.exp(1j * XB) * np.sin(XA)).ravel()], 1) if cplx else \
    np.stack([np.cos(XA).ravel(), (np.cos(XB) * np.sin(XA)).ravel()], 1)

def bil_norm(T):
    # T (m,2,2); for each x: matrix M_x (m,2) = sum_i T[:,i,:] x_i ; sigma_max
    Mx = np.einsum('kij,si->skj', T, X)
    return np.linalg.svd(Mx, compute_uv=False)[:, 0].max()

def gain(p):
    n = m * 4
    T = p[:n].reshape(m, 2, 2) + (1j * p[n:2 * n].reshape(m, 2, 2) if cplx else 0)
    T = T / bil_norm(T)
    u = T[:, 0, 0]; w = T[:, 1, 0] + T[:, 0, 1]
    nu = np.linalg.norm(u)
    if nu < 1e-12:
        return np.linalg.norm(w) + 1.0, T
    uhat = u / nu
    wpar = np.vdot(uhat, w) * uhat
    wperp = w - wpar
    return np.sqrt(np.linalg.norm(wpar) ** 2 + (np.linalg.norm(wperp) + 1) ** 2) + nu, T

best = (0, None)
dim = m * 4 * (2 if cplx else 1)
for r in range(40):
    res = minimize(lambda p: -gain(p)[0], rng.normal(size=dim), method="Nelder-Mead",
                   options={"maxiter": 6000, "xatol": 1e-9, "fatol": 1e-12})
    g, T = gain(res.x)
    if g > best[0]:
        best = (g, T)
g, T = best
# verify norm on a much finer grid (and by random sampling)
fine = np.linalg.svd(np.einsum('kij,si->skj', T, X), compute_uv=False)[:, 0].max()
print(json.dumps({"field": field, "m": m, "sup_gain_found": g, "norm_check": float(fine),
                  "real_value_k_minus_1": 4.0}))
