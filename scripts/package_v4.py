"""Build package, source distribution, reproducibility bundle, SBOM and checksums."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def main() -> int:
    out = ROOT / "artifacts/release_v4"; pkg = out / "packages"; pkg.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", str(pkg)]
    build = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    wheel = subprocess.CompletedProcess(cmd, build.returncode, build.stdout, build.stderr)
    sdist = subprocess.CompletedProcess(cmd, build.returncode, build.stdout, build.stderr)
    if build.returncode != 0:
        wheel = subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", str(pkg)], cwd=ROOT, capture_output=True, text=True)
        sdist = subprocess.run([sys.executable, "-m", "build", "--sdist", "--outdir", str(pkg)], cwd=ROOT, capture_output=True, text=True)
    bundle = out / "seion-math-core-v4-reproducibility.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in ["AGENTS.md", "README.md", "pyproject.toml", "claims", "experiments", "governance", "docs", ".ai/packs", "artifacts/reference_audit", "artifacts/qa_v4"]:
            path = ROOT / rel
            if path.is_file(): z.write(path, rel)
            elif path.exists():
                for child in path.rglob("*"):
                    if child.is_file() and "build" not in child.parts: z.write(child, child.relative_to(ROOT).as_posix())
    members = []
    for path in sorted(pkg.glob("*")) + [bundle]:
        if path.is_file(): members.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size})
    (out / "checksums.sha256").write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in members), encoding="utf-8")
    sbom = {"bomFormat": "CycloneDX", "specVersion": "1.5", "metadata": {"timestamp": datetime.now(timezone.utc).isoformat(), "component": {"name": "seion-math-core", "version": "0.4.0"}}, "components": [{"name": "numpy", "scope": "runtime"}, {"name": "scipy", "scope": "runtime"}, {"name": "sympy", "scope": "runtime"}, {"name": "PyYAML", "scope": "runtime"}]}
    (out / "sbom.cdx.json").write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    (out / "release_manifest.json").write_text(json.dumps({"version": "0.4.0", "generated_utc": datetime.now(timezone.utc).isoformat(), "wheel_exit": wheel.returncode, "sdist_exit": sdist.returncode, "artifacts": members, "policy": "candidate; human review and unresolved mathematical gates remain"}, indent=2) + "\n", encoding="utf-8")
    (out / "RELEASE_NOTES.md").write_text("# SEION Math Core v0.4.0 candidate\n\nCanonical governance/memory/graph layer, split paper sources, typed state machines, and reproducibility artifacts. Mathematical novelty, extended-grid completion, and independent human review remain blocked.\n", encoding="utf-8")
    print(json.dumps({"wheel_exit": wheel.returncode, "sdist_exit": sdist.returncode, "bundle": str(bundle)}))
    return 0 if wheel.returncode == 0 and sdist.returncode == 0 else 2
if __name__ == "__main__": raise SystemExit(main())
