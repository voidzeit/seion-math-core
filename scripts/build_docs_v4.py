"""Build a dependency-free local documentation site when MkDocs is unavailable."""
from __future__ import annotations
import html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    out = ROOT / "artifacts/docs_site"; out.mkdir(parents=True, exist_ok=True)
    docs = sorted((ROOT / "docs").rglob("*.md"))
    links = []
    for path in docs:
        rel = path.relative_to(ROOT / "docs").as_posix()
        target = out / (rel.replace("/", "__") + ".html")
        target.write_text("<meta charset='utf-8'><title>SEION</title><pre>" + html.escape(path.read_text(encoding="utf-8", errors="replace")) + "</pre>", encoding="utf-8")
        links.append(f"<li><a href='{target.name}'>{html.escape(rel)}</a></li>")
    (out / "index.html").write_text("<meta charset='utf-8'><title>SEION v4 documentation</title><h1>SEION v4 documentation</h1><p>Generated local site.</p><ul>" + "".join(links) + "</ul>", encoding="utf-8")
    (out / "BUILD_STATUS.md").write_text("# Documentation build\n\nDependency-free fallback completed. MkDocs availability is recorded by the campaign.\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
