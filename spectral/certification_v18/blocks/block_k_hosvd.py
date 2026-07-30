"""Block K — HOSVD compactness, v18 redesign.

Mission diagnosis: singular-value energy concentration alone
(`hosvd_mode_energy` in block_m_persistent_factorization.py) is descriptive,
not evidence of "canonical low-dimensional structure." This module adds
the comparisons mission section 2K explicitly requires: reconstruction
error at the chosen truncation, held-out generalization of a fitted basis,
perturbation stability (via principal angles, not vacuous Procrustes — see
gauge_utils.py / block_m's documented lesson), and a random-tensor null
control (is the real tensor's rank_needed actually smaller than what a
random tensor of the same shape/norm would show?).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.blocks.block_m_persistent_factorization import hosvd_mode_energy, principal_angles
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def tucker_reconstruction_error(tensor: torch.Tensor, ranks: list[int]) -> float:
    bases = []
    core = tensor
    for mode, k in enumerate(ranks):
        energy = hosvd_mode_energy(tensor, mode, energy_threshold=0.999999)
        u = energy["left_singular_vectors"][:, :k]
        bases.append(u)
    approx = tensor
    for mode, u in enumerate(bases):
        approx = torch.tensordot(u @ u.conj().T, approx, dims=([1], [mode]))
        approx = torch.movedim(approx, 0, mode)
    rel = (torch.linalg.norm((tensor - approx).reshape(-1)) / (torch.linalg.norm(tensor.reshape(-1)) + 1e-30)).item()
    return rel


@dataclass
class KReport:
    rank_needed_per_mode: list[int]
    reconstruction_error_at_rank_needed: float
    held_out_reconstruction_error: float
    perturbation_max_principal_angle: float
    random_tensor_rank_needed_per_mode: list[int]
    real_tensor_more_compact_than_random: bool


def hosvd_compactness_report(seed: int = 0, *, n: int = 16, rank: int = 4, cp_rank: int = 4, energy_threshold: float = 0.99, held_out_seed: int = 1000, perturbation_eps: float = 1e-3) -> KReport:
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=3, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    T = model.reduced_law_tensor_einsum(U)

    energies = [hosvd_mode_energy(T, m, energy_threshold) for m in range(T.ndim)]
    rank_needed = [e["rank_needed"] for e in energies]
    recon_err = tucker_reconstruction_error(T, rank_needed)

    # held-out generalization: fit the basis on THIS tensor, apply it to an
    # independently-seeded held-out instance's tensor, compare.
    gen_ho = torch.Generator().manual_seed(held_out_seed)
    model_ho = SpectralModelV18(n=n, rank=rank, arity=3, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen_ho)
    U_ho = orthonormalize_columns(model_ho.u())
    T_ho = model_ho.reduced_law_tensor_einsum(U_ho)
    held_out_err = tucker_reconstruction_error(T_ho, rank_needed)

    # perturbation stability via principal angles of the dominant mode-0 subspace
    noise = torch.complex(torch.randn_like(T.real) * perturbation_eps, torch.randn_like(T.real) * perturbation_eps)
    T_pert = T + noise
    e0 = hosvd_mode_energy(T, 0, energy_threshold)
    e0_pert = hosvd_mode_energy(T_pert, 0, energy_threshold)
    k = min(e0["rank_needed"], e0_pert["rank_needed"])
    pa = principal_angles(e0["left_singular_vectors"][:, :k], e0_pert["left_singular_vectors"][:, :k])

    # random-tensor null control: same shape/norm, iid random entries
    gen_rand = torch.Generator().manual_seed(seed + 777)
    random_tensor = torch.complex(
        torch.randn(*T.shape, generator=gen_rand, dtype=torch.float64), torch.randn(*T.shape, generator=gen_rand, dtype=torch.float64)
    )
    random_tensor = random_tensor * (torch.linalg.norm(T.reshape(-1)) / torch.linalg.norm(random_tensor.reshape(-1)))
    random_rank_needed = [hosvd_mode_energy(random_tensor, m, energy_threshold)["rank_needed"] for m in range(random_tensor.ndim)]

    more_compact = all(a <= b for a, b in zip(rank_needed, random_rank_needed)) and any(
        a < b for a, b in zip(rank_needed, random_rank_needed)
    )

    return KReport(
        rank_needed_per_mode=rank_needed,
        reconstruction_error_at_rank_needed=recon_err,
        held_out_reconstruction_error=held_out_err,
        perturbation_max_principal_angle=pa.max_angle_rad,
        random_tensor_rank_needed_per_mode=random_rank_needed,
        real_tensor_more_compact_than_random=more_compact,
    )
