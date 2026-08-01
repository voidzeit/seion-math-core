"""Block C — FINITE_BEALS_PROXY, v18 redesign.

Mission diagnosis: renamed explicitly to FINITE_BEALS_PROXY. This block
may report finite nested-commutator Frobenius norms only. It may NOT
certify pseudodifferentiality, Psi^0 membership, microlocal regularity, or
any continuum Beals criterion — those require an infinite/continuum
operator algebra this suite does not construct. Every function and report
below only ever produces finite matrix norms.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import torch

from spectral.certification_v18.model import commutator, fro_norm, orthonormalize_columns, projector_from_u


def build_observables(n: int, f_count: int, x_count: int, *, device: str = "cpu") -> list[tuple[str, torch.Tensor]]:
    xs = torch.linspace(0.0, 2.0 * math.pi, n, device=device, dtype=torch.float64)
    ops = []
    for k in range(1, f_count + 1):
        ops.append((f"f{k - 1}", torch.diag(torch.cos(k * xs)).to(torch.complex128)))
    if x_count > 0:
        shift = torch.zeros(n, n, dtype=torch.complex128, device=device)
        for i in range(n):
            shift[(i + 1) % n, i] = 1.0
        for k in range(x_count):
            ops.append((f"X{k}", shift))
    return ops


def nested_commutator_norms(P: torch.Tensor, ops: list[tuple[str, torch.Tensor]], max_order: int) -> list[dict]:
    entries = [{"order": 0, "kind": "P", "norm": fro_norm(P).item()}]
    small_ops = ops[: min(4, len(ops))]
    for order in range(1, max_order + 1):
        for combo in itertools.product(range(len(small_ops)), repeat=order):
            names = [small_ops[i][0] for i in combo]
            out = P
            for i in combo:
                out = commutator(small_ops[i][1], out)
            entries.append({"order": order, "kind": "_".join(names), "norm": fro_norm(out).item()})
    return entries


def random_projector(n: int, r: int, seed: int) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    U = torch.complex(torch.randn(n, r, generator=gen, dtype=torch.float64), torch.randn(n, r, generator=gen, dtype=torch.float64))
    return projector_from_u(orthonormalize_columns(U))


def smooth_projector(n: int, r: int) -> torch.Tensor:
    """Low-frequency ('smooth') subspace: the r lowest-frequency discrete
    Fourier-like real sinusoids, as columns."""
    xs = torch.linspace(0.0, 2.0 * math.pi, n, dtype=torch.float64)
    cols = []
    for k in range(r):
        cols.append(torch.cos((k + 1) * xs).to(torch.complex128))
    U = torch.stack(cols, dim=1)
    return projector_from_u(orthonormalize_columns(U))


def localized_projector(n: int, r: int) -> torch.Tensor:
    """Spatially localized subspace: r contiguous standard basis vectors."""
    U = torch.zeros(n, r, dtype=torch.complex128)
    for k in range(r):
        U[k, k] = 1.0
    return projector_from_u(orthonormalize_columns(U))


def adversarial_projector(n: int, r: int, ops: list[tuple[str, torch.Tensor]], *, steps: int = 100, seed: int = 0) -> torch.Tensor:
    """Adversarially search for a projector that MAXIMIZES the order-1
    nested commutator blowup against the given observables — the required
    adversarial control."""
    gen = torch.Generator().manual_seed(seed)
    u_re = torch.randn(n, r, generator=gen, dtype=torch.float64, requires_grad=True)
    u_im = torch.randn(n, r, generator=gen, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([u_re, u_im], lr=0.05)
    small_ops = [op for _, op in ops[: min(4, len(ops))]]
    for _ in range(steps):
        opt.zero_grad()
        U = orthonormalize_columns(torch.complex(u_re, u_im))
        P = projector_from_u(U)
        total = sum(fro_norm(commutator(op, P)) for op in small_ops)
        loss = -total
        loss.backward()
        opt.step()
    with torch.no_grad():
        U = orthonormalize_columns(torch.complex(u_re, u_im))
        return projector_from_u(U)


@dataclass
class BealsScalingReport:
    dimension_scaling: dict
    order_scaling: dict
    projector_family_comparison: dict


def scaling_study(*, dims: list[int] = (8, 16, 32), max_order: int = 2, rank: int = 3, seed: int = 0) -> BealsScalingReport:
    dim_scaling = {}
    for n in dims:
        ops = build_observables(n, f_count=2, x_count=1)
        P = random_projector(n, rank, seed)
        entries = nested_commutator_norms(P, ops, max_order=max_order)
        max_norm = max(e["norm"] for e in entries)
        dim_scaling[n] = max_norm

    n0 = dims[0]
    ops0 = build_observables(n0, f_count=2, x_count=1)
    P0 = random_projector(n0, rank, seed)
    order_scaling = {}
    for order in range(0, max_order + 1):
        entries = nested_commutator_norms(P0, ops0, max_order=order)
        max_at_order = max(e["norm"] for e in entries if e["order"] == order)
        order_scaling[order] = max_at_order

    n1 = 16
    ops1 = build_observables(n1, f_count=2, x_count=1)
    family = {
        "random": max(e["norm"] for e in nested_commutator_norms(random_projector(n1, rank, seed), ops1, max_order)),
        "smooth": max(e["norm"] for e in nested_commutator_norms(smooth_projector(n1, rank), ops1, max_order)),
        "localized": max(e["norm"] for e in nested_commutator_norms(localized_projector(n1, rank), ops1, max_order)),
        "adversarial": max(
            e["norm"] for e in nested_commutator_norms(adversarial_projector(n1, rank, ops1, steps=80, seed=seed), ops1, max_order)
        ),
    }

    return BealsScalingReport(dimension_scaling=dim_scaling, order_scaling=order_scaling, projector_family_comparison=family)
