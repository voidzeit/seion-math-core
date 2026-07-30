"""Render v4 PDFs to PNG previews and emit page/hash metadata."""
from __future__ import annotations
import hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    out = ROOT / "output/pdf"; render = out / "rendered_pages"; render.mkdir(parents=True, exist_ok=True)
    specs = [("mathematical", ROOT / "papers/tree_stability_v4/build/main.pdf"), ("software", ROOT / "papers/software_v4/build/main.pdf"), ("supplement", ROOT / "papers/supplement_v4/build/main.pdf")]
    rows = []
    for name, source in specs:
        target = out / f"seion-math-core-v4-{name}.pdf"
        if source.exists():
            shutil.copy2(source, target)
            prefix = render / name
            cmd = ["pdftoppm", "-png", "-r", "60", str(target), str(prefix)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            rows.append({"name": name, "source": str(source.relative_to(ROOT)), "path": str(target.relative_to(ROOT)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "full_render_exit": result.returncode, "rendered_page_count": len(list(render.glob(name + "-*.png")))})
        else: rows.append({"name": name, "status": "MISSING"})
    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(), "pdfs": rows, "render_policy": "all pages rendered to PNG; full-page visual and accessibility approval remains a human gate"}
    (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "RENDER_AUDIT.md").write_text("# v4 PDF render audit\n\n" + json.dumps(manifest, indent=2) + "\n\nFull visual approval remains a human gate.\n", encoding="utf-8")
    return 0 if all(row.get("full_render_exit", 1) == 0 for row in rows if "full_render_exit" in row) else 2
if __name__ == "__main__": raise SystemExit(main())
