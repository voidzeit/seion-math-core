"""Deterministic action gates; automation recommends, humans approve releases."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import AUTHORITY_RANK


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "governance" / "ACTION_POLICY.yaml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def evaluate_action(
    repo_root: str | Path,
    *,
    action: str,
    risk: str = "medium",
    evidence_authority: str = "declared",
    human_approval: bool = False,
    checks: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    policy = _load_policy(root)
    action_name = _normalize(action)
    risk_name = _normalize(risk)
    evidence_name = _normalize(evidence_authority)
    reasons: list[str] = []
    prohibited = {_normalize(item) for item in policy.get("prohibited", [])}
    if action_name in prohibited:
        reasons.append(f"action is prohibited by governance policy: {action_name}")
    if action_name in {"claim_numerical_proof", "numerical_to_proof"}:
        reasons.append("numerical evidence cannot be relabeled as proof")
    risks = policy.get("risk_levels", {})
    risk_config = risks.get(risk_name, {}) if isinstance(risks, dict) else {}
    if not risk_config:
        reasons.append(f"unknown risk level: {risk_name}")
    required_authority = str(risk_config.get("minimum_authority", "declared"))
    if AUTHORITY_RANK.get(evidence_name, -1) < AUTHORITY_RANK.get(required_authority, 99):
        reasons.append(
            f"evidence authority {evidence_name!r} is below required {required_authority!r}"
        )
    requires_human = bool(risk_config.get("human_approval", False))
    special = policy.get("special_rules", {}).get(action_name, {})
    if isinstance(special, dict):
        special_authority = str(special.get("minimum_authority", required_authority))
        if AUTHORITY_RANK.get(evidence_name, -1) < AUTHORITY_RANK.get(special_authority, 99):
            reasons.append(
                f"action requires authority {special_authority!r}, received {evidence_name!r}"
            )
        requires_human = requires_human or bool(special.get("human_approval", False))
        for check in special.get("required_checks", []):
            if not (checks or {}).get(check, False):
                reasons.append(f"required check has not been supplied as passed: {check}")
    if requires_human and not human_approval:
        reasons.append("explicit human approval is required")
    allowed = not reasons
    return {
        "action": action_name,
        "risk": risk_name,
        "evidence_authority": evidence_name,
        "required_authority": required_authority,
        "human_approval": human_approval,
        "allowed": allowed,
        "authority_granted": "approved" if allowed and human_approval else evidence_name if allowed else None,
        "reasons": reasons,
        "checks": dict(checks or {}),
        "ai_advisory_only": bool(policy.get("ai_advisory_only", True)),
    }
