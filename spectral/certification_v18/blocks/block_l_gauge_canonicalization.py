"""Block L — gauge canonicalization with explicit residual-gauge reporting,
v18 redesign.

Canonicalization here means: given a reduced tensor T (r,r,r), form a Gram
matrix G = M @ M^H where M is T's mode-0 unfolding (r x r^2), and
diagonalize G to get a canonical eigenbasis Q. This is unique only up to:

- a per-eigenvector U(1) phase, when all eigenvalues are simple (distinct);
- a full U(m) rotation within any m-dimensional degenerate eigenspace.

Reporting a single "canonical" Q without naming this residual gauge group
is exactly the mission's diagnosed defect. This module reports which
regime a given spectrum is in (simple / repeated / near-degenerate) and
what the identifiable residual gauge actually is, using PRINCIPAL ANGLES
(not free-unitary Procrustes — see gauge_utils.py's documented lesson from
block M's development) to confirm that degenerate-eigenspace bases that
disagree pointwise still agree as SUBSPACES.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.blocks.block_m_persistent_factorization import principal_angles


def gram_from_tensor(T: torch.Tensor) -> torch.Tensor:
    r = T.shape[0]
    M = T.reshape(r, -1)
    return M @ M.conj().T


def canonicalize(T: torch.Tensor, *, degeneracy_tol: float = 1e-6) -> dict:
    G = gram_from_tensor(T)
    G = 0.5 * (G + G.conj().T)
    evals, evecs = torch.linalg.eigh(G)
    # group into clusters of (near-)equal eigenvalues
    order = torch.argsort(evals, descending=True)
    evals = evals[order]
    evecs = evecs[:, order]
    clusters = []
    i = 0
    r = evals.numel()
    while i < r:
        j = i + 1
        while j < r and abs(evals[j].item() - evals[i].item()) < degeneracy_tol * max(abs(evals[i].item()), 1e-12):
            j += 1
        clusters.append((i, j))
        i = j
    max_cluster_size = max(j - i for i, j in clusters)
    if max_cluster_size == 1:
        regime = "simple_spectrum"
    elif max_cluster_size == r:
        regime = "fully_degenerate"
    else:
        regime = "partially_degenerate"
    return {
        "eigenvalues": evals,
        "eigenvectors": evecs,
        "clusters": clusters,
        "regime": regime,
        "residual_gauge_dims": [j - i for i, j in clusters],
    }


@dataclass
class GaugeCanonicalizationReport:
    regime: str
    residual_gauge_dims: list[int]
    status: str
    stability_max_principal_angle: float


def certify_canonicalization(T: torch.Tensor, *, perturbation_eps: float = 1e-8, seed: int = 0) -> GaugeCanonicalizationReport:
    result = canonicalize(T)
    gen = torch.Generator().manual_seed(seed)
    noise = torch.complex(
        torch.randn_like(T.real) * perturbation_eps, torch.randn_like(T.real) * perturbation_eps
    )
    result_pert = canonicalize(T + noise)

    max_angle = 0.0
    for (i, j) in result["clusters"]:
        # find the matching cluster in the perturbed result covering the same eigenvalue range
        u_a = result["eigenvectors"][:, i:j]
        # match by closest eigenvalue center
        center = result["eigenvalues"][i:j].mean().item()
        best = min(result_pert["clusters"], key=lambda c: abs(result_pert["eigenvalues"][c[0] : c[1]].mean().item() - center))
        u_b = result_pert["eigenvectors"][:, best[0] : best[1]]
        k = min(u_a.shape[1], u_b.shape[1])
        pa = principal_angles(u_a[:, :k], u_b[:, :k])
        max_angle = max(max_angle, pa.max_angle_rad)

    if result["regime"] == "simple_spectrum" and max_angle < 1e-4:
        status = "CANONICAL"
    elif max_angle < 1e-2:
        status = "CANONICAL_MODULO_RESIDUAL_GAUGE"
    elif max_angle < 0.5:
        status = "UNSTABLE"
    else:
        status = "NON_IDENTIFIABLE"

    return GaugeCanonicalizationReport(
        regime=result["regime"],
        residual_gauge_dims=result["residual_gauge_dims"],
        status=status,
        stability_max_principal_angle=max_angle,
    )


def make_exactly_degenerate_tensor(n: int = 3, seed: int = 0) -> torch.Tensor:
    """Construct a Gram matrix with an EXACT repeated eigenvalue (a 2-dim
    degenerate eigenspace) by symmetrizing a rank-1 update onto a 2-dim
    invariant subspace, then embed it back as a rank-3 tensor whose mode-0
    Gram matches it — a controlled positive control for the fully/partially
    degenerate regime."""
    gen = torch.Generator().manual_seed(seed)
    # Build Gram = diag(2, 1, 1) in a random basis: eigenvalues 2,1,1 (1 is repeated)
    diag = torch.diag(torch.tensor([2.0, 1.0, 1.0], dtype=torch.float64)).to(torch.complex128)
    rand = torch.complex(torch.randn(n, n, generator=gen, dtype=torch.float64), torch.randn(n, n, generator=gen, dtype=torch.float64))
    q, _ = torch.linalg.qr(rand)
    G = q @ diag @ q.conj().T
    # any T whose mode-0 unfolding M satisfies M @ M^H = G works; use M = G^(1/2) reshaped trivially (r=3, r^2=9 -> pad)
    evals, evecs = torch.linalg.eigh(0.5 * (G + G.conj().T))
    sqrt_g = evecs @ torch.diag(evals.clamp(min=0).sqrt().to(torch.complex128)) @ evecs.conj().T
    M = torch.zeros(n, n * n, dtype=torch.complex128)
    M[:, :n] = sqrt_g
    return M.reshape(n, n, n)
