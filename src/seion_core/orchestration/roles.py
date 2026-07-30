"""Loads governance/agents/*.yaml role manifests and binds them to
lifecycle stages via each manifest's `stages` field."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RoleManifest:
    agent_id: str
    role: str
    authority: str
    stages: tuple[str, ...]
    reads: tuple[str, ...]
    may_change: tuple[str, ...]
    must_not: tuple[str, ...]
    required_outputs: tuple[str, ...]
    path: Path


def load_roles(repo_root: str | Path) -> list[RoleManifest]:
    root = Path(repo_root)
    agents_dir = root / "governance" / "agents"
    roles: list[RoleManifest] = []
    for path in sorted(agents_dir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        agent_id = doc.get("agent_id") or doc.get("role") or path.stem
        roles.append(
            RoleManifest(
                agent_id=agent_id,
                role=doc.get("role", ""),
                authority=doc.get("authority", "declared"),
                stages=tuple(doc.get("stages", ())),
                reads=tuple(doc.get("reads", ())),
                may_change=tuple(doc.get("may_change") or doc.get("writes") or ()),
                must_not=tuple(doc.get("must_not") or doc.get("prohibitions") or ()),
                required_outputs=tuple(doc.get("required_outputs") or doc.get("evidence") or ()),
                path=path,
            )
        )
    return roles


def roles_for_stage(repo_root: str | Path, stage_key: str) -> list[RoleManifest]:
    return [r for r in load_roles(repo_root) if stage_key in r.stages]
