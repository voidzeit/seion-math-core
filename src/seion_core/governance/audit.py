"""Structural, epistemic, provenance, and paper-integrity audit for SEION."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..certification.claims import ALLOWED_CLAIM_STATUSES, load_yaml_registry
from .events import append_event
from .language import lint_paper_language
from .models import GovernanceIssue
from .runs import audit_run_artifacts, deduplicate_runs


REQUIRED_FILES = (
    "AGENTS.md",
    ".ai/MEMORY_MANIFEST.yaml",
    ".ai/PROJECT_REFERENCE_MANIFEST.yaml",
    ".ai/CURRENT_STATE.md",
    ".ai/DECISIONS.md",
    ".ai/TASKS.md",
    ".ai/KNOWN_BLOCKERS.md",
    ".ai/RISK_REGISTER.md",
    ".ai/TEST_MATRIX.md",
    ".ai/RUN_HISTORY.md",
    ".ai/HANDOFF.md",
    ".ai/CONTEXT_RECOVERY.md",
    ".ai/MEMORY_GOVERNANCE.md",
    ".ai/MEMORY_OWNERSHIP_MATRIX.md",
    "governance/PROJECT_MANIFEST.yaml",
    "governance/AUTHORITY_LADDER.yaml",
    "governance/MEMORY_CONTRACT.yaml",
    "governance/DEVELOPMENT_LIFECYCLE.yaml",
    "governance/ACTION_POLICY.yaml",
    "governance/RESEARCH_SOFTWARE_SPLIT.yaml",
    "claims/claims_registry.yaml",
    "claims/theorem_registry.yaml",
    "claims/novelty_registry.yaml",
    "schemas/memory_manifest.schema.json",
    "schemas/evidence_event.schema.json",
    "schemas/governance_action.schema.json",
    "artifacts/index/run_index.csv",
    "artifacts/index/claim_evidence_matrix.csv",
    "artifacts/index/theorem_dependency_matrix.csv",
    "artifacts/index/figure_provenance.csv",
    "artifacts/index/table_provenance.csv",
    "experiments/matrices/canonical_run_matrix.yaml",
    "paper/main.tex",
    "paper/quality/paper_quality_report.json",
)


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


def _refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.split(";")
    elif isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_refs(item))
    else:
        return []
    return [item.strip() for item in values if item and item.strip()]


def _local_reference(root: Path, reference: str) -> bool | None:
    lower = reference.lower()
    if lower in {"none", "null", "n/a", "not applicable", "not_applicable"}:
        return None
    if reference.startswith(("http://", "https://")):
        return None
    if " " in reference and not any(reference.endswith(ext) for ext in (".md", ".tex", ".json", ".yaml")):
        return None
    candidate = Path(reference)
    if candidate.is_absolute():
        try:
            return candidate.exists() if candidate.resolve().is_relative_to(root.resolve()) else None
        except AttributeError:
            return candidate.exists() if str(candidate).lower().startswith(str(root).lower()) else None
    return (root / candidate).exists()


def _check_registry_references(root: Path) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    claims_path = root / "claims" / "claims_registry.yaml"
    try:
        claims = load_yaml_registry(claims_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [GovernanceIssue("error", "claims_registry_invalid", str(exc), (str(claims_path),))]
    for claim in claims:
        if not isinstance(claim, dict):
            issues.append(GovernanceIssue("error", "claim_not_mapping", "claim entry is not a mapping"))
            continue
        claim_id = str(claim.get("id", "<missing-id>"))
        if not claim.get("statement"):
            issues.append(GovernanceIssue("error", "claim_statement_missing", f"{claim_id} has no statement"))
        status = claim.get("status")
        if status not in ALLOWED_CLAIM_STATUSES:
            issues.append(GovernanceIssue("error", "claim_status_invalid", f"{claim_id}: {status}"))
        evidence_fields = [
            claim.get("evidence"),
            claim.get("proof"),
            claim.get("symbolic_checks"),
            claim.get("numerical_checks"),
            claim.get("counterexamples"),
        ]
        if status not in {"definition", "open", "conjecture"} and not any(evidence_fields):
            issues.append(
                GovernanceIssue(
                    "warning",
                    "claim_evidence_missing",
                    f"{claim_id} has status {status!r} but no evidence/proof reference",
                    ("claims/claims_registry.yaml",),
                )
            )
        for field in ("evidence", "proof", "symbolic_checks", "numerical_checks", "counterexamples"):
            for reference in _refs(claim.get(field)):
                exists = _local_reference(root, reference)
                if exists is False:
                    issues.append(
                        GovernanceIssue(
                            "error",
                            "claim_reference_missing",
                            f"{claim_id}.{field} points to missing local path {reference}",
                            ("claims/claims_registry.yaml", reference),
                        )
                    )
    theorem_path = root / "claims" / "theorem_registry.yaml"
    theorem_value = _load_yaml(theorem_path)
    theorems = theorem_value.get("theorems", []) if isinstance(theorem_value, dict) else theorem_value
    if not isinstance(theorems, list):
        issues.append(GovernanceIssue("error", "theorem_registry_invalid", "theorem registry is not a list"))
    else:
        known_claims = {str(item.get("id")) for item in claims if isinstance(item, dict)}
        for theorem in theorems:
            if not isinstance(theorem, dict):
                issues.append(GovernanceIssue("error", "theorem_not_mapping", "theorem entry is not a mapping"))
                continue
            identifier = str(theorem.get("id", "<missing-id>"))
            for dependency in _refs(theorem.get("dependencies")):
                if dependency not in known_claims and not dependency.startswith("THM_"):
                    issues.append(
                        GovernanceIssue(
                            "warning",
                            "theorem_dependency_unknown",
                            f"{identifier} depends on unregistered identifier {dependency}",
                            ("claims/theorem_registry.yaml",),
                        )
                    )
            for field in ("proof_location", "symbolic_verification", "exact_examples", "numerical_examples", "counterexamples"):
                for reference in _refs(theorem.get(field)):
                    exists = _local_reference(root, reference)
                    if exists is False:
                        issues.append(
                            GovernanceIssue(
                                "error",
                                "theorem_reference_missing",
                                f"{identifier}.{field} points to missing local path {reference}",
                                ("claims/theorem_registry.yaml", reference),
                            )
                        )
    return issues


def _paper_issues(root: Path) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    quality_path = root / "paper" / "quality" / "paper_quality_report.json"
    if quality_path.exists():
        try:
            quality = json.loads(quality_path.read_text(encoding="utf-8"))
            scores = {str(item.get("id")): int(item.get("score", -1)) for item in quality.get("dimensions", [])}
            critical = quality.get("critical_dimensions", [])
            below = [item for item in critical if scores.get(item, -1) < 4]
            release_score = scores.get("release_readiness", -1)
            declared_ready = bool(quality.get("release_ready_under_critical_gate", False))
            if below and declared_ready:
                issues.append(
                    GovernanceIssue(
                        "error",
                        "quality_flag_inconsistent",
                        f"quality report declares release readiness with critical scores below 4: {below}",
                        (str(quality_path),),
                    )
                )
            if declared_ready and release_score < 4:
                issues.append(
                    GovernanceIssue(
                        "error",
                        "release_readiness_flag_inconsistent",
                        f"quality report declares ready while release_readiness score is {release_score}/5",
                        (str(quality_path),),
                    )
                )
            if not declared_ready or release_score < 4:
                issues.append(
                    GovernanceIssue(
                        "warning",
                        "paper_not_release_ready",
                        "paper quality report does not support a release-ready claim under the declared rubric",
                        (str(quality_path),),
                    )
                )
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            issues.append(GovernanceIssue("error", "quality_report_invalid", str(exc), (str(quality_path),)))
    else:
        issues.append(GovernanceIssue("warning", "quality_report_missing", "paper quality report is absent"))
    metadata = root / "paper" / "metadata.tex"
    if metadata.exists() and "SEION Mathematical Verification Contributors" in metadata.read_text(encoding="utf-8"):
        issues.append(
            GovernanceIssue(
                "warning",
                "placeholder_author_metadata",
                "paper metadata still uses a contributor placeholder instead of a verified author record",
                ("paper/metadata.tex", "CITATION.cff"),
            )
        )
    references = root / "paper" / "references.bib"
    if references.exists():
        count = len(re.findall(r"^@", references.read_text(encoding="utf-8"), re.MULTILINE))
        if count < 10:
            issues.append(
                GovernanceIssue(
                    "warning",
                    "thin_bibliography",
                    f"bibliography contains {count} entries; prior-art coverage is not yet competitive",
                    ("paper/references.bib",),
                )
            )
    return issues


def _yaml_issues(root: Path) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    paths = list((root / "governance").glob("*.yaml")) + list((root / ".ai").glob("*.yaml"))
    for path in paths:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            issues.append(GovernanceIssue("error", "yaml_invalid", str(exc), (str(path),)))
    return issues


def _index_issues(root: Path) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    claims_path = root / "claims" / "claims_registry.yaml"
    try:
        known_claims = {str(item.get("id")) for item in load_yaml_registry(claims_path)}
    except (OSError, ValueError, yaml.YAMLError):
        known_claims = set()
    matrix_path = root / "artifacts" / "index" / "claim_evidence_matrix.csv"
    if matrix_path.exists():
        try:
            with matrix_path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                claim_id = str(row.get("claim_id", ""))
                if claim_id not in known_claims:
                    issues.append(
                        GovernanceIssue(
                            "error",
                            "evidence_matrix_unknown_claim",
                            f"claim/evidence matrix references unregistered claim {claim_id!r}",
                            ("artifacts/index/claim_evidence_matrix.csv",),
                        )
                    )
                for reference in _refs(row.get("evidence")):
                    exists = _local_reference(root, reference)
                    if exists is False:
                        issues.append(
                            GovernanceIssue(
                                "error",
                                "evidence_matrix_reference_missing",
                                f"claim/evidence matrix references missing local path {reference}",
                                ("artifacts/index/claim_evidence_matrix.csv", reference),
                            )
                        )
        except (OSError, csv.Error) as exc:
            issues.append(GovernanceIssue("error", "evidence_matrix_invalid", str(exc), (str(matrix_path),)))
    theorem_path = root / "artifacts" / "index" / "theorem_dependency_matrix.csv"
    if theorem_path.exists():
        try:
            with theorem_path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                identifier = str(row.get("identifier", ""))
                if not identifier:
                    issues.append(
                        GovernanceIssue(
                            "error",
                            "theorem_matrix_identifier_missing",
                            "theorem dependency matrix contains a row without an identifier",
                            (str(theorem_path),),
                        )
                    )
        except (OSError, csv.Error) as exc:
            issues.append(GovernanceIssue("error", "theorem_matrix_invalid", str(exc), (str(theorem_path),)))
    for relative in (
        "artifacts/index/run_index.csv",
        "artifacts/index/figure_provenance.csv",
        "artifacts/index/table_provenance.csv",
    ):
        path = root / relative
        if path.exists():
            try:
                with path.open(newline="", encoding="utf-8") as stream:
                    header = next(csv.reader(stream), [])
                if not header:
                    issues.append(GovernanceIssue("error", "index_header_missing", f"{relative} has no CSV header", (relative,)))
            except (OSError, csv.Error) as exc:
                issues.append(GovernanceIssue("error", "index_invalid", str(exc), (relative,)))
    return issues


def _blocker_ids(root: Path) -> list[str]:
    path = root / ".ai" / "KNOWN_BLOCKERS.md"
    if not path.exists():
        return []
    return re.findall(r"\|\s*(B-\d+)\s*\|", path.read_text(encoding="utf-8"))


def _write_reviewer_report(root: Path, result: dict[str, Any]) -> Path:
    target = root / "docs" / "reviewer_report.md"
    lines = [
        "# Governance and reviewer report",
        "",
        "Generated by `seion-core governance audit`; this report is derived evidence, not release approval.",
        "",
        f"- Audit UTC: {result['audited_at']}",
        f"- Status: **{result['status']}**",
        f"- Branch: `{result['git'].get('branch')}`",
        f"- Commit: `{result['git'].get('commit')}`",
        "",
        "## Critical findings",
        "",
    ]
    issues = result.get("issues", [])
    if issues:
        lines.extend(
            f"- **{item['severity']}** `{item['code']}` — {item['message']}"
            for item in issues
        )
    else:
        lines.append("- None emitted by the structural audit.")
    lines.extend(
        [
            "",
            "## Scientific blockers",
            "",
            "The current blocker register is `.ai/KNOWN_BLOCKERS.md`; a green structural audit does not clear those blockers.",
            "",
            "## Run evidence",
            "",
            f"- Historical runs: {result['runs']['historical_run_count']}",
            f"- Unique scientific instances: {result['runs']['unique_scientific_instance_count']}",
            f"- Duplicate groups: {result['runs']['duplicate_group_count']}",
            "",
            "## Limitations",
            "",
            "This audit checks structure, references, artifact contracts, and declared quality flags. It does not prove mathematical theorems, independently validate prior art, or inspect every PDF page semantically.",
            "",
        ]
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def audit_governance(
    repo_root: str | Path,
    *,
    strict: bool = False,
    write_outputs: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    issues: list[GovernanceIssue] = []
    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    if missing:
        issues.append(
            GovernanceIssue(
                "error",
                "required_file_missing",
                f"{len(missing)} required governance/memory files are missing",
                tuple(missing),
            )
        )
    issues.extend(_yaml_issues(root))
    issues.extend(_check_registry_references(root))
    issues.extend(_index_issues(root))
    issues.extend(lint_paper_language(root))
    run_contract = audit_run_artifacts(root)
    if run_contract["contract_incomplete_count"]:
        issues.append(
            GovernanceIssue(
                "error",
                "run_contract_incomplete",
                f"{run_contract['contract_incomplete_count']} run artifacts lack required contract files",
                tuple(run_contract["missing_artifacts"].keys()),
            )
        )
    dedupe = deduplicate_runs(root) if write_outputs else {
        "historical_run_count": run_contract["run_count"],
        "unique_scientific_instance_count": run_contract["run_count"],
        "duplicate_group_count": 0,
        "duplicate_record_count": 0,
    }
    if dedupe.get("duplicate_group_count", 0):
        issues.append(
            GovernanceIssue(
                "warning",
                "duplicate_runs_detected",
                f"{dedupe['duplicate_group_count']} duplicate run groups detected; use the derived unique index",
                ("artifacts/index/run_index.csv", "artifacts/index/run_index_deduplicated.csv"),
            )
        )
    issues.extend(_paper_issues(root))
    status = "red" if any(item.severity == "error" for item in issues) else "yellow" if issues else "green"
    result = {
        "version": 1,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict": strict,
        "git": {
            "branch": _git(root, "branch", "--show-current"),
            "commit": _git(root, "rev-parse", "HEAD"),
            "dirty": bool(_git(root, "status", "--porcelain")),
        },
        "required_files": {"count": len(REQUIRED_FILES), "missing": missing},
        "memory_health": {
            "canonical_manifest_present": (root / ".ai" / "MEMORY_MANIFEST.yaml").exists(),
            "durable_required_files_present": len([path for path in REQUIRED_FILES if path.startswith(".ai/") and (root / path).exists()]),
            "derived_runtime_separated": True,
            "status": "green" if not any(path.startswith(".ai/") for path in missing) else "red",
        },
        "runs": {
            "historical_run_count": dedupe.get("historical_run_count", 0),
            "unique_scientific_instance_count": dedupe.get("unique_scientific_instance_count", 0),
            "duplicate_group_count": dedupe.get("duplicate_group_count", 0),
            "duplicate_record_count": dedupe.get("duplicate_record_count", 0),
            "artifact_contract": run_contract,
        },
        "scientific_blocker_ids": _blocker_ids(root),
        "issues": [item.to_dict() for item in issues],
        "limitations": [
            "Structural audit only; declared validation commands are not executed by this command.",
            "A green result is not mathematical proof or release approval.",
        ],
    }
    if write_outputs:
        target = root / "artifacts" / "index" / "governance_audit.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (root / "artifacts" / "index" / "memory_health.json").write_text(
            json.dumps(result["memory_health"], indent=2) + "\n", encoding="utf-8"
        )
        report = _write_reviewer_report(root, result)
        try:
            append_event(
                root,
                kind="governance_audit",
                source="seion-core governance audit",
                result=status,
                authority="verified" if status != "red" else "observed",
                artifacts=("artifacts/index/governance_audit.json", report.relative_to(root).as_posix()),
                limitations=result["limitations"],
            )
        except OSError:
            result.setdefault("warnings", []).append("governance event ledger could not be updated")
    result["passed"] = status == "green" if strict else status != "red"
    return result
