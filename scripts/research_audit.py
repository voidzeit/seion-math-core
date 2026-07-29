"""Read-only forensic audit for the v2 structure-preserving-reduction track.

The audit reads canonical source and already-derived evidence. It writes only
new, derived files below ``artifacts/research_audit`` and never rewrites the
historical run index, claims, theorem registry, or legacy paper.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "research_audit"

ILLUSTRATIVE_FIGURES = {
    "closure_leakage_by_method",
    "cohomology_compatibility",
    "cp_rank_error",
    "multiscale_convergence",
    "precision_escalation",
    "quadrature_convergence",
}


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True
        )
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_blockers() -> list[dict[str, str]]:
    path = ROOT / ".ai" / "KNOWN_BLOCKERS.md"
    rows: list[dict[str, str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| B-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            rows.append(
                {
                    "id": cells[0],
                    "blocker": cells[1],
                    "impact": cells[2],
                    "evidence": cells[3],
                    "resolution_condition": cells[4],
                }
            )
    minimums = {
        "B-0001": "A reviewed theorem or a preserved counterexample must connect the central reduction statement to the implementation.",
        "B-0002": "Generate and use a v2 scientific-instance index with object and input hashes; retain history unchanged.",
        "B-0003": "Register multi-seed bound-tightness data with uncertainty, metrics, and theoretical upper bounds.",
        "B-0004": "Supply verified author email and ORCID or preserve an explicit metadata blocker.",
    }
    for row in rows:
        row["minimum_result"] = minimums.get(row["id"], "Resolve the blocker with traceable evidence.")
    return rows


def theorem_snapshot() -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    theorem_doc = load_yaml(ROOT / "claims" / "theorem_registry.yaml", {"theorems": []})
    claim_doc = load_yaml(ROOT / "claims" / "claims_registry.yaml", {"claims": []})
    theorems = theorem_doc.get("theorems", [])
    claims = claim_doc.get("claims", [])
    enriched: list[dict[str, Any]] = []
    for theorem in theorems:
        proof = theorem.get("proof_location")
        symbolic = theorem.get("symbolic_verification")
        enriched.append(
            {
                **theorem,
                "proof_exists": bool(proof and (ROOT / proof).exists()),
                "symbolic_exists": bool(symbolic and (ROOT / symbolic).exists()),
            }
        )
    counts = Counter(str(item.get("status", item.get("epistemic_status", "unknown"))) for item in claims)
    return enriched, dict(sorted(counts.items())), claims


def figure_snapshot() -> tuple[list[dict[str, str]], dict[str, int]]:
    rows = read_csv(ROOT / "artifacts" / "index" / "figure_provenance.csv")
    snapshot: list[dict[str, str]] = []
    counts = Counter()
    for row in rows:
        figure_id = row.get("figure_id", "")
        classification = "illustrative_or_diagnostic" if figure_id in ILLUSTRATIVE_FIGURES else "registered_generated"
        if classification == "illustrative_or_diagnostic":
            counts["illustrative_or_diagnostic"] += 1
        else:
            counts["registered_generated"] += 1
        snapshot.append({**row, "classification": classification})
    return snapshot, dict(sorted(counts.items()))


def run_snapshot() -> dict[str, Any]:
    report = load_json(ROOT / "artifacts" / "index" / "run_deduplication_report.json", {})
    rows = read_csv(ROOT / "artifacts" / "index" / "run_index_deduplicated.csv")
    by_experiment = Counter(row.get("experiment_id", "") for row in rows)
    return {
        **report,
        "deduplicated_rows": len(rows),
        "unique_experiments": sorted(by_experiment),
        "unique_rows_by_experiment": dict(sorted(by_experiment.items())),
        "scientific_identity_note": "The legacy deduplicator identity is experiment, resolved-config fingerprint, seed, precision, backend, and device; v2 must add source commit, implementation version, object hash, and input artifact hash.",
    }


def build_dependency_graph(theorems: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []
    for claim in claims:
        identifier = str(claim.get("id", ""))
        nodes.append({"id": identifier, "kind": "claim", "status": str(claim.get("status", "unknown"))})
        for evidence in claim.get("evidence", []) or claim.get("proof", []) or []:
            if isinstance(evidence, str):
                evidence_id = f"evidence:{evidence}"
                nodes.append({"id": evidence_id, "kind": "evidence", "status": "registered"})
                edges.append({"source": identifier, "target": evidence_id, "relation": "supported_by"})
    for theorem in theorems:
        identifier = str(theorem.get("id", ""))
        nodes.append({"id": identifier, "kind": "theorem", "status": str(theorem.get("epistemic_status", "unknown"))})
        for dependency in theorem.get("dependencies", []) or []:
            edges.append({"source": identifier, "target": str(dependency), "relation": "depends_on"})
        for key, relation in (("proof_location", "proved_by"), ("symbolic_verification", "checked_by")):
            value = theorem.get(key)
            if value:
                target = f"artifact:{value}"
                nodes.append({"id": target, "kind": "artifact", "status": "present" if (ROOT / value).exists() else "missing"})
                edges.append({"source": identifier, "target": target, "relation": relation})
    unique_nodes = {node["id"]: node for node in nodes if node["id"]}
    unique_edges = {json.dumps(edge, sort_keys=True): edge for edge in edges}
    return {"version": 2, "nodes": list(unique_nodes.values()), "edges": list(unique_edges.values())}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    theorems, claim_statuses, claims = theorem_snapshot()
    figures, figure_counts = figure_snapshot()
    blockers = parse_blockers()
    runs = run_snapshot()
    quality = load_json(ROOT / "paper" / "quality" / "paper_quality_report.json", {})
    quality_scores = {item.get("id"): item.get("score") for item in quality.get("dimensions", [])}
    main_tex = ROOT / "paper" / "main.tex"
    legacy_section_files = sorted((ROOT / "paper" / "sections").glob("*.tex"))
    section_count = sum(
        len(re.findall(r"^\\section(?:\*)?\{", path.read_text(encoding="utf-8"), flags=re.MULTILINE))
        for path in legacy_section_files
    )
    if main_tex.exists():
        section_count += len(re.findall(r"^\\section(?:\*)?\{", main_tex.read_text(encoding="utf-8"), flags=re.MULTILINE))
    pdf_path = ROOT / "paper" / "build" / "main.pdf"
    current = {
        "version": 2,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git": {"branch": git("branch", "--show-current"), "commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))},
        "scope": "read-only forensic snapshot; legacy 0.1 artifacts preserved",
        "paths": {
            "source_modules": {"path": "src/seion_core", "exists": (ROOT / "src" / "seion_core").exists()},
            "theorem_docs": {"path": "docs/theorems", "count": len(list((ROOT / "docs" / "theorems").glob("*.md")))},
            "counterexample_docs": {"path": "docs/counterexamples", "count": len(list((ROOT / "docs" / "counterexamples").glob("*.md")))},
            "v2_foundations": {"path": "papers/foundations_v2", "exists": (ROOT / "papers" / "foundations_v2").exists()},
            "v2_software": {"path": "papers/software_v2", "exists": (ROOT / "papers" / "software_v2").exists()},
        },
        "formal_results": {"theorems": theorems, "claim_status_counts": claim_statuses},
        "conjectures": load_yaml(ROOT / "claims" / "conjecture_registry.yaml", {"conjectures": []}).get("conjectures", []),
        "counterexamples": load_yaml(ROOT / "claims" / "counterexample_registry.yaml", {"counterexamples": []}).get("counterexamples", []),
        "runs": runs,
        "figures": {"rows": figures, "counts": figure_counts},
        "paper": {
            "legacy_source": "paper/main.tex",
            "section_count": section_count,
            "pdf_exists": pdf_path.exists(),
            "pdf_sha256": sha256(pdf_path),
            "quality_scores": quality_scores,
            "release_ready_under_critical_gate": quality.get("release_ready_under_critical_gate", False),
        },
        "v2": {
            "foundations_source_exists": (ROOT / "papers" / "foundations_v2" / "main.tex").exists(),
            "software_source_exists": (ROOT / "papers" / "software_v2" / "main.tex").exists(),
            "theorem_registry_exists": (ROOT / "claims" / "theorem_registry_v2.yaml").exists(),
            "run_manifest_exists": (ROOT / "artifacts" / "index" / "research_v2_manifest.json").exists(),
        },
        "blockers": blockers,
        "audit_questions": {
            "proved_statements": [item["id"] for item in theorems if str(item.get("epistemic_status", "")).startswith("PROVED")],
            "standard_or_auxiliary": ["THM_STANDARD_CURVATURE_ASSOCIATOR_DIFFERENCE_V1", "THM_COHOMOLOGY_DESCENT_FINITE_V1"],
            "conjectural_or_open": [item.get("id") for item in load_yaml(ROOT / "claims" / "conjecture_registry.yaml", {"conjectures": []}).get("conjectures", [])],
            "illustrative_figures": sorted(figure_id for figure_id in ILLUSTRATIVE_FIGURES if any(row.get("figure_id") == figure_id for row in figures)),
            "minimum_missing_bridge": "A proved exact-reduction statement plus an independently tested explicit approximate-closure recurrence and assumption-removal counterexamples.",
        },
    }
    (OUT / "current_state.json").write_text(json.dumps(current, indent=2), encoding="utf-8")

    lines = [
        "# Research v2 forensic current state",
        "",
        f"Generated: `{current['generated_utc']}` on branch `{current['git']['branch']}` at `{current['git']['commit']}`; dirty worktree: `{current['git']['dirty']}`.",
        "",
        "This is a derived read-only audit. It does not overwrite the legacy paper, claims, theorem registry, or historical runs.",
        "",
        "## Formal status",
        "",
    ]
    for theorem in theorems:
        lines.append(f"- `{theorem.get('id')}`: **{theorem.get('epistemic_status')}**; proof exists={theorem.get('proof_exists')}; symbolic artifact exists={theorem.get('symbolic_exists')}.")
    lines.extend([
        "",
        "The current formal results are finite curvature/associator expansion and finite cohomology descent. Both are useful supporting results, but neither is the central reduction theorem requested for a strong mathematical paper.",
        "",
        "## Evidence status",
        "",
        f"- Historical runs: `{runs.get('historical_run_count', 'unknown')}`; unique scientific instances: `{runs.get('unique_scientific_instance_count', 'unknown')}`.",
        f"- Duplicate groups: `{runs.get('duplicate_group_count', 'unknown')}`; duplicate records: `{runs.get('duplicate_record_count', 'unknown')}`.",
        f"- Figures classified as registered generated: `{figure_counts.get('registered_generated', 0)}`; illustrative/diagnostic: `{figure_counts.get('illustrative_or_diagnostic', 0)}`.",
        f"- Legacy paper sections: `{section_count}`; quality release flag: `{quality.get('release_ready_under_critical_gate', False)}`.",
        "",
        "## Minimum bridge",
        "",
        "The smallest result that changes the scientific status is an exact typed reduction theorem with a complete tree induction, followed by a separately audited approximate-closure recurrence and counterexamples when invariance or the spectral gap is removed.",
        "",
        "## v2 status",
        "",
        "The v2 foundations and software tracks are maintained as separate outputs; this legacy audit remains fail-closed for the 0.1 release path.",
    ])
    (OUT / "current_state.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    write_csv(OUT / "blocker_matrix.csv", blockers, ["id", "blocker", "impact", "evidence", "resolution_condition", "minimum_result"])
    graph = build_dependency_graph(theorems, claims)
    (OUT / "claim_dependency_graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")

    run_rows = []
    for row in read_csv(ROOT / "artifacts" / "index" / "run_index_deduplicated.csv"):
        run_rows.append(
            {
                "experiment_id": row.get("experiment_id", ""),
                "representative_run_id": row.get("run_id", ""),
                "status": row.get("status", ""),
                "seed": row.get("seed", ""),
                "precision": row.get("precision", ""),
                "backend": row.get("backend", ""),
                "device": row.get("device", ""),
                "duplicate_count": row.get("duplicate_count", ""),
                "scientific_identity": "experiment/config/seed/precision/backend/device",
            }
        )
    write_csv(OUT / "run_deduplication_report.csv", run_rows, list(run_rows[0]) if run_rows else ["experiment_id"])

    gap_lines = [
        "# Legacy paper gap analysis",
        "",
        f"The legacy source `paper/main.tex` contains **{section_count}** sections and compiles to `{pdf_path}` with SHA-256 `{sha256(pdf_path) or 'missing'}`.",
        "",
        "## Confirmed strengths",
        "",
        "- Typed finite-dimensional laws and explicit convention names.",
        "- Two finite supporting proofs with local evidence.",
        "- Reproducibility and epistemic-status infrastructure.",
        "- Historical run preservation with a derived deduplicated view.",
        "",
        "## Research gaps",
        "",
        "- No integrated central exact-reduction theorem in the legacy registry.",
        "- No independently registered approximate-closure tightness matrix.",
        "- Current figure provenance uses wildcard run sources and several figures are illustrative or diagnostic.",
        "- Current scientific identity does not yet include source commit, implementation version, mathematical-object hash, and input-artifact hash.",
        "- No adversarial pure-math and numerical-review pair exists for v2.",
        "",
        "The legacy paper must not be relabeled as submission-ready. The v2 track must either establish a genuinely useful theorem or produce `RESEARCH_BLOCKED.md` with a precise counterexample and preserve the valid supporting results.",
    ]
    (OUT / "paper_gap_analysis.md").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "theorems": len(theorems), "claims": len(claims), "blockers": len(blockers), "figures": len(figures)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
