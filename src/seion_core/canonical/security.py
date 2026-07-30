"""Small, deterministic local security and provenance checks."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def scan_secrets(root: Path) -> dict[str, object]:
    findings = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in {".git", "node_modules", "build", "dist", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".yaml", ".yml", ".json", ".md", ".toml", ".ps1", ".sh", ".tex"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS) and "example" not in path.name.lower() and "placeholder" not in line.lower():
                findings.append({"path": str(path.relative_to(root)), "line": number})
    return {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "findings": findings, "status": "PASS" if not findings else "BLOCKED_SECRET_FINDINGS"}


def build_sbom(root: Path, output: Path) -> dict[str, object]:
    dependencies = []
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        dependencies = [line.strip().strip('"').strip("'").rstrip(",") for line in text.splitlines() if line.strip().startswith('"') and ">=" in line]
    value = {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1, "metadata": {"timestamp": datetime.now(timezone.utc).isoformat(), "component": {"type": "application", "name": "seion-math-core", "version": "0.4.0"}}, "components": [{"type": "library", "name": dep.split(">=")[0], "version": dep.split(">=")[1]} for dep in dependencies if ">=" in dep]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def checksum_files(paths: list[Path], output: Path, root: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for path in sorted(paths):
        if path.exists() and path.is_file():
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
