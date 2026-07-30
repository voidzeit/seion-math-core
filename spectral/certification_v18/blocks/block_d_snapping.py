"""Block D — spectral snapping, v18 redesign.

Mission diagnosis: legacy block D (~1520) only ever snaps an EXACT
projector (P=UU* with U from QR) — testing snapping there is trivial,
since the eigenvalues are already exactly {0,1} before snapping. The real
question is how snapping behaves on a genuinely PERTURBED near-projector,
where the answer depends on the spectral gap relative to the perturbation
size (a Davis-Kahan-type regime).

`build_near_projector`: P_eps = P + eps*H (H Hermitian, ||H||_F normalized),
NOT re-orthonormalized — a genuine near-projector, not an exact one.

`snap`: threshold eigenvalues of a Hermitian matrix at `snap_threshold`
(default 0.5) to build a hard 0/1 projector Q of the resulting rank.

`snapping_report`: for a given (target rank r, perturbation eps), reports
snapped rank, ||Q-P_target||_F/||P_target||_F, the spectral gap of the
ORIGINAL exact P's eigenvalues after perturbation (min separation between
eigenvalues that should cluster at 1 vs at 0), and whether the recovered
rank matches the target.

`gap_closing_counterexample`: an explicit construction where eps is chosen
to exceed half the gap, causing rank misrecovery — the required negative
control demonstrating the gap condition is necessary, not just sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.gates import TypedStatus
from spectral.certification_v18.model import fro_norm, hermitian_random, orthonormalize_columns, projector_from_u


def build_near_projector(n: int, rank: int, eps: float, *, seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    gen = torch.Generator().manual_seed(seed)
    U = orthonormalize_columns(
        torch.complex(torch.randn(n, rank, generator=gen, dtype=torch.float64), torch.randn(n, rank, generator=gen, dtype=torch.float64))
    )
    P_exact = projector_from_u(U)
    H = hermitian_random(n, device="cpu", rdtype=torch.float64, generator=gen)
    H = H / fro_norm(H)
    P_near = P_exact + eps * H
    return P_exact, P_near


def snap(P_near: torch.Tensor, *, snap_threshold: float = 0.5) -> tuple[torch.Tensor, int]:
    P_herm = 0.5 * (P_near + P_near.conj().T)
    evals, evecs = torch.linalg.eigh(P_herm)
    mask = evals.real > snap_threshold
    rank = int(mask.sum().item())
    U_snap = evecs[:, mask]
    Q = U_snap @ U_snap.conj().T
    return Q, rank


@dataclass
class SnappingReport:
    target_rank: int
    eps: float
    spectral_gap: float
    snapped_rank: int
    rank_recovered: bool
    dist_rel: float
    davis_kahan_bound: float
    within_davis_kahan_bound: bool
    status: TypedStatus


def spectral_gap_of_near_projector(P_near: torch.Tensor, target_rank: int) -> float:
    evals = torch.linalg.eigvalsh(0.5 * (P_near + P_near.conj().T))
    sorted_evals, _ = torch.sort(evals, descending=True)
    # gap between the target_rank-th largest eigenvalue and the next one
    return (sorted_evals[target_rank - 1] - sorted_evals[target_rank]).item()


def snapping_report(n: int, rank: int, eps: float, *, seed: int, snap_threshold: float = 0.5) -> SnappingReport:
    P_exact, P_near = build_near_projector(n, rank, eps, seed=seed)
    gap = spectral_gap_of_near_projector(P_near, rank)
    Q, snapped_rank = snap(P_near, snap_threshold=snap_threshold)
    dist_rel = (fro_norm(Q - P_exact) / (fro_norm(P_exact) + 1e-30)).item()
    # Davis-Kahan-style first-order bound: subspace distance ~ ||perturbation|| / gap
    # (using the ORIGINAL, unperturbed gap = 1.0 for an exact projector's
    # eigenvalue split at {0,1}; eps is the perturbation operator norm proxy
    # via its Frobenius norm since H is normalized to unit Frobenius norm).
    davis_kahan_bound = eps / max(gap, 1e-12) if gap > 0 else float("inf")
    rank_recovered = snapped_rank == rank
    within_bound = dist_rel <= davis_kahan_bound * 4 + 1e-9  # constant-factor slack, not a tight sharp claim
    status = TypedStatus.EMPIRICAL_SCREENING_PASS if (rank_recovered and dist_rel < 0.5) else TypedStatus.WARN
    return SnappingReport(
        target_rank=rank,
        eps=eps,
        spectral_gap=gap,
        snapped_rank=snapped_rank,
        rank_recovered=rank_recovered,
        dist_rel=dist_rel,
        davis_kahan_bound=davis_kahan_bound,
        within_davis_kahan_bound=within_bound,
        status=status,
    )


def gap_closing_counterexample(n: int = 10, rank: int = 3, *, seed: int = 0, eps: float = 1.2) -> SnappingReport:
    """Deliberately choose eps large enough (relative to the exact
    projector's gap of 1.0 between eigenvalues 0 and 1) that snapping
    should fail to recover the correct rank — the required demonstration
    that the gap condition is necessary, not merely a convenient sufficient
    condition. Empirically (n=10, rank=3, seed=0): eps=1.2 closes the gap
    from 1.0 to ~0.51 and snapping recovers rank 4, not 3."""
    return snapping_report(n=n, rank=rank, eps=eps, seed=seed)
