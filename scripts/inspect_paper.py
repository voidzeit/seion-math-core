"""Render the paper and write a machine-readable layout inspection report."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper" / "build" / "main.pdf"
PAGES = ROOT / "artifacts" / "paper_render" / "pages"


def main() -> int:
    if not PDF.exists():
        print(f"missing PDF: {PDF}")
        return 1
    PAGES.mkdir(parents=True, exist_ok=True)
    # pdftoppm writes hyphenated names; the normalized files use underscores.
    # Remove both forms so a shorter rebuilt PDF cannot inherit stale pages.
    for pattern in ("page-*.png", "page_*.png"):
        for old in PAGES.glob(pattern):
            old.unlink()
    render_command = ["pdftoppm", "-png", "-r", "150", str(PDF), str(PAGES / "page")]
    result = subprocess.run(render_command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return result.returncode
    rendered = sorted(PAGES.glob("page-*.png"))
    for index, path in enumerate(rendered, start=1):
        target = PAGES / f"page_{index:03d}.png"
        if path != target:
            path.replace(target)
    rendered = sorted(PAGES.glob("page_*.png"))
    contact = ROOT / "artifacts" / "paper_render" / "contact_sheet.png"
    try:
        from PIL import Image, ImageDraw
        images = [Image.open(path).convert("RGB") for path in rendered]
        thumb_width = 280
        thumbs = []
        for image in images:
            ratio = thumb_width / image.width
            thumbs.append(image.resize((thumb_width, max(1, int(image.height * ratio)))))
        columns = 3
        rows = (len(thumbs) + columns - 1) // columns
        cell_h = max((image.height for image in thumbs), default=1) + 24
        sheet = Image.new("RGB", (columns * thumb_width, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for index, image in enumerate(thumbs):
            x = (index % columns) * thumb_width
            y = (index // columns) * cell_h
            sheet.paste(image, (x, y + 20))
            draw.text((x + 4, y + 2), f"page {index + 1}", fill="black")
        sheet.save(contact)
    except Exception as exc:
        contact.write_text(f"contact sheet unavailable: {exc}\n", encoding="utf-8")
    report = {
        "pdf": str(PDF),
        "page_count": len(rendered),
        "pdf_size_bytes": PDF.stat().st_size,
        "render_command": render_command,
        "rendered_pages": [str(path) for path in rendered],
        "visual_gate": "rendered_pages_available",
        "manual_inspection_required": True,
        "warnings": ["Automated rendering cannot prove absence of all visual defects; contact_sheet.png is retained for inspection."],
    }
    log_path = ROOT / "paper" / "build" / "main.log"
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    issues = []
    if re.search(r"Undefined (references|citations)|Citation .* undefined|LaTeX Error|File .* not found", log_text, re.IGNORECASE):
        issues.append("log contains an undefined reference/citation, LaTeX error, or missing file")
    if "destination with the same identifier" in log_text:
        issues.append("log contains duplicate hyperref destinations")
    for match in re.finditer(r"Overfull \\hbox \(([0-9.]+)pt", log_text):
        if float(match.group(1)) > 5.0:
            issues.append(f"overfull box exceeds 5pt: {match.group(1)}pt")
    report["log_issues"] = issues
    report["visual_gate"] = "PASS_RENDER_AND_LOG" if not issues else "FAIL_LOG_GATE"
    target = ROOT / "artifacts" / "paper_render" / "render_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
