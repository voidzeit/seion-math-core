"""Gate 13.4 (``campaigns/gate13/``): certified operator-norm/Lipschitz
bounds for the path reasoner's message function and nonlinear envelope.

Closes the gap `certification.py` (Phase B4) documented honestly as
missing: "no certified operator-norm bound on closure leakage or the
nonlinear envelope's Lipschitz constant exists yet anywhere in this
repo." This module provides both, scoped to how THIS codebase's
projector actually works.

**Architecture note — why there is no separate P_x/P_a/P_q here:** the
mission brief's general closure-bound template assumes independent
input-side projectors on ``x``, ``a``, ``q`` in addition to an output-side
one. `PathReasoner`/`BatchedPathReasoner` only ever construct ONE
`StiefelProjector`, applied to the message's OUTPUT
(`message() = projector.apply(mu(x,a,q) + U(x) + V(a) + W(q))`) — `x`,
`a`, `q` themselves are never projected before entering `mu`/`U`/`V`/`W`.
So `P_x = P_a = P_q = I` identically in this architecture, and the
general formula's input-projector norm factors are `||I||_2 = 1` — not
omitted, just architecturally trivial. Every bound below reflects this
directly rather than carrying dead `* 1` factors.

**Reference vs. compressed pair:** `F_ref` = a trained checkpoint's path
reasoner with its projector DISABLED (`proj_rank=0`, so `P_o = 0`,
`(I - P_o) = I`); `F_cmp` = the SAME weights (`mu`/`U`/`V`/`W`/embeddings
unchanged) with a projector ADDED post-hoc at some `rank < dim` — never
two independently trained models (mission brief's own instruction).

Four strictly separate result types (mission brief's "Nunca permitas
convertir implícitamente un proxy en `CertifiedBound`"): a proxy can
never satisfy `CertifiedBound`'s type signature by accident — call sites
that need a certified value must receive a `CertifiedBound` instance, not
a bare float.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import torch
import torch.nn as nn

from .certification import AssumptionCheck, operator_norm
from .kernels import CPTernaryLaw, StiefelProjector

BOUND_FORMULA_VERSION = "gate13.4-v1"


@dataclass(frozen=True)
class CertifiedBound:
    """A number that IS a mathematically valid upper bound under the
    ``assumptions`` recorded alongside it — ``valid()`` must be checked
    (or ``require_valid()`` called) before using ``value`` for anything;
    a bound whose assumptions failed is not silently still "a bound"."""

    value: float
    formula: str
    assumptions: List[AssumptionCheck] = field(default_factory=list)

    def valid(self) -> bool:
        return all(a.passed for a in self.assumptions)

    def require_valid(self) -> float:
        if not self.valid():
            failed = [a.name for a in self.assumptions if not a.passed]
            raise ValueError(f"CertifiedBound({self.formula!r}) used with failed assumptions: {failed}")
        return self.value


@dataclass(frozen=True)
class ObservedError:
    """A directly measured discrepancy between two actually-computed
    quantities — not an estimate of anything."""

    value: float
    description: str


@dataclass(frozen=True)
class EmpiricalMajorant:
    """A measured proxy that has never been proved to be an upper bound
    (may fail on unseen inputs); reported ALONGSIDE a `CertifiedBound`,
    never substituted for one."""

    value: float
    description: str


@dataclass(frozen=True)
class EmpiricalErrorPredictor:
    """Same tier as `EmpiricalMajorant`, specifically for a sample-based
    proxy of a quantity that also has a certified counterpart elsewhere
    (e.g. `measure_closure_leakage_sample` in `projection.py`) — never an
    operator-norm certificate."""

    value: float
    description: str


def _identity_minus_output_projection(weight: torch.Tensor, projector: Optional[StiefelProjector]) -> torch.Tensor:
    """``(I - P_o) @ weight``. ``P_o = 0`` (no projection at all) when the
    projector is absent/disabled — the REFERENCE, uncompressed case — so
    this returns ``weight`` unchanged, giving the full (uncompressed)
    operator norm, never a silently-zeroed one."""
    if projector is None or not projector.enabled:
        return weight
    p = projector.P()
    eye = torch.eye(p.shape[0], device=weight.device, dtype=weight.dtype)
    return (eye - p) @ weight


def check_projector_gate1(projector: Optional[StiefelProjector], tol: float = 1e-4) -> List[AssumptionCheck]:
    """Gate-1 identities (`Q^T Q = I`, `P^2 = P`) PLUS a symmetry check
    (`P = P^T`) that `StiefelProjector.P() = Q Q^T` always satisfies by
    construction, but which an artificially-constructed OBLIQUE projector
    (idempotent but not self-adjoint) would fail — the mission brief's
    negative control #4. The closure/residual bounds below are valid
    operator-norm submultiplicativity facts regardless of whether `P` is
    an exact projector (they hold for ANY matrix `(I-P)`), but an oblique
    `P` breaks the orthogonal-complement geometry the certification
    pipeline's downstream reasoning assumes, so it is rejected here at the
    assumption-check layer, not silently accepted.

    ``tol=1e-4``, not a stricter value: a real-run finding while building
    Gate 13.4 -- genuine, correctly-constructed StiefelProjectors
    routinely show FP32 isometry_residual/idempotent_residual up to
    ~1.4e-6 (QR decomposition's own floating-point error, surveyed across
    30 seeds x 4 (dim, rank) pairs), so a stricter tolerance like 1e-6
    rejects mathematically valid projectors as a false negative -- this
    was caught by an end-to-end real-checkpoint certification run
    returning zero coverage for a reason that turned out to be tolerance
    miscalibration, not a bound or model problem. An oblique (genuinely
    non-symmetric) projector's symmetry_residual is orders of magnitude
    larger than this (see the oblique-projector negative control test),
    so raising the tolerance here does not weaken that rejection."""
    if projector is None or not projector.enabled:
        return [AssumptionCheck("projector_full_rank_or_absent", True, None, None, "no rank-reducing projector in the score path")]
    iso = projector.isometry_residual()
    idem = projector.idempotent_residual()
    p = projector.P()
    symmetry_residual = float(torch.linalg.norm(p - p.T).item())
    return [
        AssumptionCheck("isometry_residual", iso < tol, iso, tol, "Q^T Q = I (Gate 1)"),
        AssumptionCheck("idempotent_residual", idem < tol, idem, tol, "P^2 = P (Gate 1)"),
        AssumptionCheck("projector_symmetric", symmetry_residual < tol, symmetry_residual, tol, "P = P^T (rejects oblique projectors)"),
    ]


def cp_closure_bound(law: CPTernaryLaw, projector: Optional[StiefelProjector]) -> CertifiedBound:
    """``rho_mu <= ||(I-P_o)O||_2 * ||A||_2 * ||B||_2 * ||C||_2`` (the
    input-projector factors are identically 1, see module docstring)."""
    reduced_O = _identity_minus_output_projection(law.O.weight.detach(), projector)
    value = (
        operator_norm(reduced_O) * operator_norm(law.A.weight)
        * operator_norm(law.B.weight) * operator_norm(law.C.weight)
    )
    return CertifiedBound(
        value=value, formula="rho_mu = ||(I-P_o)O||_2 ||A||_2 ||B||_2 ||C||_2",
        assumptions=check_projector_gate1(projector),
    )


def linear_residual_bound(layer: nn.Linear, projector: Optional[StiefelProjector], name: str) -> CertifiedBound:
    """``rho_{U,V,W} <= ||(I-P_o) {U,V,W}||_2``."""
    reduced = _identity_minus_output_projection(layer.weight.detach(), projector)
    return CertifiedBound(
        value=operator_norm(reduced), formula=f"rho_{name} = ||(I-P_o){name}||_2",
        assumptions=check_projector_gate1(projector),
    )


@dataclass(frozen=True)
class MessageClosureBound:
    total: CertifiedBound
    mu: CertifiedBound
    residual_U: CertifiedBound
    residual_V: CertifiedBound
    residual_W: CertifiedBound


def message_closure_bound(
    law: CPTernaryLaw, U: nn.Linear, V: nn.Linear, W: nn.Linear, projector: Optional[StiefelProjector],
) -> MessageClosureBound:
    """``rho_message <= rho_mu + rho_U + rho_V + rho_W``. Every term is
    reported individually (mission brief: "no publiques únicamente la
    suma"), not just the total."""
    rho_mu = cp_closure_bound(law, projector)
    rho_U = linear_residual_bound(U, projector, "U")
    rho_V = linear_residual_bound(V, projector, "V")
    rho_W = linear_residual_bound(W, projector, "W")
    total_value = rho_mu.value + rho_U.value + rho_V.value + rho_W.value
    total = CertifiedBound(
        value=total_value, formula="rho_message = rho_mu + rho_U + rho_V + rho_W",
        assumptions=rho_mu.assumptions,  # identical projector -> identical assumption set
    )
    return MessageClosureBound(total=total, mu=rho_mu, residual_U=rho_U, residual_V=rho_V, residual_W=rho_W)


def message_sensitivity_bound_global(law: CPTernaryLaw, U: nn.Linear) -> CertifiedBound:
    """``L_message,x <= ||O|| ||A|| ||B|| ||C|| + ||U||`` — worst case over
    ANY unit-norm ``a``, ``q`` (uses ``||B||``/``||C||`` themselves, not a
    specific edge's ``Ba``/``Cq``). No assumptions beyond the weights
    existing — always valid, but typically loose."""
    L_mu_x = operator_norm(law.O.weight) * operator_norm(law.A.weight) * operator_norm(law.B.weight) * operator_norm(law.C.weight)
    value = L_mu_x + operator_norm(U.weight)
    return CertifiedBound(value=value, formula="L_message,x <= ||O|| ||A|| ||B|| ||C|| + ||U|| (global)", assumptions=[])


def message_sensitivity_bound_query_conditioned(
    law: CPTernaryLaw, U: nn.Linear, a_edge: torch.Tensor, q_query: torch.Tensor,
) -> CertifiedBound:
    """``L_message,x(a,q) <= ||O|| ||A|| ||Ba|| ||Cq|| + ||U||`` — uses the
    REAL ``||B(a_edge)||``/``||C(q_query)||`` for this specific edge/query
    batch (max over the batch), tighter than the global variant whenever
    the actual relation/query embeddings have norm below the worst case
    ``||B||``/``||C||`` would assume."""
    with torch.no_grad():
        Ba_norm = float(torch.linalg.norm(law.B(a_edge), dim=-1).max().item()) if a_edge.numel() else 0.0
        Cq_norm = float(torch.linalg.norm(law.C(q_query), dim=-1).max().item()) if q_query.numel() else 0.0
    L_mu_x = operator_norm(law.O.weight) * operator_norm(law.A.weight) * Ba_norm * Cq_norm
    value = L_mu_x + operator_norm(U.weight)
    return CertifiedBound(value=value, formula="L_message,x(a,q) <= ||O|| ||A|| ||Ba|| ||Cq|| + ||U|| (query-conditioned)", assumptions=[])


def envelope_lipschitz_bound(layer_norm: nn.LayerNorm) -> CertifiedBound:
    """``L_env <= L_LN * L_tanh = L_LN`` (``tanh`` is EXACTLY 1-Lipschitz,
    so it contributes a factor of 1, not omitted). ``L_LN <= 2*||gamma_LN||_inf
    / sqrt(eps)`` — a conservative, global bound (frozen exactly as given
    in the mission brief; may be loose, but is not to be replaced by a
    sampled Jacobian estimate — see `observed_envelope_jacobian_norm`
    below for that separate, non-certified quantity)."""
    gamma_inf = float(layer_norm.weight.detach().abs().max().item())
    eps = float(layer_norm.eps)
    value = 2.0 * gamma_inf / (eps ** 0.5)
    return CertifiedBound(value=value, formula="L_env <= 2*||gamma_LN||_inf / sqrt(eps) (L_tanh=1 exactly)", assumptions=[])


@torch.no_grad()
def _envelope_forward(layer_norm: nn.LayerNorm, z: torch.Tensor) -> torch.Tensor:
    return layer_norm(torch.tanh(z))


def observed_envelope_jacobian_norm(layer_norm: nn.LayerNorm, samples: torch.Tensor) -> EmpiricalMajorant:
    """Autograd-computed largest singular value of the ``LayerNorm(tanh(.))``
    Jacobian, evaluated per-sample and maximized over ``samples`` — a
    DIRECTLY OBSERVED quantity (via autograd, not sampling noise), but
    never a certified upper bound: it is only as good as the samples
    provided, unlike `envelope_lipschitz_bound`, which holds for every
    possible input."""
    max_sv = 0.0
    for i in range(samples.shape[0]):
        x = samples[i].detach().clone().requires_grad_(True)

        def f(z: torch.Tensor) -> torch.Tensor:
            return layer_norm(torch.tanh(z))

        jac = torch.autograd.functional.jacobian(f, x)
        sv = float(torch.linalg.matrix_norm(jac, ord=2).item())
        max_sv = max(max_sv, sv)
    return EmpiricalMajorant(value=max_sv, description="max singular value of d(LN(tanh(.)))/dz over the given samples (autograd, not a bound)")
