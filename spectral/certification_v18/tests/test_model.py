from __future__ import annotations

import torch

from spectral.certification_v18.model import (
    SpectralModelV18,
    commutator,
    fro_norm,
    identity,
    orthonormalize_columns,
    projector_from_u,
)


def _model(seed: int = 0, n: int = 12, rank: int = 3, arity: int = 3, cp_rank: int = 4, dtype: str = "float64") -> SpectralModelV18:
    gen = torch.Generator().manual_seed(seed)
    return SpectralModelV18(n=n, rank=rank, arity=arity, cp_rank=cp_rank, device="cpu", dtype=dtype, generator=gen)


def test_projector_is_idempotent_and_selfadjoint_by_construction():
    model = _model()
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    idem = fro_norm(P @ P - P).item()
    selfadj = fro_norm(P.conj().T - P).item()
    assert idem < 1e-10
    assert selfadj < 1e-10


def test_raw_commutator_equals_exact_algebraic_identity():
    """[Delta, P] == K @ Delta @ P - P @ Delta @ K identically, independent
    of the CP law — this is an exact algebraic fact about any projector,
    not a property of the coherent-curvature hypothesis under test."""
    model = _model()
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    K = identity(model.n, device=model.device, dtype=model.cdtype) - P
    raw_comm = commutator(model.delta, P)
    identity_form = K @ model.delta @ P - P @ model.delta @ K
    rel = fro_norm(raw_comm - identity_form).item() / (fro_norm(raw_comm).item() + 1e-30)
    assert rel < 1e-9


def test_raw_and_coherent_curvature_share_rank_bound():
    """Both raw_comm and C_theta are algebraically constrained to rank
    <= 2*rank (see model.py docstring derivation); check this numerically
    via singular value decay past that index."""
    model = _model(rank=2, n=16)
    U = orthonormalize_columns(model.u())
    P = projector_from_u(U)
    K = identity(model.n, device=model.device, dtype=model.cdtype) - P
    Phi = model.reduced_curvature_matrix(U)
    raw_comm = commutator(model.delta, P)
    C_theta = model.coherent_dynamic_curvature(U, K, Phi)
    for name, mat in (("raw_comm", raw_comm), ("C_theta", C_theta)):
        svals = torch.linalg.svdvals(mat)
        tail = svals[2 * model.rank :]
        assert tail.abs().max().item() < 1e-8, f"{name} has unexpected rank > 2*rank"


def test_cyclic_product_symmetric_by_construction():
    model = _model(arity=3, n=10, cp_rank=3)
    gen = torch.Generator().manual_seed(1)
    xs = [torch.randn(model.n, dtype=model.rdtype, generator=gen).to(model.cdtype) for _ in range(model.arity)]
    y0 = model.product(*xs)
    y1 = model.product(*(xs[1:] + xs[:1]))
    rel = fro_norm(y0 - y1).item() / (fro_norm(y0).item() + 1e-30)
    assert rel < 1e-9  # structural identity, not a learned property
