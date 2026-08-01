"""Generate the research-v3 scientific tables from registered artifacts.

No experimental value is handwritten in a LaTeX source.  This program is
the sole producer of the sixteen mandatory tables and of the prior-art
matrix used by the mathematical manuscript.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]

import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

from seion_core.research_v3.interval_certification import (  # noqa: E402
    EXACTLY_DETERMINED_POSITIVE,
    EXACTLY_ZERO_BY_THEOREM,
    NO_POSITIVE_LOWER_BOUND_OBTAINED,
    POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP,
    classify_optimality,
)

DATA = ROOT / "artifacts" / "research_v3"
INDEX = ROOT / "artifacts" / "index"
OUT = ROOT / "papers" / "tree_stability_v3" / "tables"


def esc(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\allowbreak\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def num(value: float | int | np.number | None, digits: int = 3) -> str:
    if value is None or not np.isfinite(float(value)):
        return r"\textemdash"
    value = float(value)
    if value == 0.0:
        return r"\num{0}"
    if abs(value) >= 1.0e4 or abs(value) < 1.0e-3:
        return rf"\num{{{value:.2e}}}"
    return rf"\num{{{value:.{digits}f}}}"


def write_table(name: str, header: str, rows: Iterable[str], spec: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [rf"\begin{{tabular}}{{{spec}}}", r"\toprule", header, r"\midrule"]
    lines.extend(rows)
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path = OUT / f"{name}.tex"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def table_typed_notation() -> Path:
    entries = [
        (r"$V_\tau,W_\tau$", "ambient and reduced Hilbert spaces of type $\\tau$"),
        (r"$Q_\tau,P_\tau$", "isometry and orthogonal projector $P_\\tau=Q_\\tau Q_\\tau^*$"),
        (r"$F_v,R_v$", "ambient and recursively projected values at node $v$"),
        (r"$D_v^P,D_v^N$", "tangent and normal components of $F_v-R_v$"),
        (r"$M_v,\rho_v$", "local operator-norm and closure-residual bounds"),
        (r"$B_v^F,B_v^R$", "certificates for $\\lVert F_v\\rVert$ and $\\lVert R_v\\rVert$"),
        (r"$B_v^A,B_v^P,B_v^N$", "ambient, projected, and normal error certificates"),
        (r"$C_T^{\mathrm{amb}},C_T^P$", "best universal constants for a typed tree $T$"),
    ]
    return write_table(
        "typed_notation",
        r"symbol & generated meaning \\",
        (f"{symbol} & {meaning} \\\\" for symbol, meaning in entries),
        r"@{}lp{0.68\linewidth}@{}",
    )


def table_topology_statistics() -> Path:
    data = pd.read_parquet(INDEX / "tree_instances_v3.parquet")
    rows = []
    for grammar, group in data.groupby("family", sort=True):
        rows.append(
            f"{esc(grammar)} & {int(len(group))} & {int(group['tree_hash'].nunique())} & "
            f"{int(group['internal_nodes'].min())}--{int(group['internal_nodes'].max())} & "
            f"{int(group['depth'].max())} \\\\"
        )
    return write_table(
        "topology_statistics",
        r"grammar & occurrences & unique hashes & internal nodes & max depth \\",
        rows,
        r"@{}lrrrr@{}",
    )


def _a_small() -> pd.DataFrame:
    data = pd.read_parquet(DATA / "block_A_exact_atlas.parquet")
    return data[(data["internal_nodes"] <= 4) & (data["shape_index"] == 0)]


def table_exact_small_constants() -> Path:
    data = _a_small()
    rows = []
    for keys, group in data.groupby(["arity", "internal_nodes", "error_type"], sort=True):
        arity, nodes, error = keys
        rows.append(
            f"{arity} & {nodes} & {esc(error)} & {num(group['certified_lower_bound'].max())} & "
            f"{num(group['certified_upper_bound'].min())} & "
            f"{esc('yes' if group['global_optimum_certified'].any() else 'no')} \\\\"
        )
    return write_table(
        "exact_small_constants",
        r"arity & $k$ & error & \multicolumn{1}{c}{lower} & \multicolumn{1}{c}{upper} & global certificate \\",
        rows,
        r"@{}rrlSSl@{}",
    )


def _homogeneous_table(error: str, filename: str) -> Path:
    data = pd.read_parquet(DATA / "block_B.parquet")
    lower = f"{error}_lower"
    upper = f"{error}_upper"
    rows = []
    sample = data[(data["dimension"] == 2) & (data["eta"] == data["eta"].min())]
    for keys, group in sample.groupby(["arity", "internal_nodes"], sort=True):
        arity, nodes = keys
        normalized = group[lower]
        rows.append(
            f"{arity} & {nodes} & {num(normalized.max())} & {num(group[upper].min())} & "
            f"{num((normalized / group[upper]).max())} \\\\"
        )
    label = "ambient" if error == "ambient" else "projected-root"
    return write_table(
        filename,
        rf"arity & $k$ & \multicolumn{{1}}{{c}}{{best {label} lower}} & \multicolumn{{1}}{{c}}{{theorem upper}} & \multicolumn{{1}}{{c}}{{lower/upper}} \\",
        rows,
        r"@{}rrSSS@{}",
    )


def table_nodewise_formulas() -> Path:
    formulas = [
        ("homogeneous ambient", r"$k\rho M^{k-1}\prod_\ell\lVert z_\ell\rVert$", "proved"),
        ("homogeneous projected", r"$(k-1)\rho M^{k-1}\prod_\ell\lVert z_\ell\rVert$", "proved"),
        ("nodewise subset", r"$\rho_v\prod_iB_i^R+M_v\sum_{\varnothing\ne S}\prod_{i\in S}B_i^A\prod_{j\notin S}B_j^R$", "proved"),
        ("path sum", r"$\sum_v\rho_v\prod_{e\in\pi(v)}L_e$", "proved upper"),
        ("optimized telescoping", r"$\min_\pi\sum_j w_{\pi_j}(f_{\pi_j}-r_{\pi_j})\prod_{i<j}f_{\pi_i}\prod_{i>j}r_{\pi_i}$", "proved upper"),
    ]
    return write_table(
        "nodewise_formulas",
        r"certificate & generated formula & status \\",
        (f"{esc(name)} & {formula} & {esc(status)} \\\\" for name, formula, status in formulas),
        r"@{}lp{0.58\linewidth}l@{}",
    )


def table_bound_hierarchy() -> Path:
    data = pd.read_parquet(DATA / "block_D.parquet")
    rows = []
    for pattern, group in data.groupby("pattern", sort=True):
        ratios = {
            "nodewise": group["nodewise_bound"] / group["homogeneous_ambient_bound"],
            "path": group["path_sum_bound"] / group["homogeneous_ambient_bound"],
            "mixed": group["mixed_mask_bound"] / group["homogeneous_ambient_bound"],
            "optimized": group["optimized_order_bound"] / group["homogeneous_ambient_bound"],
        }
        rows.append(
            f"{esc(pattern)} & {num(np.median(ratios['nodewise']))} & {num(np.median(ratios['path']))} & "
            f"{num(np.median(ratios['mixed']))} & {num(np.median(ratios['optimized']))} & {len(group)} \\\\"
        )
    return write_table(
        "bound_hierarchy",
        r"local pattern & \multicolumn{1}{c}{nodewise} & \multicolumn{1}{c}{path sum} & \multicolumn{1}{c}{mixed mask} & \multicolumn{1}{c}{optimized} & instances \\",
        rows,
        r"@{}lSSSSr@{}",
    )


def table_extremizer_constructions() -> Path:
    data = pd.read_parquet(DATA / "block_A_exact_atlas.parquet")
    rows = []
    for error, group in data.groupby("error_type", sort=True):
        positive = group[group["certified_upper_bound"] > 0].copy()
        positive["ratio"] = positive["certified_lower_bound"] / positive["certified_upper_bound"]
        best = positive.loc[positive["ratio"].idxmax()]
        rows.append(
            f"{esc(error)} & gated planar rotation & {int(best['arity'])} & {int(best['internal_nodes'])} & "
            f"{num(best['eta'])} & {num(best['ratio'])} & {esc(best['status'])} \\\\"
        )
    return write_table(
        "extremizer_constructions",
        r"error & construction & arity & $k$ & \multicolumn{1}{c}{$\eta$} & \multicolumn{1}{c}{lower/upper} & status \\",
        rows,
        r"@{}llrrSSl@{}",
    )


def table_optimality_gaps() -> Path:
    """One row per error type, split by the four mutually exclusive optimality classes.

    The former version reported an "exact" column that counted only the vacuous
    ``lower == upper == 0`` rows and a "near" column that counted the genuinely
    determined ones. Both columns are replaced by the four disjoint counts below, which
    sum to the configuration count.
    """
    data = pd.read_csv(INDEX / "optimality_gaps_v3.csv")
    data = data.assign(
        status=[
            classify_optimality(low, up)
            for low, up in zip(
                data["certified_lower_bound"], data["certified_upper_bound"], strict=True
            )
        ]
    )
    rows = []
    for error, group in data.groupby("error_type", sort=True):
        determined = int((group["status"] == EXACTLY_DETERMINED_POSITIVE).sum())
        zero = int((group["status"] == EXACTLY_ZERO_BY_THEOREM).sum())
        partial = int((group["status"] == POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP).sum())
        none = int((group["status"] == NO_POSITIVE_LOWER_BOUND_OBTAINED).sum())
        rows.append(
            f"{esc(error)} & {len(group)} & {determined} & {zero} & {partial} & {none} & "
            f"{num(group['absolute_gap'].median())} \\\\"
        )
    return write_table(
        "optimality_gaps",
        r"error type & configurations & determined & zero by theorem & partial & "
        r"no positive lower bound & \multicolumn{1}{c}{median abs. gap} \\",
        rows,
        r"@{}lrrrrrS@{}",
    )


def table_signed_expression_constants() -> Path:
    data = pd.read_parquet(DATA / "block_G.parquet")
    rows = []
    for expression, group in data.groupby("expression", sort=True):
        rows.append(
            f"{esc(expression)} & {num(group['triangle_upper'].iloc[0])} & "
            f"{num(group['syntactic_cancellation_upper'].min())} & "
            f"{num(group['observed_constant'].max())} & "
            f"{num(group['observed_over_triangle'].max())} & {esc(group['optimizer_status'].iloc[0])} \\\\"
        )
    return write_table(
        "signed_expression_constants",
        r"expression & \multicolumn{1}{c}{triangle} & \multicolumn{1}{c}{cancellation upper} & \multicolumn{1}{c}{observed} & \multicolumn{1}{c}{observed/triangle} & search status \\",
        rows,
        r"@{}lSSSSp{0.20\linewidth}@{}",
    )


def table_dimension_rank_interaction() -> Path:
    data = pd.read_parquet(DATA / "block_C.parquet")
    data = data[data["eta"] == 0.1]
    rows = []
    for keys, group in data.groupby(["dimension", "requested_rank_ratio"], sort=True):
        dimension, ratio = keys
        normalized = group["projected_lower"]
        rows.append(
            f"{dimension} & {num(ratio)} & {int(group['projector_rank'].median())} & "
            f"{num(normalized.max())} & {num(group['projected_upper'].min())} & "
            f"{esc('yes' if group['larger_dimension_improvement_certified'].any() else 'no')} \\\\"
        )
    return write_table(
        "dimension_rank_interaction",
        r"dimension & \multicolumn{1}{c}{rank ratio} & rank & \multicolumn{1}{c}{best normalized lower} & \multicolumn{1}{c}{upper} & improvement certified \\",
        rows,
        r"@{}rSrSSl@{}",
    )


def table_cp_projection_budget() -> Path:
    data = pd.read_parquet(DATA / "block_H.parquet")
    data = data[(data["eta"] == 0.01) & (data["topology"] == "balanced")]
    rows = []
    for keys, group in data.groupby(["dimension", "cp_rank_fraction"], sort=True):
        dimension, fraction = keys
        rows.append(
            f"{dimension} & {num(fraction)} & {int(group['cp_rank'].median())} & "
            f"{num(group['tensor_reconstruction_error'].median())} & "
            f"{num(group['recursive_representation_budget'].median())} & "
            f"{num(group['closure_budget'].median())} & "
            f"{num(group['interaction_budget'].median())} & "
            f"{num(group['total_theorem_budget'].median())} \\\\"
        )
    return write_table(
        "cp_projection_budget",
        r"dim. & \multicolumn{1}{c}{rank frac.} & rank & \multicolumn{1}{c}{tensor err.} & \multicolumn{1}{c}{representation} & \multicolumn{1}{c}{closure} & \multicolumn{1}{c}{interaction} & \multicolumn{1}{c}{total upper} \\",
        rows,
        r"@{}rSrSSSSS@{}",
    )


def table_precision_conditioning() -> Path:
    data = pd.read_parquet(DATA / "block_I.parquet")
    rows = []
    for keys, group in data.groupby(["precision", "case"], sort=True):
        precision, case = keys
        rows.append(
            f"{esc(precision)} & {esc(case)} & {num(group['residual'].max())} & "
            f"{num(group['backward_error'].max())} & {num(group['condition_estimate'].max())} & "
            f"{num(group['bound_violation_margin'].min())} \\\\"
        )
    return write_table(
        "precision_conditioning",
        r"precision & case & \multicolumn{1}{c}{max residual} & \multicolumn{1}{c}{backward error} & \multicolumn{1}{c}{condition est.} & \multicolumn{1}{c}{min bound margin} \\",
        rows,
        r"@{}llSSSS@{}",
    )


def table_cpu_gpu_parity() -> Path:
    data = pd.read_parquet(DATA / "block_I.parquet").dropna(subset=["cpu_gpu_parity"])
    rows = []
    for precision, group in data.groupby("precision", sort=True):
        rows.append(
            f"{esc(precision)} & {len(group)} & {num(group['cpu_gpu_parity'].max())} & "
            f"{num(group['cpu_gpu_parity'].median())} & {esc('pass' if group['cpu_gpu_parity'].max() < 1e-6 else 'review')} \\\\"
        )
    return write_table(
        "cpu_gpu_parity",
        r"precision & cases & \multicolumn{1}{c}{max abs. difference} & \multicolumn{1}{c}{median difference} & result \\",
        rows,
        r"@{}lrSSl@{}",
    )


def table_failures_counterexamples() -> Path:
    failures = pd.read_csv(INDEX / "failures_v3.csv")
    invalid = pd.read_parquet(DATA / "block_E.parquet")
    invalid = invalid[invalid["control"] == "invalid_edge"]
    rows = [
        f"registered run failures & {len(failures)} & {esc('none' if failures.empty else 'inspect registry')} \\\\ ",
        f"invalid typed edges & {len(invalid)} & {esc('rejected before evaluation')} \\\\ ",
        f"zero projected one-node constant & {int((_a_small()['error_type'].eq('projected') & _a_small()['global_optimum_certified']).sum())} & exact control \\\\ ",
        f"fixed-$\\eta$ universal sharpness & 1 & open; no optimality claim \\\\ ",
        f"extended optimizer grid & 1 & resource-gated and pending \\\\ ",
    ]
    return write_table(
        "failure_counterexample_registry",
        r"item & count & disposition \\",
        rows,
        r"@{}lrl@{}",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def table_reproducibility_manifest() -> Path:
    full = json.loads((DATA / "full_execution_manifest.json").read_text(encoding="utf-8"))
    enumeration = json.loads((DATA / "tree_enumeration_summary.json").read_text(encoding="utf-8"))
    entries = [
        ("source commit", full["source_commit"][:12]),
        ("scientific instances A--I", str(full["scientific_instances"])),
        ("enumerated tree occurrences", str(enumeration["rows"])),
        ("unique tree hashes", str(enumeration["unique_mathematical_objects"])),
        ("leakage masks", str(full["leakage_masks_executed"])),
        ("CPU/GPU max difference", f"{full['maximum_cpu_gpu_parity_error']:.3e}"),
        ("optimizer trajectories requested", str(full["optimizer_trajectories_requested_extended"])),
        ("optimizer status", full["optimizer_grid_status"]),
        ("release status", "FAIL_CLOSED_NOVELTY"),
    ]
    return write_table(
        "reproducibility_manifest",
        r"field & generated value \\",
        (f"{esc(key)} & {esc(value)} \\\\" for key, value in entries),
        r"@{}lp{0.55\linewidth}@{}",
    )


def build_prior_art_matrix() -> tuple[Path, Path]:
    registry_path = ROOT / "claims" / "prior_art_registry_v3.yaml"
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    records = raw.get("records", raw.get("entries", raw if isinstance(raw, list) else []))
    if isinstance(records, dict):
        records = list(records.values())
    normalized = []
    for record in records:
        normalized.append(
            {
                "id": record.get("id", record.get("key", "unidentified")),
                "area": record.get("area", record.get("topic", record.get("source", "unspecified"))),
                "established_result": record.get("established_result", record.get("result", "")),
                "closest_known_construction": record.get("closest_known_construction", record.get("closest_source", "")),
                "exact_overlap": record.get("exact_overlap", ""),
                "genuine_difference": record.get("genuine_difference", ""),
                "theorem_level_novelty": record.get("theorem_level_novelty", record.get("novelty_status", "NOT_ESTABLISHED")),
                "computational_novelty": record.get("computational_novelty", "NOT_ESTABLISHED"),
                "limitation": record.get("limitation", record.get("novelty_limitation", "")),
            }
        )
    frame = pd.DataFrame(normalized)
    csv_path = DATA / "prior_art_matrix.csv"
    frame.to_csv(csv_path, index=False)
    rows = []
    status_labels = {
        "STANDARD_RESTRICTION_RESULT": "standard restriction",
        "KNOWN_BOUND_NEW_SPECIALIZATION": "known-bound specialization",
        "NOVELTY_NOT_ESTABLISHED": "novelty not established",
        "STANDARD_MULTILINEAR_BOUND": "standard multilinear bound",
    }
    for _, row in frame.head(14).iterrows():
        rows.append(
            f"{esc(row['area'])} & {esc(row['exact_overlap'])} & {esc(row['genuine_difference'])} & "
            f"{esc(status_labels.get(row['theorem_level_novelty'], row['theorem_level_novelty']))} \\\\"
        )
    tex_path = write_table(
        "prior_art_matrix",
        r"area & overlap & v3 difference & novelty status \\",
        rows,
        (
            r"@{}>{\raggedright\arraybackslash}p{0.17\linewidth}"
            r">{\raggedright\arraybackslash}p{0.26\linewidth}"
            r">{\raggedright\arraybackslash}p{0.31\linewidth}"
            r">{\raggedright\arraybackslash}p{0.16\linewidth}@{}"
        ),
    )
    return csv_path, tex_path


def _class_count(frame: pd.DataFrame, wanted: str) -> int:
    """Count rows of ``frame`` falling in one optimality class.

    The class is recomputed from the certified bounds rather than read from any stored
    ``status`` column, so that historical artifacts written under the earlier, inverted
    vocabulary are reclassified rather than trusted.
    """
    return sum(
        classify_optimality(low, up) == wanted
        for low, up in zip(
            frame["certified_lower_bound"], frame["certified_upper_bound"], strict=True
        )
    )


def write_results_macros() -> Path:
    full = json.loads((DATA / "full_execution_manifest.json").read_text(encoding="utf-8"))
    enumeration = json.loads((DATA / "tree_enumeration_summary.json").read_text(encoding="utf-8"))
    gaps = pd.read_csv(INDEX / "optimality_gaps_v3.csv")
    exact = pd.read_parquet(DATA / "block_A_exact_atlas.parquet")
    fmt_int = lambda value: f"{int(value):,}".replace(",", "{,}")
    lines = [
        "% Generated by scripts/build_tree_constants_v3_tables.py.",
        rf"\newcommand{{\VThreeScientificInstances}}{{{fmt_int(full['scientific_instances'])}}}",
        rf"\newcommand{{\VThreeTreeOccurrences}}{{{fmt_int(enumeration['rows'])}}}",
        rf"\newcommand{{\VThreeUniqueTrees}}{{{fmt_int(enumeration['unique_mathematical_objects'])}}}",
        rf"\newcommand{{\VThreeLeakageMasks}}{{{fmt_int(full['leakage_masks_executed'])}}}",
        # Optimality classification. The former single macro \VThreeExactCells counted
        # every row with lower == upper, without separating the genuinely determined
        # constants from the vacuous rows where the proved upper bound is itself zero.
        # Those two situations are now counted separately, and the number of
        # configurations for which no positive lower bound was obtained is reported
        # explicitly rather than being hidden inside a "maximum relative gap" of 1.
        rf"\newcommand{{\VThreeDeterminedPositive}}{{{fmt_int(_class_count(gaps, EXACTLY_DETERMINED_POSITIVE))}}}",
        rf"\newcommand{{\VThreeZeroByTheorem}}{{{fmt_int(_class_count(gaps, EXACTLY_ZERO_BY_THEOREM))}}}",
        rf"\newcommand{{\VThreePartialLowerBound}}{{{fmt_int(_class_count(gaps, POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP))}}}",
        rf"\newcommand{{\VThreeNoPositiveLowerBound}}{{{fmt_int(_class_count(gaps, NO_POSITIVE_LOWER_BOUND_OBTAINED))}}}",
        rf"\newcommand{{\VThreeGapRegistryRows}}{{{fmt_int(len(gaps))}}}",
        rf"\newcommand{{\VThreeNoPositiveLowerPercent}}{{\num{{{100.0 * _class_count(gaps, NO_POSITIVE_LOWER_BOUND_OBTAINED) / len(gaps):.1f}}}}}",
        rf"\newcommand{{\VThreeExactAtlasDeterminedPositive}}{{{fmt_int(_class_count(exact, EXACTLY_DETERMINED_POSITIVE))}}}",
        rf"\newcommand{{\VThreeExactAtlasZeroByTheorem}}{{{fmt_int(_class_count(exact, EXACTLY_ZERO_BY_THEOREM))}}}",
        rf"\newcommand{{\VThreeMaxAbsoluteGap}}{{\num{{{float(gaps['absolute_gap'].max()):.3g}}}}}",
        rf"\newcommand{{\VThreeMaxParity}}{{\num{{{float(full['maximum_cpu_gpu_parity_error']):.3e}}}}}",
        rf"\newcommand{{\VThreeCoreWallSeconds}}{{\num{{{float(full['wall_seconds']):.2f}}}}}",
        rf"\newcommand{{\VThreeExtendedTrajectories}}{{{fmt_int(full['optimizer_trajectories_requested_extended'])}}}",
        rf"\newcommand{{\VThreeSourceCommit}}{{\texttt{{{full['source_commit'][:12]}}}}}",
        r"\newcommand{\VThreeFigureCount}{18}",
        r"\newcommand{\VThreeTableCount}{16}",
        r"\newcommand{\VThreeReleaseStatus}{\texttt{FAIL\_CLOSED\_NOVELTY}}",
    ]
    path = ROOT / "papers" / "tree_stability_v3" / "generated_results.tex"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    outputs = [
        table_typed_notation(),
        table_topology_statistics(),
        table_exact_small_constants(),
        _homogeneous_table("ambient", "homogeneous_ambient_constants"),
        _homogeneous_table("projected", "homogeneous_projected_constants"),
        table_nodewise_formulas(),
        table_bound_hierarchy(),
        table_extremizer_constructions(),
        table_optimality_gaps(),
        table_signed_expression_constants(),
        table_dimension_rank_interaction(),
        table_cp_projection_budget(),
        table_precision_conditioning(),
        table_cpu_gpu_parity(),
        table_failures_counterexamples(),
        table_reproducibility_manifest(),
    ]
    prior_csv, prior_tex = build_prior_art_matrix()
    outputs.append(prior_tex)
    macro_path = write_results_macros()
    manifest = {
        "generator": str(Path(__file__).relative_to(ROOT)),
        "mandatory_table_count": 16,
        "supplementary_table_count": 1,
        "tables": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(path),
            }
            for path in outputs
        ],
        "prior_art_csv": str(prior_csv.relative_to(ROOT)).replace("\\", "/"),
        "generated_results_macros": str(macro_path.relative_to(ROOT)).replace("\\", "/"),
        "source_artifacts": sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in list(DATA.glob("block_*.parquet")) + [INDEX / "tree_instances_v3.parquet"]
        ),
    }
    (DATA / "table_manifest_v3.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"mandatory_tables": 16, "supplementary_tables": 1, "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
