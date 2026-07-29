from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


AUTHORITY_RANK = {"declared": 0, "observed": 1, "verified": 2, "approved": 3}
RUN_STATUS_RANK = {
    "COMPLETE": 4,
    "COMPLETE_WITH_WARNINGS": 3,
    "RECOVERED": 2,
    "NONCOMPARABLE": 1,
    "INTERRUPTED": 0,
    "FAILED_MATHEMATICAL_GATE": 0,
    "FAILED_NUMERICAL_GATE": 0,
    "FAILED_RUNTIME": 0,
}


@dataclass(frozen=True)
class GovernanceIssue:
    severity: str
    code: str
    message: str
    paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "paths": list(self.paths),
        }


@dataclass
class RunRecord:
    run_id: str
    experiment_id: str
    status: str
    epistemic_status: str | None
    precision: str | None
    seed: int | None
    backend: str | None
    device: str | None
    created_utc: str | None
    run_path: str
    config_fingerprint: str
    metrics: dict[str, Any] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)
    missing_artifacts: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str, str, str, str, str]:
        """Scientific identity; repeated attempts with the same key are not new seeds."""
        return (
            self.experiment_id,
            self.config_fingerprint,
            "" if self.seed is None else str(self.seed),
            self.precision or "",
            self.backend or "",
            self.device or "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "status": self.status,
            "epistemic_status": self.epistemic_status,
            "precision": self.precision,
            "seed": self.seed,
            "backend": self.backend,
            "device": self.device,
            "created_utc": self.created_utc,
            "run_path": self.run_path,
            "config_fingerprint": self.config_fingerprint,
            "missing_artifacts": list(self.missing_artifacts),
            "metrics": self.metrics,
        }
