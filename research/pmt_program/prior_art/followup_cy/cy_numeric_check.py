"""PRIOR-ART-R-CY heuristic numerical check (NOT a proof).

Compares the Combettes-Yamada 2015 composition constant (Prop. 2.5, eq. (2.8))
    phi(alpha_1..alpha_m) = 1 / (1 + 1 / sum_i alpha_i/(1-alpha_i))
with the PMT constant
    gBox(eta) = max_{theta_u in [0, arcsin eta_u]} |1 - prod_u w(theta_u)|,  w(t) = cos t e^{it}.

Facts used (elementary, re-derived here, checked numerically below):
  * c lies in the SRG disk D(1-a, a) of a-averaged operators  iff  a >= amin(c) := |1-c|^2 / (2 (1 - Re c)).
  * For c = w(t), |1-w|^2 = sin^2 t = 1 - Re w, so amin(w(t)) = 1/2 for every t in (0, pi/2]: every point of the
    arc lies on the boundary circle of D(1/2, 1/2); no disk D(1-a, a) with a < 1/2 contains any arc point but 1.
  * max_{z in D(1-a, a)} |1 - z| = 2a (attained at z = 1 - 2a).
Correspondences (preregistered, PROTOCOL_CY.md 3.6):
  (A) containment: alpha_u = inf{a : w([0, arcsin eta_u]) subset D(1-a, a)} = 1/2 for eta_u > 0.
      phi-averagedness of the composition then gives the valid but cap-blind bound gBox <= 2 phi = 2m/(m+1).
  (B) single-factor matching: alpha_u = eta_u / 2 (so 2 alpha_u = max_t |1 - w(t)| = eta_u). Not a containment,
      so 2 phi(eta/2) is NOT a proven bound on gBox; we only record whether it happens to dominate.
Also: (T) tightness of phi in the planar complex-scalar model for m = 3, 4 (sup over products of boundary points of
D(1-a_i, a_i) of amin(prod c_i) vs phi), and (D) max |1 - z| over the product of full disks vs 2 phi.

Run: python cy_numeric_check.py  (writes cy_numeric_check_output.txt next to this file)
"""
from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "cy_numeric_check_output.txt"
LINES: list[str] = []


def say(s: str = "") -> None:
    print(s)
    LINES.append(s)


def phi(alphas) -> float:
    k = sum(a / (1 - a) for a in alphas)
    return 1.0 / (1.0 + 1.0 / k)


def w(t):
    return np.cos(t) * np.exp(1j * t)


def amin(c):
    c = np.asarray(c)
    den = 2 * (1 - c.real)
    return np.where(den > 1e-300, np.abs(1 - c) ** 2 / np.maximum(den, 1e-300), 0.0)


def box_max(f, caps, n=None, refine=6):
    """Maximize f(theta vector) over prod [0, cap_u]: vectorized grid, then shrinking local grids."""
    m = len(caps)
    n = n or {1: 2001, 2: 801, 3: 161, 4: 61, 5: 25}[m]
    grids = [np.linspace(0, c, n) for c in caps]
    best_val, best_x = -1.0, None
    # chunk over first coordinate to save memory
    for i0, t0 in enumerate(grids[0]):
        mesh = np.meshgrid(*([np.array([t0])] + grids[1:]), indexing="ij")
        vals = f(mesh)
        j = np.unravel_index(np.argmax(vals), vals.shape)
        if vals[j] > best_val:
            best_val = float(vals[j])
            best_x = np.array([mesh[k][j] for k in range(m)])
    h = np.array(caps) / (n - 1)
    for _ in range(refine):
        loc = [np.clip(np.linspace(best_x[k] - h[k], best_x[k] + h[k], 21), 0, caps[k]) for k in range(m)]
        mesh = np.meshgrid(*loc, indexing="ij")
        vals = f(mesh)
        j = np.unravel_index(np.argmax(vals), vals.shape)
        if vals[j] >= best_val:
            best_val = float(vals[j])
            best_x = np.array([mesh[k][j] for k in range(m)])
        h = h / 10
    return best_val, best_x


def gbox(eta):
    caps = [math.asin(e) for e in eta]

    def f(mesh):
        z = np.ones_like(mesh[0], dtype=complex)
        for t in mesh:
            z = z * w(t)
        return np.abs(1 - z)

    return box_max(f, caps)


def main() -> None:
    say("PRIOR-ART-R-CY numerical heuristic check (not a proof). numpy " + np.__version__)
    # sanity: amin on the circle |z-1/2|=1/2
    ts = np.linspace(1e-3, math.pi / 2, 1000)
    say(f"[fact] amin(w(t)) over t in (0,pi/2]: min={amin(w(ts)).min():.12f} max={amin(w(ts)).max():.12f} (expect 1/2)")
    say(f"[fact] max|1-w(t)| on [0,asin eta] = eta: eta=0.3 -> {np.abs(1 - w(np.linspace(0, math.asin(0.3), 10001))).max():.12f}")
    say()
    etas = [
        (1.0,), (0.3,),
        (1.0, 1.0), (0.5, 0.5), (0.2, 0.9), (0.1, 0.1),
        (1.0, 1.0, 1.0), (0.3, 0.3, 0.3), (0.1, 0.5, 0.9), (0.05, 0.05, 0.05), (0.9, 0.9, 0.2),
        (1.0, 1.0, 1.0, 1.0), (0.2, 0.4, 0.6, 0.8), (0.1, 0.1, 0.1, 0.1),
    ]
    say("eta | gBox | (A) 2*phi(1/2,..)=2m/(m+1) | A valid? | (B) 2*phi(eta/2) | B >= gBox? | ratio B/gBox | sum eta (first order)")
    for eta in etas:
        m = len(eta)
        g, x = gbox(eta)
        A = 2 * phi([0.5] * m)
        B = 2 * phi([e / 2 for e in eta])
        say(f"{eta} | {g:.6f} | {A:.6f} | {g <= A + 1e-9} | {B:.6f} | {B >= g - 1e-9} | {B / g:.4f} | {sum(eta):.3f}"
            f"   argmax theta={np.round(x, 4).tolist()} caps={[round(math.asin(e), 4) for e in eta]}")
    say()
    # placement independence sanity (trivial for the scalar functional: product commutes)
    g1, _ = gbox((0.1, 0.5, 0.9))
    g2, _ = gbox((0.9, 0.1, 0.5))
    say(f"[perm] gBox(0.1,0.5,0.9)={g1:.9f}  gBox(0.9,0.1,0.5)={g2:.9f}")
    say()
    # (T) tightness of phi in the planar complex-scalar model
    say("(T) planar scalar model: c_i = 1-a_i + a_i e^{i psi_i};  sup amin(prod c_i) vs phi(a)")
    rng = np.random.default_rng(20260914)
    for alphas in [(0.5, 0.5, 0.5), (0.2, 0.5, 0.8), (0.1, 0.3, 0.6, 0.9), (0.5, 0.5)]:
        m = len(alphas)
        a = np.array(alphas)
        best = 0.0
        # global random sample
        for _ in range(40):
            psi = rng.uniform(-math.pi, math.pi, size=(20000, m))
            c = np.prod(1 - a + a * np.exp(1j * psi), axis=1)
            best = max(best, float(amin(c).max()))
        # near z = 1: psi_i = s * r_i with small s and weights matching curvature (psi_i proportional to 1/alpha_i * kappa_i?)
        near = []
        for s in (1e-1, 1e-2, 1e-3):
            psis = rng.normal(size=(20000, m)) * s
            c = np.prod(1 - a + a * np.exp(1j * psis), axis=1)
            near.append(float(amin(c).max()))
        say(f"alpha={alphas} phi={phi(alphas):.6f}  global sup~{best:.6f}  near-1 sup (s=.1,.01,.001)={[round(v, 6) for v in near]}"
            f"  exceeds phi? {max([best] + near) > phi(alphas) + 1e-9}")
    say()
    # (D) max |1-z| over the product of full disks D(1-a_i, a_i) (= over boundary circles by the maximum principle)
    say("(D) max |1 - prod c_i| over product of disks D(1-a_i,a_i)  vs  2 phi(a)   [distance functional vs averagedness]")
    for alphas in [(0.5, 0.5), (0.5, 0.5, 0.5), (0.2, 0.5, 0.8), (0.05, 0.05, 0.05)]:
        m = len(alphas)
        a = np.array(alphas)

        def f(mesh, a=a):
            z = np.ones_like(mesh[0], dtype=complex)
            for k, t in enumerate(mesh):
                z = z * (1 - a[k] + a[k] * np.exp(1j * t))
            return np.abs(1 - z)

        v, _ = box_max(f, [2 * math.pi] * m)
        say(f"alpha={alphas}  max|1-z|={v:.6f}  2phi={2 * phi(alphas):.6f}  sum 2a_i={2 * sum(alphas):.3f}")
    say()
    say("Interpretation guide: (A) is valid but independent of eta (cap-blind); (B) is not a containment and is recorded only")
    say("as a heuristic comparison; (T) tests whether phi is the supremum in the planar scalar model (tightness heuristic);")
    say("(D) shows whether a sharp averagedness constant also gives the sharp distance-from-1 functional.")
    OUT.write_text("\n".join(LINES) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
