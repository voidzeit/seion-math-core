from __future__ import annotations

import json
from pathlib import Path

import yaml


ALLOWED_CLAIM_STATUSES = {
    "definition", "proved", "proved_under_assumptions", "symbolically_verified",
    "numerically_verified", "empirical", "heuristic", "conjecture", "open", "refuted", "superseded",
}


def load_yaml_registry(path: str | Path) -> list[dict]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if value is None:
        return []
    if isinstance(value, dict) and "claims" in value:
        value = value["claims"]
    if not isinstance(value, list):
        raise ValueError(f"registry {path} must contain a list or claims key")
    for record in value:
        if record.get("status") not in ALLOWED_CLAIM_STATUSES:
            raise ValueError(f"unsupported claim status: {record.get('status')}")
    return value


def claims_lint(repo_root: str | Path) -> dict:
    root = Path(repo_root)
    registry = load_yaml_registry(root / "claims" / "claims_registry.yaml")
    return {"claims": len(registry), "invalid_statuses": [], "passed": True}

