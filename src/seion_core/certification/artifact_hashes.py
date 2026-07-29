from __future__ import annotations

import hashlib
import json
from pathlib import Path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_artifacts(directory: str | Path) -> dict[str, str]:
    directory = Path(directory)
    hashes = {}
    for path in sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "artifact_hashes.json"):
        hashes[str(path.relative_to(directory)).replace("\\", "/")] = hash_file(path)
    (directory / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    return hashes

