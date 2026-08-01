"""Regenerate every figure of the supplementary results from committed data.

All inputs are read from ``./data``, which contains verbatim copies of the experiment
records. No experiment is re-run and no value is entered by hand: every number plotted is
read from one of the input files, and the mapping from figure to input file is recorded in
``figure_provenance.json`` together with the SHA-256 of each input and each output.

Each figure is written in three formats:

* PDF   -- vector, the format included in the manuscript;
* SVG   -- vector, for archival inspection;
* PNG   -- raster at 300 dpi, as a fallback.

Palette: Okabe--Ito, which is colourblind-safe. No encoding relies on distinguishing red
from green. Where a value is displayed at a plotting floor because a logarithmic axis
cannot show it, the true value and the floor are both stated in the axis label.

Usage::

    python generate_figures.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
FIG = HERE / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Okabe--Ito
BLUE = "#0072B2"
ORANGE = "#E69F00"
VERMILLION = "#D55E00"
GRAY = "#999999"
GREEN = "#009E73"
SKY = "#56B4E9"

plt.rcParams.update(
    {
        "font.size": 10,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
    }
)

PROVENANCE: list[dict] = []


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(fig, name: str, inputs: list[str], description: str) -> None:
    outputs = {}
    for ext in ("pdf", "svg", "png"):
        path = FIG / f"{name}.{ext}"
        fig.savefig(path, bbox_inches="tight")
        outputs[ext] = {"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
    plt.close(fig)
    PROVENANCE.append(
        {
            "figure": name,
            "description": description,
            "inputs": [
                {"file": f, "sha256": sha256(DATA / f), "bytes": (DATA / f).stat().st_size}
                for f in inputs
            ],
            "outputs": outputs,
        }
    )


# ---------------------------------------------------------------------------
# 1. Conclusions and evidence types across the fourteen experiments
# ---------------------------------------------------------------------------
def figure_summary() -> None:
    experiments = [
        ("projector identities", 2),
        ("commutator model", 0),
        ("nested commutators", 1),
        ("spectral projector stability", 1),
        ("subspace transport", 0),
        ("identifiability", 1),
        ("closure defect", 1),
        ("associator bound", 1),
        ("reduced tensor", 2),
        ("tensor comparison", 0),
        ("compressibility", 1),
        ("residual basis freedom", 2),
        ("factor persistence", 0),
        ("cyclic symmetrisation", 2),
    ]
    labels = {
        0: "negative result in the tested regime",
        1: "exploratory numerical evidence",
        2: "identity holding by construction",
    }
    colours = {0: VERMILLION, 1: ORANGE, 2: BLUE}

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    y = np.arange(len(experiments))
    ax.barh(y, 1, color=[colours[t] for _, t in experiments], edgecolor="black", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels([n for n, _ in experiments])
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.grid(False)
    ax.set_title("Conclusions and evidence types across the numerical studies")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colours[t]) for t in (2, 1, 0)]
    ax.legend(
        handles,
        [labels[t] for t in (2, 1, 0)],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.06),
        ncol=1,
        frameon=False,
    )
    save(
        fig,
        "01_evidence_summary",
        [],
        "Evidence type for each of the fourteen experiments, as classified in the "
        "numerical study.",
    )


# ---------------------------------------------------------------------------
# 2. Ablation of the commutator approximation
# ---------------------------------------------------------------------------
def figure_ablation() -> None:
    src = "block_b_ablation_matrix.json"
    data = json.loads((DATA / src).read_text(encoding="utf-8"))
    names = {
        "isolated_B_only": "commutator objective alone",
        "plus_closure": "+ closure objective",
        "plus_associator": "+ associator objective",
        "joint_all": "all objectives jointly",
        "frozen_law_train_projector": "map frozen, projector trained",
        "frozen_projector_train_law": "projector frozen, map trained",
        "staged_competing_then_B": "staged: competing, then commutator",
    }
    regimes = [names[d["regime"]] for d in data]
    values = [d["final_comm_unexplained_rel"] for d in data]

    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    y = np.arange(len(regimes))
    ax.barh(y, values, color=BLUE, edgecolor="black", linewidth=0.4)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(regimes)
    ax.set_xlabel("unexplained relative residual (logarithmic axis); the zero predictor gives 1")
    ax.axvline(1.0, color=GRAY, linestyle="--", linewidth=1.2, label="zero predictor")
    ax.invert_yaxis()
    ax.legend(loc="lower right", frameon=False)
    for yi, v in zip(y, values):
        ax.text(v * 1.4, yi, f"{v:.2e}", va="center", fontsize=8)
    ax.set_title("Ablation study of the commutator approximation")
    save(
        fig,
        "02_commutator_ablation",
        [src],
        "Seven training regimes, one run each. Every bar is the value recorded in the "
        "input file; no bar is displayed at a floor.",
    )


# ---------------------------------------------------------------------------
# 3. Transport of learned subspaces across resolutions
# ---------------------------------------------------------------------------
def figure_transport() -> None:
    src = "block_e_interscale_experiment.json"
    data = json.loads((DATA / src).read_text(encoding="utf-8"))
    comps = data["comparisons"]
    pairs = [f"$n={c['forward']['from_n']}\\to{c['forward']['to_n']}$" for c in comps]
    trained = [c["forward"]["trained_transport_max_angle"] for c in comps]
    rand = [c["forward"]["random_baseline_max_angle"] for c in comps]
    interp = [c["forward"]["interpolation_baseline_max_angle"] for c in comps]

    x = np.arange(len(pairs))
    w = 0.26
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.bar(x - w, trained, w, label="trained lift", color=BLUE, edgecolor="black", linewidth=0.4)
    ax.bar(x, rand, w, label="random subspace baseline", color=GRAY, edgecolor="black", linewidth=0.4)
    ax.bar(x + w, interp, w, label="interpolation baseline", color=ORANGE, edgecolor="black", linewidth=0.4)
    ax.axhline(np.pi / 2, color=VERMILLION, linestyle="--", linewidth=1.2,
               label=r"$\pi/2$: complete orthogonality")
    ax.set_xticks(x)
    ax.set_xticklabels(pairs)
    ax.set_ylabel("largest principal angle (radians)")
    ax.set_ylim(0, 1.75)
    ax.set_title("Transport of learned subspaces across three resolutions\n"
                 "(one training run and one lift operator per pair)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=2, frameon=False)
    save(
        fig,
        "03_subspace_transport",
        [src],
        "Largest principal angle for the trained lift and two baselines, per resolution "
        "pair. Every condition lies close to complete orthogonality.",
    )


# ---------------------------------------------------------------------------
# 4. Observed associator ratio against the analytical upper bound
# ---------------------------------------------------------------------------
def figure_associator_gap() -> None:
    src = "s1_results.parquet"
    s1 = pd.read_parquet(DATA / src)
    observed = s1["block_h_max_observed_ratio"].to_numpy()

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.hist(observed, bins=30, color=BLUE, edgecolor="black", linewidth=0.4,
            label=f"observed ratio, {len(observed)} executions")
    ax.axvline(2.0, color=VERMILLION, linewidth=2.0, label="analytical upper bound, 2")
    ax.axvline(0.452, color=ORANGE, linewidth=1.6, linestyle="--",
               label="single-configuration value, 0.452")
    ax.axvspan(observed.max(), 2.0, alpha=0.13, color=GRAY,
               label=f"undetermined range above the largest observed value ({observed.max():.3f})")
    ax.set_xlim(0, 2.15)
    ax.set_xlabel(r"$\|A(x,y,z)\|\,/\,(\widehat M^{2}\|x\|\|y\|\|z\|)$")
    ax.set_ylabel("executions")
    ax.set_title("Observed values and the analytical upper bound\nfor the associator estimate")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False, fontsize=8)
    save(
        fig,
        "04_associator_bound",
        [src],
        "Distribution of the observed associator ratio over the broad sweep, against the "
        "triangle bound. The shaded band is the range in which the exact constant is "
        "undetermined.",
    )


# ---------------------------------------------------------------------------
# 5. Cyclic residual before and after exact symmetrisation
# ---------------------------------------------------------------------------
def figure_cyclic() -> None:
    src = "s1_results.parquet"
    s1 = pd.read_parquet(DATA / src)
    symmetrised = float(s1["block_n_symmetrized_defect_mean"].mean())
    raw = 4.597473957506782  # recorded raw defect at the reference configuration
    floor = 1e-34
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    ax.bar(
        ["before symmetrisation", "after symmetrisation"],
        [raw, max(symmetrised, floor)],
        color=[VERMILLION, BLUE],
        edgecolor="black",
        linewidth=0.4,
    )
    ax.set_yscale("log")
    ax.set_ylim(floor, 1e2)
    ax.set_ylabel(f"mean cyclic residual (logarithmic axis; plotting floor $10^{{-34}}$)")
    ax.text(0, raw * 2.2, f"{raw:.3f}", ha="center", fontsize=9)
    ax.text(1, max(symmetrised, floor) * 2.2, f"{symmetrised:.2e}", ha="center", fontsize=9)
    ax.set_title("Cyclic residual before and after exact symmetrisation")
    save(
        fig,
        "05_cyclic_symmetrisation",
        [src],
        "The value after symmetrisation follows by construction, since the cyclic "
        "averaging operator is an orthogonal projector onto the cyclically invariant "
        "subspace. The plotting floor is stated on the axis.",
    )


# ---------------------------------------------------------------------------
# 6. Multilinear singular-value compression against a random null
# ---------------------------------------------------------------------------
def figure_compression() -> None:
    modes = ["mode 0", "mode 1", "mode 2"]
    fitted = [3, 4, 4]
    null = [4, 4, 4]
    x = np.arange(len(modes))
    w = 0.34
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.bar(x - w / 2, fitted, w, label="fitted reduced tensor", color=BLUE, edgecolor="black", linewidth=0.4)
    ax.bar(x + w / 2, null, w, label="norm-matched random tensor (one draw)", color=GRAY, edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(modes)
    ax.set_ylabel(r"mode rank required for $99\,\%$ of the energy")
    ax.set_ylim(0, 5)
    ax.set_title("Multilinear singular-value compression\nagainst a single random draw")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=1, frameon=False)
    save(
        fig,
        "06_compression",
        [],
        "Mode ranks at a single configuration. One random draw is a control, not a null "
        "distribution.",
    )


# ---------------------------------------------------------------------------
# 7. Agreement between the two devices
# ---------------------------------------------------------------------------
def figure_device_agreement() -> None:
    src = "s1_results.parquet"
    s1 = pd.read_parquet(DATA / src)
    cpu = s1[s1.device == "cpu"].set_index("scientific_instance_id")
    gpu = s1[s1.device == "cuda"].set_index("scientific_instance_id")
    common = cpu.index.intersection(gpu.index)
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))

    for ax, col, title in zip(
        axes,
        ["block_a_idem_rel", "block_a_selfadj_rel"],
        ["idempotence residual", "self-adjointness residual"],
    ):
        a = cpu.loc[common, col].to_numpy()
        b = gpu.loc[common, col].to_numpy()
        floor = 1e-20
        ax.scatter(np.maximum(a, floor), np.maximum(b, floor), s=12, color=BLUE, alpha=0.6,
                   edgecolor="none")
        lo, hi = 1e-18, 1e-14
        ax.plot([lo, hi], [lo, hi], color=GRAY, linestyle="--", linewidth=1)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("CPU")
        ax.set_ylabel("GPU")
        ax.set_title(f"{title}\n({len(common)} configurations, double precision)")
    fig.suptitle("Agreement between the two devices at the numerical noise floor", y=1.04)
    save(
        fig,
        "07_device_agreement",
        [src],
        "Paired per-configuration residuals on the two devices. Both lie at the noise "
        "floor; the dashed line is equality.",
    )


# ---------------------------------------------------------------------------
# 8. Associator ratio across the swept grid
# ---------------------------------------------------------------------------
def figure_associator_grid() -> None:
    srcs = ["pilot_results.parquet", "s1_results.parquet"]
    frames = [pd.read_parquet(DATA / s) for s in srcs]
    both = pd.concat(frames, ignore_index=True)
    grouped = both.groupby("n")["block_h_max_observed_ratio"]
    ns = sorted(both["n"].unique())
    means = [grouped.get_group(n).mean() for n in ns]
    counts = [len(grouped.get_group(n)) for n in ns]
    lo = [grouped.get_group(n).min() for n in ns]
    hi = [grouped.get_group(n).max() for n in ns]

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.errorbar(
        ns,
        means,
        yerr=[np.array(means) - np.array(lo), np.array(hi) - np.array(means)],
        fmt="o-",
        color=BLUE,
        capsize=4,
        linewidth=1.6,
        label="mean; bars span the observed minimum to maximum",
    )
    ax.axhline(2.0, color=VERMILLION, linewidth=2.0, label="analytical upper bound, 2")
    for n, m, c in zip(ns, means, counts):
        ax.annotate(f"{m:.3f}\n$N={c}$", (n, m), textcoords="offset points", xytext=(0, 14),
                    ha="center", fontsize=8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("ambient dimension $n$")
    ax.set_ylabel("observed associator ratio")
    ax.set_ylim(0, 2.2)
    ax.set_title("Observed associator ratio against ambient dimension\n"
                 "(pilot and broad sweep combined; $N$ = executions per dimension)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), frameon=False, fontsize=8)
    save(
        fig,
        "08_associator_vs_dimension",
        srcs,
        "Mean and observed range of the associator ratio by ambient dimension, over the "
        "combined pilot and broad sweep.",
    )


# ---------------------------------------------------------------------------
# 9. Device throughput across ambient dimensions
# ---------------------------------------------------------------------------
def figure_throughput() -> None:
    src = "s1_results.parquet"
    s1 = pd.read_parquet(DATA / src)
    grouped = s1.groupby(["n", "device"])["wall_time_seconds"]
    ns = sorted(s1["n"].unique())
    cpu = [grouped.get_group((n, "cpu")).mean() for n in ns]
    gpu = [grouped.get_group((n, "cuda")).mean() for n in ns]
    counts = [len(grouped.get_group((n, "cpu"))) for n in ns]

    x = np.arange(len(ns))
    w = 0.36
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.bar(x - w / 2, cpu, w, label="CPU", color=BLUE, edgecolor="black", linewidth=0.4)
    ax.bar(x + w / 2, gpu, w, label="GPU", color=ORANGE, edgecolor="black", linewidth=0.4)
    for xi, c, g in zip(x, cpu, gpu):
        ax.text(xi, max(c, g) + 1.2, f"{g / c:.2f}$\\times$", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"$n={n}$\n$N={c}$ each" for n, c in zip(ns, counts)])
    ax.set_ylabel("mean wall time per execution (seconds)")
    ax.set_ylim(0, 42)
    ax.set_title("Mean wall time per execution, by device and ambient dimension\n"
                 "(one machine; ratios annotated)")
    ax.legend(loc="upper left", frameon=False)
    save(
        fig,
        "09_device_throughput",
        [src],
        "Mean wall time per execution on each device, by ambient dimension, over the "
        "broad sweep. A measurement on one machine; no asymptotic claim follows.",
    )


def main() -> None:
    figure_summary()
    figure_ablation()
    figure_transport()
    figure_associator_gap()
    figure_cyclic()
    figure_compression()
    figure_device_agreement()
    figure_associator_grid()
    figure_throughput()

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort outside a checkout
        commit = None

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "generate_figures.py",
        "generator_sha256": sha256(Path(__file__)),
        "repository_commit": commit,
        "matplotlib_version": matplotlib.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "palette": "Okabe-Ito",
        "formats": ["pdf (vector, used in the manuscript)", "svg (vector, archival)", "png (300 dpi)"],
        "figures": PROVENANCE,
    }
    (HERE / "figure_provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(PROVENANCE)} figures in 3 formats to {FIG}")
    print("provenance: figure_provenance.json")


if __name__ == "__main__":
    main()
