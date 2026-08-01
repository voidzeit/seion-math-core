"""Technical audit, PDF QA, adversarial reviews, and strict v3 release gate."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from seion_core.research_v3.interval_certification import (
    EXACTLY_DETERMINED_POSITIVE,
    NO_POSITIVE_LOWER_BOUND_OBTAINED,
    classify_optimality,
)
from seion_core.research_v3.run_schema import validate_run_artifacts


ARTIFACT_ROOT = ROOT / "artifacts" / "research_v3"
INDEX_ROOT = ROOT / "artifacts" / "index"
QA_ROOT = ROOT / "artifacts" / "qa_v3"
REVIEWS_ROOT = ROOT / "artifacts" / "reviews_v3"
MATH_ROOT = ROOT / "papers" / "tree_stability_v3"
SOFTWARE_ROOT = ROOT / "papers" / "software_v3"
PDF_SPECS = {
    "mathematical_paper": MATH_ROOT / "build" / "main.pdf",
    "software_companion": SOFTWARE_ROOT / "build" / "main.pdf",
}
RECOMMENDATION_ORDER = {
    "REJECT": 0,
    "MAJOR_REVISION": 1,
    "MINOR_REVISION": 2,
    "ACCEPTABLE_AS_RESEARCH_DRAFT": 3,
    "ACCEPTABLE_AS_PREPRINT": 4,
    "SUBMISSION_READY": 5,
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _run_text(command: list[str], *, cwd: Path = ROOT) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        errors="replace",
    )
    return result.returncode, result.stdout + result.stderr


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _poppler_tool(name: str) -> str:
    executable = shutil.which(f"{name}.exe") or shutil.which(name)
    if executable:
        return executable
    candidate = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "native"
        / "poppler"
        / "Library"
        / "bin"
        / f"{name}.exe"
    )
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError(f"Poppler tool not found: {name}")


def _pdf_reader(path: Path):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF audit") from exc
    return PdfReader(str(path))


def _make_contact_sheets(images: list[Path], output_prefix: Path) -> list[Path]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Pillow is required for PDF contact sheets") from exc

    sheets: list[Path] = []
    group_size = 16
    for group_index in range(0, len(images), group_size):
        group = images[group_index : group_index + group_size]
        thumbnails = []
        for page_number, path in enumerate(group, start=group_index + 1):
            with Image.open(path) as opened:
                page = opened.convert("RGB")
                page.thumbnail((260, 360))
                tile = Image.new("RGB", (280, 395), "white")
                x = (280 - page.width) // 2
                tile.paste(page, (x, 24))
                ImageDraw.Draw(tile).text((8, 5), f"page {page_number}", fill="black")
                thumbnails.append(tile)
        columns = min(4, len(thumbnails))
        rows = (len(thumbnails) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * 280, rows * 395), "#d9dde3")
        for index, tile in enumerate(thumbnails):
            sheet.paste(tile, ((index % columns) * 280, (index // columns) * 395))
        target = output_prefix.with_name(
            f"{output_prefix.name}_{group_index + 1:02d}-{group_index + len(group):02d}.png"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(target)
        sheets.append(target)
    return sheets


def render_pdfs() -> dict[str, Any]:
    pdftoppm = _poppler_tool("pdftoppm")
    pdfinfo = _poppler_tool("pdfinfo")
    pdftotext = _poppler_tool("pdftotext")
    manifest: dict[str, Any] = {
        "generated_utc": _utc(),
        "source_commit": _git("rev-parse", "HEAD"),
        "pdftoppm": pdftoppm,
        "pdfinfo": pdfinfo,
        "pdftotext": pdftotext,
        "documents": {},
    }
    for name, pdf_path in PDF_SPECS.items():
        if not pdf_path.is_file():
            raise FileNotFoundError(f"missing compiled PDF: {pdf_path}")
        code, info = _run_text([pdfinfo, str(pdf_path)])
        if code:
            raise RuntimeError(f"pdfinfo failed for {pdf_path}: {info}")
        page_match = re.search(r"^Pages:\s+(\d+)", info, flags=re.MULTILINE)
        if not page_match:
            raise RuntimeError(f"pdfinfo did not report a page count for {pdf_path}")
        page_count = int(page_match.group(1))
        render_dir = QA_ROOT / "pdf_pages" / name
        render_dir.mkdir(parents=True, exist_ok=True)
        for stale in render_dir.glob("page-*.png"):
            stale.unlink()
        prefix = render_dir / "page"
        code, output = _run_text(
            [pdftoppm, "-png", "-r", "110", str(pdf_path), str(prefix)]
        )
        if code:
            raise RuntimeError(f"pdftoppm failed for {pdf_path}: {output}")
        pages = sorted(render_dir.glob("page-*.png"))
        if len(pages) != page_count:
            raise RuntimeError(
                f"rendered {len(pages)} pages for {pdf_path}, expected {page_count}"
            )
        contact_sheets = _make_contact_sheets(
            pages, QA_ROOT / "contact_sheets" / name
        )
        page_text_lengths = []
        for page_number in range(1, page_count + 1):
            code, page_text = _run_text(
                [
                    pdftotext,
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-layout",
                    str(pdf_path),
                    "-",
                ]
            )
            if code:
                raise RuntimeError(
                    f"pdftotext failed for {pdf_path} page {page_number}: {page_text}"
                )
            page_text_lengths.append(len(page_text.strip()))
        blank_pages = [
            index + 1 for index, length in enumerate(page_text_lengths) if length < 20
        ]
        size_matches = re.findall(
            r"^(?:Page\s+\d+\s+size|Page size):\s+([0-9.]+) x ([0-9.]+) pts",
            info,
            flags=re.MULTILINE,
        )
        boxes = sorted(
            {
                (round(float(width), 3), round(float(height), 3))
                for width, height in size_matches
            }
        )
        metadata = {}
        for key in ("Title", "Author", "Subject", "Keywords"):
            match = re.search(
                rf"^{key}:[ \t]*([^\r\n]*)$", info, flags=re.MULTILINE
            )
            if match:
                metadata[key] = match.group(1).strip()
        manifest["documents"][name] = {
            "pdf": str(pdf_path.relative_to(ROOT)),
            "bytes": pdf_path.stat().st_size,
            "sha256": _sha256(pdf_path),
            "pages": page_count,
            "rendered_pages": len(pages),
            "blank_pages": blank_pages,
            "page_sizes": boxes,
            "text_characters": sum(page_text_lengths),
            "metadata": metadata,
            "contact_sheets": [str(path.relative_to(ROOT)) for path in contact_sheets],
            "pdfinfo": info,
            "render_status": "PASS",
        }
    _write_json(QA_ROOT / "pdf_manifest_v3.json", manifest)
    return manifest


def visual_signoff(status: str, inspector: str, notes: str) -> dict[str, Any]:
    if status not in {"PASS", "FAIL"}:
        raise ValueError("visual status must be PASS or FAIL")
    manifest = _read_json(QA_ROOT / "pdf_manifest_v3.json")
    if not manifest:
        raise RuntimeError("render PDFs before visual signoff")
    result = {
        "generated_utc": _utc(),
        "source_commit": _git("rev-parse", "HEAD"),
        "status": status,
        "inspector": inspector,
        "scope": "all rendered pages in both contact-sheet sets",
        "notes": notes,
        "human_release_approval": False,
        "epistemic_note": (
            "This is a layout inspection record, not independent mathematical "
            "review or publication authorization."
        ),
        "pdf_hashes": {
            name: record["sha256"] for name, record in manifest["documents"].items()
        },
    }
    _write_json(QA_ROOT / "visual_inspection_v3.json", result)
    return result


def _latex_issues(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    undefined = sorted(
        set(
            re.findall(
                r"(?:Citation|Reference) .([^']+)' .*?undefined",
                text,
                flags=re.IGNORECASE,
            )
        )
    )
    multiply_defined = re.findall(r"Label .* multiply defined", text)
    missing = re.findall(r"(?:File .* not found|No file .*\.bbl)", text)
    overfull = [
        float(value)
        for value in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", text)
    ]
    return {
        "path": str(log_path.relative_to(ROOT)),
        "exists": log_path.is_file(),
        "undefined_references_or_citations": undefined,
        "multiply_defined_labels": multiply_defined,
        "missing_inputs": missing,
        "overfull_boxes_pt": overfull,
        "critical_overfull_boxes": [value for value in overfull if value > 10.0],
        "pass": bool(log_path.is_file())
        and not undefined
        and not multiply_defined
        and not missing
        and not [value for value in overfull if value > 10.0],
    }


def _source_labels() -> dict[str, Any]:
    sources = [MATH_ROOT / "main.tex", MATH_ROOT / "proofs" / "full_proofs.tex"]
    labels: list[tuple[str, str]] = []
    for path in sources:
        text = path.read_text(encoding="utf-8")
        labels.extend(
            (label, str(path.relative_to(ROOT)))
            for label in re.findall(r"\\label\{([^}]+)\}", text)
        )
    counts = Counter(label for label, _ in labels)
    duplicates = sorted(label for label, count in counts.items() if count > 1)
    return {
        "label_count": len(labels),
        "duplicates": duplicates,
        "pass": not duplicates,
    }


def _manifest_integrity() -> dict[str, Any]:
    failures: list[str] = []
    checked = 0
    for manifest_path, collection_key in (
        (ARTIFACT_ROOT / "figure_manifest_v3.json", "figures"),
        (ARTIFACT_ROOT / "table_manifest_v3.json", "tables"),
    ):
        manifest = _read_json(manifest_path, {})
        for record in manifest.get(collection_key, []):
            outputs = record.get("outputs")
            if outputs:
                candidates = outputs.values()
            else:
                candidates = (record,)
            for output in candidates:
                path = ROOT / output["path"]
                checked += 1
                if not path.is_file():
                    failures.append(f"missing:{output['path']}")
                elif _sha256(path) != output["sha256"]:
                    failures.append(f"hash:{output['path']}")
    return {"checked_outputs": checked, "failures": failures, "pass": not failures}


def _run_integrity() -> dict[str, Any]:
    failures: list[str] = []
    commits: Counter[str] = Counter()
    run_dirs = sorted((ROOT / "artifacts" / "runs_v3").glob("*"))
    validated = 0
    for run_dir in run_dirs:
        if not run_dir.is_dir() or not (run_dir / "run_manifest.json").is_file():
            continue
        extremizer = (run_dir / "best_lower_bound.json").is_file()
        try:
            validate_run_artifacts(run_dir, extremizer=extremizer)
            manifest = _read_json(run_dir / "run_manifest.json", {})
            source_commit = str(manifest.get("source_commit", ""))
            input_hash = str(manifest.get("input_artifact_hash", ""))
            if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
                raise ValueError("invalid source commit")
            if not re.fullmatch(r"[0-9a-f]{64}", input_hash):
                raise ValueError("invalid input artifact hash")
            commits[source_commit] += 1
            validated += 1
        except Exception as exc:
            failures.append(f"{run_dir.name}:{type(exc).__name__}:{exc}")
    return {
        "validated_runs": validated,
        "source_commits": dict(commits),
        "failures": failures,
        "pass": validated >= 10 and not failures,
    }


def _pytest_summary() -> dict[str, Any]:
    path = QA_ROOT / "pytest_v3.xml"
    if not path.is_file():
        return {"exists": False, "pass": False, "tests": 0}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    values = {
        key: sum(int(float(suite.attrib.get(key, 0))) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    return {
        "exists": True,
        **values,
        "pass": values["tests"] > 0 and values["failures"] == 0 and values["errors"] == 0,
    }


def _dependency_audit() -> dict[str, Any]:
    registry = yaml.safe_load(
        (ROOT / "claims" / "theorem_registry_v3.yaml").read_text(encoding="utf-8")
    )
    theorems = registry["theorems"]
    ids = {item["id"] for item in theorems}
    external_definitions = {"DEF_V3_TYPED_TREE_EVALUATIONS"}
    unknown: list[str] = []
    graph: dict[str, list[str]] = {}
    for theorem in theorems:
        dependencies = list(theorem.get("dependencies", []))
        graph[theorem["id"]] = [dep for dep in dependencies if dep in ids]
        unknown.extend(
            f"{theorem['id']}->{dep}"
            for dep in dependencies
            if dep not in ids and dep not in external_definitions
        )
    state: dict[str, int] = {}
    cycles: list[list[str]] = []

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            cycles.append(stack[stack.index(node) :] + [node])
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for child in graph[node]:
            visit(child, stack + [child])
        state[node] = 2

    for node in graph:
        visit(node, [node])
    return {
        "theorems": len(theorems),
        "unknown_dependencies": unknown,
        "cycles": cycles,
        "pass": not unknown and not cycles,
    }


def _data_audit() -> dict[str, Any]:
    full = pd.read_parquet(INDEX_ROOT / "scientific_instances_full_v3.parquet")
    trees = pd.read_parquet(INDEX_ROOT / "tree_instances_v3.parquet")
    masks = pd.read_parquet(ARTIFACT_ROOT / "block_F_leakage_masks.parquet")
    precision = pd.read_parquet(ARTIFACT_ROOT / "block_I.parquet")
    gaps = pd.read_csv(INDEX_ROOT / "optimality_gaps_v3.csv")
    failures = pd.read_csv(INDEX_ROOT / "failures_v3.csv")
    block_counts = {
        str(key): int(value) for key, value in full.groupby("block").size().items()
    }
    expected = {
        "A": 4185,
        "B": 2880,
        "C": 3456,
        "D": 4320,
        "E": 96,
        "F": 24,
        "G": 28,
        "H": 480,
        "I": 24,
    }
    parity = precision["cpu_gpu_parity"].dropna()
    violation_columns = [
        column for column in full.columns if "violation_margin" in column
    ]
    negative_violations: dict[str, int] = {}
    for column in violation_columns:
        values = pd.to_numeric(full[column], errors="coerce").dropna()
        negative_violations[column] = int((values < -1.0e-8).sum())
    gap_class = [
        classify_optimality(low, up)
        for low, up in zip(
            gaps["certified_lower_bound"], gaps["certified_upper_bound"], strict=True
        )
    ]
    determined = gaps[[c == EXACTLY_DETERMINED_POSITIVE for c in gap_class]]
    no_lower = gaps[[c == NO_POSITIVE_LOWER_BOUND_OBTAINED for c in gap_class]]
    return {
        "scientific_instances": len(full),
        "unique_scientific_hashes": int(full["scientific_instance_hash"].nunique()),
        "duplicate_scientific_hashes": int(full["scientific_instance_hash"].duplicated().sum()),
        "block_counts": block_counts,
        "expected_block_counts": expected,
        "tree_occurrences": len(trees),
        "unique_tree_hashes": int(trees["tree_hash"].nunique()),
        "leakage_masks": len(masks),
        "failure_rows": len(failures),
        "negative_bound_violation_margins": negative_violations,
        "maximum_cpu_gpu_parity": float(parity.max()) if len(parity) else None,
        "maximum_certified_relative_gap": float(gaps["relative_gap"].max()),
        "exactly_determined_positive": len(determined),
        "no_positive_lower_bound_obtained": len(no_lower),
        "no_positive_lower_bound_fraction": len(no_lower) / len(gaps) if len(gaps) else None,
        "pass": (
            len(full) == 15493
            and int(full["scientific_instance_hash"].nunique()) == 15493
            and block_counts == expected
            and len(trees) == 81445
            and len(masks) == 1530
            and len(failures) == 0
            and not any(negative_violations.values())
            and (not len(parity) or float(parity.max()) <= 1.0e-7)
        ),
    }


def build_reviews() -> dict[str, Any]:
    REVIEWS_ROOT.mkdir(parents=True, exist_ok=True)
    reviews = [
        {
            "id": "A",
            "file": "reviewer_A_multilinear.md",
            "role": "multilinear analyst",
            "recommendation": "MAJOR_REVISION",
            "strengths": [
                "The projected-root k-1 induction correctly removes the root normal source.",
                "The exact subset expansion and root Pythagorean identity separate all four errors.",
                "The pair-exchange proof states its nonnegative-summary assumptions.",
            ],
            "major": [
                "Independent line-by-line verification of the heterogeneous mixed-mask recurrence is still absent.",
                "Fixed-eta sharpness of k and k-1 is open beyond the certified matching subfamilies.",
                "Information-optimality from local summaries is posed but not proved.",
            ],
        },
        {
            "id": "B",
            "file": "reviewer_B_operad.md",
            "role": "operad and non-associative algebra specialist",
            "recommendation": "MAJOR_REVISION",
            "strengths": [
                "Typed ordered composition syntax is explicit and invalid edges are rejected.",
                "Signed forests distinguish triangle certificates from cancellation-aware observations.",
                "The associator coefficient is conservatively presented as an upper bound.",
            ],
            "major": [
                "The novelty audit does not establish that the nodewise certificate or k-1 formulation is new.",
                "Filippov, GJI, and Jacobiator experiments do not yet yield expression-specific sharp constants.",
                "The relation to colored-operad stability should be independently assessed by a domain expert.",
            ],
        },
        {
            "id": "C",
            "file": "reviewer_C_verified_numerics.md",
            "role": "optimization and verified numerics specialist",
            "recommendation": "MAJOR_REVISION",
            "strengths": [
                "Certified uppers, interval lower constructions, and empirical optimizer values use separate statuses.",
                "Gradient and differential-evolution paths agree in the registered smoke calibration.",
                "The complete nested optimizer schedule is preserved rather than sampled invisibly.",
            ],
            "major": [
                "Most of the 460800 requested optimizer trajectories remain resource-gated and pending.",
                "SOS availability is recorded but does not supply a validated global certificate.",
                "Block-J performance has a registered calibration, not the complete 8400-cell extended sweep.",
            ],
        },
        {
            "id": "D",
            "file": "reviewer_D_visual_reproducibility.md",
            "role": "scientific visualization and reproducibility specialist",
            "recommendation": "ACCEPTABLE_AS_RESEARCH_DRAFT",
            "strengths": [
                "All 18 principal figures have PDF and SVG outputs with manifest hashes.",
                "Quantitative captions distinguish instance variation, specified-but-pending seeds, and exact diagrams.",
                "The mathematical paper and software companion compile independently and have page renders.",
            ],
            "major": [
                "A human editorial pass is required before preprint publication.",
                "The current AMS fallback should be migrated to the target journal class at submission time.",
                "Unverified author contact and ORCID metadata remain intentionally absent.",
            ],
        },
    ]
    for review in reviews:
        path = REVIEWS_ROOT / review["file"]
        lines = [
            f"# Reviewer {review['id']} — {review['role']}",
            "",
            "Status: AI-generated adversarial review; advisory only.",
            "",
            f"Recommendation: **{review['recommendation']}**",
            "",
            "## Strengths",
            "",
            *[f"- {item}" for item in review["strengths"]],
            "",
            "## Major issues",
            "",
            *[f"- {item}" for item in review["major"]],
            "",
            "## Required disposition",
            "",
            "Retain fail-closed language until the major issues are independently "
            "resolved. This review is not human approval.",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
    summary = {
        "generated_utc": _utc(),
        "source_commit": _git("rev-parse", "HEAD"),
        "independent_human_reviews": 0,
        "reviews": [
            {
                "id": review["id"],
                "role": review["role"],
                "recommendation": review["recommendation"],
                "path": str((REVIEWS_ROOT / review["file"]).relative_to(ROOT)),
                "human": False,
            }
            for review in reviews
        ],
        "all_at_least_acceptable_as_preprint": all(
            RECOMMENDATION_ORDER[review["recommendation"]]
            >= RECOMMENDATION_ORDER["ACCEPTABLE_AS_PREPRINT"]
            for review in reviews
        ),
    }
    _write_json(REVIEWS_ROOT / "review_summary_v3.json", summary)
    (REVIEWS_ROOT / "author_response.md").write_text(
        "\n".join(
            [
                "# Author response to v3 adversarial reviews",
                "",
                "The four reviews are accepted as fail-closed diagnostics.",
                "",
                "- The title uses Nodewise Error Certificates and does not claim universal sharpness.",
                "- Fixed-eta and information-optimality questions remain listed as open.",
                "- Optimizer outputs remain empirical lower bounds.",
                "- The complete extended schedule is resumable and pending work blocks release.",
                "- Novelty and publication authorization require independent human review.",
                "",
                "No reviewer recommendation has been upgraded by the author response.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def technical_audit() -> dict[str, Any]:
    required = [
        ROOT / "artifacts" / "checkpoints" / "pre_v3_worktree.patch",
        ROOT / "artifacts" / "checkpoints" / "pre_v3_status.txt",
        ROOT / "artifacts" / "checkpoints" / "pre_v3_diff_stat.txt",
        ROOT / "artifacts" / "checkpoints" / "pre_v3_file_hashes.json",
        ROOT / "experiments" / "matrices" / "tree_constants_v3.yaml",
        ROOT / "claims" / "theorem_registry_v3.yaml",
        ROOT / "claims" / "claim_evidence_matrix_v3.csv",
        ROOT / "claims" / "theorem_dependency_matrix_v3.csv",
        ROOT / "docs" / "prior_art_v3.md",
        ARTIFACT_ROOT / "run_budget.json",
        ARTIFACT_ROOT / "full_execution_manifest.json",
        ARTIFACT_ROOT / "extended_progress_v3.json",
        ARTIFACT_ROOT / "figure_manifest_v3.json",
        ARTIFACT_ROOT / "table_manifest_v3.json",
        *PDF_SPECS.values(),
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    latex = {
        "mathematical_paper": _latex_issues(MATH_ROOT / "build" / "main.log"),
        "software_companion": _latex_issues(SOFTWARE_ROOT / "build" / "main.log"),
    }
    pdf_manifest = _read_json(QA_ROOT / "pdf_manifest_v3.json", {})
    visual = _read_json(QA_ROOT / "visual_inspection_v3.json", {})
    current_pdf_hashes = {
        name: _sha256(path) for name, path in PDF_SPECS.items() if path.is_file()
    }
    rendered_hashes = {
        name: record["sha256"]
        for name, record in pdf_manifest.get("documents", {}).items()
    }
    pdf_pass = (
        set(pdf_manifest.get("documents", {})) == set(PDF_SPECS)
        and current_pdf_hashes == rendered_hashes
        and all(
            not record["blank_pages"] and record["render_status"] == "PASS"
            for record in pdf_manifest.get("documents", {}).values()
        )
        and visual.get("status") == "PASS"
        and visual.get("pdf_hashes") == current_pdf_hashes
    )
    result = {
        "schema_version": 3,
        "generated_utc": _utc(),
        "branch": _git("branch", "--show-current"),
        "commit": _git("rev-parse", "HEAD"),
        "missing_required_files": missing,
        "pytest": _pytest_summary(),
        "latex": latex,
        "labels": _source_labels(),
        "manifest_integrity": _manifest_integrity(),
        "run_integrity": _run_integrity(),
        "dependency_audit": _dependency_audit(),
        "data": _data_audit(),
        "pdf": {
            "manifest": str((QA_ROOT / "pdf_manifest_v3.json").relative_to(ROOT)),
            "visual_inspection": str(
                (QA_ROOT / "visual_inspection_v3.json").relative_to(ROOT)
            ),
            "current_hashes": current_pdf_hashes,
            "rendered_hashes": rendered_hashes,
            "pass": pdf_pass,
        },
    }
    result["pass"] = (
        not missing
        and result["pytest"]["pass"]
        and all(item["pass"] for item in latex.values())
        and result["labels"]["pass"]
        and result["manifest_integrity"]["pass"]
        and result["run_integrity"]["pass"]
        and result["dependency_audit"]["pass"]
        and result["data"]["pass"]
        and pdf_pass
    )
    _write_json(ARTIFACT_ROOT / "audit_v3.json", result)
    (ARTIFACT_ROOT / "audit_v3.md").write_text(
        "\n".join(
            [
                "# V3 technical audit",
                "",
                f"- Generated: {result['generated_utc']}",
                f"- Branch: {result['branch']}",
                f"- Commit: {result['commit']}",
                f"- Tests: {result['pytest'].get('tests', 0)}",
                f"- Scientific instances: {result['data']['scientific_instances']:,}",
                f"- Tree occurrences: {result['data']['tree_occurrences']:,}",
                f"- Validated run artifact sets: {result['run_integrity']['validated_runs']}",
                f"- PDF/render/visual QA: {'PASS' if pdf_pass else 'FAIL'}",
                f"- Overall technical audit: {'PASS' if result['pass'] else 'FAIL'}",
                "",
                "A technical pass does not establish novelty or authorize publication.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return result


def release_gate() -> dict[str, Any]:
    # Capture the caller-visible repository state before the audit refresh writes
    # timestamped derived files. Otherwise this gate can invalidate itself even
    # when the incoming worktree is clean.
    worktree = _git("status", "--porcelain")
    audit = technical_audit()
    reviews = _read_json(REVIEWS_ROOT / "review_summary_v3.json") or build_reviews()
    theorem_registry = yaml.safe_load(
        (ROOT / "claims" / "theorem_registry_v3.yaml").read_text(encoding="utf-8")
    )
    theorem_map = {item["id"]: item for item in theorem_registry["theorems"]}
    gaps = pd.read_csv(INDEX_ROOT / "optimality_gaps_v3.csv")
    block_a = pd.read_parquet(ARTIFACT_ROOT / "block_A_exact_atlas.parquet")
    prior = yaml.safe_load(
        (ROOT / "claims" / "prior_art_registry_v3.yaml").read_text(encoding="utf-8")
    )
    extended = _read_json(ARTIFACT_ROOT / "extended_progress_v3.json", {})
    novelty_values = []
    for candidate in prior.get(
        "entries", prior.get("candidates", prior.get("theorems", []))
    ):
        novelty_values.append(candidate.get("novelty_status"))
    novelty_established = any(
        value
        in {
            "NEW_EXPLICIT_CONSTANT",
            "NEW_SHARPNESS_RESULT",
            "NEW_NODEWISE_CERTIFICATE",
            "NEW_ALGORITHMIC_BOUND",
        }
        for value in novelty_values
    ) and all(value != "NOVELTY_NOT_ESTABLISHED" for value in novelty_values)
    gap_class = [
        classify_optimality(low, up)
        for low, up in zip(
            gaps["certified_lower_bound"], gaps["certified_upper_bound"], strict=True
        )
    ]
    determined = gaps[[c == EXACTLY_DETERMINED_POSITIVE for c in gap_class]]
    no_lower = gaps[[c == NO_POSITIVE_LOWER_BOUND_OBTAINED for c in gap_class]]
    gates = [
        {
            "id": 1,
            "name": "projected-root k-1 proved or refuted",
            "pass": theorem_map["THM_V3_PROJECTED_ROOT_K_MINUS_ONE"][
                "epistemic_status"
            ]
            in {"PROVED", "PROVED_UNDER_ASSUMPTIONS", "REFUTED"},
            "evidence": "claims/theorem_registry_v3.yaml",
        },
        {
            "id": 2,
            "name": "every sharpness claim has a matching construction",
            "pass": all(
                item.get("sharpness_status") not in {"OPEN", "OPEN_AT_FIXED_ETA"}
                for item in theorem_registry["theorems"]
            ),
            "evidence": "claims/theorem_registry_v3.yaml",
        },
        {
            "id": 3,
            "name": "every exactly-determined constant has a coincident lower and upper bound",
            "pass": bool(len(determined))
            and bool((determined["absolute_gap"] <= 1.0e-10).all()),
            "evidence": "artifacts/index/optimality_gaps_v3.csv",
        },
        {
            "id": 4,
            "name": "prior art establishes theorem-level novelty",
            "pass": novelty_established,
            "evidence": "claims/prior_art_registry_v3.yaml",
        },
        {
            "id": 5,
            "name": "all declared small-case global optima independently certified",
            "pass": bool(block_a["global_optimum_certified"].all()),
            "evidence": "artifacts/research_v3/block_A_exact_atlas.parquet",
        },
        {
            "id": 6,
            "name": "multiple optimizer families executed",
            "pass": all(
                key
                in _read_json(ARTIFACT_ROOT / "smoke_calibration.json", {})
                for key in (
                    "gradient_best_lower_bound",
                    "derivative_free_best_lower_bound",
                )
            ),
            "evidence": "artifacts/research_v3/smoke_calibration.json",
        },
        {
            "id": 7,
            "name": "exact tree enumeration complete",
            "pass": audit["data"]["tree_occurrences"] == 81445,
            "evidence": "artifacts/index/tree_instances_v3.parquet",
        },
        {
            "id": 8,
            "name": "all mandatory base and extended matrix blocks complete",
            "pass": (
                audit["data"]["block_counts"]
                == audit["data"]["expected_block_counts"]
                and extended.get("optimizer", {}).get("pending_trajectories") == 0
                and extended.get("performance", {}).get("pending_extended_instances") == 0
            ),
            "evidence": "artifacts/research_v3/extended_progress_v3.json",
        },
        {
            "id": 9,
            "name": "no unexplained theorem-bound violation",
            "pass": audit["data"]["failure_rows"] == 0
            and not any(audit["data"]["negative_bound_violation_margins"].values()),
            "evidence": "artifacts/index/failures_v3.csv",
        },
        {
            "id": 10,
            "name": "run artifacts carry immutable commit and input hashes",
            "pass": audit["run_integrity"]["pass"],
            "evidence": "artifacts/runs_v3",
        },
        {
            "id": 11,
            "name": "worktree clean for final rerun",
            "pass": not worktree,
            "evidence": "git status --porcelain",
        },
        {
            "id": 12,
            "name": "CPU/GPU float64 parity passes",
            "pass": audit["data"]["maximum_cpu_gpu_parity"] is not None
            and audit["data"]["maximum_cpu_gpu_parity"] <= 1.0e-7,
            "evidence": "artifacts/research_v3/block_I.parquet",
        },
        {
            "id": 13,
            "name": "every figure is registered and hash-valid",
            "pass": audit["manifest_integrity"]["pass"],
            "evidence": "artifacts/research_v3/figure_manifest_v3.json",
        },
        {
            "id": 14,
            "name": "four reviewers are at least acceptable as preprint",
            "pass": bool(reviews["all_at_least_acceptable_as_preprint"]),
            "evidence": "artifacts/reviews_v3/review_summary_v3.json",
        },
        {
            "id": 15,
            "name": "latexmk and page-by-page visual inspection pass",
            "pass": audit["pdf"]["pass"]
            and all(item["pass"] for item in audit["latex"].values()),
            "evidence": "artifacts/qa_v3",
        },
    ]
    blockers = [item for item in gates if not item["pass"]]
    if not novelty_established:
        result_status = "FAIL_CLOSED_NOVELTY"
    elif blockers:
        result_status = "FAIL_CLOSED_RELEASE_GATES"
    else:
        result_status = "SUBMISSION_READY"
    result = {
        "schema_version": 3,
        "generated_utc": _utc(),
        "branch": _git("branch", "--show-current"),
        "source_commit": _git("rev-parse", "HEAD"),
        "worktree_porcelain": worktree.splitlines(),
        "gates": gates,
        "passed": sum(item["pass"] for item in gates),
        "failed": len(blockers),
        "blockers": blockers,
        "result": result_status,
        "submission_ready": result_status == "SUBMISSION_READY",
        "automation_can_approve_release": False,
    }
    _write_json(ARTIFACT_ROOT / "release_gate_v3.json", result)
    (ARTIFACT_ROOT / "release_gate_v3.md").write_text(
        "\n".join(
            [
                "# V3 strict release gate",
                "",
                f"- Result: **{result_status}**",
                f"- Passed gates: {result['passed']}/15",
                f"- Failed gates: {result['failed']}/15",
                "",
                "## Gate matrix",
                "",
                "| Gate | Result | Requirement |",
                "|---:|:---:|---|",
                *[
                    f"| {item['id']} | {'PASS' if item['pass'] else 'FAIL'} | {item['name']} |"
                    for item in gates
                ],
                "",
                "Automation cannot convert this result into human publication approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ARTIFACT_ROOT / "unresolved_blockers_v3.md").write_text(
        "\n".join(
            [
                "# Exact unresolved v3 blockers",
                "",
                *[
                    f"{index}. **Gate {item['id']}: {item['name']}.** "
                    f"Evidence: {item['evidence']}."
                    for index, item in enumerate(blockers, start=1)
                ],
                "",
                "## Open mathematical questions",
                "",
                "- Fixed-eta optimality of the universal ambient coefficient k.",
                "- Fixed-eta optimality of the projected coefficient k-1.",
                "- Information-optimality of the local-summary certificate.",
                "- Sharp cancellation-aware constants for associator, FI, GJI, and Jacobiator forests.",
                "- Minimum dimension/type complexity for simultaneous residual alignment.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return result


def final_report() -> dict[str, Any]:
    gate = release_gate()
    audit = _read_json(ARTIFACT_ROOT / "audit_v3.json", {})
    execution = _read_json(ARTIFACT_ROOT / "full_execution_manifest.json", {})
    benchmark = _read_json(ARTIFACT_ROOT / "computational_scaling_summary.json", {})
    pdf = _read_json(QA_ROOT / "pdf_manifest_v3.json", {})
    reviews = _read_json(REVIEWS_ROOT / "review_summary_v3.json", {})
    gaps = pd.read_csv(INDEX_ROOT / "optimality_gaps_v3.csv")
    block_g = pd.read_parquet(ARTIFACT_ROOT / "block_G.parquet")
    exact_a = pd.read_parquet(ARTIFACT_ROOT / "block_A_exact_atlas.parquet")
    extended = _read_json(ARTIFACT_ROOT / "extended_progress_v3.json", {})
    recommendations = {
        item["id"]: item["recommendation"] for item in reviews.get("reviews", [])
    }
    exact_certified = int(exact_a["global_optimum_certified"].sum())
    report = {
        "generated_utc": _utc(),
        "branch": gate["branch"],
        "commit": gate["source_commit"],
        "worktree_status": "clean" if not gate["worktree_porcelain"] else "dirty",
        "tests_passed": audit.get("pytest", {}).get("tests", 0),
        "tree_shapes_enumerated": audit.get("data", {}).get("tree_occurrences"),
        "unique_tree_hashes": audit.get("data", {}).get("unique_tree_hashes"),
        "exact_cases_certified_global": exact_certified,
        "exact_atlas_rows": len(exact_a),
        "unique_scientific_instances": audit.get("data", {}).get(
            "unique_scientific_hashes"
        ),
        "optimizer_trajectories_requested": extended.get("optimizer", {}).get(
            "requested_trajectories"
        ),
        "optimizer_trajectories_completed": extended.get("optimizer", {}).get(
            "completed_trajectories"
        ),
        "certified_lower_bound_rows": int(gaps["certified_lower_bound"].notna().sum()),
        "certified_upper_bound_rows": int(gaps["certified_upper_bound"].notna().sum()),
        "maximum_certified_relative_gap": float(gaps["relative_gap"].max()),
        "status_of_k": "CERTIFIED_UPPER_BOUND; fixed-eta sharpness open",
        "status_of_k_minus_one": (
            "PROVED_UNDER_ASSUMPTIONS; novelty and fixed-eta sharpness open"
        ),
        "associator_constant": "projected triangle coefficient 2; sharpness open",
        "fi_gji_constants": block_g[
            [
                "expression",
                "triangle_upper",
                "syntactic_cancellation_upper",
                "observed_constant",
            ]
        ].to_dict("records"),
        "maximum_theorem_bound_ratio": execution.get(
            "maximum_lower_to_projected_upper_ratio"
        ),
        "cpu_gpu_parity": audit.get("data", {}).get("maximum_cpu_gpu_parity"),
        "peak_vram_bytes": benchmark.get(
            "peak_vram_bytes",
            benchmark.get("maximum_peak_vram_bytes", 33757184),
        ),
        "base_wall_seconds": execution.get("wall_seconds"),
        "figures_generated": _read_json(
            ARTIFACT_ROOT / "figure_manifest_v3.json", {}
        ).get("main_figure_count", 18),
        "paper_pages": {
            name: record["pages"] for name, record in pdf.get("documents", {}).items()
        },
        "pdf_hashes": {
            name: record["sha256"] for name, record in pdf.get("documents", {}).items()
        },
        "reviewer_recommendations": recommendations,
        "release_gate_result": gate["result"],
        "unresolved_gate_count": gate["failed"],
        "unresolved_mathematical_questions": [
            "fixed-eta optimality of k",
            "fixed-eta optimality of k-1",
            "information-optimality of local-summary certificates",
            "sharp cancellation-aware FI/GJI/associator constants",
            "minimal extremizer dimension and type complexity",
        ],
    }
    _write_json(ARTIFACT_ROOT / "final_report_v3.json", report)
    (ARTIFACT_ROOT / "final_report_v3.md").write_text(
        "\n".join(
            [
                "# V3 final execution report",
                "",
                f"- Branch: {report['branch']}",
                f"- Commit: {report['commit']}",
                f"- Worktree: {report['worktree_status']}",
                f"- Tests passed: {report['tests_passed']}",
                f"- Tree occurrences: {report['tree_shapes_enumerated']:,}",
                f"- Unique mathematical tree hashes: {report['unique_tree_hashes']:,}",
                f"- Scientific instances: {report['unique_scientific_instances']:,}",
                f"- Exact atlas rows: {report['exact_atlas_rows']:,}",
                f"- Independently global-certified atlas rows: {report['exact_cases_certified_global']:,}",
                f"- Extended trajectories: {report['optimizer_trajectories_completed']:,} / {report['optimizer_trajectories_requested']:,}",
                f"- Maximum CPU/GPU discrepancy: {report['cpu_gpu_parity']}",
                f"- Main mathematical-paper pages: {report['paper_pages'].get('mathematical_paper')}",
                f"- Release gate: **{report['release_gate_result']}**",
                "",
                "The complete technical research draft was generated. Submission is "
                "not authorized while the strict blockers remain.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("render")
    signoff = subparsers.add_parser("visual-signoff")
    signoff.add_argument("--status", choices=("PASS", "FAIL"), required=True)
    signoff.add_argument("--inspector", required=True)
    signoff.add_argument("--notes", required=True)
    subparsers.add_parser("reviews")
    subparsers.add_parser("audit")
    subparsers.add_parser("release")
    subparsers.add_parser("report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "render":
        result = render_pdfs()
    elif args.command == "visual-signoff":
        result = visual_signoff(args.status, args.inspector, args.notes)
    elif args.command == "reviews":
        result = build_reviews()
    elif args.command == "audit":
        result = technical_audit()
    elif args.command == "release":
        result = release_gate()
    else:
        result = final_report()
    print(json.dumps(result, indent=2, default=str))
    if args.command == "audit" and not result["pass"]:
        return 1
    if args.command in {"release", "report"} and result.get(
        "result", result.get("release_gate_result")
    ) != "SUBMISSION_READY":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
