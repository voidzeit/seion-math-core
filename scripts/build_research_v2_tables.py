"""Render compact scientific tables from registered v2 CSV artifacts."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers" / "foundations_v2" / "tables"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write(path: Path, text: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tex(value: object) -> str:
    return str(value).replace("_", r"\_").replace("%", r"\%")


def fmt(value: float, digits: int = 3) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000 or abs(value) < 1e-3:
        return f"{value:.2e}"
    return f"{value:.{digits}f}"


def aggregate(rows: list[dict[str, str]], key: str, metric: str) -> list[tuple[str, float, float, int]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row[key]].append(float(row[metric]))
    output = []
    for group, values in sorted(groups.items(), key=lambda item: str(item[0])):
        array = np.asarray(values, dtype=float)
        output.append((group, float(np.mean(array)), float(np.std(array, ddof=1)) if len(array) > 1 else 0.0, len(array)))
    return output


def table_projector() -> None:
    rows = read_csv(ROOT / "artifacts" / "index" / "projector_recovery_v2.csv")
    leakage = {group: (mean, std, n) for group, mean, std, n in aggregate(rows, "method", "closure_leakage")}
    angle = {group: (mean, std, n) for group, mean, std, n in aggregate(rows, "method", "principal_angle_radians")}
    order = ["known_invariant", "random", "pca", "svd", "spectral", "closure_minimizing"]
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"method & leakage mean & leakage sd & angle mean (rad) \\",
        r"\midrule",
    ]
    for method in order:
        lmean, lstd, n = leakage[method]
        amean = angle[method][0]
        lines.append(f"{tex(method)} & {fmt(lmean)} & {fmt(lstd)} & {fmt(amean)} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write(OUT / "projector_recovery.tex", "\n".join(lines))


def table_bounds() -> None:
    rows = read_csv(ROOT / "artifacts" / "index" / "bound_tightness_v2.csv")
    groups = defaultdict(list)
    for row in rows:
        groups[(row["tree_family"], row["epsilon_requested"])].append(float(row["tightness_ratio"]))
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"tree family & $\rho$ & tightness mean & seeds \\",
        r"\midrule",
    ]
    for (family, epsilon), values in sorted(groups.items()):
        array = np.asarray(values)
        lines.append(f"{tex(family)} & {tex(epsilon)} & {fmt(float(np.mean(array)))} & {len(values)} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write(OUT / "bound_tightness.tex", "\n".join(lines))


def table_cp() -> None:
    rows = [row for row in read_csv(ROOT / "artifacts" / "index" / "cp_rank_sweep_v2.csv") if int(float(row["rank"])) > 0]
    error = {group: (mean, std, n) for group, mean, std, n in aggregate(rows, "rank", "relative_frobenius_error")}
    runtime = {group: mean for group, mean, _, _ in aggregate(rows, "rank", "runtime_seconds")}
    lines = [
        r"\begin{tabular}{rrrr}",
        r"\toprule",
        r"rank & relative error mean & relative error sd & runtime (s) \\",
        r"\midrule",
    ]
    for rank in sorted(error, key=int):
        mean, std, _ = error[rank]
        lines.append(f"{rank} & {fmt(mean)} & {fmt(std)} & {fmt(runtime[rank])} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write(OUT / "cp_rank_tradeoff.tex", "\n".join(lines))


def table_spectral() -> None:
    rows = [row for row in read_csv(ROOT / "artifacts" / "index" / "spectral_gap_v2.csv") if row["control"] == "positive_gap"]
    groups = defaultdict(list)
    for row in rows:
        groups[(row["gap"], row["relative_perturbation"])].append(float(row["snapped_projector_distance"]))
    lines = [
        r"\begin{tabular}{rrrr}",
        r"\toprule",
        r"$\gamma$ & $\lVert E\rVert/\gamma$ & distance mean & seeds \\",
        r"\midrule",
    ]
    for (gap, relative), values in sorted(groups.items(), key=lambda item: (float(item[0][0]), float(item[0][1]))):
        lines.append(f"{tex(gap)} & {tex(relative)} & {fmt(float(np.mean(values)))} & {len(values)} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    write(OUT / "spectral_gap.tex", "\n".join(lines))


def table_manifest() -> None:
    manifest = (ROOT / "artifacts" / "index" / "research_v2_manifest.json").read_text(encoding="utf-8")
    import json

    data = json.loads(manifest)
    lines = [
        r"\begin{tabular}{lr}",
        r"\toprule",
        r"field & value \\",
        r"\midrule",
        f"implementation & {tex(data['implementation_version'])} \\\\",
        f"total runs & {data['total_runs']} \\\\",
        f"complete runs & {data['complete_runs']} \\\\",
        f"unique instances & {data['unique_scientific_instances']} \\\\",
        f"seeds per principal family & {data['required_seed_count']} \\\\",
        f"legacy history modified & {tex(data['legacy_history_modified'])} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
    ]
    write(OUT / "manifest.tex", "\n".join(lines))


def main() -> int:
    table_projector()
    table_bounds()
    table_cp()
    table_spectral()
    table_manifest()
    print(f"generated tables in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
