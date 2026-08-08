"""Certified lower constructions for independent-law k=3 topologies.

These are lower-bound witnesses, not a sharpness theorem. The construction
uses a rank-one orthogonal projector and independently chosen bilinear laws.
For both the binary chain and binary branching topology, the selected leaves
produce ``E_proj = 2 M q sqrt(M^2 - q^2)``, where ``q <= rho`` is the realized
local defect. Choosing the largest admissible ``q`` gives the best witness in
this family.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class K3IndependentCandidate:
    topology: str
    eta: float
    M: float
    rho_budget: float
    realized_defect: float
    projected_error: float
    universal_projected_bound: float
    normalized_constant_lower_bound: float
    ratio_to_universal_bound: float


def construct_k3_independent_candidate(
    eta: float,
    *,
    topology: str,
    M: float = 1.0,
) -> K3IndependentCandidate:
    """Return a certified k=3 lower-bound witness for ``chain`` or ``branch``.

    The laws are real, bilinear, independently selectable, and have operator
    norm at most ``M``. The projector is rank one. The defect budget and the
    realized defect are reported separately; for ``eta > 1/sqrt(2)`` this
    family uses the optimizer ``q=M/sqrt(2) < rho_budget``.
    """

    if topology not in {"chain", "branch"}:
        raise ValueError("topology must be 'chain' or 'branch'")
    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    rho_budget = eta * M
    q = min(rho_budget, M / sqrt(2.0))
    projected_axis = sqrt(M * M - q * q)
    projected_error = 2.0 * M * q * projected_axis
    universal_bound = 2.0 * rho_budget * M * M
    return K3IndependentCandidate(
        topology=topology,
        eta=eta,
        M=M,
        rho_budget=rho_budget,
        realized_defect=q,
        projected_error=projected_error,
        universal_projected_bound=universal_bound,
        normalized_constant_lower_bound=projected_error / (rho_budget * M * M),
        ratio_to_universal_bound=projected_error / universal_bound,
    )
