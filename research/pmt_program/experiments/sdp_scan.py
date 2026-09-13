import numpy as np, math, sys
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "math_closure", "k4_exploration"))
from chain_gram_sdp import solve_chain_sdp
def G(n, eta):
    th = np.linspace(0, math.asin(eta), 200001)
    return np.max(np.abs(1 - (np.cos(th)*np.exp(1j*th))**n))
for n in (2,3,4,5):
    for eta in (0.02, 0.05, 0.1, 0.3, 0.5, 0.6, 0.8, 1.0):
        r = solve_chain_sdp(eta, active_stages=n)
        C_sdp = r["normalized_error"]; C_th = G(n, eta)/eta
        extra = f" (n-C)/eta^2 = {(n-C_sdp)/eta**2:.6f}" if eta <= 0.1 else ""
        print(f"k={n+1} eta={eta:4.2f} SDP C={C_sdp:.9f} formula C={C_th:.9f} diff={C_sdp-C_th:+.2e} [{r['solver_status']}]{extra}", flush=True)
