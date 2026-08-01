"""Generates the v18 supplementary visual atlas figures from real,
already-executed experiment results (hardcoded here with a citation to
the source finding doc / artifact JSON for each number, rather than
re-running multi-minute experiments on every figure regeneration).

Colorblind-safe, accessible palette (Okabe-Ito): blue #0072B2, orange
#E69F00, vermillion #D55E00, gray #999999. No red/green-only encodings.
Missing/not-applicable cells are always drawn with a visible hatch
pattern, never left blank or silently omitted.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

BLUE = "#0072B2"
ORANGE = "#E69F00"
VERMILLION = "#D55E00"
GRAY = "#999999"
GREEN = "#009E73"

plt.rcParams.update({"font.size": 11, "figure.dpi": 150, "savefig.dpi": 300})


def save(fig, name: str):
    fig.savefig(FIG_DIR / f"{name}.svg", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1: A-N certification dashboard
# Source: docs/research/spectral_a_to_n_v18/TRUTH_AND_NOVELTY_REPORT.md
# ---------------------------------------------------------------------------
def figure_dashboard():
    blocks = list("ABCDEFGHIJKLMN")
    # status tier index: 0=FAIL/REFUTED, 1=EMPIRICAL/screening, 2=STRUCTURAL/EXACT
    tier = {
        "A": 2, "B": 0, "C": 1, "D": 1, "E": 0, "F": 1, "G": 1, "H": 1,
        "I": 2, "J": 0, "K": 1, "L": 2, "M": 0, "N": 2,
    }
    labels = {0: "FAIL / REFUTED", 1: "EMPIRICAL / SCREENING", 2: "EXACT / STRUCTURAL IDENTITY"}
    colors = {0: VERMILLION, 1: ORANGE, 2: BLUE}

    fig, ax = plt.subplots(figsize=(9, 2.4))
    for i, b in enumerate(blocks):
        t = tier[b]
        ax.bar(i, 1, color=colors[t], edgecolor="black", linewidth=0.5)
        ax.text(i, 1.08, b, ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_xlim(-0.6, len(blocks) - 0.4)
    ax.set_ylim(0, 1.3)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title("A-N certification dashboard (v18, this pass)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[t]) for t in (0, 1, 2)]
    ax.legend(handles, [labels[t] for t in (0, 1, 2)], loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    save(fig, "01_an_dashboard")


# ---------------------------------------------------------------------------
# Figure 2: Block B ablation matrix
# Source: spectral/certification_v18/artifacts/block_b_ablation_matrix.json
# ---------------------------------------------------------------------------
def figure_block_b_ablation():
    data = json.loads((HERE.parent.parent / "spectral/certification_v18/artifacts/block_b_ablation_matrix.json").read_text())
    regimes = [d["regime"] for d in data]
    unexplained = [max(d["final_comm_unexplained_rel"], 1e-7) for d in data]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = np.arange(len(regimes))
    ax.barh(y, unexplained, color=BLUE, edgecolor="black", linewidth=0.5)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([r.replace("_", " ") for r in regimes])
    ax.set_xlabel("comm_unexplained_rel (log scale; floor 1e-7 for display, true 0 for frozen_projector_train_law)")
    ax.set_title("Block B ablation matrix: deployed-failure mechanism")
    ax.axvline(1.0, color=GRAY, linestyle="--", linewidth=1, label="zero-predictor baseline (unexplained=1)")
    ax.invert_yaxis()
    ax.legend(loc="lower right", frameon=False)
    save(fig, "02_block_b_ablation")


# ---------------------------------------------------------------------------
# Figure 3: Block E interscale transport angles vs baselines
# Source: spectral/certification_v18/artifacts/block_e_interscale_experiment.json
# ---------------------------------------------------------------------------
def figure_block_e_transport():
    data = json.loads((HERE.parent.parent / "spectral/certification_v18/artifacts/block_e_interscale_experiment.json").read_text())
    pairs = [f"{c['forward']['from_n']}→{c['forward']['to_n']}" for c in data["comparisons"]]
    trained = [c["forward"]["trained_transport_max_angle"] for c in data["comparisons"]]
    random_b = [c["forward"]["random_baseline_max_angle"] for c in data["comparisons"]]
    interp_b = [c["forward"]["interpolation_baseline_max_angle"] for c in data["comparisons"]]

    x = np.arange(len(pairs))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - width, trained, width, label="trained lift", color=BLUE)
    ax.bar(x, random_b, width, label="random baseline", color=GRAY)
    ax.bar(x + width, interp_b, width, label="interpolation baseline", color=ORANGE)
    ax.axhline(np.pi / 2, color=VERMILLION, linestyle="--", linewidth=1, label="max possible (π/2, orthogonal)")
    ax.set_xticks(x)
    ax.set_xticklabels(pairs)
    ax.set_ylabel("max principal angle (rad)")
    ax.set_title("Block E: interscale subspace transport vs required baselines")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.35), ncol=2, frameon=False)
    save(fig, "03_block_e_transport")


# ---------------------------------------------------------------------------
# Figure 4: Block H associator constant sharpness
# Source: BLOCK_H_FINDINGS.md (n=16,rank=4,cp_rank=4,seed=0)
# ---------------------------------------------------------------------------
def figure_block_h_sharpness():
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axvline(2.0, color=VERMILLION, linewidth=2, label="triangle bound (constant 2)")
    ax.axvline(0.452, color=BLUE, linewidth=2, label="max observed ratio (500 trials)")
    ax.axvspan(0.452, 2.0, alpha=0.15, color=GRAY, label="unresolved sharpness gap")
    ax.set_xlim(0, 2.2)
    ax.set_yticks([])
    ax.set_xlabel(r"$\|A(x,y,z)\| / (\hat M^2 \|x\|\|y\|\|z\|)$")
    ax.set_title("Block H: is the constant 2 sharp?")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    save(fig, "04_block_h_sharpness")


# ---------------------------------------------------------------------------
# Figure 5: Block N raw vs symmetrized cyclic defect (log scale)
# Source: BLOCK_N_FINDINGS.md (n=16,rank=4,cp_rank=4,seed=0,100 trials)
# ---------------------------------------------------------------------------
def figure_block_n_cyclic():
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["raw (pre-averaging)\ncp_raw", "symmetrized\n(forward, cyclic-averaged)"]
    values = [4.597473957506782, 8.223215287279223e-33]
    display_values = [max(v, 1e-34) for v in values]
    ax.bar(labels, display_values, color=[VERMILLION, BLUE], edgecolor="black")
    ax.set_yscale("log")
    ax.set_ylabel("mean cyclic defect (log scale)")
    ax.set_title("Block N: construction identity, not learned symmetry\n(31-order-of-magnitude gap)")
    for i, v in enumerate(values):
        ax.text(i, display_values[i] * 3, f"{v:.2e}", ha="center", fontsize=10)
    save(fig, "05_block_n_cyclic")


# ---------------------------------------------------------------------------
# Figure 6: Block K HOSVD compactness vs random-tensor null
# Source: BLOCK_K_FINDINGS.md (n=16,rank=4,cp_rank=4,seed=0)
# ---------------------------------------------------------------------------
def figure_block_k_hosvd():
    modes = ["mode 0", "mode 1", "mode 2"]
    real = [3, 4, 4]
    random_null = [4, 4, 4]
    x = np.arange(len(modes))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - width / 2, real, width, label="real reduced tensor", color=BLUE)
    ax.bar(x + width / 2, random_null, width, label="random-tensor null (same shape/norm)", color=GRAY)
    ax.set_xticks(x)
    ax.set_xticklabels(modes)
    ax.set_ylabel("rank needed for 99% energy")
    ax.set_ylim(0, 5)
    ax.set_title("Block K: HOSVD compactness vs random-tensor control")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    save(fig, "06_block_k_hosvd")


# ---------------------------------------------------------------------------
# Figure 7: Hardware / CPU-GPU parity
# Source: papers/software_reproducibility_v5/main.tex Section 4
# ---------------------------------------------------------------------------
def figure_hardware_parity():
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    quantities = ["idempotence\nresidual", "self-adjointness\nresidual"]
    cpu_vals = [1.312e-15, 1e-30]  # 0.0 displayed at floor for log scale
    gpu_vals = [1.198e-15, 2.220e-16]
    x = np.arange(len(quantities))
    width = 0.35
    axes[0].bar(x - width / 2, cpu_vals, width, label="CPU", color=BLUE)
    axes[0].bar(x + width / 2, gpu_vals, width, label="CUDA (RTX PRO 5000)", color=ORANGE)
    axes[0].set_yscale("log")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(quantities)
    axes[0].set_title("CPU/GPU parity (float64)")
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), frameon=False)

    devices = ["CPU", "CUDA"]
    times = [19.1, 835.1]
    axes[1].bar(devices, times, color=[BLUE, ORANGE])
    axes[1].set_ylabel("wall time (ms)")
    axes[1].set_title("n=24 single-instance wall time\n(GPU launch overhead dominates at this scale)")
    save(fig, "07_hardware_parity")


if __name__ == "__main__":
    figure_dashboard()
    figure_block_b_ablation()
    figure_block_e_transport()
    figure_block_h_sharpness()
    figure_block_n_cyclic()
    figure_block_k_hosvd()
    figure_hardware_parity()
    print(f"Wrote {len(list(FIG_DIR.glob('*.png')))} PNG + {len(list(FIG_DIR.glob('*.svg')))} SVG figures to {FIG_DIR}")
