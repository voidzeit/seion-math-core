"""Block A — projector validity, v18 redesign.

Formal spec: given U in C^{n x r} with orthonormal columns (produced by QR,
`orthonormalize_columns`), P := U U* is checked for:

    idempotence:      ||P^2 - P||_F / ||P||_F
    self-adjointness: ||P* - P||_F / ||P||_F
    rank:             trace(P) vs r (should equal r exactly for exact P)
    spectral clusters: eigenvalues of P should cluster at exactly {0, 1}
    perturbation stability: how idem/selfadj residuals scale under a
        controlled perturbation of U (first-order sanity, not a claim about
        the learned subspace)

Non-implication (mission section 2A, enforced by construction here, not
just prose): P = U U* is idempotent and self-adjoint FOR ANY orthonormal U
— this is a QR-construction identity, not evidence that the r-dimensional
subspace spanned by U is scientifically meaningful. This module never
reports a status stronger than STRUCTURAL_IDENTITY_PASS for idempotence/
self-adjointness precisely because they hold independent of what U
"means" — see `certify_projector`'s docstring and BLOCK_A_FINDINGS.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.gates import TypedStatus
from spectral.certification_v18.model import fro_norm, orthonormalize_columns, projector_from_u


@dataclass
class ProjectorReport:
    idem_rel: float
    selfadj_rel: float
    rank_trace: float
    rank_target: int
    rank_error: float
    eigenvalue_cluster_max_deviation: float
    status: TypedStatus


def certify_projector(U: torch.Tensor, *, tol: float = 1e-10) -> ProjectorReport:
    """STRUCTURAL_IDENTITY_PASS is the ceiling here by design: idempotence
    and self-adjointness of P=UU* hold for ANY orthonormal U, so passing
    them certifies the QR construction, not the learned subspace's
    relevance. See BLOCK_A_FINDINGS.md."""
    U = orthonormalize_columns(U)
    P = projector_from_u(U)
    r = U.shape[1]

    idem_rel = (fro_norm(P @ P - P) / (fro_norm(P) + 1e-30)).item()
    selfadj_rel = (fro_norm(P.conj().T - P) / (fro_norm(P) + 1e-30)).item()
    rank_trace = torch.real(torch.trace(P)).item()
    rank_error = abs(rank_trace - r)

    evals = torch.linalg.eigvalsh(0.5 * (P + P.conj().T))
    dist_to_0_or_1 = torch.minimum(evals.abs(), (evals - 1).abs())
    eigenvalue_cluster_max_deviation = dist_to_0_or_1.max().item()

    ok = max(idem_rel, selfadj_rel, rank_error, eigenvalue_cluster_max_deviation) < tol
    status = TypedStatus.STRUCTURAL_IDENTITY_PASS if ok else TypedStatus.WARN
    return ProjectorReport(
        idem_rel=idem_rel,
        selfadj_rel=selfadj_rel,
        rank_trace=rank_trace,
        rank_target=r,
        rank_error=rank_error,
        eigenvalue_cluster_max_deviation=eigenvalue_cluster_max_deviation,
        status=status,
    )


def perturbation_stability_sweep(U: torch.Tensor, *, epsilons: list[float], seed: int = 0) -> list[dict]:
    """First-order sanity check: does the idempotence residual grow
    linearly (or worse) with a controlled perturbation applied to U BEFORE
    QR re-orthonormalization? This bounds how much QR reconstruction
    "absorbs" a perturbation, not whether the perturbed subspace is still
    scientifically meaningful."""
    gen = torch.Generator().manual_seed(seed)
    n, r = U.shape
    direction = torch.complex(
        torch.randn(n, r, generator=gen, dtype=torch.float64), torch.randn(n, r, generator=gen, dtype=torch.float64)
    )
    direction = direction / fro_norm(direction)
    rows = []
    for eps in epsilons:
        U_pert = orthonormalize_columns(U + eps * direction)
        report = certify_projector(U_pert, tol=1e-10)
        rows.append({"epsilon": eps, "idem_rel": report.idem_rel, "selfadj_rel": report.selfadj_rel})
    return rows


def exact_small_case_2x2() -> ProjectorReport:
    """Hand-verifiable n=2, r=1 case: U = [1, 0]^T exactly. P = [[1,0],[0,0]]
    exactly (no floating-point construction noise beyond machine epsilon).
    """
    U = torch.tensor([[1.0], [0.0]], dtype=torch.complex128)
    return certify_projector(U, tol=1e-14)
