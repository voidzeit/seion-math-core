"""Build the registered vector figure suite for research-v2."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIGURE_ROOT = ROOT / "papers" / "foundations_v2" / "figures"
sys.path.insert(0, str(ROOT / "papers" / "foundations_v2"))
from figure_style import PALETTE, apply_style  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def num(row: dict[str, str], key: str) -> float:
    return float(row[key])


def save_figure(fig: plt.Figure, name: str) -> None:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_ROOT / f"{name}.pdf", metadata={"Creator": "SEION Math Core research_v2.1"})
    fig.savefig(FIGURE_ROOT / f"{name}.svg", metadata={"Creator": "SEION Math Core research_v2.1"})
    plt.close(fig)


def add_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = PALETTE["gray"]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color=color,
            shrinkA=5,
            shrinkB=5,
        )
    )


def box(ax, center: tuple[float, float], label: str, color: str, width: float = 1.35) -> None:
    x, y = center
    patch = FancyBboxPatch(
        (x - width / 2, y - 0.28),
        width,
        0.56,
        boxstyle="round,pad=0.035,rounding_size=0.06",
        facecolor="white",
        edgecolor=color,
        linewidth=1.5,
    )
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center", color=PALETTE["gray"])


def fig01_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.0, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")
    centers = [(0.8, 1.15), (2.35, 1.15), (3.9, 1.15), (5.45, 1.15), (7.0, 1.15), (8.65, 1.15)]
    labels = [r"$(V,\mu)$", r"$A_\mu$", r"$\mathcal{E}$", r"$P=QQ^*$", r"$(W,\bar\mu)$", "certificates"]
    colors = [PALETTE["blue"], PALETTE["purple"], PALETTE["orange"], PALETTE["green"], PALETTE["blue"], PALETTE["vermillion"]]
    for center, label, color in zip(centers, labels, colors):
        box(ax, center, label, color)
    for start, end in zip(centers[:-1], centers[1:]):
        add_arrow(ax, (start[0] + 0.7, start[1]), (end[0] - 0.7, end[1]))
    ax.text(3.15, 1.62, "exact: invariant subspace", ha="center", color=PALETTE["green"], fontsize=8)
    ax.text(5.25, 0.52, "approximate: residual + gap", ha="center", color=PALETTE["vermillion"], fontsize=8)
    ax.plot([4.55, 5.45], [0.62, 0.92], color=PALETTE["vermillion"], linestyle="--", linewidth=1.0)
    ax.text(0.8, 0.45, "object", ha="center", fontsize=8, color=PALETTE["gray"])
    ax.text(3.9, 0.45, "identity / defect", ha="center", fontsize=8, color=PALETTE["gray"])
    ax.text(8.65, 0.45, "evidence", ha="center", fontsize=8, color=PALETTE["gray"])
    save_figure(fig, "fig01_canonical_pipeline")


def draw_tree(ax, root: tuple[float, float], children: list[tuple[float, float]], labels: list[str], root_label: str = r"$\mu$") -> None:
    x, y = root
    for child in children:
        ax.plot([x, child[0]], [y - 0.07, child[1] + 0.07], color=PALETTE["gray"], linewidth=1.0)
    ax.text(x, y, root_label, ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.16", facecolor="white", edgecolor=PALETTE["blue"], linewidth=1.2))
    for (cx, cy), label in zip(children, labels):
        ax.text(cx, cy, label, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.14", facecolor="white", edgecolor=PALETTE["orange"], linewidth=1.0))


def fig02_trees() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 2.5))
    specs = [
        (r"$\mu(\mu(x_1,x_2,x_3),x_4,x_5)$", [r"$\mu$", r"$x_4$", r"$x_5$"], [r"$x_1$", r"$x_2$", r"$x_3$"]),
        (r"$\mu(x_1,x_2,\mu(x_3,x_4,x_5))$", [r"$x_1$", r"$x_2$", r"$\mu$"], [r"$x_3$", r"$x_4$", r"$x_5$"]),
        (r"$\mu\circ_1\mu$", [r"$x_1$", r"$\mu$", r"$x_5$"], [r"$x_2$", r"$x_3$", r"$x_4$"]),
    ]
    for ax, (title, top, bottom) in zip(axes, specs):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_title(title, fontsize=8)
        children = [(0.18, 0.18), (0.5, 0.18), (0.82, 0.18)]
        draw_tree(ax, (0.5, 0.78), children, top)
        ax.text(0.18, 0.05, bottom[0], ha="center", fontsize=8)
        ax.text(0.5, 0.05, bottom[1], ha="center", fontsize=8)
        ax.text(0.82, 0.05, bottom[2], ha="center", fontsize=8)
    save_figure(fig, "fig02_ternary_composition_trees")


def fig03_diagram() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 2.6)
    ax.axis("off")
    box(ax, (1.35, 1.95), r"$W^{\otimes n}$", PALETTE["green"], 1.8)
    box(ax, (5.85, 1.95), r"$W$", PALETTE["green"], 1.25)
    box(ax, (1.35, 0.65), r"$V^{\otimes n}$", PALETTE["blue"], 1.8)
    box(ax, (5.85, 0.65), r"$V$", PALETTE["blue"], 1.25)
    add_arrow(ax, (2.25, 1.95), (5.15, 1.95), PALETTE["green"])
    add_arrow(ax, (2.25, 0.65), (5.15, 0.65), PALETTE["blue"])
    add_arrow(ax, (1.35, 1.62), (1.35, 0.98), PALETTE["purple"])
    add_arrow(ax, (5.85, 1.62), (5.85, 0.98), PALETTE["purple"])
    ax.text(3.7, 2.18, r"$\bar\mu$", color=PALETTE["green"], ha="center")
    ax.text(3.7, 0.38, r"$\mu$", color=PALETTE["blue"], ha="center")
    ax.text(0.75, 1.3, r"$Q^{\otimes n}$", rotation=90, va="center", color=PALETTE["purple"])
    ax.text(6.55, 1.3, r"$Q$", rotation=90, va="center", color=PALETTE["purple"])
    ax.text(3.6, 1.3, "commutes under exact closure", ha="center", color=PALETTE["green"], fontsize=8)
    save_figure(fig, "fig03_exact_reduction_diagram")


def fig04_geometry() -> None:
    fig = plt.figure(figsize=(5.6, 4.2))
    ax = fig.add_subplot(111, projection="3d")
    grid = np.linspace(-1.0, 1.0, 2)
    plane_x, plane_y = np.meshgrid(grid, grid)
    plane_z = np.zeros_like(plane_x)
    ax.plot_surface(plane_x, plane_y, plane_z, color=PALETTE["light"], alpha=0.85, shade=False)
    ax.plot([-1, 1, 1, -1, -1], [-1, -1, 1, 1, -1], [0, 0, 0, 0, 0], color=PALETTE["blue"], linewidth=1.0)
    x = np.array([0.2, -0.4, 0.5])
    y = np.array([0.7, 0.1, 0.45])
    tangent = np.array([0.2, 0.15, 0.0])
    normal = np.array([0.0, 0.0, 0.5])
    output = x + y + tangent + normal
    ax.quiver(0, 0, 0, *(x + y), color=PALETTE["gray"], arrow_length_ratio=0.08)
    ax.quiver(*(x + y), *tangent, color=PALETTE["green"], arrow_length_ratio=0.12)
    ax.quiver(*(x + y + tangent), *normal, color=PALETTE["vermillion"], arrow_length_ratio=0.12)
    ax.scatter(*output, color=PALETTE["vermillion"], s=32)
    ax.text(-0.8, -0.8, 0.06, r"$\operatorname{ran}P$", color=PALETTE["blue"])
    ax.text(*(output + np.array([0.02, 0.02, 0.03])), r"$\mu(Px_1,\ldots,Px_n)$", color=PALETTE["vermillion"], fontsize=8)
    ax.text(*(output + np.array([0.0, 0.0, -0.18])), r"$(I-P)\mu(\cdot)$", color=PALETTE["vermillion"], fontsize=8)
    ax.set_xlabel(r"$e_1$")
    ax.set_ylabel(r"$e_2$")
    ax.set_zlabel(r"$e_\perp$")
    ax.view_init(elev=22, azim=-58)
    save_figure(fig, "fig04_closure_leakage_geometry")


def fig05_recovery(rows: list[dict[str, str]]) -> None:
    methods = ["known_invariant", "random", "pca", "svd", "spectral", "closure_minimizing"]
    labels = ["known", "random", "PCA", "SVD", "spectral", "closure-min"]
    leakage = [[num(row, "closure_leakage") for row in rows if row["method"] == method] for method in methods]
    angles = [[num(row, "principal_angle_radians") for row in rows if row["method"] == method] for method in methods]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.5), sharex=True)
    for ax, values, ylabel in zip(axes, [leakage, angles], ["sampled closure leakage", "principal angle (rad)"]):
        bp = ax.boxplot(values, patch_artist=True, widths=0.58, showmeans=True, meanline=False)
        for patch, color in zip(bp["boxes"], [PALETTE["green"], PALETTE["vermillion"], PALETTE["orange"], PALETTE["blue"], PALETTE["purple"], PALETTE["gray"]]):
            patch.set_facecolor(color)
            patch.set_alpha(0.35)
            patch.set_edgecolor(color)
        ax.set_xticks(range(1, len(labels) + 1), labels, rotation=25, ha="right")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.55)
    axes[0].set_yscale("log")
    fig.suptitle("Projector recovery over five registered seeds", y=1.02)
    save_figure(fig, "fig05_projector_recovery")


def fig06_cp(rows: list[dict[str, str]]) -> None:
    nonzero = [row for row in rows if int(float(row["rank"])) > 0]
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in nonzero:
        grouped[int(float(row["rank"]))].append(row)
    ranks = sorted(grouped)
    errors = [np.mean([num(row, "relative_frobenius_error") for row in grouped[rank]]) for rank in ranks]
    runtimes = [np.mean([num(row, "runtime_seconds") for row in grouped[rank]]) for rank in ranks]
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    axes[0].plot(ranks, errors, marker="o", color=PALETTE["blue"])
    axes[0].set_xlabel("CP rank")
    axes[0].set_ylabel("relative Frobenius error")
    axes[0].set_title("reconstruction")
    axes[0].grid(axis="y", color="#D9D9D9", linewidth=0.55)
    axes[1].plot(ranks, runtimes, marker="s", color=PALETTE["orange"])
    axes[1].set_xlabel("CP rank")
    axes[1].set_ylabel("runtime (s)")
    axes[1].set_title("cost")
    axes[1].grid(axis="y", color="#D9D9D9", linewidth=0.55)
    fig.suptitle("CP rank sweep: five seeds per rank", y=1.02)
    save_figure(fig, "fig06_cp_rank_tradeoff")


def fig07_spectral(rows: list[dict[str, str]]) -> None:
    positive = [row for row in rows if row["control"] == "positive_gap"]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3))
    eig_gap = 0.2
    axes[0].axhline(0.5, color=PALETTE["vermillion"], linestyle="--", linewidth=1.0)
    values = [0.5 - eig_gap, 0.5 + eig_gap, 0.1, 0.9]
    axes[0].scatter(range(len(values)), values, s=34, color=PALETTE["blue"])
    axes[0].set_xticks(range(4), [r"$\lambda_1$", r"$\lambda_2$", r"$\lambda_3$", r"$\lambda_4$"])
    axes[0].set_ylabel("eigenvalue")
    axes[0].set_title(r"threshold and gap $\gamma$")
    axes[0].text(3.35, 0.51, r"$1/2$", color=PALETTE["vermillion"], fontsize=8)
    ratios = np.array([num(row, "perturbation_norm") / num(row, "gap") for row in positive])
    distances = np.array([num(row, "snapped_projector_distance") for row in positive])
    gaps = np.array([num(row, "gap") for row in positive])
    for gap in sorted(set(gaps)):
        mask = gaps == gap
        axes[1].scatter(ratios[mask], distances[mask], s=22, label=fr"$\gamma={gap:g}$")
    x = np.linspace(0, 0.4, 100)
    axes[1].plot(x, np.minimum(1.0, 4.0 * x), color=PALETTE["gray"], linestyle="--", label="bound")
    axes[1].set_xlabel(r"$\|E\|_2/\gamma$")
    axes[1].set_ylabel(r"$\|S(A+E)-S(A)\|_2$")
    axes[1].set_title("positive-gap stability")
    axes[1].legend(ncol=2)
    axes[1].grid(axis="y", color="#D9D9D9", linewidth=0.55)
    save_figure(fig, "fig07_spectral_gap_stability")


def fig08_convergence(rows: list[dict[str, str]]) -> None:
    positive = [row for row in rows if float(row["epsilon_requested"]) > 0]
    families = ["single", "associator_left", "balanced"]
    fig, ax = plt.subplots(figsize=(5.7, 3.7))
    for family, color, marker in zip(families, [PALETTE["blue"], PALETTE["orange"], PALETTE["green"]], ["o", "s", "^"]):
        grouped: dict[float, list[float]] = defaultdict(list)
        for row in positive:
            if row["tree_family"] == family:
                grouped[float(row["epsilon_requested"])].append(float(row["observed_error"]))
        eps = np.array(sorted(grouped))
        means = np.array([np.mean(grouped[value]) for value in eps])
        stds = np.array([np.std(grouped[value], ddof=1) for value in eps])
        ax.errorbar(eps, means, yerr=stds, marker=marker, color=color, capsize=3, label=family.replace("_", " "))
        slope = np.polyfit(np.log(eps), np.log(means), 1)[0]
        ax.text(eps[-1] * 0.72, means[-1] * (1.5 if family != "balanced" else 0.6), fr"$\hat{{p}}={slope:.2f}$", color=color, fontsize=8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"closure residual $\rho$")
    ax.set_ylabel(r"observed $\|F_T-R_T\|$")
    ax.set_title("registered finite closure-residual convergence")
    ax.legend()
    ax.grid(which="both", color="#E2E2E2", linewidth=0.5)
    save_figure(fig, "fig08_closure_convergence")


def fig09_dag() -> None:
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    ax.set_xlim(0, 8.2)
    ax.set_ylim(0, 3.8)
    ax.axis("off")
    nodes = {
        "definition": ((0.8, 2.8), "definition", PALETTE["blue"]),
        "exact": ((2.5, 2.8), "exact reduction", PALETTE["green"]),
        "approx": ((4.4, 2.8), "auxiliary bound", PALETTE["orange"]),
        "snap": ((6.4, 2.8), "gap theorem", PALETTE["purple"]),
        "parity": ((2.5, 1.1), "parity tests", PALETTE["blue"]),
        "tight": ((4.4, 1.1), "tightness runs", PALETTE["orange"]),
        "counter": ((6.4, 1.1), "counterexamples", PALETTE["vermillion"]),
    }
    for _, (center, label, color) in nodes.items():
        box(ax, center, label, color, width=1.4)
    for left, right in [("definition", "exact"), ("exact", "approx"), ("approx", "snap"), ("exact", "parity"), ("approx", "tight"), ("snap", "counter")]:
        add_arrow(ax, (nodes[left][0][0] + 0.7, nodes[left][0][1]), (nodes[right][0][0] - 0.7, nodes[right][0][1]), PALETTE["gray"])
    ax.text(4.1, 3.45, "claim / evidence dependency DAG", ha="center", fontsize=10, weight="semibold")
    ax.text(4.1, 0.35, "green = exact; orange = auxiliary; red = assumption-removal evidence", ha="center", fontsize=8, color=PALETTE["gray"])
    save_figure(fig, "fig09_claim_evidence_dag")


def main() -> int:
    apply_style()
    recovery = read_csv(ROOT / "artifacts" / "index" / "projector_recovery_v2.csv")
    cp = read_csv(ROOT / "artifacts" / "index" / "cp_rank_sweep_v2.csv")
    spectral = read_csv(ROOT / "artifacts" / "index" / "spectral_gap_v2.csv")
    bounds = read_csv(ROOT / "artifacts" / "index" / "bound_tightness_v2.csv")
    fig01_pipeline()
    fig02_trees()
    fig03_diagram()
    fig04_geometry()
    fig05_recovery(recovery)
    fig06_cp(cp)
    fig07_spectral(spectral)
    fig08_convergence(bounds)
    fig09_dag()
    print(f"generated vector figures in {FIGURE_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
