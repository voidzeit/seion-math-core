"""Block B — full deployed-failure ablation matrix.

Extends block_b_commutator.py's capacity-ceiling result (isolated B
objective drives comm_unexplained_rel to ~0) with the mechanism-diagnosis
matrix the mission requires: is the deployed WARN/FAIL result (all
historical checkpoints, coherence_ratio <= 0) caused by objective
conflict, scale imbalance, gradient starvation, parameterization, or
non-identifiability? Each regime below isolates one candidate mechanism.

Regimes:
- isolated: B objective only (already in block_b_commutator.py; repeated
  here for a single consistent report).
- plus_closure / plus_associator: B jointly with ONE competing objective
  (closure defect / projected-associator defect respectively), equal
  weight — tests whether ANY single competing objective alone reproduces
  the deployed degradation, or whether it takes many simultaneously.
- joint_all: B with BOTH competing objectives simultaneously, equal
  weight — closer to (but far simpler than) the historical 16-term loss.
- staged: train on the competing objectives FIRST (B weight 0), then
  switch to B-only — tests whether a bad starting point (a U shaped by
  other objectives) prevents B from later reaching its own optimum, i.e.
  gradient starvation/local-optimum trapping rather than a fundamental
  conflict.
- frozen_law_train_projector: freeze the CP law's parameters at their
  random initial values, train only U — isolates whether the projector
  alone (without also shaping the law) can satisfy B.
- frozen_projector_train_law: the reverse — freeze U, train only the CP
  law's parameters (which determine Phi via the associator) — isolates
  whether reshaping the law alone (holding the subspace fixed) suffices.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from spectral.certification_v18.model import SpectralModelV18, commutator, fro_norm, identity, orthonormalize_columns, projector_from_u


def _closure_defect(model: SpectralModelV18, U: torch.Tensor, y2: torch.Tensor, extras: list) -> torch.Tensor:
    parts = []
    for i in range(U.shape[1]):
        y = model.product(U[:, i], y2, *extras)
        y_in = U @ (U.conj().T @ y)
        parts.append(y - y_in)
    residual = torch.cat(parts)
    return torch.sum(residual.real**2) + torch.sum(residual.imag**2)


def _associator_defect(model: SpectralModelV18, U: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    a = model.associator(x, y, z)
    P = projector_from_u(U)
    a_proj = P @ a
    res = a - a_proj
    return torch.sum(res.real**2) + torch.sum(res.imag**2)


def _comm_unexplained_rel(model: SpectralModelV18, U: torch.Tensor) -> torch.Tensor:
    P = projector_from_u(U)
    K = identity(model.n, device=model.device, dtype=model.cdtype) - P
    Phi = model.reduced_curvature_matrix(U)
    raw_comm = commutator(model.delta, P)
    c_theta = model.coherent_dynamic_curvature(U, K, Phi)
    return fro_norm(raw_comm - c_theta) / (fro_norm(raw_comm) + 1e-30)


@dataclass
class AblationRow:
    regime: str
    final_comm_unexplained_rel: float
    final_closure_defect: float
    final_associator_defect: float


def _train(
    model: SpectralModelV18,
    *,
    steps: int,
    lr: float,
    weight_b: float,
    weight_closure: float,
    weight_assoc: float,
    train_law: bool,
    train_projector: bool,
    gen: torch.Generator,
) -> dict:
    params = []
    if train_projector:
        params += [model.u_re, model.u_im]
    if train_law:
        params += list(model.product.parameters())
    if not params:
        params = [model.u_re]  # avoid empty-optimizer edge case; effectively frozen if lr later set to 0 externally

    opt = torch.optim.Adam(params, lr=lr)
    extras = [model.anchor.detach() for _ in range(model.arity - 2)]
    y2 = torch.complex(torch.randn(model.n, generator=gen, dtype=torch.float64), torch.randn(model.n, generator=gen, dtype=torch.float64))
    y2 = y2 / torch.linalg.norm(y2)
    x_a = torch.complex(torch.randn(model.n, generator=gen, dtype=torch.float64), torch.randn(model.n, generator=gen, dtype=torch.float64))
    y_a = torch.complex(torch.randn(model.n, generator=gen, dtype=torch.float64), torch.randn(model.n, generator=gen, dtype=torch.float64))
    z_a = torch.complex(torch.randn(model.n, generator=gen, dtype=torch.float64), torch.randn(model.n, generator=gen, dtype=torch.float64))

    for _ in range(steps):
        opt.zero_grad()
        U = orthonormalize_columns(model.u())
        loss = torch.zeros((), dtype=torch.float64)
        if weight_b > 0:
            loss = loss + weight_b * _comm_unexplained_rel(model, U) ** 2
        if weight_closure > 0:
            loss = loss + weight_closure * _closure_defect(model, U, y2, extras)
        if weight_assoc > 0:
            loss = loss + weight_assoc * _associator_defect(model, U, x_a, y_a, z_a)
        loss.backward()
        opt.step()

    with torch.no_grad():
        U = orthonormalize_columns(model.u())
        return {
            "comm_unexplained_rel": _comm_unexplained_rel(model, U).item(),
            "closure_defect": _closure_defect(model, U, y2, extras).item(),
            "associator_defect": _associator_defect(model, U, x_a, y_a, z_a).item(),
        }


def full_ablation_matrix(seed: int = 0, *, n: int = 16, rank: int = 4, cp_rank: int = 4, steps: int = 400, lr: float = 5e-3) -> list[AblationRow]:
    rows = []
    regimes = [
        ("isolated_B_only", dict(weight_b=1.0, weight_closure=0.0, weight_assoc=0.0, train_law=True, train_projector=True)),
        ("plus_closure", dict(weight_b=1.0, weight_closure=1.0, weight_assoc=0.0, train_law=True, train_projector=True)),
        ("plus_associator", dict(weight_b=1.0, weight_closure=0.0, weight_assoc=1.0, train_law=True, train_projector=True)),
        ("joint_all", dict(weight_b=1.0, weight_closure=1.0, weight_assoc=1.0, train_law=True, train_projector=True)),
        ("frozen_law_train_projector", dict(weight_b=1.0, weight_closure=0.0, weight_assoc=0.0, train_law=False, train_projector=True)),
        ("frozen_projector_train_law", dict(weight_b=1.0, weight_closure=0.0, weight_assoc=0.0, train_law=True, train_projector=False)),
    ]
    for name, kwargs in regimes:
        gen = torch.Generator().manual_seed(seed)
        model = SpectralModelV18(n=n, rank=rank, arity=3, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
        result = _train(model, steps=steps, lr=lr, **kwargs, gen=gen)
        rows.append(
            AblationRow(
                regime=name,
                final_comm_unexplained_rel=result["comm_unexplained_rel"],
                final_closure_defect=result["closure_defect"],
                final_associator_defect=result["associator_defect"],
            )
        )

    # staged: train on closure+associator FIRST (B weight 0), then switch to B-only
    gen = torch.Generator().manual_seed(seed)
    model = SpectralModelV18(n=n, rank=rank, arity=3, cp_rank=cp_rank, device="cpu", dtype="float64", generator=gen)
    _train(model, steps=steps // 2, lr=lr, weight_b=0.0, weight_closure=1.0, weight_assoc=1.0, train_law=True, train_projector=True, gen=gen)
    result_staged = _train(model, steps=steps // 2, lr=lr, weight_b=1.0, weight_closure=0.0, weight_assoc=0.0, train_law=True, train_projector=True, gen=gen)
    rows.append(
        AblationRow(
            regime="staged_competing_then_B",
            final_comm_unexplained_rel=result_staged["comm_unexplained_rel"],
            final_closure_defect=result_staged["closure_defect"],
            final_associator_defect=result_staged["associator_defect"],
        )
    )
    return rows
