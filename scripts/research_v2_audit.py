"""Fail-closed audit for the structure-preserving-reduction v2 deliverables."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "research_audit"

REQUIRED_FIGURES = [
    "fig01_canonical_pipeline",
    "fig02_ternary_composition_trees",
    "fig03_exact_reduction_diagram",
    "fig04_closure_leakage_geometry",
    "fig05_projector_recovery",
    "fig06_cp_rank_tradeoff",
    "fig07_spectral_gap_stability",
    "fig08_closure_convergence",
    "fig09_claim_evidence_dag",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "pages": 0, "sha256": None}
    try:
        from pypdf import PdfReader

        pages = len(PdfReader(str(path)).pages)
    except Exception as exc:  # pragma: no cover - depends on local PDF runtime
        command = shutil.which("pdfinfo")
        if command and command.lower().endswith(".cmd"):
            command_path = Path(command)
            candidate = command_path.parent.parent.parent / "native" / "poppler" / "Library" / "bin" / "pdfinfo.exe"
            if candidate.exists():
                command = str(candidate)
        if command:
            result = subprocess.run([command, str(path)], capture_output=True, text=True, check=False)
            match = re.search(r"^Pages:\s+(\d+)", result.stdout, flags=re.MULTILINE)
            if result.returncode == 0 and match:
                return {"exists": True, "pages": int(match.group(1)), "sha256": sha256(path), "reader": "pdfinfo"}
        return {"exists": True, "pages": None, "sha256": sha256(path), "reader_error": str(exc)}
    return {"exists": True, "pages": pages, "sha256": sha256(path)}


def numeric(rows: list[dict[str, str]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row[field]))
        except (KeyError, TypeError, ValueError):
            pass
    return values


def group_key(row: dict[str, str]) -> tuple[str, str]:
    experiment = row.get("experiment_id", "")
    if experiment == "V2_APPROX_CLOSURE_BOUND":
        return experiment, f"{row.get('tree_family')}|epsilon={row.get('epsilon_requested')}"
    if experiment == "V2_PROJECTOR_RECOVERY":
        return experiment, row.get("method", "")
    if experiment == "V2_CP_RANK_SWEEP":
        return experiment, f"rank={row.get('rank')}"
    return experiment, f"{row.get('control')}|gap={row.get('gap')}|relative={row.get('relative_perturbation')}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "artifacts" / "index" / "research_v2_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    run_rows = read_csv(ROOT / "artifacts" / "index" / "run_index_v2.csv")
    bound_rows = read_csv(ROOT / "artifacts" / "index" / "bound_tightness_v2.csv")
    summary_rows = read_csv(ROOT / "artifacts" / "index" / "research_v2_summary.csv")
    theorem_registry_path = ROOT / "claims" / "theorem_registry_v2.yaml"
    theorem_registry = yaml.safe_load(theorem_registry_path.read_text(encoding="utf-8")) if theorem_registry_path.exists() else {}
    claims = read_csv(ROOT / "claims" / "claim_evidence_matrix_v2.csv")
    dependencies = read_csv(ROOT / "claims" / "theorem_dependency_matrix_v2.csv")

    complete_rows = [row for row in run_rows if row.get("status") == "complete"]
    bound_failures = [
        row
        for row in bound_rows
        if row.get("status") == "complete"
        and float(row.get("observed_error", 0.0)) > float(row.get("theoretical_bound", 0.0)) + 1e-12
    ]
    tightness = numeric(bound_rows, "tightness_ratio")
    parity_rows = [row for row in run_rows if row.get("experiment_id") == "V2_CPU_GPU_PARITY"]
    parity_errors = numeric(parity_rows, "max_abs_error")
    grouped_seeds: dict[str, set[str]] = defaultdict(set)
    for row in run_rows:
        experiment, group = group_key(row)
        grouped_seeds[f"{experiment}|{group}"].add(row.get("seed", ""))
    principal_seed_groups = {
        key: len(seeds)
        for key, seeds in sorted(grouped_seeds.items())
        if not key.startswith("V2_SPECTRAL_GAP|no_gap|")
    }

    figure_info: dict[str, dict[str, Any]] = {}
    missing_figures: list[str] = []
    for figure in REQUIRED_FIGURES:
        pdf = ROOT / "papers" / "foundations_v2" / "figures" / f"{figure}.pdf"
        svg = ROOT / "papers" / "foundations_v2" / "figures" / f"{figure}.svg"
        figure_info[figure] = {
            "pdf": {"exists": pdf.exists(), "bytes": pdf.stat().st_size if pdf.exists() else 0, "sha256": sha256(pdf)},
            "svg": {"exists": svg.exists(), "bytes": svg.stat().st_size if svg.exists() else 0, "sha256": sha256(svg)},
        }
        if not pdf.exists() or not svg.exists():
            missing_figures.append(figure)

    pdfs = {
        "foundations_main": pdf_info(ROOT / "papers" / "foundations_v2" / "build" / "main.pdf"),
        "foundations_draft": pdf_info(ROOT / "papers" / "foundations_v2" / "build" / "draft_not_for_submission.pdf"),
        "software_companion": pdf_info(ROOT / "papers" / "software_v2" / "build" / "main.pdf"),
    }
    render_root = ROOT / "artifacts" / "pdf" / "research_v2_pages"
    rendered_png_count = len(list(render_root.glob("*.png"))) if render_root.exists() else 0

    foundations_source = ROOT / "papers" / "foundations_v2" / "main.tex"
    foundations_text = foundations_source.read_text(encoding="utf-8") if foundations_source.exists() else ""
    novelty_established = any(
        str(theorem.get("novelty_status", "")).upper() in {"ESTABLISHED_NEW_RESULT", "CLAIMED_NEW_RESULT"}
        for theorem in theorem_registry.get("theorems", [])
    )
    metadata_lower = foundations_text.lower()
    metadata_blocked = any(
        phrase in metadata_lower
        for phrase in ("metadata blocker", "not supplied in the repository", "metadata are absent")
    )
    metadata_verified = not metadata_blocked
    blockers: list[dict[str, str]] = []
    if not novelty_established:
        blockers.append(
            {
                "id": "V2-B-0001",
                "title": "Theorem-level novelty is not established",
                "evidence": "claims/theorem_registry_v2.yaml and papers/foundations_v2/RESEARCH_BLOCKED.md",
            }
        )
    if not metadata_verified:
        blockers.append(
            {
                "id": "V2-B-0002",
                "title": "Author email and ORCID remain unverified",
                "evidence": "papers/foundations_v2/main.tex front matter",
            }
        )
    checks = {
        "all_registered_runs_complete": bool(run_rows) and len(complete_rows) == len(run_rows),
        "five_seeds_for_principal_groups": bool(principal_seed_groups) and min(principal_seed_groups.values()) >= 5,
        "bound_rows_respect_bound": not bound_failures and len(bound_rows) == 60,
        "cpu_gpu_parity_rows_complete": len(parity_rows) == 5 and all(row.get("status_detail") == "complete" for row in parity_rows),
        "cpu_gpu_error_below_tolerance": bool(parity_errors) and max(parity_errors) <= 1e-12,
        "required_vector_figures_present": not missing_figures,
        "paper_pdfs_present": all(item["exists"] and (item.get("pages") or 0) > 0 for item in pdfs.values()),
        "rendered_pages_present": rendered_png_count >= 36,
        "claim_matrix_present": len(claims) >= 10,
        "dependency_matrix_present": len(dependencies) >= 7,
        "blocked_status_is_explicit": (ROOT / "papers" / "foundations_v2" / "RESEARCH_BLOCKED.md").exists(),
        "legacy_history_not_modified_by_runner": manifest.get("legacy_history_modified") is False,
    }
    strict_gate = all(checks.values()) and not blockers
    state = {
        "version": 2,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "v2 deliverable audit; legacy 0.1 artifacts are outside the v2 write set",
        "manifest": manifest,
        "checks": checks,
        "strict_gate": strict_gate,
        "blockers": blockers,
        "runs": {
            "total": len(run_rows),
            "complete": len(complete_rows),
            "failed": len(run_rows) - len(complete_rows),
            "unique_scientific_instances": manifest.get("unique_scientific_instances"),
            "principal_seed_groups": principal_seed_groups,
        },
        "bound_validation": {
            "rows": len(bound_rows),
            "failures": len(bound_failures),
            "max_tightness_ratio": max(tightness) if tightness else None,
        },
        "parity": {
            "rows": len(parity_rows),
            "max_abs_error": max(parity_errors) if parity_errors else None,
            "vram_recorded": all(int(float(row.get("vram_peak_bytes", 0) or 0)) > 0 for row in parity_rows),
        },
        "theorems": theorem_registry.get("theorems", []),
        "claims": claims,
        "dependency_matrix": dependencies,
        "figures": figure_info,
        "missing_figures": missing_figures,
        "pdfs": pdfs,
        "rendered_pages": {"root": str(render_root.relative_to(ROOT)), "png_count": rendered_png_count},
        "review_files": {
            str(path.relative_to(ROOT)): {"exists": path.exists(), "sha256": sha256(path)}
            for path in sorted((ROOT / "artifacts" / "reviews").glob("*.md"))
        },
    }
    (OUT / "v2_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    lines = [
        "# Research v2 audit",
        "",
        f"Generated: `{state['generated_utc']}`.",
        "",
        f"Strict gate: **{'PASS' if strict_gate else 'FAIL-CLOSED'}**.",
        "",
        "The v2 numerical and reproducibility checks are evaluated separately "
        "from the novelty gate. A complete run matrix does not turn standard "
        "consequences into a new theorem.",
        "",
        "## Checks",
        "",
    ]
    for name, value in checks.items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            f"- Runs: `{len(run_rows)}` total, `{len(complete_rows)}` complete, `{len(bound_failures)}` bound violations.",
            f"- Unique scientific instances: `{manifest.get('unique_scientific_instances')}`.",
            f"- Maximum bound tightness ratio: `{max(tightness) if tightness else 'n/a'}`.",
            f"- Maximum recorded CPU/GPU discrepancy: `{max(parity_errors) if parity_errors else 'n/a'}`.",
            f"- Vector figure pairs: `{len(REQUIRED_FIGURES) - len(missing_figures)}/{len(REQUIRED_FIGURES)}`.",
            f"- Rendered PNG pages/previews: `{rendered_png_count}`.",
            "",
            "## Scientific blockers",
            "",
        ]
    )
    for blocker in blockers:
        lines.append(f"- `{blocker['id']}` — **{blocker['title']}** ({blocker['evidence']}).")
    lines.extend(
        [
            "",
            "The foundations PDF is therefore a draft/not-for-submission artifact; "
            "the software companion is the appropriate reproducibility deliverable "
            "until a genuinely new theorem and verified author metadata are supplied.",
            "",
        ]
    )
    (OUT / "v2_state.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(OUT / "v2_state.json"), "strict_gate": strict_gate, "checks": checks}, indent=2))
    return 0 if strict_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
