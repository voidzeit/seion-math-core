"""Explicit contract for the fixed-eta ``k>=4`` PMT frontier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class K4Frontier:
    """A fail-closed description of what is known for fixed-eta ``k=4``."""

    status: str = "OPEN_PROBLEM"
    universal_upper_coefficient: str = "k - 1 = 3"
    exact_constant: None = None
    allowed_evidence: tuple[str, ...] = (
        "PROVED_UPPER_BOUND",
        "CERTIFIED_LOWER_BOUND",
        "NUMERICAL_OBSERVATION",
        "CONJECTURE",
    )
    forbidden_upgrade: str = "A finite numerical search cannot set exact_constant."


K4_FRONTIER = K4Frontier()


def k4_frontier(*, observation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a serializable open-problem record, preserving observations.

    ``observation`` is intentionally copied under a separate key and never
    promoted to a constant.  This is the API boundary for future k=4 searches.
    """

    record = {
        "status": K4_FRONTIER.status,
        "universal_upper_coefficient": K4_FRONTIER.universal_upper_coefficient,
        "exact_constant": None,
        "epistemic_rule": K4_FRONTIER.forbidden_upgrade,
    }
    if observation is not None:
        record["observation"] = dict(observation)
        record["observation_status"] = "NUMERICAL_OBSERVATION"
    return record
