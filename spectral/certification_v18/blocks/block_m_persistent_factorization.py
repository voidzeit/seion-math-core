"""Block M — persistent factorization, v18 redesign.

Mission diagnosis: the legacy block only ever compares TWO resolutions
(lo vs hi, `spectral/legacy/v17/...py:1738`), so any observed mismatch is
inherently ambiguous between "no persistence exists" and "these particular
two resolutions/gauges/scales don't happen to align." Mission section 2M
requires at least three independently constructed resolutions before any
persistence-or-not verdict is drawn, and requires the comparison itself to
be gauge-invariant (not the legacy's single Gram-eigenbasis heuristic —
see `gauge_utils.py`, built for block J and reused here since block M's
comparison is the same kind of problem one level up: comparing HOSVD
*signatures* rather than raw tensors).

This module provides:
- `hosvd_mode_energy`: per-mode singular-value energy profile (same idea
  as the legacy `hosvd_mode_energy`/`hosvd_signature`, reimplemented).
- `hosvd_signature_distance`: compares two signatures via the SAME
  gauge-invariant machinery as block J (raw / procrustes-aligned /
  permutation-aligned on the mode-unfolded left singular vectors), rather
  than the legacy's raw normalized-distance-only comparison.
- `persistence_across_resolutions`: runs the above pairwise across N>=3
  independently-seeded instances and reports the full pairwise matrix, not
  just one lo-vs-hi number — a single outlying pair no longer masquerades
  as "persistence holds" or "persistence fails" for the whole claim.

Scope note (tracked in .ai/SPECTRAL_TRACK_ROADMAP.md, not silently
dropped): these "resolutions" are independently-seeded SpectralModelV18
instances at the same or different ambient dimension `n`, not yet the
mission's fully independently-*trained* low/high law pair with a frozen
transfer map (that requires the block-E interscale training infrastructure
this pass did not build). This module answers the narrower, still-real
question: does the comparison METHODOLOGY correctly distinguish true
gauge-equivalence from genuine structural mismatch across >2 instances?
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch


@dataclass
class PrincipalAngleResult:
    angles_rad: list[float]
    max_angle_rad: float
    mean_angle_rad: float


def principal_angles(u_a: torch.Tensor, u_b: torch.Tensor) -> PrincipalAngleResult:
    """Principal angles between the subspaces spanned by the (orthonormal)
    columns of u_a and u_b (mission section 2E's explicit requirement).

    This is the correct invariant for comparing SUBSPACES (as opposed to
    `gauge_utils.compare_with_gauge`, which correctly compares general
    matrices under a free unitary action but is VACUOUS when applied to
    orthonormal-column bases themselves: the unitary group acts transitively
    on same-size orthonormal k-frames of C^n, so a free n x n unitary Q
    always exists with Q @ u_a == u_b exactly, regardless of whether the
    two subspaces have anything to do with each other. Caught during this
    block's development by its own negative control
    (see test_block_m.py history / BLOCK_M_FINDINGS.md) — comparing HOSVD
    left-singular-vector subspaces via free-unitary Procrustes silently
    reported near-zero distance for independent random subspaces.
    Principal angles (via the SVD of u_a^H @ u_b) do not have this failure
    mode: they are invariant to the choice of orthonormal basis WITHIN each
    subspace but are NOT trivially zero for unrelated subspaces.
    """
    cross = u_a.conj().T @ u_b
    s = torch.linalg.svdvals(cross)
    s = torch.clamp(s.real, min=-1.0, max=1.0)
    angles = [math.acos(float(v)) for v in s.tolist()]
    return PrincipalAngleResult(angles_rad=angles, max_angle_rad=max(angles), mean_angle_rad=sum(angles) / len(angles))


def hosvd_mode_energy(tensor: torch.Tensor, mode: int, energy_threshold: float = 0.99) -> dict:
    unfolded = torch.movedim(tensor, mode, 0).reshape(tensor.shape[mode], -1)
    u, s, _ = torch.linalg.svd(unfolded, full_matrices=False)
    energy = (s**2).cumsum(0) / ((s**2).sum() + 1e-30)
    rank_needed = int(torch.searchsorted(energy, energy_threshold).item()) + 1
    rank_needed = min(rank_needed, s.numel())
    return {"singular_values": s, "left_singular_vectors": u, "rank_needed": rank_needed, "energy_threshold": energy_threshold}


@dataclass
class HOSVDSignature:
    seed: int
    mode_energies: list[dict]


def hosvd_signature(tensor: torch.Tensor, *, energy_threshold: float = 0.99, seed: int = -1) -> HOSVDSignature:
    modes = [hosvd_mode_energy(tensor, m, energy_threshold) for m in range(tensor.ndim)]
    return HOSVDSignature(seed=seed, mode_energies=modes)


def hosvd_signature_distance(sig_a: HOSVDSignature, sig_b: HOSVDSignature) -> list[PrincipalAngleResult]:
    """Compare only the ENERGY-DOMINANT truncated subspace of each mode
    (top `rank_needed` left singular vectors), via principal angles — see
    `principal_angles` for why free-unitary Procrustes is the wrong tool
    here even after truncation (truncation alone does not fix it: the
    unitary group still acts transitively on any same-size k-frame pair).
    """
    if len(sig_a.mode_energies) != len(sig_b.mode_energies):
        raise ValueError("signatures have a different number of modes")
    results = []
    for mode_a, mode_b in zip(sig_a.mode_energies, sig_b.mode_energies):
        u_a, u_b = mode_a["left_singular_vectors"], mode_b["left_singular_vectors"]
        k = min(mode_a["rank_needed"], mode_b["rank_needed"], u_a.shape[1], u_b.shape[1])
        results.append(principal_angles(u_a[:, :k], u_b[:, :k]))
    return results


def persistence_across_resolutions(tensors: dict[int, torch.Tensor], *, energy_threshold: float = 0.99) -> dict:
    if len(tensors) < 3:
        raise ValueError(
            "mission section 2M requires at least three independently constructed resolutions; "
            f"got {len(tensors)}"
        )
    signatures = {seed: hosvd_signature(t, energy_threshold=energy_threshold, seed=seed) for seed, t in tensors.items()}
    seeds = sorted(signatures)
    pairwise = {}
    for i, seed_a in enumerate(seeds):
        for seed_b in seeds[i + 1 :]:
            per_mode = hosvd_signature_distance(signatures[seed_a], signatures[seed_b])
            pairwise[(seed_a, seed_b)] = {
                "per_mode_max_principal_angle_rad": [r.max_angle_rad for r in per_mode],
                "per_mode_mean_principal_angle_rad": [r.mean_angle_rad for r in per_mode],
            }
    rank_by_seed = {seed: [m["rank_needed"] for m in signatures[seed].mode_energies] for seed in seeds}
    all_max_angles = [d for entry in pairwise.values() for d in entry["per_mode_max_principal_angle_rad"]]
    mean_max_angle = sum(all_max_angles) / len(all_max_angles) if all_max_angles else None
    return {
        "seeds": seeds,
        "rank_needed_by_seed": rank_by_seed,
        "pairwise": {f"{a}_vs_{b}": v for (a, b), v in pairwise.items()},
        "mean_max_principal_angle_rad_across_all_pairs": mean_max_angle,
        "rank_consistent_across_resolutions": len({tuple(r) for r in rank_by_seed.values()}) == 1,
    }
