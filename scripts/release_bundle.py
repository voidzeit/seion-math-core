"""Assemble a traceable release bundle."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "artifacts" / "release"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_paths(target: Path, paths: list[Path]) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
            elif path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file() and ".git" not in child.parts:
                        archive.write(child, child.relative_to(ROOT).as_posix())


def build_quality_pdf(target: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    report_path = ROOT / "paper" / "quality" / "paper_quality_report.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    with PdfPages(target) as pdf:
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        lines = ["SEION Math Core paper quality report", "", "Fields Medal caliber is aspirational, not an award claim.", ""]
        for item in data["dimensions"]:
            lines.append(f"{item['id']}: {item['score']}/5 - {item['justification']}")
        lines.extend(["", f"critical-gate release-ready flag: {data['release_ready_under_critical_gate']}"])
        ax.text(0.04, 0.96, "\n".join(lines), va="top", family="DejaVu Sans", fontsize=9, wrap=True)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def main() -> int:
    source_pdf = ROOT / "paper" / "build" / "main.pdf"
    if not source_pdf.exists():
        print(f"missing paper PDF: {source_pdf}")
        return 1
    RELEASE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_pdf, RELEASE / "seion_math_core_paper.pdf")
    source_paths = [ROOT / "src", ROOT / "tests", ROOT / "experiments", ROOT / "claims", ROOT / "docs", ROOT / "paper", ROOT / "pyproject.toml", ROOT / "uv.lock", ROOT / "README.md", ROOT / "scripts"]
    zip_paths(RELEASE / "source_archive.zip", source_paths)
    reproducibility_paths = [ROOT / "experiments", ROOT / "claims", ROOT / "paper" / "generated", ROOT / "artifacts" / "index", ROOT / "artifacts" / "system", ROOT / "artifacts" / "data"]
    zip_paths(RELEASE / "reproducibility_bundle.zip", reproducibility_paths)
    for name in ["run_index.csv", "claim_evidence_matrix.csv", "theorem_dependency_matrix.csv"]:
        source = ROOT / "artifacts" / "index" / name
        if source.exists():
            shutil.copy2(source, RELEASE / name)
    quality_pdf = RELEASE / "paper_quality_report.pdf"
    build_quality_pdf(quality_pdf)
    (RELEASE / "RELEASE_NOTES.md").write_text("# SEION Math Core 0.1.0\n\nThis is an initial finite-dimensional reproducibility release. It includes typed n-ary laws, associator conventions, projector certificates, finite cohomology checks, generated figures/tables, a compiled paper, and explicit open research blockers.\n", encoding="utf-8")
    (RELEASE / "REPRODUCE.md").write_text("# Reproduce\n\n```powershell\npython -m pip install -e .\n.\\scripts\\run_full_blackwell.ps1\n.\\scripts\\build_paper.ps1\n```\n\nThe paper command is `.\\scripts\\build_paper.ps1`. The primary full command is `.\\scripts\\run_full_blackwell.ps1`.\n", encoding="utf-8")
    entries = []
    for path in sorted(RELEASE.iterdir()):
        if path.name == "checksums.sha256" or not path.is_file():
            continue
        entries.append(f"{sha256(path)}  {path.name}")
    (RELEASE / "checksums.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")
    print(json.dumps({"release": str(RELEASE), "files": [path.name for path in sorted(RELEASE.iterdir())]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

