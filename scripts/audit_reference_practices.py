"""Read-only audit of the five design-reference repositories.

The script only reads the reference paths and writes SEION-owned audit outputs.
It intentionally records adaptation and rejection decisions instead of copying
foreign project structure into the mathematical core.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "reference_audit"
DOC = ROOT / "docs" / "governance" / "reference_practice_review.md"

REFERENCES = {
    "ai-memory-orchestrator": Path(r"C:\Documents\ai-memory-orchestrator"),
    "ema-ai": Path(r"C:\Documents\Hyperghaps EMA\EMA-AI"),
    "aec-agentic": Path(r"C:\Documents\AEC_Agentic"),
    "bluebim-web": Path(r"C:\Documents\SFC\bluebim-web"),
    "pixelcity-smoke-test": Path(r"C:\Documents\ometeos\pixelcity_smoke_test"),
}

PRACTICES = [
    ("ai-memory-orchestrator", ".ai/manifest.yaml", "canonical Git-native memory", "The manifest names .ai as canonical and separates machine, packs, and runtime paths.", "prevents state loss and competing memory authorities", "implemented", "Python/stdlib", "adopt", ".ai/MEMORY_MANIFEST.yaml", "Already compatible with SEION; retain with mathematical authority levels."),
    ("ai-memory-orchestrator", ".ai/machine/graph.json", "graph neighborhood context", "Machine graph exports support bounded retrieval and task context.", "reduces context overload and stale handoffs", "implemented", "JSON graph", "adopt", "src/seion_core/canonical/context_compiler.py", "Use deterministic graph BFS and explain inclusion/exclusion."),
    ("ai-memory-orchestrator", "amo/io.py", "atomic file helpers", "Central IO helpers create parent directories and write UTF-8 JSON/text.", "reduces partial-write corruption", "implemented", "Python/stdlib", "adopt with strengthening", "src/seion_core/canonical/atomic.py", "Add locks, backups, optimistic hashes, and append-only events."),
    ("ai-memory-orchestrator", ".ai/evolution/", "evolution and retrieval metrics", "Optimization cycles and benchmark outputs are retained in .ai/evolution.", "makes context quality measurable", "implemented", "JSON/JSONL", "adopt", ".ai/evolution/", "Use repository health metrics without inventing a single health score."),
    ("ema-ai", ".ai/AGENT_POLICY_REGISTRY.yaml", "authority ladder", "Generative models propose; deterministic engines assign status; humans approve ambiguous changes.", "prevents AI self-approval", "implemented", "YAML policy", "adopt", "governance/AUTHORITY_LADDER.yaml", "Map formal proof and validated computation above empirical observations."),
    ("ema-ai", ".github/workflows/ci.yml", "multi-job CI", "Independent backend, frontend, governance, contracts, and memory-integrity jobs run with least permissions.", "isolates failure domains", "implemented", "GitHub Actions", "adopt", ".github/workflows/canonical-v4.yml", "Replace product-specific jobs with math, artifacts, docs, paper, package, and security jobs."),
    ("ema-ai", ".ai/KNOWN_BLOCKERS.md", "explicit blocker ledger", "Capability states and validation boundaries are recorded as implemented, pending, blocked, or stale.", "prevents release overclaims", "implemented", "Markdown", "adopt", ".ai/KNOWN_BLOCKERS.md", "Keep mathematical, software, data, and human-review blockers separate."),
    ("ema-ai", ".ai/MEMORY/RELEASE_STATE_LEDGER.md", "release candidate evidence", "Release artifacts carry exact source identity, hashes, and human gates.", "makes release decisions auditable", "implemented", "Markdown/YAML", "adopt", "artifacts/release_v4/", "Use separate paper, software, dataset, and extended-experiment decisions."),
    ("aec-agentic", "agents/, standard/, schemas/", "typed domain entities", "The control plane organizes typed agents, schemas, commands, and bounded contexts.", "prevents untyped cross-domain writes", "implemented", "Python/JSON Schema", "adopt", "src/seion_core/canonical/models.py", "Use dataclasses plus JSON-serializable records, no service mesh."),
    ("aec-agentic", "agents/ and audit trails", "append-only evidence and review decisions", "Candidate evidence is distinct from accepted evidence and review decisions are recorded.", "preserves epistemic provenance", "implemented", "JSONL events", "adopt", "claims/evidence_ledger.jsonl and .ai/evidence/", "Agents may propose; services append events; accepted authority is explicit."),
    ("aec-agentic", "apps/connectors/", "application-service boundaries", "Domain operations are routed through services rather than arbitrary direct mutations.", "centralizes validation and policy", "partial", "Python/TypeScript", "adopt narrowly", "src/seion_core/canonical/services.py", "Implement file-backed application services suitable for a research repository."),
    ("aec-agentic", "infra/ and docker-compose.yml", "distributed deployment infrastructure", "The reference includes cloud/database/service orchestration.", "supports product deployment", "implemented", "Docker/cloud", "reject", "none", "SEION is a finite mathematical repository; no PostgreSQL, Kubernetes, or microservices requirement exists."),
    ("bluebim-web", ".obsidian/ and .ai/", "human-readable graph mirror", "Obsidian graph views and markdown notes expose repository structure to humans.", "improves navigation and review", "implemented", "Obsidian/Markdown", "adopt as derived mirror", ".obsidian/seion-memory/", "Canonical authority remains structured Git data; managed markers preserve human text."),
    ("bluebim-web", ".claude/skills/", "managed generated sections", "Generated content is bounded by explicit markers and can be synchronized without overwriting human prose.", "prevents mirror drift and destructive regeneration", "partial", "Markdown scripts", "adopt", "scripts/build_obsidian_mirror.py", "Use SEION-GENERATED and BEGIN/END markers."),
    ("bluebim-web", "src/server/ and public/", "web application runtime", "The reference uses a frontend/server product architecture.", "serves interactive domain workflows", "implemented", "Node/React", "reject", "none", "A read-only static graph viewer is sufficient for SEION."),
    ("pixelcity-smoke-test", "pubspec.yaml and test/", "small smoke-test package", "The app keeps a narrow package manifest and a minimal test entrypoint.", "supports fast validation of a bounded slice", "implemented", "Flutter/Dart", "adopt conceptually", "scripts/run_fast.ps1 and tests/", "Use focused smoke tiers for certificates without importing Flutter tooling."),
    ("pixelcity-smoke-test", "android/, ios/, web/, windows/", "multi-platform application scaffold", "The reference carries platform-specific application targets.", "ships a user-facing app", "implemented", "Flutter platforms", "reject", "none", "External application/platform code is explicitly outside the mathematical core."),
]

REJECTED = [
    ("ema-ai", "PostgreSQL dashboard truth", "Product dashboard persistence is not needed for finite research evidence; JSONL and Parquet artifacts are canonical.", "no database dependency", "data/release evidence services"),
    ("aec-agentic", "Docker/Kubernetes microservices", "Distributed deployment would add operational surface without improving theorem or artifact authority.", "modular monolith", "src/seion_core/canonical"),
    ("bluebim-web", "frontend application shell", "SEION only needs a local read-only graph viewer, not a product UI or authenticated server.", "static HTML/JS viewer", "docs/graph"),
    ("pixelcity-smoke-test", "Flutter platform directories", "Mobile/desktop platform code is unrelated to finite-dimensional mathematics.", "Python/LaTeX/Actions", "none"),
    ("ai-memory-orchestrator", "embedding/vector retrieval as authority", "Semantic retrieval can assist context but cannot supersede exact registries or proofs.", "deterministic graph and path selection", "src/seion_core/canonical/context_compiler.py"),
]


def git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def inventory() -> list[dict[str, object]]:
    records = []
    for name, path in REFERENCES.items():
        files = [p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts]
        records.append(
            {
                "repository": name,
                "path": str(path),
                "exists": path.exists(),
                "git_head": git_head(path),
                "file_count": len(files),
                "top_level": sorted(p.name for p in path.iterdir())[:80] if path.exists() else [],
                "audited_read_only": True,
            }
        )
    return records


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog_fields = ["source_repository", "source_path", "practice_name", "exact_behavior", "problem_solved", "maturity", "dependencies", "applicability_to_seion", "adaptation_decision", "target_seion_component", "reason"]
    catalog = [dict(zip(catalog_fields, row)) for row in PRACTICES]
    write_csv(OUT / "practice_catalog.csv", catalog_fields, catalog)
    write_csv(OUT / "adaptation_matrix.csv", catalog_fields, [row for row in catalog if row["adaptation_decision"] != "reject"])
    rejected_fields = ["source_repository", "practice_name", "reason_rejected", "replacement_practice", "target_component"]
    write_csv(OUT / "rejected_practices.csv", rejected_fields, [dict(zip(rejected_fields, row)) for row in REJECTED])
    (OUT / "reference_repo_inventory.json").write_text(
        json.dumps({"schema_version": 1, "audited_utc": datetime.now(timezone.utc).isoformat(), "repositories": inventory(), "scope": "read-only; no reference repository mutation"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    DOC.parent.mkdir(parents=True, exist_ok=True)
    adopted = [row for row in catalog if row["adaptation_decision"].startswith("adopt")]
    rejected = [row for row in catalog if row["adaptation_decision"] == "reject"]
    DOC.write_text(
        "\n".join(
            [
                "# Reference-practice review",
                "",
                "This audit was executed read-only on the five user-designated reference repositories. No files, formatting, commits, or generated outputs were written there.",
                "",
                f"Audit timestamp: `{datetime.now(timezone.utc).isoformat()}`.",
                "",
                "## Canonical decision",
                "",
                "SEION adopts only practices that improve mathematical provenance, deterministic context recovery, reviewability, or release safety. It remains a Python modular monolith with file-backed evidence; product databases, cloud services, frontend stacks, and mobile platform scaffolds are rejected.",
                "",
                "## Adopted or narrowly adapted",
                "",
            ]
            + [f"- **{row['practice_name']}** from `{row['source_repository']}:{row['source_path']}` -> `{row['target_seion_component']}`: {row['reason']}" for row in adopted]
            + ["", "## Rejected or out of scope", ""]
            + [f"- **{row[1]}** from `{row[0]}`: {row[2]} Replacement: {row[3]}." for row in REJECTED]
            + ["", "## Evidence files", "", "- `artifacts/reference_audit/reference_repo_inventory.json`", "- `artifacts/reference_audit/practice_catalog.csv`", "- `artifacts/reference_audit/adaptation_matrix.csv`", "- `artifacts/reference_audit/rejected_practices.csv`", "", "The five reference repositories remain inspiration-only and are not dependencies."]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"repositories": len(REFERENCES), "practices": len(catalog), "rejected": len(REJECTED), "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
