from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CertificateStatus:
    code: str
    reason: str
    epistemic_status: str


VALID_STATUSES = {
    "COMPLETE",
    "COMPLETE_WITH_WARNINGS",
    "FAILED_MATHEMATICAL_GATE",
    "FAILED_NUMERICAL_GATE",
    "FAILED_RUNTIME",
    "INTERRUPTED",
    "RECOVERED",
    "NONCOMPARABLE",
}

