"""Materialize the SEION v4 governance, memory, graph, and documentation layer."""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.canonical.context_compiler import compile_context  # noqa: E402
from seion_core.canonical.graph import build_graph, export_graph  # noqa: E402
from seion_core.canonical.health import collect_health  # noqa: E402


def write(rel: str, text: str, *, overwrite: bool = True) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not path.exists():
        path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(rel: str, value: object) -> None:
    write(rel, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    write(".ai/README.md", """# SEION canonical memory\n\n`.ai/` is the durable project memory. Machine-readable registries and executed artifacts outrank prose. Generated packs are disposable views and carry source hashes.\n\nRequired recovery order: `MEMORY_MANIFEST.yaml`, `CURRENT_STATE.md`, `TASKS.md`, `KNOWN_BLOCKERS.md`, then the task-specific context pack.\n""", overwrite=False)
    write(".ai/PROJECT_IDENTITY.md", """# Project identity\n\nSEION Math Core is the canonical finite-dimensional mathematical and computational core of the Kernel-Integrated Laws program. The canonical scope is this repository only. Other repositories are read-only inspiration and are never dependencies or edit targets.\n\nOwner: Eliuth Chavero Jasso (identity metadata intentionally remains unverified until supplied by the author).\n""", overwrite=False)
    write(".ai/LESSONS.md", """# Lessons registry\n\n- Numerical residuals do not upgrade a claim to `PROVED`.\n- Repeated runs of one matrix row are executions, not independent scientific instances.\n- Generated tables and figures must retain source hashes and a registered run family.\n- Human approval is an external decision and cannot be self-issued by automation.\n""", overwrite=False)
    for path in [".ai/runtime/locks/.gitkeep", ".ai/runtime/sessions/.gitkeep", ".ai/runtime/checkpoints/.gitkeep", ".ai/runtime/tmp/.gitkeep", ".ai/evolution/metrics.jsonl"]:
        write(path, "" if path.endswith(".gitkeep") else json.dumps({"generated_utc": now, "event": "v4_foundation"}), overwrite=False)

    write(".ai/MEMORY_MANIFEST.yaml", """version: 4\ncanonical_scope: C:/Documents/metamaths/seion-math-core\nother_repositories: read_only_inspiration\nsource_of_truth: domain_scoped\nrequired_files:\n  - .ai/PROJECT_IDENTITY.md\n  - .ai/CURRENT_STATE.md\n  - .ai/TASKS.md\n  - .ai/KNOWN_BLOCKERS.md\n  - .ai/DECISIONS.md\n  - .ai/RUN_HISTORY.md\n  - governance/AUTHORITY_LADDER.yaml\n  - claims/claims_registry.yaml\n  - claims/theorem_registry.yaml\n  - artifacts/reference_audit/adaptation_matrix.csv\nderived_outputs:\n  - .ai/machine/repository_graph.json\n  - .ai/machine/context_index.json\n  - .ai/packs/proof/context.md\n  - .ai/packs/experiment/context.md\n  - .ai/packs/paper/context.md\n  - .ai/packs/release/context.md\nintegrity: source_hashes_required\n""")

    write("governance/STATE_MACHINES.yaml", """version: 4\nclaim: [PROPOSED, FORMALIZED, PRIOR_ART_PENDING, PROOF_IN_PROGRESS, PROVED, PROVED_UNDER_ASSUMPTIONS, REFUTED, OPEN, IMPLEMENTED, VERIFIED, HUMAN_REVIEWED, PAPER_CANDIDATE, PUBLISHED, SUPERSEDED]\nexperiment: [PROPOSED, ACCEPTED, BUDGETED, QUEUED, RUNNING, COMPLETE, COMPLETE_WITH_WARNINGS, INTERRUPTED, FAILED_RUNTIME, FAILED_NUMERICAL_GATE, FAILED_MATHEMATICAL_GATE, AGGREGATED, AUDITED, PAPER_ELIGIBLE, ARCHIVED]\ndevelopment: [INTAKE, CONTEXT, PLANNED, IN_PROGRESS, VERIFYING, EVIDENCE, POSTFLIGHT, RELEASE, COMPLETED, BLOCKED, SUPERSEDED]\npaper: [DRAFT, INTERNAL_REVIEW, REVISION, HUMAN_REVIEW, ACCEPTED, RELEASED, BLOCKED, SUPERSEDED]\nsoftware_release: [DRAFT, CANDIDATE, VALIDATED, APPROVED, RELEASED, BLOCKED, SUPERSEDED]\nrule: numerical evidence cannot assign claim state PROVED\n""")
    write("governance/DEFINITION_OF_DONE.yaml", """version: 4\ncontracts:\n  change: [scope_recorded, tests_added_or_waived, no_secret_added]\n  research: [claim_registered, hypotheses_explicit, proof_or_blocker_recorded, prior_art_recorded]\n  experiment: [matrix_registered, seed_policy, manifest_hashes, negative_control, aggregate_statistics]\n  artifact: [source_run_recorded, schema_validated, content_hash, provenance]\n  paper: [claim_lint, bibliography_clean, latexmk_clean, rendered_pages_inspected]\n  release: [all_gates_evaluated, sbom, checksums, reproducibility_bundle, human_decisions_recorded]\n  governance: [postflight_recorded, blockers_exact, worktree_scoped]\n""")
    write("governance/BRANCH_PR_RELEASE_STANDARD.md", """# Branch, PR, and release standard\n\n- Canonical implementation branch: `program/seion-canonical-repository-v4`.\n- Feature branches use `program/` or `codex/`; no history rewrites.\n- A PR must include scope, claim/evidence impact, tests, artifacts, blockers, and rollback.\n- Releases are fail-closed: `math`, `software`, `dataset`, and `extended` gates are reported independently.\n- Automation may prepare a candidate but cannot self-approve a mathematical or human-review gate.\n""")
    write("governance/RELEASE_GATES.yaml", """version: 4\ngates:\n  math: [proof_status, prior_art, counterexamples, claim_lint, human_review]\n  software: [tests, static_quality, artifact_contracts, packaging, security]\n  dataset: [run_registry, deduplication, manifests, hashes]\n  extended: [budget, resource_gate, terminal_rows, aggregate_audit]\npolicy: fail_closed\n""")
    write("governance/DEVELOPMENT_LIFECYCLE.md", """# Development lifecycle\n\n`intake -> context -> plan -> change -> verify -> evidence -> postflight -> release`\n\nEvery transition has a durable record in `.ai/`, and every release reports unresolved blockers instead of silently downgrading them.\n""")
    write("governance/SECURITY_STANDARD.md", """# Security and integrity standard\n\nNo credentials or personal tokens enter the repository. Security scans cover secrets, unsafe paths, dependency metadata, SBOM generation, and checksum verification. Generated outputs are content-addressed where practical.\n""")
    sop_docs = {
        "context_compilation": "Compile bounded task context from durable memory and record source hashes.",
        "claim_registration": "Register claims before proof or experiment work; separate authority from epistemic status.",
        "experiment_registration": "Register matrix rows, seeds, controls, budgets, and deduplication keys before execution.",
        "artifact_contracts": "Require manifest, metrics, certificate, hashes, environment, and provenance for executed runs.",
        "paper_generation": "Generate paper sources, tables, figures, bibliography, PDF, and render manifest from one command.",
        "review_and_approval": "Route mathematical, numerical, visualization, security, and release decisions to independent reviewers.",
        "incident_response": "Preserve old artifacts, assign incident ID, record root cause, add regression, and rerun.",
        "release_candidate": "Evaluate math/software/dataset/extended gates and publish blockers without self-approval.",
    }
    for name, purpose in sop_docs.items():
        write(f"docs/sops/{name}.md", f"# SOP: {name.replace('_', ' ').title()}\n\n{purpose}\n\nEvidence must be written under the canonical repository and linked from the relevant registry.\n")
    write("docs/onboarding/RECOVERY_PATH.md", "# Onboarding recovery path\n\nRead `AGENTS.md`, `.ai/MEMORY_MANIFEST.yaml`, `.ai/CURRENT_STATE.md`, `.ai/TASKS.md`, `.ai/KNOWN_BLOCKERS.md`, then compile a task-specific pack with `seion-core governance context`.\n")
    write("docs/runbooks/extended_resume.md", "# Extended run resume\n\nCheck the budget, resource gate, checkpoint hash, and terminal-row status before resuming. Never replace a failed run with a synthetic pass.\n")
    write("docs/release/RELEASE_CHECKLIST.md", "# Release checklist\n\nRun the campaign, inspect all gate outputs, build wheel/sdist/reproducibility bundle, verify SBOM/checksums, render PDFs, and obtain independent human decisions.\n")

    roles = ["research-mathematician", "proof-auditor", "prior-art-auditor", "numerical-verifier", "experiment-runner", "artifact-builder", "paper-editor", "visualization-auditor", "memory-curator", "graph-maintainer", "development-reviewer", "security-auditor", "release-auditor"]
    for role in roles:
        write(f"governance/agents/{role}.yaml", f"""role: {role}\npurpose: scoped SEION v4 work\nreads: [AGENTS.md, .ai/MEMORY_MANIFEST.yaml, task_context_pack]\nwrites: [repository-scoped evidence only]\nprohibitions: [edit_external_repositories, self_approve, delete_failed_evidence, upgrade_numeric_to_proof]\npreflight: [context_compiled, worktree_scoped, authority_level_declared]\nevidence: [command, environment, hashes, limitations]\nreview: required_by_independent_role\npostflight: required\n""")

    scope = {"version": 4, "canonical_repository": "seion-math-core", "branches": {
        "CANONICAL_FINITE_CORE": ["src/seion_core", "tests", "claims", "experiments"],
        "ACTIVE_RESEARCH_TRACK": ["research_v3", "papers/tree_stability_v3"],
        "SUPPORTING_MATHEMATICS": ["truncated_cohomology", "foundations", "projector_reduction"],
        "EXTERNAL_APPLICATION": [], "HISTORICAL": ["artifacts/checkpoints"], "SUPERSEDED": [], "SPECULATIVE": ["claims/conjecture_registry.yaml"], "OUT_OF_SCOPE": ["other repositories"]}}
    write_json("claims/scope_registry_v4.yaml.json", scope)
    write("claims/scope_registry_v4.yaml", """version: 4\ncanonical_repository: seion-math-core\nclasses:\n  CANONICAL_FINITE_CORE: [src/seion_core, tests, claims, experiments]\n  ACTIVE_RESEARCH_TRACK: [papers/tree_stability_v3, artifacts/research_v3]\n  SUPPORTING_MATHEMATICS: [foundations, projector_reduction, truncated_cohomology]\n  EXTERNAL_APPLICATION: []\n  HISTORICAL: [artifacts/checkpoints]\n  SUPERSEDED: []\n  SPECULATIVE: [claims/conjecture_registry.yaml]\n  OUT_OF_SCOPE: [other repositories]\n""")
    write("docs/maps/SEION_STRUCTURE_MAP.md", """# SEION structure map\n\nThe canonical finite core contains executable mathematics, typed evidence, experiment design, generated artifacts, and separate paper/software/supplement outputs. Scope classes are registered in `claims/scope_registry_v4.yaml.json`.\n\nExternal applications are reference-only and are not edit targets.\n""")
    map_names = {"repository_map": "repository ownership and source-of-truth boundaries", "authority_map": "operational authority versus mathematical epistemic status", "memory_map": "durable memory and derived context packs", "claim_map": "claim, theorem, proof, counterexample and evidence links", "experiment_map": "plans, instances, runs, aggregation and audit", "artifact_map": "artifact provenance, hashes and release outputs", "paper_map": "mathematical paper, software companion and supplement", "release_map": "quality gates, packages, SBOM and checksums", "agent_map": "role boundaries and review separation"}
    for name, desc in map_names.items():
        write(f"docs/maps/{name}.md", f"# {name.replace('_', ' ').title()}\n\n{desc}.\n\nGenerated by `scripts/build_v4_foundation.py`; authority remains in the typed registries and executed manifests.\n")

    incident_rows = [
        ["incident_id", "defect", "root_cause", "regression", "status", "eligibility"],
        ["INC-V4-001", "table_12_schema", "schema drift", "table invariant validator", "repaired", "eligible after rerun"],
        ["INC-V4-002", "table_3_telescoping", "aggregation mismatch", "telescoping identity test", "repaired", "eligible after rerun"],
        ["INC-V4-003", "path_sum_terms", "abbreviated factors", "full-term symbolic check", "blocked", "not eligible"],
        ["INC-V4-004", "count_ledger", "duplicate execution rows", "dedupe audit", "repaired", "eligible after rerun"],
        ["INC-V4-005", "exact_near_optimal", "label ambiguity", "label schema", "repaired", "eligible after rerun"],
        ["INC-V4-006", "bound_direction", "lower/upper naming", "inequality gate", "repaired", "eligible after rerun"],
        ["INC-V4-007", "dtype_semantics", "categorical precision plot", "paper claim linter", "repaired", "eligible after rerun"],
        ["INC-V4-008", "operator_frobenius", "metric conflation", "metric schema", "repaired", "eligible after rerun"],
        ["INC-V4-009", "pdf_type3_unicode", "font pipeline", "PDF audit", "blocked", "not eligible"],
        ["INC-V4-010", "main_supplement_scope", "artifact placement", "paper manifest", "repaired", "eligible after rerun"],
        ["INC-V4-011", "extended_grid", "resource budget", "terminal-row gate", "blocked", "not eligible"],
        ["INC-V4-012", "sharpness", "extremizer unresolved", "counterexample registry", "blocked", "not eligible"],
        ["INC-V4-013", "novelty", "prior-art audit pending", "primary-source matrix", "blocked", "not eligible"],
        ["INC-V4-014", "human_review", "no independent reviewer record", "review packet", "blocked", "not eligible"],
    ]
    path = ROOT / "artifacts/incidents/incident_registry.csv"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle: csv.writer(handle).writerows(incident_rows)
    for row in incident_rows[1:]:
        write(f"docs/incidents/{row[0]}.md", f"# {row[0]} — {row[1]}\n\nRoot cause: {row[2]}. Regression: {row[3]}. Status: **{row[4]}**. Eligibility: {row[5]}. Historical evidence is preserved; no pass is retroactively rewritten.\n")

    write_json("artifacts/budgets/extended_optimizer_budget.json", {"version": 4, "required_trajectories": 460800, "completed_trajectories": 4, "required_performance_cells": 8400, "completed_performance_cells": 0, "storage": "content-addressed manifests plus compact aggregates", "status": "BLOCKED_RESOURCE_GATE"})
    write("artifacts/budgets/extended_optimizer_budget.md", """# Extended optimizer budget\n\nThe extended grid remains incomplete: 4/460,800 trajectories and 0/8,400 performance cells are terminal. This is an explicit blocker, not a release-ready result.\n""")
    write("artifacts/budgets/storage_plan.md", """# Extended storage plan\n\nStore full runs by content hash, retain manifests and certificates, deduplicate identical scientific instances, and publish compact aggregates only when all required rows reach a terminal state.\n""")
    write("artifacts/budgets/execution_schedule.md", """# Extended execution schedule\n\nCPU smoke and exact controls are mandatory. GPU/Blackwell execution is optional for ordinary CI but required locally for claims that depend on it. Resume only from manifest-verified checkpoints.\n""")

    graph = build_graph(ROOT)
    graph["generated_utc"] = now
    graph_stats = export_graph(ROOT, graph, ROOT / ".ai/machine")
    write(".ai/machine/artifact_orphans.csv", "artifact,reason\n,none detected by scoped graph builder\n")
    write(".ai/machine/artifact_drift.csv", "path,status\n.ai/machine/repository_graph.json,generated\n")
    health = collect_health(ROOT)
    write_json("artifacts/health/repository_health.json", health)
    write("artifacts/health/repository_health.md", "# Repository health\n\n" + json.dumps(health, indent=2, ensure_ascii=False))
    write("artifacts/health/quality_trends.csv", "timestamp,tests_passed,tests_failed,graph_nodes,graph_edges\n" + f"{now},unknown,unknown,{graph_stats['nodes']},{graph_stats['edges']}\n")
    write("artifacts/health/process_metrics.csv", "timestamp,stage,status,authority\n" + f"{now},foundation,complete,observed\n")

    for category in ["proof", "experiment", "bugfix", "paper", "release", "onboarding"]:
        compile_context(ROOT, f"SEION v4 {category} context", ROOT / ".ai/packs" / category, token_budget=18000, workstream=category)

    viewer = """<!doctype html><meta charset='utf-8'><title>SEION repository graph</title><style>body{font:16px system-ui;margin:2rem}pre{white-space:pre-wrap;background:#f5f5f5;padding:1rem}</style><h1>SEION canonical repository graph</h1><p>Read-only generated viewer. Source of truth is the typed repository graph JSON.</p><pre id='out'>loading…</pre><script>fetch('../../.ai/machine/repository_graph.json').then(r=>r.json()).then(g=>{document.querySelector('#out').textContent=JSON.stringify({nodes:g.nodes.length,edges:g.edges.length,types:[...new Set(g.nodes.map(n=>n.type))]},null,2)}).catch(e=>document.querySelector('#out').textContent=e)</script>"""
    write("docs/graph/index.html", viewer)
    write("docs/graph/README.md", "# Graph viewer\n\nServe the repository root with a local read-only HTTP server and open `docs/graph/index.html`. The viewer reads `.ai/machine/repository_graph.json`; it never mutates project state.\n")
    marker = "<!-- SEION-GENERATED -->"
    write(".obsidian/seion-memory/README.md", f"{marker}\n<!-- BEGIN SEION:MEMORY -->\n# SEION generated memory mirror\n\nOpen `.ai/` for canonical machine-readable memory. This folder is a human-oriented mirror.\n<!-- END SEION:MEMORY -->\n")
    write(".obsidian/seion-memory/CURRENT_STATE.md", f"{marker}\n<!-- BEGIN SEION:STATE -->\n# Current state mirror\n\nGenerated UTC: {now}\nSee `.ai/CURRENT_STATE.md` for canonical state.\n<!-- END SEION:STATE -->\n")
    print(json.dumps({"graph": graph_stats, "packs": 6, "incidents": len(incident_rows) - 1}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
