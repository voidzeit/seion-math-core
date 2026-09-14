import numpy as np
rng = np.random.default_rng(1)
best = 0; arg=None
for rep in range(60):
    n = 2_000_000
    a, b, g = np.sort(rng.uniform(0, np.pi/2, (3, n)), axis=0)  # a<=b<=g
    p, q = rng.uniform(0, np.pi/2, (2, n))
    kap = -np.cos(a + b)
    ok = (a + b > np.pi/2) & (kap > np.cos(g)*np.cos(p)*np.cos(q) + np.sin(p)*np.sin(q))
    val = (np.cos(p) + np.cos(a)*np.cos(b)*np.cos(g)*np.cos(q))**2
    val = np.where(ok, val, 0)
    i = int(np.argmax(val))
    if val[i] > best: best, arg = val[i], (a[i], b[i], g[i], p[i], q[i])
print("STAR residual sup ~", best, "sqrt", np.sqrt(best), "vs 81/49 =", 81/49, "args", arg)
# BBR residual: 1 + 2 r kappa + r^2 with r <= (1-kappa)/2
k = np.linspace(0,1,1000001); print("BBR residual sup", (1 + (1-k)*k + (1-k)**2/4).max(), "(4/3)")
