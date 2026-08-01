"""Package rebuild/verify script (Gate 7: "package rebuild script
succeeds"). Regenerates MANIFEST.json and checksums.sha256 from the
package's GIT-INDEXED content (via `git show :path`), not raw disk
bytes.

Why: this package sits inside a git repository with a Windows
core.autocrlf=true default and .gitattributes rules forcing LF for text
files. That combination means the on-disk working-tree bytes for a text
file can legitimately be CRLF (smudged on checkout) while the actual
committed/indexed blob - what a FRESH CLONE ANYWHERE ELSE will see - is
LF. Computing checksums from raw disk reads would silently record the
*local, possibly-smudged* byte sequence, which would then fail
verification for anyone who clones this repository fresh. Reading
through `git show :path` always returns the canonical, filter-clean
content, matching what git will actually check out, regardless of the
current local working tree's line-ending state. This script must
therefore be run from inside the git working copy (it shells out to
`git`), not from an extracted/standalone copy of just this directory -
see the standalone fallback note in `verify()` below for that case.

Usage:
    python rebuild_manifest_and_checksums.py            # regenerate both
    python rebuild_manifest_and_checksums.py --verify    # check only
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
PKG_NAME = PKG.name


def _git_show(rel_path: str) -> bytes | None:
    """Content of a path as recorded in the git index, or None if the
    path isn't tracked there (e.g. this script is run before `git add`,
    or from a standalone extracted copy with no .git present)."""

    try:
        result = subprocess.run(
            ["git", "show", f":{PKG_NAME}/{rel_path}"],
            cwd=PKG.parent, capture_output=True, check=True,
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def compute_checksums() -> dict[str, str]:
    files = sorted(
        p for p in PKG.rglob("*")
        if p.is_file() and p.name not in ("checksums.sha256", "MANIFEST.json")
    )
    checksums = {}
    for f in files:
        rel = str(f.relative_to(PKG)).replace("\\", "/")
        content = _git_show(rel)
        if content is None:
            # Not yet staged in git (or standalone copy with no .git) -
            # fall back to a raw disk read; only correct if this file's
            # bytes are already in their final, canonical form (true for
            # binary files, and for text files with a consistent
            # checkout policy everywhere this package is distributed).
            content = f.read_bytes()
        checksums[rel] = hashlib.sha256(content).hexdigest()
    return checksums


def write_checksums(checksums: dict[str, str]) -> None:
    lines = [f"{digest}  {path}" for path, digest in sorted(checksums.items())]
    (PKG / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_manifest(checksums: dict[str, str]) -> None:
    all_files = sorted(set(checksums) | {"checksums.sha256", "MANIFEST.json"})
    total_bytes = sum((PKG / f).stat().st_size for f in checksums) + (PKG / "checksums.sha256").stat().st_size
    manifest = {
        "package": PKG.name,
        "file_count": len(all_files),
        "total_bytes": total_bytes,
        "files": all_files,
        "checksum_provenance": "sha256 of git-indexed (canonical, filter-clean) content via 'git show :path', not raw disk bytes - see this script's module docstring",
    }
    (PKG / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")


def verify() -> bool:
    recorded = {}
    for line in (PKG / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, path = line.split("  ", 1)
        recorded[path] = digest
    actual = compute_checksums()
    mismatches = [p for p in recorded if recorded[p] != actual.get(p)]
    missing = [p for p in recorded if p not in actual]
    extra = [p for p in actual if p not in recorded]
    ok = not mismatches and not missing
    print(f"checked {len(recorded)} recorded checksums against {len(actual)} files")
    print(f"mismatches: {len(mismatches)}, missing: {len(missing)}, extra (untracked, not an error): {len(extra)}")
    if mismatches:
        print("MISMATCHES:", mismatches[:10])
    if missing:
        print("MISSING:", missing[:10])
    return ok


def main() -> None:
    if "--verify" in sys.argv:
        ok = verify()
        sys.exit(0 if ok else 1)
    checksums = compute_checksums()
    write_checksums(checksums)
    write_manifest(checksums)
    print(f"rebuilt checksums.sha256 ({len(checksums)} files) and MANIFEST.json")


if __name__ == "__main__":
    main()
