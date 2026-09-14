"""Figure: the k=3 extremal landscape and its two regimes.

The sharp constant W_3 is usually read off a piecewise formula, which hides why
the transition sits at eta_c = sqrt(2/3). Geometrically the picture is simple:
there is a fixed surface

    E(q,s)^2 = q^2 + (1-q^2) s^2 + 2 q sqrt(1-q^2) s sqrt(1-s^2),

whose global maximum lives at (sqrt(2/3), sqrt(2/3)) with height 2/sqrt(3), and
the closure budget only controls how much of that surface is reachable: the
admissible region is the square [0, eta]^2. Below eta_c the corner of the square
is the best reachable point (budget-limited); at eta_c the corner reaches the
peak; beyond it the square keeps growing over terrain that is already lower
(geometry-limited), so the absolute worst-case error freezes.

E on the diagonal q = s = t is exactly g(t) = t sqrt(4 - 3 t^2), the function
whose stationary point gives t^2 = 2/3 -- so the diagonal section of this
surface is the curve behind the theorem.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

ETA_C = np.sqrt(2.0 / 3.0)
E_MAX = 2.0 / np.sqrt(3.0)


def surface(q, s):
    """Max projected error reachable from first leakage q and second leakage s."""
    return np.sqrt(q**2 + (1 - q**2) * s**2
                   + 2 * q * np.sqrt(1 - q**2) * s * np.sqrt(1 - s**2))


def G3(eta):
    """Absolute extremal error: eta * W_3(eta)."""
    eta = np.asarray(eta, dtype=float)
    return np.where(eta <= ETA_C, eta * np.sqrt(4 - 3 * eta**2), E_MAX)


def W3(eta):
    eta = np.asarray(eta, dtype=float)
    return np.where(eta <= ETA_C, np.sqrt(4 - 3 * eta**2), E_MAX / eta)


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(13.5, 5.8))

    # ---------------- left: the extremal mountain ----------------
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    n = 220
    g = np.linspace(0, 1, n)
    Q, S = np.meshgrid(g, g)
    Z = surface(Q, S)
    ax.plot_surface(Q, S, Z, cmap="viridis", alpha=0.72, linewidth=0,
                    antialiased=True, rstride=3, cstride=3)
    ax.contour(Q, S, Z, levels=12, zdir="z", offset=0, cmap="viridis",
               linewidths=0.6, alpha=0.55)

    t = np.linspace(0, 1, 400)
    ax.plot(t, t, surface(t, t), color="crimson", lw=2.2, zorder=6,
            label=r"diagonal $q=s$:  $g(t)=t\sqrt{4-3t^2}$")
    ax.scatter([ETA_C], [ETA_C], [E_MAX], color="crimson", s=70,
               edgecolor="white", linewidth=1.1, zorder=10, depthshade=False)
    ax.text(ETA_C, ETA_C, E_MAX + 0.12,
            r"$(\sqrt{2/3},\sqrt{2/3},\,2/\sqrt{3})$", color="crimson",
            fontsize=9, ha="center")

    # Budget squares on the floor: the admissible region [0, eta]^2.
    for eta, style in [(0.30, ":"), (0.55, ":"), (ETA_C, "-"), (0.95, "--")]:
        xs = [0, eta, eta, 0, 0]
        ys = [0, 0, eta, eta, 0]
        crit = abs(eta - ETA_C) < 1e-9
        ax.plot(xs, ys, zs=0, zdir="z", color="crimson" if crit else "0.25",
                lw=2.0 if crit else 1.0, ls=style, alpha=0.95 if crit else 0.6)
        ax.text(eta, -0.055, 0, rf"$\eta={eta:.2f}$" if not crit else r"$\eta_c$",
                fontsize=7.5, color="crimson" if crit else "0.3", ha="center")

    ax.set_xlabel(r"$q=\|D_1\|$   (first leakage)", fontsize=9, labelpad=2)
    ax.set_ylabel(r"$s=\|Qy\|$   (second leakage)", fontsize=9, labelpad=2)
    ax.set_zlabel(r"$E(q,s)$   surviving projected error", fontsize=9, labelpad=2)
    ax.set_zlim(0, 1.35)
    ax.view_init(elev=26, azim=-131)
    ax.set_title("Extremal landscape: the peak is fixed,\nonly the reachable square grows",
                 fontsize=10.5, pad=2)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.85)

    # ---------------- right: the two regimes ----------------
    ax2 = fig.add_subplot(1, 2, 2)
    e = np.linspace(1e-3, 1.0, 900)
    ax2.plot(e, G3(e), color="crimson", lw=2.4,
             label=r"$G_3(\eta)=\eta\,W_3(\eta)$   absolute error")
    ax2.plot(e, W3(e), color="steelblue", lw=2.0,
             label=r"$W_3(\eta)=C_3^{P,\mathrm{fin}}(\eta)$   constant")
    ax2.axhline(E_MAX, color="crimson", ls=":", lw=1.1)
    ax2.axvline(ETA_C, color="0.35", ls="--", lw=1.1)
    ax2.axhline(2.0, color="0.6", ls=":", lw=1.0)

    ax2.text(0.02, 2.03, r"universal bound $k-1=2$", fontsize=8, color="0.4")
    ax2.text(0.845, E_MAX + 0.035, r"$2/\sqrt{3}$", fontsize=9, color="crimson")
    ax2.text(ETA_C + 0.012, 0.16, r"$\eta_c=\sqrt{2/3}$", fontsize=9, rotation=90,
             color="0.3")
    ax2.annotate("budget-limited\n(extremizer spends the whole budget)",
                 xy=(0.40, G3(0.40)), xytext=(0.06, 1.55), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=0.9, color="0.35"))
    ax2.annotate("geometry-limited\n(absolute error frozen; only the\ndenominator keeps growing)",
                 xy=(0.93, E_MAX), xytext=(0.40, 0.42), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=0.9, color="0.35"))

    ax2.set_xlabel(r"$\eta=\rho/M$", fontsize=10)
    ax2.set_xlim(0, 1.0)
    ax2.set_ylim(0, 2.15)
    ax2.grid(alpha=0.25, lw=0.6)
    ax2.legend(loc="center right", fontsize=8.5, framealpha=0.9)
    ax2.set_title(r"Why $W_3$ decays after $\eta_c$: the numerator saturated",
                  fontsize=10.5)

    fig.tight_layout()
    paths = []
    for ext in ("png", "pdf"):
        p = out_dir / f"extremal_mountain.{ext}"
        fig.savefig(p, dpi=190 if ext == "png" else None, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


def self_check() -> None:
    """The picture must agree with the theorem, not merely look like it."""
    g = np.linspace(0, 1, 3001)
    Q, S = np.meshgrid(g, g)
    Z = surface(Q, S)
    i = np.unravel_index(np.nanargmax(Z), Z.shape)
    assert abs(Z[i] - E_MAX) < 1e-6, (Z[i], E_MAX)
    assert abs(Q[i] - ETA_C) < 2e-3 and abs(S[i] - ETA_C) < 2e-3
    t = np.linspace(0, 1, 20001)
    assert np.allclose(surface(t, t), t * np.sqrt(4 - 3 * t**2), atol=1e-12)
    for eta in (0.1, 0.3, 0.55, ETA_C, 0.8, 0.95, 1.0):
        mask = (Q <= eta + 1e-12) & (S <= eta + 1e-12)
        assert abs(np.nanmax(Z[mask]) - float(G3(eta))) < 2e-3, eta
    print("self-check passed: surface peak, diagonal section and budget maxima "
          "all agree with W_3")


if __name__ == "__main__":
    self_check()
    for p in build(Path(__file__).resolve().parent):
        print("wrote", p)
