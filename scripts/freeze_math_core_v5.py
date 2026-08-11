"""Generate a freeze manifest that cannot repeat the 2026-08-09 drift.

The previous V5 review manifest recorded a SHA256 for
``claims/theorem_registry_v5.yaml`` that exists in no blob on any ref: the
freeze was taken against an uncommitted working tree, so the frozen state can
never be diffed against. A manifest that only records content hashes cannot
detect this.

This generator therefore records, per artifact, both the working-tree hash and
whether that exact content is reachable from git, and refuses to declare the
freeze reconstructible unless every artifact is committed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ARTIFACTS = [
    "research/math_closure/FROZEN_CORE_V5_2026-08-11.md",
    "claims/theorem_registry_v5.yaml",
    "research/math_closure/k2/saturation_iff_theorem.tex",
    "research/math_closure/k3/general_upper_envelope.tex",
    "research/math_closure/k3/m13_unconditional_chain_envelope.tex",
    "research/math_closure/k3/m14_exact_chain_constant.tex",
    "research/math_closure/k3/m15_exact_branching_constant.tex",
    "research/math_closure/k3/m16_general_binary_class_corollary.tex",
    "research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex",
    "research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.tex",
    "research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.tex",
    "research/math_closure/dag/exact_path_constant.tex",
    "research/math_closure/dag/dag_asymptotic_sharpness.tex",
    "research/math_closure/dimension_rank/growing_tree_dimension_counterexample.tex",
    "research/math_closure/dimension_rank/fixed_tree_support_compression.tex",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def committed_blob_matches(path: str, digest: str) -> tuple[bool, str | None]:
    """Is this exact content reachable from git, and under which blob?"""
    code, blob = git("rev-parse", f"HEAD:{path}")
    if code != 0:
        return False, None
    raw = subprocess.run(["git", "cat-file", "blob", blob], capture_output=True).stdout
    return hashlib.sha256(raw).hexdigest().upper() == digest, blob[:12]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    _, head = git("rev-parse", "HEAD")
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")

    entries, uncommitted, missing = [], [], []
    for rel in ARTIFACTS:
        path = root / rel
        if not path.exists():
            missing.append(rel)
            continue
        digest = sha256(path)
        matches, blob = committed_blob_matches(rel, digest)
        entries.append({
            "path": rel,
            "sha256_worktree": digest,
            "committed_at_head": matches,
            "blob": blob,
        })
        if not matches:
            uncommitted.append(rel)

    reconstructible = not uncommitted and not missing
    manifest = {
        "freeze": "MATH_CORE_V5_2026-08-11",
        "title": "Projected Multilinear Trees: Sharp Error Constants Under Approximate Closure",
        "branch": branch,
        "git_head": head,
        "artifacts": entries,
        "missing": missing,
        "uncommitted_at_head": uncommitted,
        "reconstructible_from_git": reconstructible,
        "status": "FROZEN_RECONSTRUCTIBLE" if reconstructible else "FROZEN_BUT_NOT_RECONSTRUCTIBLE",
        "note": (
            "A freeze is only meaningful if its artifacts can be recovered later. "
            "The 2026-08-09 review manifest recorded a registry hash present in no blob "
            "on any ref, so that snapshot cannot be diffed against. Commit every listed "
            "artifact and regenerate before treating this freeze as authoritative."
        ),
        "epistemic_status": {
            "novelty": "NOT_ESTABLISHED (0 of 41 registry entries)",
            "independent_human_review": "NONE",
            "verdict": "CANDIDATE_FOR_EXTERNAL_REVIEW_NOT_APPROVED",
        },
    }
    out = root / "research/math_closure/FROZEN_CORE_V5_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"freeze      : {manifest['freeze']}")
    print(f"branch/head : {branch} / {head[:12]}")
    print(f"artifacts   : {len(entries)} listed, {len(missing)} missing")
    print(f"uncommitted : {len(uncommitted)}")
    for rel in uncommitted:
        print(f"    {rel}")
    print(f"status      : {manifest['status']}")
    print(f"written     : {out.relative_to(root)}")
    return 0 if reconstructible else 2


if __name__ == "__main__":
    sys.exit(main())
