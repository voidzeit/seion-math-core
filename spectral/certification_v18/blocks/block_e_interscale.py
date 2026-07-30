"""Block E — interscale subspace transport, v18 redesign.

Mission diagnosis: the legacy interscale check derives the high-resolution
TARGET from the low-resolution model's own lifted subspace
(`build_highres_U_target_from_lowres`), then certifies agreement with that
same derived target — circular by construction. This module instead:

1. Trains THREE genuinely independent `SpectralModelV18` instances at
   three different ambient dimensions (no resolution's model or objective
   ever references another resolution).
2. Builds ONE frozen Gaussian-kernel lift operator per pair of dimensions
   (never trained, never touched by any objective).
3. Transports each resolution's independently-trained subspace to every
   other resolution via the frozen lift, and compares against that OTHER
   resolution's OWN independently-trained subspace via principal angles
   (not raw distance, not vacuous Procrustes — see gauge_utils.py's
   documented lesson).
4. Reports two required baselines: a RANDOM baseline (lift a randomly
   initialized, untrained subspace instead of the real trained one) and an
   INTERPOLATION baseline (nearest-index lift instead of the Gaussian
   kernel) — transport is only meaningful evidence if it beats both.

Three resolutions (mission's explicit >=3 requirement) means the largest
is naturally treated as a held-out target relative to any pairwise
comparison built only from the two smaller ones.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.blocks.block_m_persistent_factorization import principal_angles
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def gaussian_lift_operator(n_lo: int, n_hi: int) -> torch.Tensor:
    x_lo = torch.linspace(0.0, 1.0, n_lo, dtype=torch.float64)
    x_hi = torch.linspace(0.0, 1.0, n_hi, dtype=torch.float64)
    dist = (x_hi[:, None] - x_lo[None, :]).abs()
    width = 1.5 / max(n_lo, 1)
    w = torch.exp(-((dist / max(width, 1e-8)) ** 2))
    w = w / w.sum(dim=1, keepdim=True).clamp(min=1e-12)
    return w.to(torch.complex128)  # (n_hi, n_lo)


def nearest_index_lift_operator(n_lo: int, n_hi: int) -> torch.Tensor:
    """Interpolation baseline: nearest-neighbor index mapping instead of a
    Gaussian kernel — a cruder, non-smooth transfer map."""
    x_lo = torch.linspace(0.0, 1.0, n_lo, dtype=torch.float64)
    x_hi = torch.linspace(0.0, 1.0, n_hi, dtype=torch.float64)
    idx = torch.argmin((x_hi[:, None] - x_lo[None, :]).abs(), dim=1)
    w = torch.zeros(n_hi, n_lo, dtype=torch.float64)
    w[torch.arange(n_hi), idx] = 1.0
    return w.to(torch.complex128)


def train_resolution(seed: int, *, n: int, rank: int, arity: int = 3, cp_rank: int, steps: int = 200, lr: float = 0.02) -> torch.Tensor:
    """Train ONE resolution's subspace against ITS OWN closure objective
    only — no cross-resolution reference of any kind."""
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    extras = [model.anchor.detach() for _ in range(arity - 2)]
    y2 = torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64))
    y2 = y2 / torch.linalg.norm(y2)
    for _ in range(steps):
        opt.zero_grad()
        U = orthonormalize_columns(model.u())
        parts = []
        for i in range(rank):
            y = model.product(U[:, i], y2, *extras)
            y_in = U @ (U.conj().T @ y)
            parts.append(y - y_in)
        residual = torch.cat(parts)
        loss = torch.sum(residual.real**2) + torch.sum(residual.imag**2)
        loss.backward()
        opt.step()
    with torch.no_grad():
        return orthonormalize_columns(model.u()).detach()


@dataclass
class TransportComparison:
    from_n: int
    to_n: int
    trained_transport_max_angle: float
    random_baseline_max_angle: float
    interpolation_baseline_max_angle: float
    beats_random_baseline: bool
    beats_interpolation_baseline: bool


def transport_and_compare(U_lo: torch.Tensor, U_hi_real: torch.Tensor, n_lo: int, n_hi: int, rank: int, *, seed: int) -> TransportComparison:
    L_gauss = gaussian_lift_operator(n_lo, n_hi)
    L_nn = nearest_index_lift_operator(n_lo, n_hi)

    def lift_and_compare(U_source: torch.Tensor, L: torch.Tensor) -> float:
        lifted = orthonormalize_columns(L @ U_source)
        pa = principal_angles(lifted, U_hi_real)
        return pa.max_angle_rad

    trained_angle = lift_and_compare(U_lo, L_gauss)
    interp_angle = lift_and_compare(U_lo, L_nn)

    gen = torch.Generator().manual_seed(seed + 9999)
    U_random = orthonormalize_columns(
        torch.complex(torch.randn(n_lo, rank, generator=gen, dtype=torch.float64), torch.randn(n_lo, rank, generator=gen, dtype=torch.float64))
    )
    random_angle = lift_and_compare(U_random, L_gauss)

    return TransportComparison(
        from_n=n_lo,
        to_n=n_hi,
        trained_transport_max_angle=trained_angle,
        random_baseline_max_angle=random_angle,
        interpolation_baseline_max_angle=interp_angle,
        beats_random_baseline=trained_angle < random_angle,
        beats_interpolation_baseline=trained_angle < interp_angle,
    )


def interscale_experiment(*, resolutions: list[int] = (12, 18, 24), rank: int = 3, cp_rank: int = 4, seed: int = 0, steps: int = 200) -> dict:
    if len(resolutions) < 3:
        raise ValueError("mission section 2E requires at least three resolutions")
    trained = {n: train_resolution(seed + i, n=n, rank=rank, cp_rank=cp_rank, steps=steps) for i, n in enumerate(resolutions)}

    comparisons = []
    for i, n_a in enumerate(resolutions):
        for n_b in resolutions[i + 1 :]:
            fwd = transport_and_compare(trained[n_a], trained[n_b], n_a, n_b, rank, seed=seed)
            bwd_lift = gaussian_lift_operator(n_b, n_a)
            bwd_lifted = orthonormalize_columns(bwd_lift @ trained[n_b])
            bwd_angle = principal_angles(bwd_lifted, trained[n_a]).max_angle_rad
            comparisons.append({"forward": fwd, "backward_max_angle": bwd_angle})

    held_out = max(resolutions)
    return {
        "resolutions": list(resolutions),
        "held_out_resolution": held_out,
        "comparisons": comparisons,
        "any_forward_beats_both_baselines": any(
            c["forward"].beats_random_baseline and c["forward"].beats_interpolation_baseline for c in comparisons
        ),
    }
