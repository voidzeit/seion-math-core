"""Block H — associator bound and constant-2 sharpness, v18 redesign.

Formal setup: A(x,y,z) := (x o y) o z - x o (y o z), using the anchored
product (extra CP-law legs closed with the fixed anchor vector, matching
`SpectralModelV18.associator`). Let M_hat be an adversarially-refined
empirical estimate of the law's operator constant:
    M_hat = sup_{||a||=||b||=1} ||anchored_product(a,b)|| .
A naive triangle-inequality bound gives
    ||A(x,y,z)|| <= ||(x o y) o z|| + ||x o (y o z)||
                 <= M_hat^2 (||x|| ||y|| ||z||) + M_hat^2 (||x|| ||y|| ||z||)
                 =  2 * M_hat^2 * ||x|| ||y|| ||z||
— this is where the mission's constant "2" comes from: it is the number of
terms in the associator's defining difference, not a derived fact about
the law. This module tests whether that factor-of-2 upper bound is SHARP
(achieved arbitrarily closely by some explicit (x,y,z)) or whether the two
terms T1=(x o y) o z and T2=x o (y o z) are empirically correlated enough
that the true worst-case ratio is strictly below 2 (a "cancellation-aware"
bound).

ambient_associator / projected_associator / normal_leakage separate the
raw associator from its projected-subspace component and the leakage into
the orthogonal complement (mission's explicit A/P/normal split), reusing
`certify_projector`-style U/P machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns, projector_from_u


def _unit(v: torch.Tensor) -> torch.Tensor:
    return v / (torch.linalg.norm(v) + 1e-30)


def estimate_law_operator_bound(model: SpectralModelV18, *, trials: int = 500, adversarial_steps: int = 150, seed: int = 0) -> float:
    gen = torch.Generator().manual_seed(seed)
    extras = [model.anchor.detach() for _ in range(model.arity - 2)]

    def sample_ratio(a, b):
        y = model.product(a, b, *extras)
        return torch.linalg.norm(y)

    best = 0.0
    for _ in range(trials):
        a = _unit(torch.complex(torch.randn(model.n, generator=gen, dtype=model.rdtype), torch.randn(model.n, generator=gen, dtype=model.rdtype)))
        b = _unit(torch.complex(torch.randn(model.n, generator=gen, dtype=model.rdtype), torch.randn(model.n, generator=gen, dtype=model.rdtype)))
        best = max(best, sample_ratio(a, b).item())

    a_re = torch.randn(model.n, generator=gen, dtype=model.rdtype, requires_grad=True)
    a_im = torch.randn(model.n, generator=gen, dtype=model.rdtype, requires_grad=True)
    b_re = torch.randn(model.n, generator=gen, dtype=model.rdtype, requires_grad=True)
    b_im = torch.randn(model.n, generator=gen, dtype=model.rdtype, requires_grad=True)
    opt = torch.optim.Adam([a_re, a_im, b_re, b_im], lr=0.05)
    for _ in range(adversarial_steps):
        opt.zero_grad()
        a = _unit(torch.complex(a_re, a_im))
        b = _unit(torch.complex(b_re, b_im))
        loss = -sample_ratio(a, b)
        loss.backward()
        opt.step()
        best = max(best, -loss.item())
    return best


@dataclass
class AssociatorConstantReport:
    m_hat: float
    triangle_bound_constant: float
    max_observed_ratio: float
    sharpness_gap: float
    t1_t2_mean_cosine: float
    verdict: str


def associator_constant_report(seed: int = 0, *, n: int = 16, rank: int = 4, arity: int = 3, cp_rank: int = 4, trials: int = 300, adversarial_steps: int = 150) -> AssociatorConstantReport:
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
    m_hat = estimate_law_operator_bound(model, trials=200, adversarial_steps=100, seed=seed)

    extras = [model.anchor.detach() for _ in range(arity - 2)]

    def associator_and_terms(x, y, z):
        xy = model.product(x, y, *extras)
        yz = model.product(y, z, *extras)
        t1 = model.product(xy, z, *extras)
        t2 = model.product(x, yz, *extras)
        return t1 - t2, t1, t2

    ratios = []
    cosines = []
    best_ratio = 0.0
    for _ in range(trials):
        x = _unit(torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64)))
        y = _unit(torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64)))
        z = _unit(torch.complex(torch.randn(n, generator=gen, dtype=torch.float64), torch.randn(n, generator=gen, dtype=torch.float64)))
        a, t1, t2 = associator_and_terms(x, y, z)
        denom = m_hat**2 + 1e-30
        ratio = (torch.linalg.norm(a) / denom).item()
        ratios.append(ratio)
        cos = torch.real(torch.sum(torch.conj(t1) * t2)) / (torch.linalg.norm(t1) * torch.linalg.norm(t2) + 1e-30)
        cosines.append(cos.item())
        best_ratio = max(best_ratio, ratio)

    # adversarial refinement over (x,y,z) jointly
    xr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    xi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    yr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    yi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    zr = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    zi = torch.randn(n, generator=gen, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([xr, xi, yr, yi, zr, zi], lr=0.05)
    for _ in range(adversarial_steps):
        opt.zero_grad()
        x = _unit(torch.complex(xr, xi))
        y = _unit(torch.complex(yr, yi))
        z = _unit(torch.complex(zr, zi))
        a, _, _ = associator_and_terms(x, y, z)
        loss = -torch.linalg.norm(a) / (m_hat**2 + 1e-30)
        loss.backward()
        opt.step()
        best_ratio = max(best_ratio, -loss.item())

    triangle_bound_constant = 2.0
    sharpness_gap = triangle_bound_constant - best_ratio
    mean_cos = sum(cosines) / len(cosines)
    if sharpness_gap < 0.05:
        verdict = "CONSTANT_2_EMPIRICALLY_SHARP"
    elif sharpness_gap > 0.5:
        verdict = "CONSTANT_2_NOT_SHARP_TIGHTER_BOUND_AVAILABLE"
    else:
        verdict = "SHARPNESS_UNRESOLVED_GAP_MODERATE"

    return AssociatorConstantReport(
        m_hat=m_hat,
        triangle_bound_constant=triangle_bound_constant,
        max_observed_ratio=best_ratio,
        sharpness_gap=sharpness_gap,
        t1_t2_mean_cosine=mean_cos,
        verdict=verdict,
    )


def ambient_projected_normal_split(model: SpectralModelV18, U: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> dict:
    """Separate the ambient associator into its projected (in-subspace) and
    normal (leakage) components — mission's explicit A/projected/normal
    split for block H."""
    P = projector_from_u(U)
    extras = [model.anchor.detach() for _ in range(model.arity - 2)]
    xy = model.product(x, y, *extras)
    yz = model.product(y, z, *extras)
    ambient = model.product(xy, z, *extras) - model.product(x, yz, *extras)
    projected = P @ ambient
    normal = ambient - projected
    ambient_norm = torch.linalg.norm(ambient).item() + 1e-30
    return {
        "ambient_norm": ambient_norm,
        "projected_norm": torch.linalg.norm(projected).item(),
        "normal_norm": torch.linalg.norm(normal).item(),
        "normal_leakage_fraction": torch.linalg.norm(normal).item() / ambient_norm,
    }
