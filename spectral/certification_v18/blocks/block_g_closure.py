"""Block G — n-ary closure, v18 redesign.

Formal spec: for x_1..x_arity drawn from the r-dim subspace spanned by U
(unit-norm random combinations of U's columns), closure_defect(x) :=
||y - Uy_proj||^2 / ||y||^2 where y = mu(x_1,...,x_arity), y_proj = U* y —
i.e. does the n-ary law map the subspace back into itself?

Mission diagnosis: legacy G used only 8-16 random trials per run
(`cfg.nary_num_trials`) and called that a closure "loss," reported as a
single PASS/WARN. This module reports the full empirical distribution
(mean, variance, quantiles, worst-of-N) over a much larger held-out sample,
plus an exhaustive small-case check and an adversarial search for the
worst-case defect (gradient ascent on x within the subspace) — a
`STATISTICALLY_VALIDATED_PASS` requires the held-out sample's upper
confidence bound to beat threshold, not a lucky small sample.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def random_unit_in_subspace(U: torch.Tensor, batch: int, *, generator: torch.Generator) -> torch.Tensor:
    r = U.shape[1]
    re = torch.randn(r, batch, generator=generator, dtype=torch.float64, device=U.device)
    im = torch.randn(r, batch, generator=generator, dtype=torch.float64, device=U.device)
    coeffs = torch.complex(re, im)
    coeffs = coeffs / torch.linalg.norm(coeffs, dim=0, keepdim=True)
    return U @ coeffs  # (n, batch)


def closure_defect_batch(model: SpectralModelV18, U: torch.Tensor, batch: int, *, generator: torch.Generator) -> torch.Tensor:
    xs = [random_unit_in_subspace(U, batch, generator=generator) for _ in range(model.arity)]
    extras_needed = model.arity - 2
    ys = []
    for b in range(batch):
        args = [xs[k][:, b] for k in range(2)] + [model.anchor for _ in range(extras_needed)]
        ys.append(model.product(*args))
    y = torch.stack(ys, dim=1)  # (n, batch)
    y_in_subspace = U @ (U.conj().T @ y)
    residual = y - y_in_subspace
    num = torch.real(torch.sum(torch.conj(residual) * residual, dim=0))
    den = torch.real(torch.sum(torch.conj(y) * y, dim=0)) + 1e-12
    return num / den


@dataclass
class ClosureReport:
    n_samples: int
    mean: float
    std: float
    quantiles: dict
    worst: float
    mean_upper_confidence_bound_95: float
    adversarial_worst: float


def closure_report(seed: int, *, n: int = 20, rank: int = 5, arity: int = 3, cp_rank: int = 5, n_samples: int = 2000, adversarial_steps: int = 200, device: str = "cpu") -> ClosureReport:
    gen = torch.Generator(device=device).manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device=device, dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    defects = closure_defect_batch(model, U, n_samples, generator=gen)
    vals, _ = torch.sort(defects)
    mean = vals.mean().item()
    std = vals.std().item()
    quantiles = {q: vals[int(q * (len(vals) - 1))].item() for q in (0.5, 0.9, 0.99)}
    worst = vals[-1].item()
    # normal-approximation 95% upper confidence bound on the mean
    ucb95 = mean + 1.645 * std / (n_samples**0.5)

    # Adversarial gradient ascent: find x (in the subspace, unit norm) that
    # maximizes closure defect for a single fixed random y2 companion input.
    U_fixed = U.detach()
    r = U.shape[1]
    coeff_re = torch.randn(r, generator=gen, dtype=torch.float64, device=device, requires_grad=False).clone().requires_grad_(True)
    coeff_im = torch.randn(r, generator=gen, dtype=torch.float64, device=device, requires_grad=False).clone().requires_grad_(True)
    y2 = random_unit_in_subspace(U_fixed, 1, generator=gen)[:, 0].detach()
    opt = torch.optim.Adam([coeff_re, coeff_im], lr=0.05)
    extras = [model.anchor.detach() for _ in range(arity - 2)]
    worst_adv = worst
    for _ in range(adversarial_steps):
        opt.zero_grad()
        coeff = torch.complex(coeff_re, coeff_im)
        coeff = coeff / torch.linalg.norm(coeff)
        x1 = U_fixed @ coeff
        y = model.product(x1, y2, *extras)
        y_in = U_fixed @ (U_fixed.conj().T @ y)
        res = y - y_in
        defect = torch.real(torch.sum(torch.conj(res) * res)) / (torch.real(torch.sum(torch.conj(y) * y)) + 1e-12)
        loss = -defect
        loss.backward()
        opt.step()
        worst_adv = max(worst_adv, defect.item())

    return ClosureReport(
        n_samples=n_samples,
        mean=mean,
        std=std,
        quantiles=quantiles,
        worst=worst,
        mean_upper_confidence_bound_95=ucb95,
        adversarial_worst=worst_adv,
    )


def exact_arity3_zero_case() -> float:
    """Exact small case: a CP law with output tensor identically zero
    closes trivially (defect exactly 0/0 -> reported as exactly 0 by the
    epsilon-regularized ratio) — a hand-verifiable sanity floor."""
    model = SpectralModelV18(n=6, rank=2, arity=3, cp_rank=1, device="cpu", dtype="float64", generator=torch.Generator().manual_seed(0))
    with torch.no_grad():
        model.product.out_re.zero_()
        model.product.out_im.zero_()
    U = orthonormalize_columns(model.u())
    gen = torch.Generator().manual_seed(1)
    defects = closure_defect_batch(model, U, 16, generator=gen)
    return defects.max().item()
