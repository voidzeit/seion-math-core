"""Gate 4 (oracle scope): autograd flows through every Fase-1 object.

This does not audit a trainer's regularizer weights (that is Fase 3/8's
job, on real loss functions); it checks that the mathematical objects
themselves are differentiable end to end, since a broken gradient path
here would silently break every later phase built on top of them.
"""
import pytest
import torch

from seion_kgr_reference_fp64 import CPTernaryLaw, MessagePassingLayer, Projector, SeionicScalarScorer

pytestmark = pytest.mark.symbolic


def test_cp_forward_gradients_reach_all_four_factors():
    dim, rank = 4, 3
    A = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    B = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    C = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    O = torch.randn(dim, rank, dtype=torch.float64, requires_grad=True)
    cp = CPTernaryLaw(A=A, B=B, C=C, O=O)
    x = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    a = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    q = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    out = cp.forward(x, a, q).sum()
    out.backward()
    for name, tensor in (("A", A), ("B", B), ("C", C), ("O", O), ("x", x), ("a", a), ("q", q)):
        assert tensor.grad is not None, f"{name} has no gradient"
        assert float(tensor.grad.norm().item()) > 0.0, f"{name} gradient is zero"


def test_cp_dense_reconstruction_is_intentionally_non_differentiable():
    """``dense_tensor_explicit_loops`` builds its cross-check tensor from
    plain Python ``float()`` conversions specifically so it shares no
    tensor-op code path with ``forward`` (CLM_KGR_002's independence
    requirement). That means it must NOT be used inside a training loop
    and must NOT carry gradients — this test documents and locks that
    property rather than asserting the opposite."""
    dim, rank = 2, 2
    A = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    B = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    C = torch.randn(rank, dim, dtype=torch.float64, requires_grad=True)
    O = torch.randn(dim, rank, dtype=torch.float64, requires_grad=True)
    cp = CPTernaryLaw(A=A, B=B, C=C, O=O)
    K = cp.dense_tensor_explicit_loops()
    assert not K.requires_grad
    with pytest.raises(RuntimeError):
        K.sum().backward()


def test_message_passing_gradients_reach_law_and_residual_branches():
    dim = 4
    A = torch.randn(2, dim, dtype=torch.float64, requires_grad=True)
    B = torch.randn(2, dim, dtype=torch.float64, requires_grad=True)
    C = torch.randn(2, dim, dtype=torch.float64, requires_grad=True)
    O = torch.randn(dim, 2, dtype=torch.float64, requires_grad=True)
    U = torch.randn(dim, dim, dtype=torch.float64, requires_grad=True)
    V = torch.randn(dim, dim, dtype=torch.float64, requires_grad=True)
    W = torch.randn(dim, dim, dtype=torch.float64, requires_grad=True)
    layer = MessagePassingLayer(mu=CPTernaryLaw(A, B, C, O), U=U, V=V, W=W, P_out=Projector.identity(dim))
    x = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    a = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    q = torch.randn(dim, dtype=torch.float64, requires_grad=True)
    out = layer.message_projected(x, a, q).sum()
    out.backward()
    for name, tensor in (("A", A), ("B", B), ("C", C), ("O", O), ("U", U), ("V", V), ("W", W)):
        assert tensor.grad is not None and float(tensor.grad.norm().item()) > 0.0, name


def test_seionic_scorer_gradients_reach_entity_and_cp_factors():
    dim_e = dim_r = dim_q = 3
    rank = 2
    entity = torch.randn(4, dim_e, dtype=torch.float64, requires_grad=True)
    A = torch.randn(rank, dim_e, dtype=torch.float64, requires_grad=True)
    B = torch.randn(rank, dim_r, dtype=torch.float64, requires_grad=True)
    C = torch.randn(rank, dim_r, dtype=torch.float64, requires_grad=True)
    O = torch.randn(dim_q, rank, dtype=torch.float64, requires_grad=True)
    T = torch.randn(dim_q, dim_e, dtype=torch.float64, requires_grad=True)
    relation = torch.randn(2, dim_r, dtype=torch.float64, requires_grad=True)
    scorer = SeionicScalarScorer(entity=entity, A=A, B=B, C=C, O=O, T=T, relation=relation)
    score = scorer.score_all_candidates(0, 0).sum()
    score.backward()
    for name, tensor in (
        ("entity", entity),
        ("A", A),
        ("B", B),
        ("C", C),
        ("O", O),
        ("T", T),
        ("relation", relation),
    ):
        assert tensor.grad is not None and float(tensor.grad.norm().item()) > 0.0, name
