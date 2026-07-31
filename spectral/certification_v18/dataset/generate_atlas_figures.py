"""Generate the A-N track's visual atlas figures (SEION V5 Phase 10) from
real, already-computed data only -- no fabricated or illustrative-only
numbers. Each figure is written as PNG (300dpi) + SVG, with its source
data and a sha256 manifest, per mission section 10.

Run: python -m spectral.certification_v18.dataset.generate_atlas_figures
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from spectral.certification_v18.final_gate_evaluation import main as compute_final_gate

ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(__file__).resolve().parent
FIGURES = DATASET / "figures"
TABLES = DATASET / "tables"
HASHES = DATASET / "hashes"

STATUS_COLOR = {
    "STRUCTURAL_IDENTITY_PASS": "#4C72B0",
    "NUMERICAL_SANITY_PASS": "#64B5CD",
    "EMPIRICAL_SCREENING_PASS": "#55A868",
    "STATISTICALLY_VALIDATED_PASS": "#8172B2",
    "VALIDATED_NUMERICAL_CERTIFICATE": "#937860",
    "EXACT_CERTIFICATE": "#2CA02C",
    "WARN": "#DD8452",
    "FAIL": "#C44E52",
    "NOT_APPLICABLE": "#BBBBBB",
    "NOT_CERTIFIABLE_AS_DEFINED": "#7F7F7F",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_figure(fig, name: str, source_data: dict) -> dict:
    png_path = FIGURES / f"{name}.png"
    svg_path = FIGURES / f"{name}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    data_path = TABLES / f"{name}.json"
    data_path.write_text(json.dumps(source_data, indent=2, default=str), encoding="utf-8")
    manifest = {
        "figure": name,
        "generator": "spectral/certification_v18/dataset/generate_atlas_figures.py",
        "source_data": f"tables/{name}.json",
        "hashes": {
            "png": sha256_file(png_path),
            "svg": sha256_file(svg_path),
            "source_data": sha256_file(data_path),
        },
    }
    (HASHES / f"{name}.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def figure_gate_status_overview() -> dict:
    """Figure 21 (mission list: 'claim-proof-code-run-evidence graph' analogue
    for A-N): the 8 A-N critical gates and their computed typed status,
    directly from final_gate_evaluation.py -- not re-typed by hand."""
    result = compute_final_gate()
    gates = result["gate_status"]
    order = list(gates.keys())
    statuses = [gates[g] for g in order]
    colors = [STATUS_COLOR.get(s, "#000000") for s in statuses]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(order, [1] * len(order), color=colors)
    for i, status in enumerate(statuses):
        ax.text(0.5, i, status, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title(f"A-N critical gate status -> {result['final_state']}")
    ax.invert_yaxis()
    fig.tight_layout()
    return write_figure(fig, "21_gate_status_overview", result)


def figure_block_status_summary() -> dict:
    """Per-block typed status, directly from final_gate_evaluation.py."""
    result = compute_final_gate()
    blocks = result["block_status"]
    order = list(blocks.keys())
    statuses = [blocks[b] for b in order]
    colors = [STATUS_COLOR.get(s, "#000000") for s in statuses]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(order, [1] * len(order), color=colors)
    for i, status in enumerate(statuses):
        ax.text(0.5, i, status, ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title("A-N block-by-block typed status (14 blocks)")
    ax.invert_yaxis()
    fig.tight_layout()
    return write_figure(fig, "22_block_status_summary", result)


def figure_s1_gpu_cpu_crossover() -> dict | None:
    """Figure: mean wall time by device x n across the Phase 4 S1 broad
    screening sweep, testing whether the Phase 3 pilot's GPU<CPU finding
    (only tested up to n=24) reverses at larger n. Skipped if the S1
    sweep has not completed yet -- never fabricated."""
    s1_path = ROOT / "artifacts" / "phase4_s1_broad_screening" / "s1_results.parquet"
    if not s1_path.exists():
        return None
    df = pd.read_parquet(s1_path)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for device, group in df.groupby("device"):
        means = group.groupby("n")["wall_time_seconds"].mean().sort_index()
        ax.plot(means.index, means.values, marker="o", label=device)
    ax.set_xlabel("n (ambient dimension)")
    ax.set_ylabel("mean wall time per cell (s)")
    ax.set_title("Phase 4 S1: CPU vs GPU wall time, n up to 96")
    ax.legend()
    fig.tight_layout()
    source = df.groupby(["device", "n"])["wall_time_seconds"].mean().reset_index().to_dict("records")
    return write_figure(fig, "25_s1_gpu_cpu_crossover", {"rows": source})


def main() -> list[dict]:
    for directory in (FIGURES, TABLES, HASHES):
        directory.mkdir(parents=True, exist_ok=True)
    manifests = [figure_gate_status_overview(), figure_block_status_summary()]
    crossover = figure_s1_gpu_cpu_crossover()
    if crossover is not None:
        manifests.append(crossover)
    index_path = DATASET / "manifests" / "figure_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(manifests, indent=2), encoding="utf-8")
    return manifests


if __name__ == "__main__":
    result = main()
    print(json.dumps({"figures_generated": len(result)}, indent=2))
