"""Deterministic, explainable task-context compilation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


TASK_HINTS = {
    "proof": ["claims", "docs/theorems_v3", "papers/tree_stability_v3/proofs", "src/seion_core/research_v3", "tests/research_v3"],
    "experiment": ["experiments", "artifacts/research_v3", "scripts/tree_constants_v3", "src/seion_core/research_v3", "tests/research_v3"],
    "paper": ["papers/tree_stability_v3", "papers/software_v3", "papers/supplement_v4", "claims", "artifacts/qa_v3"],
    "release": ["governance", ".ai", "scripts", ".github", "artifacts/research_v3", "artifacts/release_v4"],
    "bugfix": ["src", "tests", "docs/incidents", ".ai/KNOWN_BLOCKERS.md"],
    "onboarding": ["README.md", ".ai/README.md", "docs/onboarding", "docs/maps", "governance"],
}


def classify_task(task: str) -> str:
    value = task.lower()
    for category, words in {
        "proof": ("proof", "theorem", "lemma", "sharpness"),
        "experiment": ("run", "experiment", "gpu", "optimizer", "matrix"),
        "paper": ("paper", "figure", "table", "latex", "render"),
        "release": ("release", "package", "wheel", "sbom", "security", "ci"),
        "bugfix": ("bug", "fix", "failure", "regression", "inconsistency"),
        "onboarding": ("onboard", "recover", "context", "new agent"),
    }.items():
        if any(word in value for word in words):
            return category
    return "onboarding"


def compile_context(root: Path, task: str, output_dir: Path, token_budget: int = 12000, workstream: str | None = None, extra: list[str] | None = None) -> dict[str, Any]:
    category = workstream or classify_task(task)
    candidates = list(TASK_HINTS.get(category, TASK_HINTS["onboarding"])) + list(extra or [])
    all_files: list[Path] = []
    reasons: dict[str, str] = {}
    for hint in candidates:
        path = root / hint
        if path.is_file():
            all_files.append(path)
            reasons[hint] = f"direct task-category match: {category}"
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in {".py", ".md", ".yaml", ".yml", ".csv", ".tex", ".json"}:
                    rel = child.relative_to(root).as_posix()
                    all_files.append(child)
                    reasons[rel] = f"within relevant workstream path: {hint}"
    unique = {path.resolve(): path for path in all_files}
    ranked = sorted(unique.values(), key=lambda path: (0 if path.name in {"CURRENT_STATE.md", "TASKS.md", "KNOWN_BLOCKERS.md", "MEMORY_MANIFEST.yaml"} else 1, str(path)))
    selected: list[Path] = []
    used = 0
    for path in ranked:
        text = path.read_text(encoding="utf-8", errors="replace")
        cost = max(1, len(text) // 4)
        if selected and used + cost > token_budget:
            continue
        selected.append(path)
        used += cost
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    sections = []
    for path in selected:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": rel, "sha256": digest, "reason": reasons.get(rel, "dependency of selected workstream"), "included": True, "estimated_tokens": max(1, len(text) // 4)})
        sections.append(f"\n## {rel}\n\n{text[:max(1000, (token_budget * 4) // max(1, len(selected)))]}\n")
    omitted = sorted(set(reasons) - {item["path"] for item in entries})
    for rel in omitted:
        entries.append({"path": rel, "reason": reasons[rel], "included": False, "estimated_tokens": 0})
    manifest = {"schema_version": 1, "task": task, "category": category, "workstream": workstream, "token_budget": token_budget, "estimated_tokens": used, "selected_count": len(selected), "candidate_count": len(reasons)}
    (output_dir / "context_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "context_explain.json").write_text(json.dumps({"included": entries, "excluded": [entry for entry in entries if not entry["included"]]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "source_hashes.json").write_text(json.dumps({entry["path"]: entry.get("sha256") for entry in entries if entry.get("sha256")}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "context.md").write_text("# Deterministic SEION context pack\n\n" + f"Task: {task}\nCategory: {category}\nEstimated tokens: {used}/{token_budget}\n" + "".join(sections), encoding="utf-8")
    return manifest
