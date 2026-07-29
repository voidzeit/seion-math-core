"""Build the 18 registered vector figures for the v3 research track."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT / "artifacts" / "research_v3"
INDEX = ROOT / "artifacts" / "index"
OUT = ROOT / "papers" / "tree_stability_v3" / "figures"
BUILD = OUT / ".tikz_build"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))

from style import COLORS, LINESTYLES, MARKERS, apply_style, light_grid, panel_label  # noqa: E402
from seion_core.research_v3.tree_enumeration import label_shape, topology_family_shape  # noqa: E402
from seion_core.research_v3.typed_tree import Leaf, Node, Tree  # noqa: E402


apply_style()
OUT.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
FIGURES: list[dict[str, Any]] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def register(
    number: int | str,
    name: str,
    title: str,
    *,
    sources: list[Path],
    unique_instances: int | str,
    seeds: int | str,
    restarts: int | str,
    metric: str,
    uncertainty: str,
    theoretical_reference: str,
    supported: str,
    not_supported: str,
    caption: str,
    supplementary: bool = False,
) -> None:
    pdf = OUT / f"{name}.pdf"
    svg = OUT / f"{name}.svg"
    if not pdf.is_file() or not svg.is_file():
        raise RuntimeError(f"missing vector outputs for {name}")
    FIGURES.append(
        {
            "number": number,
            "name": name,
            "title": title,
            "supplementary": supplementary,
            "sources": [rel(path) for path in sources],
            "source_sha256": {rel(path): sha256(path) for path in sources if path.is_file()},
            "unique_instances": unique_instances,
            "seeds": seeds,
            "restarts": restarts,
            "metric": metric,
            "uncertainty": uncertainty,
            "theoretical_reference": theoretical_reference,
            "conclusion_supported": supported,
            "conclusion_not_supported": not_supported,
            "caption_latex": caption,
            "outputs": {
                "pdf": {"path": rel(pdf), "sha256": sha256(pdf), "bytes": pdf.stat().st_size},
                "svg": {"path": rel(svg), "sha256": sha256(svg), "bytes": svg.stat().st_size},
            },
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    metadata = {"Creator": "SEION Math Core research-v3 registered figure builder"}
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", metadata=metadata)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata=metadata)
    plt.close(fig)


def compile_tikz(number: int, name: str, title: str, sources: list[Path], caption: str) -> None:
    source = HERE / f"{name}.tex"
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={BUILD}",
            str(source),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    built_pdf = BUILD / f"{name}.pdf"
    shutil.copy2(built_pdf, OUT / f"{name}.pdf")
    subprocess.run(
        ["dvisvgm", "--pdf", "--page=1", "--exact", f"--output={OUT / f'{name}.svg'}", str(built_pdf)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    register(
        number,
        name,
        title,
        sources=[source, *sources],
        unique_instances="definition/proof object",
        seeds="not applicable",
        restarts="not applicable",
        metric="structural semantics",
        uncertainty="none; exact diagram",
        theoretical_reference="typed tree definitions and exact decomposition theorem",
        supported="the displayed definitions and dependency structure",
        not_supported="numerical sharpness or theorem-level novelty",
        caption=caption,
    )


def figure01() -> None:
    compile_tikz(
        1,
        "fig01_typed_tree_semantics",
        "Typed tree semantics",
        [ROOT / "docs" / "theorems_v3" / "typed_model.md"],
        "Typed ordered-tree semantics. Types determine the ambient spaces, isometries, projectors, and admissible node laws; ambient evaluation, recursive projection, and the local normal residual are distinct operations. This exact definitional diagram has no sampling uncertainty and supports no sharpness or novelty claim.",
    )


def figure02() -> None:
    compile_tikz(
        2,
        "fig02_exact_node_decomposition",
        "Exact node error decomposition",
        [ROOT / "docs" / "theorems_v3" / "exact_subset_expansion.md"],
        "Exact node-error decomposition. The local residual and every nonempty subset of propagated child errors appear in the multilinear identity, followed by the orthogonal tangent/normal split. This is a proof diagram with no statistical uncertainty; it does not establish optimal constants.",
    )


def figure03() -> None:
    path = DATA / "block_D.parquet"
    data = pd.read_parquet(path)
    methods = [
        ("homogeneous_ambient_bound", "homogeneous"),
        ("nodewise_bound", "nodewise"),
        ("path_sum_bound", "path sum"),
        ("mixed_mask_bound", "mixed mask"),
        ("optimized_order_bound", "optimized"),
    ]
    patterns = list(data["pattern"].drop_duplicates())
    palette = [COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["vermillion"], COLORS["purple"], COLORS["sky"], COLORS["gray"], COLORS["black"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(methods))
    for index, pattern in enumerate(patterns):
        group = data[data["pattern"] == pattern]
        medians, lows, highs = [], [], []
        base = group["homogeneous_ambient_bound"].to_numpy()
        for column, _ in methods:
            ratios = group[column].to_numpy() / base
            lows.append(np.quantile(ratios, 0.1))
            medians.append(np.median(ratios))
            highs.append(np.quantile(ratios, 0.9))
        ax.errorbar(
            x + (index - (len(patterns) - 1) / 2) * 0.035,
            medians,
            yerr=[np.asarray(medians) - lows, np.asarray(highs) - medians],
            color=palette[index % len(palette)],
            marker=MARKERS[index % len(MARKERS)],
            linestyle=LINESTYLES[index % len(LINESTYLES)],
            capsize=2,
            label=pattern,
        )
    ax.set_xticks(x, [label for _, label in methods])
    ax.set_ylabel("certificate / homogeneous ambient certificate")
    ax.set_yscale("log")
    ax.set_title("Same-instance hierarchy; median and 10--90% range")
    ax.legend(ncol=min(3, len(patterns)))
    light_grid(ax, "y")
    save(fig, "fig03_bound_hierarchy")
    caption = (
        f"Bound hierarchy on block D ({len(data):,} unique registered instances; declared seed count 10, no optimizer restarts). "
        "The metric is each sound certificate divided by the homogeneous ambient certificate; points are medians and bars are 10--90 percent instance quantiles, not seed uncertainty. "
        "The homogeneous theorem is the reference. The data support instancewise tightening for nonuniform local patterns, but do not prove any certificate globally optimal."
    )
    register(3, "fig03_bound_hierarchy", "Bound hierarchy", sources=[path], unique_instances=len(data), seeds=10, restarts=0, metric="certificate/homogeneous certificate", uncertainty="10--90% variation across mathematical instances", theoretical_reference="homogeneous k theorem", supported="nodewise tightening on heterogeneous instances", not_supported="global optimality of any certificate", caption=caption)


def _constant_value(frame: pd.DataFrame, error: str) -> pd.Series:
    return frame[f"{error}_lower"].copy()


def _atlas_panel(axes, data: pd.DataFrame, title_suffix: str = "") -> None:
    errors = ["ambient", "projected", "normal"]
    nodes = sorted(data["internal_nodes"].unique())
    arities = sorted(data["arity"].unique())
    for ax, error in zip(axes, errors):
        matrix = np.full((len(arities), len(nodes)), np.nan)
        annotations: dict[tuple[int, int], str] = {}
        for yi, arity in enumerate(arities):
            for xi, k in enumerate(nodes):
                group = data[(data["arity"] == arity) & (data["internal_nodes"] == k)]
                if group.empty:
                    continue
                lower = _constant_value(group, error)
                ratio = lower / group[f"{error}_upper"].replace(0, np.nan)
                best_index = ratio.fillna(0).idxmax()
                matrix[yi, xi] = float(ratio.loc[best_index]) if np.isfinite(ratio.loc[best_index]) else 1.0
                best = group.loc[best_index]
                annotations[(yi, xi)] = f"{lower.loc[best_index]:.2g}/{best[f'{error}_upper']:.2g}\n{str(best['topology'])[:3]}"
        image = ax.imshow(matrix, origin="lower", aspect="auto", vmin=0, vmax=1, cmap="cividis")
        for (yi, xi), label in annotations.items():
            color = "white" if matrix[yi, xi] < 0.45 else "black"
            ax.text(xi, yi, label, ha="center", va="center", fontsize=5.7, color=color)
        ax.set_xticks(range(len(nodes)), nodes)
        ax.set_yticks(range(len(arities)), arities)
        ax.set_xlabel("internal nodes $k$")
        ax.set_ylabel("arity")
        ax.set_title(error + title_suffix)
    return image


def figure04() -> None:
    path = DATA / "block_B.parquet"
    data = pd.read_parquet(path)
    sample = data[(data["dimension"] == 2) & (data["projector_rank"] == 1) & (data["eta"] == data["eta"].min())]
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.25))
    image = _atlas_panel(axes, sample)
    fig.colorbar(image, ax=axes, label="best lower / certified upper", shrink=0.82)
    fig.suptitle("Universal-constant atlas (tile label: lower/upper and topology prefix)")
    save(fig, "fig04_universal_constant_atlas")
    caption = (
        f"Universal constant atlas from block B ({len(sample):,} dimension-two instances selected from {len(data):,}; 20 seeds and eight restarts are specified for the pending extended search). "
        "Tile color is the best certified explicit lower divided by the homogeneous upper; text gives lower/upper and the maximizing topology prefix. Interval enclosure is used for the construction, with no sampling uncertainty. "
        "The atlas supports exact or near-matching cells where the ratio is one, but does not establish fixed-$\\eta$ optimality across the full matrix."
    )
    register(4, "fig04_universal_constant_atlas", "Universal constant atlas", sources=[path], unique_instances=len(sample), seeds="20 specified; extended pending", restarts="8 specified; extended pending", metric="certified lower/certified upper", uncertainty="directed interval enclosure for construction; topology variation shown", theoretical_reference="$k$ ambient and $k-1$ projected homogeneous bounds", supported="matching cells for explicit constructions", not_supported="fixed-eta global optimality", caption=caption)

    for topology in sorted(sample["topology"].unique()):
        subset = sample[sample["topology"] == topology]
        fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.25))
        image = _atlas_panel(axes, subset, f"; {topology.replace('_', ' ')}")
        fig.colorbar(image, ax=axes, label="lower / upper", shrink=0.82)
        fig.suptitle(f"Supplementary constant atlas: {topology.replace('_', ' ')}")
        safe = topology.replace("_", "-")
        name = f"atlas_fig04_{safe}"
        save(fig, name)
        register(f"S4-{safe}", name, f"Supplementary constant atlas: {topology}", sources=[path], unique_instances=len(subset), seeds="20 specified; extended pending", restarts="8 specified; extended pending", metric="certified lower/certified upper", uncertainty="directed interval construction enclosure", theoretical_reference="homogeneous constants", supported="topology-resolved lower/upper comparison", not_supported="global optimality", caption=f"Supplementary topology-resolved block-B atlas for {topology.replace('_', ' ')} ({len(subset)} instances).", supplementary=True)


def figure05() -> None:
    path = DATA / "block_B.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["arity"] == 2) & (data["dimension"] == 2) & (data["projector_rank"] == 1) & (data["internal_nodes"] == 8)]
    topologies = [value for value in ("left_comb", "maximally_balanced", "high_strahler") if value in set(selected["topology"])]
    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    for index, topology in enumerate(topologies):
        group = selected[selected["topology"] == topology].sort_values("eta")
        lower = group["projected_lower"]
        ax.plot(group["eta"], lower, marker=MARKERS[index], linestyle=LINESTYLES[index], color=[COLORS["blue"], COLORS["orange"], COLORS["green"]][index], label=f"{topology.replace('_', ' ')} lower")
    upper = float(selected["projected_upper"].iloc[0])
    ax.axhline(upper, color=COLORS["black"], linestyle="--", label=f"theorem upper $k-1={upper:g}$")
    ax.set_xscale("log")
    ax.set_xlabel(r"closure parameter $\eta$")
    ax.set_ylabel(r"normalized projected lower $E_P/(\eta M^{k-1})$")
    ax.set_title("Sharpness profile for selected binary eight-node trees")
    ax.legend()
    light_grid(ax, "both")
    save(fig, "fig05_sharpness_profile")
    caption = (
        f"Sharpness profile from block B ({len(selected)} unique binary eight-node instances; the requested 20 seeds and eight restarts remain extended). "
        "The metric is the interval-certified explicit projected error divided by $\\eta M^{{k-1}}$; the dashed reference is the proved $k-1=7$ upper. "
        "There is no statistical uncertainty in the explicit construction. The plot supports an admissible lower profile, not a globally optimal $C_T(\\eta)$."
    )
    register(5, "fig05_sharpness_profile", "Sharpness profile", sources=[path], unique_instances=len(selected), seeds="20 requested; not executed in base", restarts="8 requested; not executed in base", metric="projected error/(eta M^(k-1))", uncertainty="interval enclosure only", theoretical_reference="$k-1$ projected theorem", supported="eta-dependent explicit lower profiles", not_supported="global C_T(eta) optimality", caption=caption)


def figure06() -> None:
    path = DATA / "block_B.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["arity"] == 2) & (data["dimension"] == 2) & (data["projector_rank"] == 1) & (data["topology"] == "left_comb") & (data["eta"] == data["eta"].min())].sort_values("internal_nodes")
    k = selected["internal_nodes"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.25))
    axes[0].plot(k, k, color=COLORS["black"], linestyle="--", label="$k$ theorem")
    axes[0].plot(k, selected["ambient_lower"], color=COLORS["blue"], marker="o", label="certified construction")
    axes[0].set_ylabel("ambient normalized constant")
    axes[0].set_title("ambient root error")
    axes[1].plot(k, k - 1, color=COLORS["black"], linestyle="--", label="$k-1$ theorem")
    axes[1].plot(k, selected["projected_lower"], color=COLORS["orange"], marker="s", label="certified construction")
    axes[1].set_ylabel("projected normalized constant")
    axes[1].set_title("projected/reduced root error")
    for index, ax in enumerate(axes):
        ax.set_xlabel("internal nodes $k$")
        ax.legend()
        light_grid(ax, "both")
        panel_label(ax, chr(ord("a") + index))
    save(fig, "fig06_k_vs_k_minus_one")
    caption = (
        f"The $k$ versus $k-1$ theorem on {len(selected)} registered binary left-comb instances (block B, dimension two, smallest $\\eta$; interval-certified lower construction, no seed uncertainty). "
        "Ambient and projected errors are normalized by $\\eta M^{{k-1}}$ and compared with the proved universal coefficients. "
        "The ambient construction matches the linear coefficient in these cells, whereas the displayed small-$\\eta$ projected construction remains far below $k-1$; projected fixed-$\\eta$ sharpness and novelty remain unresolved."
    )
    register(6, "fig06_k_vs_k_minus_one", "$k$ versus $k-1$ theorem", sources=[path], unique_instances=len(selected), seeds="not applicable to certified construction", restarts="not applicable", metric="normalized ambient/projected constants", uncertainty="directed interval enclosure", theoretical_reference="$k$ and $k-1$ homogeneous theorems", supported="ambient matching on the selected construction and validity of both uppers", not_supported="projected fixed-positive-eta optimality or novelty", caption=caption)


def figure07() -> None:
    path = DATA / "block_B.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["dimension"] == 2) & (data["projector_rank"] == 1) & np.isclose(data["eta"], 0.1)].copy()
    selected["sharpness"] = selected["projected_lower"] / selected["projected_upper"].replace(0, np.nan)
    fig, ax = plt.subplots(figsize=(6.8, 4.15))
    norm = Normalize(vmin=float(selected["imbalance"].min()), vmax=float(selected["imbalance"].max()))
    for index, arity in enumerate(sorted(selected["arity"].unique())):
        group = selected[selected["arity"] == arity]
        scatter = ax.scatter(
            group["depth"],
            group["path_length_sum"],
            c=group["imbalance"],
            cmap="viridis",
            norm=norm,
            s=14 + 8 * group["strahler_number"],
            marker=MARKERS[index],
            edgecolors=np.where(group["sharpness"].fillna(0).to_numpy() > 0.9, COLORS["vermillion"], COLORS["gray"]),
            linewidths=0.65,
            alpha=0.82,
            label=f"arity {arity}",
        )
    colorbar = fig.colorbar(scatter, ax=ax, label="imbalance")
    colorbar.ax.tick_params(labelsize=7)
    ax.set_xlabel("tree depth")
    ax.set_ylabel("root path-length sum")
    ax.set_title("Topology phase diagram; marker size encodes Strahler number")
    ax.legend(title="ordered grammar")
    light_grid(ax, "both")
    save(fig, "fig07_topology_phase_diagram")
    caption = (
        f"Topology phase diagram from block B ({len(selected):,} unique $\\eta=0.1$ instances; requested optimizer seeds/restarts are pending). "
        "Depth and root path-length sum define the axes, color is imbalance, size is Strahler number, and a vermillion edge marks an explicit projected lower/upper ratio above 0.9. "
        "These are exact topology statistics with interval lower values. The plot supports topology-dependent certificate behavior, not a causal phase transition or universal extremal topology."
    )
    register(7, "fig07_topology_phase_diagram", "Topology phase diagram", sources=[path], unique_instances=len(selected), seeds="optimizer grid pending", restarts="optimizer grid pending", metric="topology statistics and explicit projected lower/upper ratio", uncertainty="none for topology; interval enclosure for lower construction", theoretical_reference="$k-1$ projected upper", supported="association between tree invariants and observed sharpness", not_supported="causal phase transition or universal extremal topology", caption=caption)


def _tree_layout(tree: Tree):
    positions: dict[tuple[int, ...], tuple[float, float]] = {}
    internal_paths: list[tuple[int, ...]] = []
    leaf_x = 0

    def visit(item: Tree, path: tuple[int, ...], depth: int) -> float:
        nonlocal leaf_x
        if isinstance(item, Leaf):
            x = float(leaf_x)
            leaf_x += 1
            positions[path] = (x, -float(depth))
            return x
        internal_paths.append(path)
        xs = [visit(child, (*path, slot), depth + 1) for slot, child in enumerate(item.children)]
        x = float(np.mean(xs))
        positions[path] = (x, -float(depth))
        return x

    visit(tree, (), 0)
    return positions, internal_paths


def _path_item(tree: Tree, path: tuple[int, ...]) -> Tree:
    item = tree
    for slot in path:
        if isinstance(item, Leaf):
            raise ValueError("path passes a leaf")
        item = item.children[slot]
    return item


def figure08() -> None:
    path = INDEX / "node_contributions_v3.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["internal_nodes"] == 8) & (data["topology"] == "balanced")].sort_values("node_index")
    tree = label_shape(topology_family_shape(8, 2, "maximally_balanced"))
    positions, internal_paths = _tree_layout(tree)
    values = selected["shapley_projected"].to_numpy()
    scale = max(np.max(np.abs(values)), 1.0e-15)
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 5.1), gridspec_kw={"height_ratios": [1.2, 1]})
    ax = axes[0]
    for path_key, (x, y) in positions.items():
        item = _path_item(tree, path_key)
        if isinstance(item, Node):
            for slot in range(len(item.children)):
                cx, cy = positions[(*path_key, slot)]
                ax.plot([x, cx], [y, cy], color=COLORS["gray"], linewidth=0.8, zorder=1)
    for index, path_key in enumerate(internal_paths):
        x, y = positions[path_key]
        color = plt.cm.cividis(0.15 + 0.8 * abs(values[index]) / scale)
        ax.scatter([x], [y], s=270, facecolor=color, edgecolor=COLORS["black"], linewidth=0.8, zorder=3)
        ax.text(x, y, f"{index}\n{values[index]:.2g}", ha="center", va="center", fontsize=6.2, zorder=4)
    for path_key, (x, y) in positions.items():
        if isinstance(_path_item(tree, path_key), Leaf):
            ax.scatter([x], [y], s=22, facecolor="white", edgecolor=COLORS["orange"], zorder=3)
    ax.set_title("Balanced eight-node tree; node label is Shapley contribution")
    ax.axis("off")
    x = np.arange(len(selected))
    axes[1].bar(x - 0.18, selected["main_effect"], width=0.36, color=COLORS["blue"], edgecolor=COLORS["black"], label="single-node main effect")
    axes[1].bar(x + 0.18, selected["shapley_projected"], width=0.36, color=COLORS["orange"], edgecolor=COLORS["black"], hatch="//", label="all-mask Shapley attribution")
    axes[1].set_xlabel("preorder internal-node index")
    axes[1].set_ylabel("projected-error contribution")
    axes[1].legend(ncol=2)
    light_grid(axes[1], "y")
    save(fig, "fig08_node_contribution_map")
    caption = (
        f"Node contribution map for one balanced eight-node tree from block F (eight internal nodes, all $2^8=256$ leakage masks, no seed or restart sampling). "
        "The metric is projected root error: the tree labels show Shapley attribution and the lower panel compares single-node main effects with all-mask Shapley values; numerical efficiency residual is below $10^{{-12}}$. "
        "The exhaustive mask calculation supports attribution on this registered construction, not a unique physical causal interpretation."
    )
    register(8, "fig08_node_contribution_map", "Node contribution map", sources=[path, DATA / "block_F_leakage_masks.parquet"], unique_instances=1, seeds="not applicable", restarts="not applicable", metric="projected-error main effect and Shapley attribution", uncertainty="exhaustive 256-mask evaluation", theoretical_reference="exact subset expansion", supported="complete attribution for the selected construction", not_supported="unique causal interpretation", caption=caption)


def _mobius(values: np.ndarray, k: int) -> np.ndarray:
    coefficients = np.asarray(values, dtype=float).copy()
    for bit in range(k):
        for mask in range(2**k):
            if mask & (1 << bit):
                coefficients[mask] -= coefficients[mask ^ (1 << bit)]
    return coefficients


def figure09() -> None:
    path = DATA / "block_F_leakage_masks.parquet"
    data = pd.read_parquet(path)
    records = []
    for (k, topology, digest), group in data.groupby(["internal_nodes", "topology", "tree_hash"], sort=True):
        ordered = group.sort_values("mask")
        coefficients = _mobius(ordered["projected_error"].to_numpy(), int(k))
        by_order = defaultdict(float)
        for mask, value in enumerate(coefficients):
            if mask:
                by_order[int(mask.bit_count())] += abs(float(value))
        total = sum(by_order.values()) or 1.0
        records.append({"k": int(k), "topology": topology, "main": by_order[1] / total, "pair": by_order[2] / total, "higher": sum(value for order, value in by_order.items() if order >= 3) / total})
    frame = pd.DataFrame(records)
    summary = frame.groupby("k")[["main", "pair", "higher"]].median().reset_index()
    fig, ax = plt.subplots(figsize=(6.4, 3.65))
    bottom = np.zeros(len(summary))
    for column, label, color, hatch in [
        ("main", "main effects", COLORS["blue"], ""),
        ("pair", "pair interactions", COLORS["orange"], "//"),
        ("higher", "order $\\geq3$", COLORS["green"], "xx"),
    ]:
        ax.bar(summary["k"], summary[column], bottom=bottom, color=color, edgecolor=COLORS["black"], hatch=hatch, label=label)
        bottom += summary[column].to_numpy()
    ax.set_xlabel("internal nodes $k$")
    ax.set_ylabel("median fraction of absolute Möbius mass")
    ax.set_ylim(0, 1)
    ax.set_title("Residual interactions from every leakage mask")
    ax.legend(ncol=3)
    light_grid(ax, "y")
    save(fig, "fig09_residual_interactions")
    caption = (
        f"Residual interaction decomposition from all {len(data):,} block-F mask evaluations ({len(frame)} trees, no seeds or optimizer restarts). "
        "For each tree, the exact set function of projected error is Möbius-inverted; bars show topology-median fractions of absolute coefficient mass from first-, second-, and higher-order subsets. "
        "The reference is the exact subset expansion. This supports nonadditive local-error interactions in the explicit construction, not sign-free additivity or universality."
    )
    register(9, "fig09_residual_interactions", "Residual interaction decomposition", sources=[path], unique_instances=len(frame), seeds="not applicable", restarts="not applicable", metric="absolute Möbius interaction mass by order", uncertainty="median variation over three topology families", theoretical_reference="exact local subset expansion", supported="presence and order of mask interactions", not_supported="additivity or universal interaction fractions", caption=caption)


def figure10() -> None:
    path = DATA / "block_D.parquet"
    data = pd.read_parquet(path).copy()
    data["ratio"] = data["optimized_order_bound"] / data["mixed_mask_bound"].replace(0, np.nan)
    patterns = sorted(data["pattern"].unique())
    arities = sorted(data["arity"].unique())
    fig, ax = plt.subplots(figsize=(7.0, 3.65))
    positions, values, colors = [], [], []
    labels = []
    pos = 1
    for arity in arities:
        for index, pattern in enumerate(patterns):
            group = data[(data["arity"] == arity) & (data["pattern"] == pattern)]["ratio"].dropna()
            positions.append(pos)
            values.append(group.to_numpy())
            colors.append([COLORS["blue"], COLORS["orange"], COLORS["green"]][index % 3])
            labels.append(f"{arity}:{pattern}")
            pos += 1
        pos += 0.5
    boxplot = ax.boxplot(values, positions=positions, widths=0.58, patch_artist=True, showfliers=False, whis=(5, 95))
    for patch, color in zip(boxplot["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
        patch.set_edgecolor(color)
    ax.axhline(1.0, color=COLORS["black"], linestyle="--", linewidth=0.9, label="mixed-mask/reference order")
    ax.set_xticks(positions, labels, rotation=40, ha="right")
    ax.set_ylabel("optimized telescoping / mixed-mask certificate")
    ax.set_title("Optimal slot ordering; boxes span 5--95% of instances")
    ax.legend()
    light_grid(ax, "y")
    save(fig, "fig10_optimal_telescoping_order")
    caption = (
        f"Optimal telescoping order on all {len(data):,} block-D instances (declared seed count 10; no optimizer restart is used by the exact sorting rule). "
        "The metric is optimized-order certificate divided by the registered mixed-mask/reference-order certificate; boxes show median, quartiles, and 5--95 percent mathematical-instance variation. "
        "The pair-exchange theorem is the reference. The result supports never-worse and sometimes smaller certificates, but not optimality among all possible non-telescoping proof strategies."
    )
    register(10, "fig10_optimal_telescoping_order", "Optimal telescoping order", sources=[path], unique_instances=len(data), seeds=10, restarts=0, metric="optimized telescoping/mixed-mask reference certificate", uncertainty="5--95% mathematical-instance variation", theoretical_reference="pair-exchange ordering theorem", supported="optimality within the declared telescoping family", not_supported="optimality among all proof strategies", caption=caption)


def figure11() -> None:
    candidates = sorted((ROOT / "artifacts" / "runs_v3").glob("v3_smoke_*/extremizer_tensor.npz"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError("registered smoke extremizer is missing")
    source = candidates[-1]
    with np.load(source) as archive:
        key = archive.files[0]
        tensor = np.asarray(archive[key])
    if tensor.ndim < 3:
        raise RuntimeError("unexpected extremizer tensor shape")
    tangent = tensor[0]
    normal = tensor[1]
    vmax = max(float(np.max(np.abs(tangent))), float(np.max(np.abs(normal))), 1.0e-12)
    fig, axes = plt.subplots(1, 3, figsize=(8.5, 3.1), gridspec_kw={"width_ratios": [1, 1, 1.2]})
    for index, (ax, block, title) in enumerate(zip(axes[:2], [tangent, normal], ["tangent output block", "normal output block"])):
        image = ax.imshow(block, cmap="coolwarm", vmin=-vmax, vmax=vmax, origin="lower")
        for (row, column), value in np.ndenumerate(block):
            ax.text(column, row, f"{value:.3g}", ha="center", va="center", fontsize=7)
        ax.set_xticks(range(block.shape[1]))
        ax.set_yticks(range(block.shape[0]))
        ax.set_xlabel("second input coordinate")
        ax.set_ylabel("first input coordinate")
        ax.set_title(title)
        panel_label(ax, chr(ord("a") + index))
    fig.colorbar(image, ax=axes[:2], shrink=0.75, label="tensor entry")
    ax = axes[2]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [(0.5, 0.82, "$R_u$ tangent mass", COLORS["blue"]), (0.5, 0.52, "$\\mu(R_u,\\cdot)$ rotates", COLORS["orange"]), (0.5, 0.22, "later gates align residuals", COLORS["green"])]
    for x, y, label, color in boxes:
        patch = FancyBboxPatch((x - 0.34, y - 0.08), 0.68, 0.16, boxstyle="round,pad=0.02", facecolor="white", edgecolor=color, linewidth=1.1)
        ax.add_patch(patch)
        ax.text(x, y, label, ha="center", va="center")
    for (_, y1, _, _), (_, y2, _, _) in zip(boxes[:-1], boxes[1:]):
        ax.add_patch(FancyArrowPatch((0.5, y1 - 0.09), (0.5, y2 + 0.09), arrowstyle="-|>", mutation_scale=11, color=COLORS["gray"]))
    ax.set_title("registered alignment mechanism")
    panel_label(ax, "c")
    save(fig, "fig11_extremizer_geometry")
    caption = (
        "Extremizer geometry from the registered v3 smoke run (one explicit rank-one gated-rotation tensor, four gradient trajectories and one derivative-free recheck). "
        "Panels (a,b) show the actual tangent and normal output tensor blocks; panel (c) summarizes the certified mechanism. Entries are exact stored inputs up to float64 representation, without statistical uncertainty. "
        "The figure supports admissibility and alignment of this lower construction, not uniqueness or global optimality."
    )
    register(11, "fig11_extremizer_geometry", "Extremizer geometry", sources=[source, candidates[-1].parent / "best_lower_bound.json"], unique_instances=1, seeds=2, restarts=2, metric="registered tensor entries and attained normalized lower", uncertainty="independent optimizer disagreement recorded separately", theoretical_reference="gated planar-rotation construction", supported="admissibility and local residual alignment", not_supported="uniqueness or global optimality", caption=caption)


def figure12() -> None:
    path = DATA / "block_A_exact_atlas.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["arity"] == 2) & (data["shape_index"] == 0) & np.isclose(data["eta"], 0.1) & (data["internal_nodes"] <= 6)].copy()
    order = {"ambient": 0, "projected": 1, "normal": 2}
    selected["sort"] = selected["internal_nodes"] * 3 + selected["error_type"].map(order)
    selected = selected.sort_values("sort")
    labels = [f"k={int(row.internal_nodes)} {row.error_type}" for row in selected.itertuples()]
    y = np.arange(len(selected))
    lower = selected["certified_lower_bound"].to_numpy()
    upper = selected["certified_upper_bound"].to_numpy()
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.hlines(y, lower, upper, color=COLORS["gray"], linewidth=1.4)
    colors = [COLORS["green"] if bool(value) else COLORS["blue"] for value in selected["global_optimum_certified"]]
    ax.scatter(lower, y, marker="<", color=colors, s=38, label="certified lower")
    ax.scatter(upper, y, marker=">", color=COLORS["black"], s=38, label="proved upper")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("normalized constant")
    ax.set_title("Certified intervals for exact small registered cases")
    ax.legend(ncol=2)
    light_grid(ax, "x")
    save(fig, "fig12_certified_optimality_gaps")
    exact_count = int(selected["global_optimum_certified"].sum())
    caption = (
        f"Certified optimality gaps for {len(selected)} block-A binary small cases at $\\eta=0.1$ (no random seeds or restarts). "
        f"Horizontal intervals join the directed-interval explicit lower to the proved upper; green lower marks the {exact_count} globally certified zero/small cases. "
        "The homogeneous $k$ and $k-1$ theorems are the references. Closed intervals establish only the marked exact cases; open intervals are reported as unresolved, not as numerical optima."
    )
    register(12, "fig12_certified_optimality_gaps", "Certified optimality gaps", sources=[path], unique_instances=len(selected), seeds="not applicable", restarts="not applicable", metric="certified normalized lower and upper", uncertainty="directed interval enclosure", theoretical_reference="$k$ ambient and $k-1$ projected upper bounds", supported=f"global optimality in {exact_count} marked cases", not_supported="optimality in nonclosed intervals", caption=caption)


def figure13() -> None:
    path = DATA / "block_G.parquet"
    data = pd.read_parquet(path)
    records = []
    for expression, group in data.groupby("expression", sort=True):
        records.append(
            {
                "expression": expression,
                "triangle": float(group["triangle_upper"].iloc[0]),
                "cancellation": float(group["syntactic_cancellation_upper"].min()),
                "observed": float(group["observed_constant"].max()),
            }
        )
    frame = pd.DataFrame(records).sort_values("triangle")
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    height = 0.22
    ax.barh(y + height, frame["triangle"], height=height, color=COLORS["gray"], edgecolor=COLORS["black"], label="triangle upper")
    ax.barh(y, frame["cancellation"], height=height, color=COLORS["blue"], edgecolor=COLORS["black"], hatch="//", label="cancellation-aware upper")
    ax.barh(y - height, frame["observed"], height=height, color=COLORS["orange"], edgecolor=COLORS["black"], label="registered adversarial lower")
    labels = [value.replace("five_input_", "").replace("_", " ") for value in frame["expression"]]
    ax.set_yticks(y, labels)
    ax.set_xlabel("normalized signed-forest constant")
    ax.set_title("Cancellation is bounded separately from observed alignment")
    ax.legend(ncol=3, loc="lower right")
    light_grid(ax, "x")
    save(fig, "fig13_signed_polynomial_cancellation")
    caption = (
        f"Signed-polynomial cancellation across {len(frame)} registered forest families and {len(data)} block-G instances (20 optimizer seeds requested; the full restart grid is pending). "
        "The exact metric is the normalized signed-forest residual: triangle and syntactic-cancellation bars are certified uppers, while the orange bar is the largest registered explicit/adversarial lower over $\\eta$. "
        "The forest triangle theorem is the reference. The comparison supports improved bookkeeping in declared expressions, not globally sharp associator, FI, or GJI constants."
    )
    register(13, "fig13_signed_polynomial_cancellation", "Signed-polynomial cancellation", sources=[path], unique_instances=len(data), seeds="20 requested; pilot only", restarts="extended pending", metric="normalized signed-forest residual constant", uncertainty="variation over eta; empirical searches labeled lower only", theoretical_reference="signed-forest triangle upper", supported="cancellation-aware bookkeeping improvements", not_supported="globally sharp FI/GJI/associator constants", caption=caption)


def figure14() -> None:
    path = DATA / "block_H.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["dimension"] == 64) & (data["internal_nodes"] == 8) & (data["topology"] == "balanced") & np.isclose(data["eta"], 0.01)].sort_values("cp_rank_fraction")
    x = np.arange(len(selected))
    components = [
        ("recursive_representation_budget", "representation upper", COLORS["blue"], ""),
        ("closure_budget", "closure upper", COLORS["orange"], "//"),
        ("interaction_budget", "interaction upper", COLORS["green"], "xx"),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    bottom = np.zeros(len(selected))
    for column, label, color, hatch in components:
        ax.bar(x, selected[column], bottom=bottom, color=color, edgecolor=COLORS["black"], hatch=hatch, label=label)
        bottom += selected[column].to_numpy()
    ax.plot(x, selected["total_theorem_budget"], color=COLORS["black"], marker="D", linestyle="--", label="proved total upper")
    ax.set_xticks(x, [f"{value:.2g}" for value in selected["cp_rank_fraction"]])
    ax.set_xlabel("CP rank fraction")
    ax.set_ylabel("upper-bound budget")
    ax.set_title("Layered CP plus projection inequality; stacked height is the defined upper sum")
    ax.legend(ncol=2)
    light_grid(ax, "y")
    save(fig, "fig14_cp_projection_budget")
    caption = (
        f"CP plus projection budget for {len(selected)} selected block-H instances (dimension 64, eight-node balanced tree, $\\eta=0.01$; ten seeds are declared for the extended empirical matrix). "
        "Bars are the separately proved representation, closure, and interaction upper terms; their stack is the definition of the theorem upper and does not assert equality with error. "
        "The layered CP/projection inequality is the reference. The figure supports budget separation, not tightness or CP identifiability."
    )
    register(14, "fig14_cp_projection_budget", "CP plus projection error budget", sources=[path], unique_instances=len(selected), seeds="10 declared; analytic base", restarts=0, metric="representation/closure/interaction upper-bound components", uncertainty="analytic bounds; no empirical uncertainty", theoretical_reference="CP plus projection budget theorem", supported="separation of error sources", not_supported="additive equality, tightness, or CP identifiability", caption=caption)


def figure15() -> None:
    path = DATA / "block_C.parquet"
    data = pd.read_parquet(path)
    selected = data[(data["arity"] == 2) & (data["internal_nodes"] == 24) & np.isclose(data["eta"], 0.1)].copy()
    dimensions = sorted(selected["dimension"].unique())
    ratios = sorted(selected["requested_rank_ratio"].unique())
    topologies = [value for value in ("comb", "balanced") if value in set(selected["topology"])]
    fig, axes = plt.subplots(1, len(topologies), figsize=(7.8, 3.45), squeeze=False)
    for index, topology in enumerate(topologies):
        ax = axes[0, index]
        matrix = np.full((len(dimensions), len(ratios)), np.nan)
        subset = selected[selected["topology"] == topology]
        for yi, dimension in enumerate(dimensions):
            for xi, rank_ratio in enumerate(ratios):
                group = subset[(subset["dimension"] == dimension) & np.isclose(subset["requested_rank_ratio"], rank_ratio)]
                if not group.empty:
                    matrix[yi, xi] = float((group["projected_lower"] / group["projected_upper"]).max())
        image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="cividis", vmin=0, vmax=1)
        for (yi, xi), value in np.ndenumerate(matrix):
            if np.isfinite(value):
                ax.text(xi, yi, f"{value:.2f}", ha="center", va="center", color="white" if value < 0.45 else "black", fontsize=7)
        ax.set_xticks(range(len(ratios)), [f"{value:.3g}" for value in ratios])
        ax.set_yticks(range(len(dimensions)), dimensions)
        ax.set_xlabel("requested projector-rank ratio")
        ax.set_ylabel("ambient dimension")
        ax.set_title(topology)
        panel_label(ax, chr(ord("a") + index))
    fig.colorbar(image, ax=axes.ravel().tolist(), label="normalized lower / upper", shrink=0.8)
    fig.suptitle("Dimension/rank phase diagram for binary 24-node trees")
    save(fig, "fig15_dimension_rank_phase")
    caption = (
        f"Dimension/rank phase diagram from {len(selected)} block-C instances (binary 24-node trees, $\\eta=0.1$; ten optimizer seeds requested but not executed in the analytic base). "
        "Each tile is the embedded dimension-two projected lower divided by the $k-1$ upper; values are interval-enclosed and have no seed uncertainty. "
        "The embedding theorem is the reference. The grid supports dimension-independent admissibility of the construction, but no certified improvement from extra dimensions or ranks."
    )
    register(15, "fig15_dimension_rank_phase", "Dimension/rank phase diagram", sources=[path], unique_instances=len(selected), seeds="10 requested; extended pending", restarts="extended pending", metric="embedded projected lower/certified upper", uncertainty="interval enclosure; dimension/rank grid variation", theoretical_reference="dimension embedding and $k-1$ upper", supported="dimension-independent admissibility", not_supported="improvement from higher dimension/rank", caption=caption)


def figure16() -> None:
    candidates = sorted((ROOT / "artifacts" / "runs_v3").glob("v3_smoke_*/optimization_history.csv"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError("optimization history is missing")
    path = candidates[-1]
    data = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(6.8, 3.75))
    adam = data[data["phase"] == "adam"]
    for index, ((seed, restart), group) in enumerate(adam.groupby(["seed", "restart"], sort=True)):
        group = group.sort_values("step")
        ax.plot(group["step"], group["ratio"], marker=MARKERS[index % len(MARKERS)], markevery=max(1, len(group) // 5), linestyle=LINESTYLES[index % len(LINESTYLES)], color=[COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["purple"]][index % 4], label=f"Adam seed {int(seed)}, restart {int(restart)}")
    derivative = data[data["phase"] == "differential_evolution"]
    if not derivative.empty:
        ax.scatter([adam["step"].max()], [derivative["ratio"].max()], marker="X", s=65, color=COLORS["vermillion"], edgecolor=COLORS["black"], label="differential evolution")
    ax.axhline(1.0, color=COLORS["black"], linestyle="--", label="certified upper")
    ax.set_xlabel("recorded optimization step")
    ax.set_ylabel("attained lower / certified upper")
    ax.set_ylim(0, 1.04)
    ax.set_title("Every pilot trajectory; no failed search is hidden")
    ax.legend(ncol=2)
    light_grid(ax, "both")
    save(fig, "fig16_adversarial_convergence")
    trajectories = adam.groupby(["seed", "restart"]).ngroups + (1 if not derivative.empty else 0)
    caption = (
        f"Adversarial optimization convergence for the registered smoke calibration ({trajectories} displayed trajectories: four Adam starts and one independent differential-evolution recheck; one mathematical instance). "
        "The metric is attained normalized lower divided by the certified upper; every recorded step and all searches are shown, with no confidence interval inferred from restarts. "
        "The upper certificate is the reference. Agreement near one supports a strong empirical lower for this instance, not a global optimizer certificate or completion of the 460,800-trajectory extended grid."
    )
    register(16, "fig16_adversarial_convergence", "Adversarial optimization convergence", sources=[path, path.parent / "optimality_gap.json"], unique_instances=1, seeds=2, restarts=2, metric="attained lower/certified upper", uncertainty="all pilot trajectories shown; optimizer disagreement recorded", theoretical_reference="certified smoke upper 1", supported="independent empirical agreement on one instance", not_supported="global optimality or extended-grid completion", caption=caption)


def figure17() -> None:
    path = DATA / "computational_scaling.parquet"
    data = pd.read_parquet(path)
    backends = list(data["backend"].drop_duplicates())
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.25))
    palette = [COLORS["gray"], COLORS["blue"], COLORS["vermillion"]]
    for index, backend in enumerate(backends):
        group = data[data["backend"] == backend].sort_values("internal_nodes")
        k = group["internal_nodes"].to_numpy()
        median = group["median_seconds_per_tree"].to_numpy()
        low = group["minimum_seconds_per_tree"].to_numpy()
        high = group["maximum_seconds_per_tree"].to_numpy()
        axes[0].errorbar(k, median, yerr=[median - low, high - median], marker=MARKERS[index], linestyle=LINESTYLES[index], color=palette[index], capsize=2, label=backend.replace("_", " "))
        axes[1].plot(k, group["throughput_internal_nodes_per_second"], marker=MARKERS[index], linestyle=LINESTYLES[index], color=palette[index], label=backend.replace("_", " "))
        axes[2].plot(k, group["peak_vram_bytes"] / (1024**2), marker=MARKERS[index], linestyle=LINESTYLES[index], color=palette[index], label=backend.replace("_", " "))
    axes[0].set_yscale("log")
    axes[1].set_yscale("log")
    axes[0].set_ylabel("seconds per tree")
    axes[1].set_ylabel("internal nodes / second")
    axes[2].set_ylabel("peak allocated VRAM (MiB)")
    titles = ["wall time", "throughput", "device memory"]
    for index, ax in enumerate(axes):
        ax.set_xlabel("internal nodes $k$")
        ax.set_title(titles[index])
        light_grid(ax, "both")
        panel_label(ax, chr(ord("a") + index))
    axes[0].legend(ncol=1)
    save(fig, "fig17_computational_scaling")
    caption = (
        f"Environment-specific scaling benchmark ({len(data)} registered backend/size cells; five timing repeats and 15--30 calls per repeat). "
        "Panels show median wall time with min--max repeat range, derived node throughput, and peak allocated VRAM for the coordinate reference, vectorized NumPy CPU, and CUDA evaluator; float64 outputs agree exactly in this invariant control. "
        "No asymptotic complexity or cross-hardware performance claim is supported."
    )
    register(17, "fig17_computational_scaling", "Computational scaling", sources=[path, DATA / "computational_scaling_summary.json"], unique_instances=len(data), seeds="not applicable", restarts="five timing repeats", metric="median wall time, throughput, peak VRAM", uncertainty="min--max over five timing repeats", theoretical_reference="bounded-arity linear tree traversal", supported="local reference/CPU/GPU scaling and parity", not_supported="cross-hardware or asymptotic performance superiority", caption=caption)


def figure18() -> None:
    compile_tikz(
        18,
        "fig18_claim_evidence_dag",
        "Claim/evidence/extremizer DAG",
        [
            ROOT / "claims" / "theorem_registry_v3.yaml",
            ROOT / "claims" / "claim_evidence_matrix_v3.csv",
            DATA / "full_execution_manifest.json",
        ],
        "Claim/evidence/extremizer dependency graph generated from the v3 theorem and evidence registries. Proved upper bounds, certified or empirical lower evidence, experiments, and unresolved novelty are separate epistemic layers. The graph supports traceability only; it does not turn a search result into a theorem or authorize release.",
    )


def _write_caption_file() -> None:
    words = {
        1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
        7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve",
        13: "Thirteen", 14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
    }
    lines = ["% Generated by scripts/figures_v3/build.py; do not edit experimental captions by hand."]
    for record in FIGURES:
        if record["supplementary"] or not isinstance(record["number"], int):
            continue
        caption = record["caption_latex"].replace("%", r"\%")
        lines.append(rf"\newcommand{{\FigCaption{words[record['number']]}}}{{{caption}}}")
    (OUT / "captions.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for builder in (
        figure01, figure02, figure03, figure04, figure05, figure06,
        figure07, figure08, figure09, figure10, figure11, figure12,
        figure13, figure14, figure15, figure16, figure17, figure18,
    ):
        builder()
    main_figures = [record for record in FIGURES if not record["supplementary"]]
    if len(main_figures) != 18 or {record["number"] for record in main_figures} != set(range(1, 19)):
        raise RuntimeError("the mandatory 18-figure contract is incomplete")
    _write_caption_file()
    manifest = {
        "generator": rel(Path(__file__)),
        "mandatory_figure_count": len(main_figures),
        "supplementary_figure_count": len(FIGURES) - len(main_figures),
        "all_outputs_vector": True,
        "default_matplotlib_style_used": False,
        "figures": FIGURES,
    }
    manifest_path = DATA / "figure_manifest_v3.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"mandatory_figures": len(main_figures), "supplementary_figures": len(FIGURES) - len(main_figures), "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
