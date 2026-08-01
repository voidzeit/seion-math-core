"""Produce the exact fail-closed handoff and unresolved-blocker report."""
from __future__ import annotations
import csv, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = [Path(r"C:/Documents/ai-memory-orchestrator"), Path(r"C:/Documents/Hyperghaps EMA/EMA-AI"), Path(r"C:/Documents/AEC_Agentic"), Path(r"C:/Documents/SFC/bluebim-web"), Path(r"C:/Documents/ometeos/pixelcity_smoke_test")]

def run(*args: str) -> dict:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return {"command": " ".join(args), "exit_code": p.returncode, "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-1000:]}

def main() -> int:
    out = ROOT / "artifacts/release_v4"; out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    blockers = [
        {"id":"BLOCK-V4-MATH-SHARPNESS", "status":"OPEN", "statement":"Fixed-positive-eta sharpness extremizers and k-1 sharpness are not complete."},
        {"id":"BLOCK-V4-MATH-CONSTANTS", "status":"OPEN", "statement":"Approximate closure, spectral snapping, and cancellation-aware FI/GJI/Jacobiator constants require proof-quality completion."},
        {"id":"BLOCK-V4-NOVELTY", "status":"OPEN", "statement":"Theorem-level novelty is not approved; primary-source prior-art adjudication remains a human research decision."},
        {"id":"BLOCK-V4-EXTENDED-GRID", "status":"OPEN", "statement":"Extended grid is 4/460800 optimizer trajectories and 0/8400 performance cells."},
        {"id":"BLOCK-V4-PDF-REVIEW", "status":"OPEN", "statement":"Automated compile/render passed, but full visual and accessibility approval remains human."},
        {"id":"BLOCK-V4-INDEPENDENT-REVIEW", "status":"OPEN", "statement":"Independent mathematical, numerical, visualization, security, and release reviews are pending."},
        {"id":"BLOCK-V4-WORKTREE", "status":"OPEN", "statement":"User-owned .obsidian/graph.json and .obsidian/workspace.json remain intentionally unmodified by this task's scope policy."},
    ]
    graph = json.loads((ROOT / ".ai/machine/repository_graph.json").read_text(encoding="utf-8"))
    render = json.loads((ROOT / "output/pdf/render_manifest.json").read_text(encoding="utf-8")) if (ROOT / "output/pdf/render_manifest.json").exists() else {}
    external = []
    for path in EXTERNAL:
        value = {"path": str(path), "exists": path.exists(), "checked_read_only": True}
        if (path / ".git").exists():
            value["status"] = subprocess.run(["git", "status", "--short"], cwd=path, capture_output=True, text=True).stdout.strip()
        external.append(value)
    commands = [run("python", "-m", "pytest", "-q"), run("python", "scripts/audit_v4.py"), run("python", "-m", "seion_core.cli.main", "governance", "audit", "--json"), run("python", "-m", "seion_core.cli.main", "governance", "dedupe-runs")]
    handoff = {"schema_version":4, "generated_utc":now, "branch":run("git", "branch", "--show-current")["stdout_tail"].strip(), "commit":run("git", "rev-parse", "HEAD")["stdout_tail"].strip(), "canonical_repository":str(ROOT), "external_repositories":external, "graph":{"nodes":len(graph.get("nodes",[])),"edges":len(graph.get("edges",[]))}, "pdfs":render.get("pdfs",[]), "packages":sorted(p.name for p in (out / "packages").glob("*") if p.is_file()), "blockers":blockers, "commands":commands, "release_status":"FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW"}
    (out / "final_canonical_handoff.json").write_text(json.dumps(handoff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Final canonical handoff v4", "", f"Generated: {now}", f"Branch: `{handoff['branch']}`", f"Commit at handoff: `{handoff['commit']}`", "", "## Status", "`FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW`", "", "## Graph", f"{len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges.", "", "## Unresolved blockers"] + [f"- **{item['id']}** — {item['statement']}" for item in blockers] + ["", "## Scope", "All changes and generated outputs are under `C:/Documents/metamaths/seion-math-core`. The five named external repositories were only inspected read-only.", "", "## Required human decisions", "Independent proof audit, prior-art novelty decision, visual PDF review, security/release review, and authorization to publish."]
    (out / "final_canonical_handoff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "EXACT_UNRESOLVED_BLOCKERS.md").write_text("# Exact unresolved blockers\n\n" + "\n".join(f"- `{x['id']}`: {x['statement']}" for x in blockers) + "\n", encoding="utf-8")
    (out / "PR_BODY.md").write_text("# SEION canonical repository v4\n\nThis branch adds the canonical governance, memory, evidence, graph, paper, supplement, packaging, and release-candidate infrastructure. It remains fail-closed: see `EXACT_UNRESOLVED_BLOCKERS.md`; no human approval is implied.\n", encoding="utf-8")
    rows = [["claim_or_result", "status", "authority", "evidence_or_blocker"], ["finite recursive tree certificates", "verified scoped", "verified", "artifacts/research_v3"], ["exact invariant reduction", "conditional candidate", "declared", "docs/research/V4_MATHEMATICAL_PROGRAM.md"], ["approximate closure constants", "blocked", "declared", "BLOCK-V4-MATH-CONSTANTS"], ["extended optimizer grid", "blocked", "observed", "BLOCK-V4-EXTENDED-GRID"], ["theorem novelty", "blocked", "declared", "BLOCK-V4-NOVELTY"]]
    with (out / "claim_evidence_matrix_v4.csv").open("w", newline="", encoding="utf-8") as h: csv.writer(h).writerows(rows)
    with (out / "theorem_dependency_matrix_v4.csv").open("w", newline="", encoding="utf-8") as h: csv.writer(h).writerows([["node","depends_on","status"],["exact_invariance","isometry+exact_closure","conditional_candidate"],["operadic_identity_descent","exact_invariance","blocked_independent_audit"],["approximate_associator_bound","closure_residual+norm","open"],["spectral_snapping","gap_around_half","open"]])
    return 0
if __name__ == "__main__": raise SystemExit(main())
