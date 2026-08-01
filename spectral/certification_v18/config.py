"""v18 audit configuration.

Genuine redesign, not a rename of v17's `AuditConfig`
(`spectral/legacy/v17/seion_master_audit_A_to_N_v17_blackwell_repro_fix.py`,
class at ~line 571). The key structural difference: `eval_mode` here is a
hard contract enforced by `validate()`, not a label that only loosens
thresholds (see `thresholds_for_mode` in the legacy script, which was the
*only* place screening vs certification actually differed in v17).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvalMode(str, Enum):
    SCREENING = "screening"
    CERTIFICATION = "certification"


class Dtype(str, Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    COMPLEX64 = "complex64"
    COMPLEX128 = "complex128"


_CERTIFICATION_REQUIRED_DTYPES = {Dtype.FLOAT64, Dtype.COMPLEX128}


class ConfigValidationError(ValueError):
    pass


@dataclass
class AuditConfigV18:
    seed: int
    device: str
    dtype: Dtype
    eval_mode: EvalMode

    # Ambient problem dimensions (same intent as v17, kept for continuity).
    n: int = 24
    n_hi: int | None = None
    rank: int = 6
    arity: int = 3
    cp_rank: int = 6
    hi_cp_rank: int | None = None

    # Reproducibility contract. Defaults intentionally differ from v17
    # (which defaulted restore_rng=False, strict_resume=False and never had
    # a run in the historical log override them — see
    # spectral/legacy/v17/legacy_claim_reclassification.yaml).
    restore_rng: bool = True
    strict_resume: bool = True
    resume: bool = False
    resume_path: str | None = None
    resume_optimizer: bool = True

    # A seed that was never used for any training/optimization step in this
    # run's lineage; required non-empty for STATISTICALLY_VALIDATED_PASS or
    # higher on any stochastic-trial block (G, H, N).
    held_out_seeds: tuple[int, ...] = field(default_factory=tuple)

    # Certification-mode hardware/determinism contract.
    tf32_disabled: bool = True
    deterministic_algorithms: bool = True

    steps: int = 1200
    lr: float = 1e-3

    def validate(self) -> None:
        errors: list[str] = []
        if self.eval_mode == EvalMode.CERTIFICATION:
            if self.dtype not in _CERTIFICATION_REQUIRED_DTYPES:
                errors.append(
                    f"certification mode requires dtype in {sorted(d.value for d in _CERTIFICATION_REQUIRED_DTYPES)}, got {self.dtype.value}"
                )
            if not self.tf32_disabled:
                errors.append("certification mode requires tf32_disabled=True")
            if not self.deterministic_algorithms:
                errors.append("certification mode requires deterministic_algorithms=True")
            if self.resume and not self.restore_rng:
                errors.append("certification mode forbids resume with restore_rng=False")
            if self.resume and not self.strict_resume:
                errors.append("certification mode forbids resume with strict_resume=False")
            if not self.held_out_seeds:
                errors.append(
                    "certification mode requires at least one held_out_seeds entry distinct "
                    "from the training seed"
                )
            if self.seed in self.held_out_seeds:
                errors.append("training seed must not also appear in held_out_seeds")
        if errors:
            raise ConfigValidationError(
                f"AuditConfigV18 failed validation for eval_mode={self.eval_mode.value}: "
                + "; ".join(errors)
            )
