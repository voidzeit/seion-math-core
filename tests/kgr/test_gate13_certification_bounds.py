"""Gate 13.4 acceptance tests (``campaigns/gate13/``): analytic bound
validity + the mission brief's mandatory negative controls.

Covers, in order: CP-closure and linear-residual operator-norm bounds
never violated across random sweeps; message sensitivity (global and
query-conditioned) never violated against an actual autograd Jacobian;
the LayerNorm+tanh envelope bound never violated (including an FP64
small-dimension exact-Jacobian comparison); the multi-hop recurrence
bound never violated against a REAL reference-vs-compressed state
difference; state-to-score/ranking certification never produces a false
certificate; and the required negative controls (dropping a bound
factor, underestimating a norm, type-rejecting a sample-mean proxy,
rejecting an oblique projector, insufficient margin, unsupported
selector, a deliberately corrupted bound showing up as an observed
violation, and the mathematical guarantee that a certified query's
ranking never flips).
"""
from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.certification import certify_path_query
from seion_kgr.certified_bounds import (
    CertifiedBound,
    EmpiricalErrorPredictor,
    check_projector_gate1,
    cp_closure_bound,
    envelope_lipschitz_bound,
    linear_residual_bound,
    message_closure_bound,
    message_sensitivity_bound_global,
    message_sensitivity_bound_query_conditioned,
    observed_envelope_jacobian_norm,
)
from seion_kgr.certified_path import propagate_certified_state_bounds
from seion_kgr.frontier_ops import build_csr_adjacency
from seion_kgr.kernels import CPTernaryLaw, StiefelProjector
from seion_kgr.reasoner import Adjacency
from seion_kgr.reasoner_batched import BatchedPathReasoner

TOL = 1e-5


def _small_graph():
    out_edges = {
        0: [(0, 1), (1, 2)], 1: [(0, 3)], 2: [(1, 3)],
        3: [(0, 4), (1, 5)], 4: [(0, 6)], 5: [(1, 6)], 7: [(0, 8)],
    }
    return Adjacency(out_edges), 10


# ------------------------------------------------------------------ CP closure + linear residual


def test_cp_closure_bound_never_violated_random_sweep():
    torch.manual_seed(0)
    dim, rank, proj_rank = 8, 4, 3
    law = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    projector = StiefelProjector(dim, proj_rank)
    bound = cp_closure_bound(law, projector)
    assert bound.valid()

    p = projector.P()
    for _ in range(500):
        x, a, q = (torch.randn(dim) for _ in range(3))
        x, a, q = x / x.norm(), a / a.norm(), q / q.norm()
        out = law(x, a, q)
        residual = out - p @ out
        assert residual.norm().item() <= bound.value + 1e-6


def test_linear_residual_bounds_never_violated_random_sweep():
    torch.manual_seed(1)
    dim, proj_rank = 8, 3
    U = nn.Linear(dim, dim, bias=False)
    nn.init.xavier_uniform_(U.weight)
    projector = StiefelProjector(dim, proj_rank)
    bound = linear_residual_bound(U, projector, "U")
    p = projector.P()
    for _ in range(500):
        x = torch.randn(dim)
        x = x / x.norm()
        out = U(x)
        residual = out - p @ out
        assert residual.norm().item() <= bound.value + 1e-6


def test_message_closure_bound_never_violated_random_sweep():
    torch.manual_seed(2)
    dim, rank, proj_rank = 8, 4, 3
    law = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    U, V, W = (nn.Linear(dim, dim, bias=False) for _ in range(3))
    for layer in (U, V, W):
        nn.init.xavier_uniform_(layer.weight, gain=0.1)
    projector = StiefelProjector(dim, proj_rank)
    mc = message_closure_bound(law, U, V, W, projector)
    p = projector.P()
    for _ in range(500):
        x, a, q = (torch.randn(dim) for _ in range(3))
        x, a, q = x / x.norm(), a / a.norm(), q / q.norm()
        m_tilde = law(x, a, q) + U(x) + V(a) + W(q)
        residual = m_tilde - p @ m_tilde
        assert residual.norm().item() <= mc.total.value + 1e-6


# ------------------------------------------------------------------ Lipschitz sensitivity


def test_message_sensitivity_bounds_never_violated_vs_autograd_jacobian():
    torch.manual_seed(3)
    dim, rank = 6, 3
    law = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    U = nn.Linear(dim, dim, bias=False)
    nn.init.xavier_uniform_(U.weight)

    global_bound = message_sensitivity_bound_global(law, U)
    for _ in range(100):
        # unit-normalized: ||B||_2/||C||_2 (used by the global bound) are
        # sup-over-unit-ball quantities, so the query-conditioned bound is
        # only guaranteed <= the global one when a,q themselves are unit norm.
        a = torch.randn(dim)
        a = a / a.norm()
        q = torch.randn(dim)
        q = q / q.norm()

        def f(x):
            return law(x, a, q) + U(x)

        x0 = torch.randn(dim, requires_grad=True)
        jac = torch.autograd.functional.jacobian(f, x0)
        observed_sv = torch.linalg.matrix_norm(jac, ord=2).item()
        assert observed_sv <= global_bound.value + 1e-4

        query_bound = message_sensitivity_bound_query_conditioned(law, U, a.unsqueeze(0), q.unsqueeze(0))
        assert observed_sv <= query_bound.value + 1e-4
        # query-conditioned must never be LOOSER than the global bound's own worst case
        # (it uses the actual Ba/Cq norms, which are <= the operator norms ||B||/||C||)
        assert query_bound.value <= global_bound.value + 1e-4


# ------------------------------------------------------------------ nonlinear envelope


def test_envelope_lipschitz_bound_never_violated_fp32_sweep():
    torch.manual_seed(4)
    dim = 8
    ln = nn.LayerNorm(dim)
    bound = envelope_lipschitz_bound(ln)
    samples = torch.randn(30, dim) * 5
    observed = observed_envelope_jacobian_norm(ln, samples)
    assert observed.value <= bound.value + 1e-4


def test_envelope_lipschitz_bound_never_violated_fp64_small_dim_exact_jacobian():
    """FP64, small dimension — the mission brief's specific '3. LayerNorm
    bound never violated against exact Jacobians in small dimensions'
    analytic test."""
    torch.manual_seed(5)
    dim = 3
    ln = nn.LayerNorm(dim, dtype=torch.float64)
    bound = envelope_lipschitz_bound(ln)
    for _ in range(200):
        z0 = torch.randn(dim, dtype=torch.float64, requires_grad=True)

        def f(z):
            return ln(torch.tanh(z))

        jac = torch.autograd.functional.jacobian(f, z0)
        observed_sv = torch.linalg.matrix_norm(jac, ord=2).item()
        assert observed_sv <= bound.value + 1e-9


# ------------------------------------------------------------------ multi-hop recurrence vs a REAL reference/compressed pair


def _build_ref_cmp_pair(dim=8, rank=4, proj_rank=3, num_layers=1, selector_mode="full_neighborhood", seed=0):
    torch.manual_seed(seed)
    ref = BatchedPathReasoner(dim=dim, rank=rank, num_layers=num_layers, max_neighbors=16, proj_rank=0, selector_mode=selector_mode)
    cmp = BatchedPathReasoner(dim=dim, rank=rank, num_layers=num_layers, max_neighbors=16, proj_rank=proj_rank, selector_mode=selector_mode)
    sd, cmp_sd = ref.state_dict(), cmp.state_dict()
    for k in sd:
        if k in cmp_sd:
            cmp_sd[k] = sd[k]
    cmp.load_state_dict(cmp_sd)
    return ref, cmp


def test_multihop_recurrence_bound_never_violated_vs_real_state_difference():
    from seion_kgr.path_reasoner_output import PathReasonerOutput

    adjacency, num_nodes = _small_graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    ref, cmp = _build_ref_cmp_pair(num_layers=2)
    relation_embed = torch.randn(4, ref.dim)
    h, r, t = torch.tensor([0, 1, 2, 3]), torch.tensor([0, 0, 0, 0]), torch.tensor([3, 4, 5, 6])
    qv = relation_embed[r]

    frontier_ref = ref.run_batch_frontiers(csr, relation_embed, h, r, t, qv, seed=0, training=False)
    frontier_cmp = cmp.run_batch_frontiers(csr, relation_embed, h, r, t, qv, seed=0, training=False)
    bounds, ledger, closure = propagate_certified_state_bounds(cmp, csr, relation_embed, h, r, t, qv, seed=0, training=False)

    out_ref = PathReasonerOutput.from_batched_frontier(frontier_ref, num_nodes, ref.unreached_state)
    out_cmp = PathReasonerOutput.from_batched_frontier(frontier_cmp, num_nodes, cmp.unreached_state)
    assert bounds, "no (query,node) reached — fixture too degenerate to test the recurrence"
    for (q, n), bound in bounds.items():
        assert bound.valid()
        s_ref = out_ref.state_for(torch.tensor([q]), torch.tensor([n]))[0]
        s_cmp = out_cmp.state_for(torch.tensor([q]), torch.tensor([n]))[0]
        observed = (s_ref - s_cmp).norm().item()
        assert observed <= bound.value + 1e-4


# ------------------------------------------------------------------ state-to-score / ranking: never a false certificate


def test_certify_path_query_never_produces_a_false_certificate():
    """Construct scores where the gold candidate's margin is EXACTLY at
    the certification threshold (2*epsilon), then perturb the runner-up's
    score by up to epsilon in the adversarial direction — for any
    CERTIFIED query, the ranking must never flip, by the bound's own
    mathematical guarantee (mission brief negative control #8)."""
    torch.manual_seed(6)
    entity = nn.Embedding(5, 4)
    dim = 4
    bound = CertifiedBound(value=0.5, formula="test", assumptions=[])
    gamma_r = 1.0
    from seion_kgr.certification import entity_norm_bound
    C_E = entity_norm_bound(entity.weight)
    epsilon = abs(gamma_r) * (C_E / (dim ** 0.5)) * bound.value

    gold_index = 4
    runner_up = 3.0
    scores = torch.tensor([0.0, 1.0, 2.0, runner_up, runner_up + 2.0 * epsilon + 0.01])  # gold strictly the max, margin just above 2*epsilon
    result = certify_path_query(0, scores, gold_index, bound, gamma_r, entity.weight, dim)
    assert result.certified_rank_stable
    assert int(scores.argmax().item()) == gold_index

    # Adversarially perturb every OTHER candidate upward by <= epsilon and
    # the gold candidate downward by <= epsilon — the certified bound
    # guarantees the true (uncertain) scores could differ by at most
    # epsilon in either direction, so rank must still hold under ANY such
    # perturbation.
    for _ in range(200):
        perturbed = scores.clone()
        perturbed[gold_index] -= epsilon * torch.rand(1).item()  # worst case: gold pushed DOWN by up to epsilon
        for i in range(scores.numel()):
            if i != gold_index:
                perturbed[i] += epsilon * torch.rand(1).item()  # worst case: every rival pushed UP by up to epsilon
        assert int(perturbed.argmax().item()) == gold_index, (
            "a certified query's ranking flipped under a within-bound adversarial perturbation"
        )


def test_certify_path_query_insufficient_margin_is_not_certified():
    entity = nn.Embedding(5, 4)
    dim = 4
    bound = CertifiedBound(value=10.0, formula="test", assumptions=[])  # deliberately huge -> epsilon huge -> margin can't clear it
    scores = torch.tensor([0.0, 1.0, 0.5, 0.3, 1.1])
    result = certify_path_query(0, scores, 4, bound, gamma_r=1.0, entity_weight=entity.weight, dim=dim)
    assert not result.certified_rank_stable


def test_certify_path_query_unreached_gold_is_not_certified():
    entity = nn.Embedding(5, 4)
    result = certify_path_query(0, torch.randn(5), 2, None, gamma_r=1.0, entity_weight=entity.weight, dim=4)
    assert not result.certified_rank_stable
    assert result.state_error_bound is None
    assert "never reached" in result.certificate_reason


# ------------------------------------------------------------------ negative controls


def test_negative_control_dropping_the_reduction_factor_causes_violations():
    """A bound missing one of its required multiplicative factors (here:
    scaled down as if a factor of ~20 had been dropped, calibrated so
    random unit-ball sampling reliably exposes it — see the loose-bound
    discussion in this module: random directions rarely hit the TRUE
    worst case, so a merely modest understatement is not exposed within a
    bounded sweep) must show observed violations."""
    torch.manual_seed(7)
    dim, rank, proj_rank = 8, 4, 3
    law = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    projector = StiefelProjector(dim, proj_rank)
    correct_bound = cp_closure_bound(law, projector)
    corrupted_bound = correct_bound.value * 0.02  # simulates dropping a real multiplicative factor
    p = projector.P()
    violations = 0
    for _ in range(2000):
        x, a, q = (torch.randn(dim) for _ in range(3))
        x, a, q = x / x.norm(), a / a.norm(), q / q.norm()
        out = law(x, a, q)
        residual = (out - p @ out).norm().item()
        if residual > corrupted_bound:
            violations += 1
    assert violations > 0, "dropping a bound factor did not produce ANY violation — the sweep is not sensitive enough to be a meaningful negative control"
    assert correct_bound.valid()


def test_negative_control_underestimated_norm_causes_violations():
    torch.manual_seed(8)
    dim, rank, proj_rank = 8, 4, 3
    law = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
    projector = StiefelProjector(dim, proj_rank)
    correct = cp_closure_bound(law, projector)
    understated = CertifiedBound(value=correct.value * 0.01, formula="deliberately understated x100", assumptions=correct.assumptions)
    p = projector.P()
    violations = 0
    for _ in range(500):
        x, a, q = (torch.randn(dim) for _ in range(3))
        x, a, q = x / x.norm(), a / a.norm(), q / q.norm()
        out = law(x, a, q)
        residual = (out - p @ out).norm().item()
        if residual > understated.value:
            violations += 1
    assert violations > 0


def test_negative_control_sample_mean_proxy_is_type_rejected_not_used_as_a_bound():
    """`measure_closure_leakage_sample` (projection.py) is an
    `empirical_error_predictor`-tier quantity, not a certified bound — it
    must be structurally impossible to pass where `certify_path_query`
    expects a `CertifiedBound`."""
    from seion_kgr.projection import measure_closure_leakage_sample

    torch.manual_seed(9)
    dim, proj_rank = 8, 3
    projector = StiefelProjector(dim, proj_rank)
    sample_result = measure_closure_leakage_sample(projector, torch.randn(16, dim))
    proxy = EmpiricalErrorPredictor(value=sample_result["mean_ratio"], description="projection.py sample-mean closure leakage")

    entity = nn.Embedding(5, dim)
    import pytest
    with pytest.raises(TypeError):
        certify_path_query(0, torch.randn(5), 0, proxy, 1.0, entity.weight, dim)


def test_negative_control_oblique_projector_is_rejected():
    """An artificially-constructed OBLIQUE projector (idempotent, P^2=P,
    but NOT symmetric) must fail `check_projector_gate1`'s new symmetry
    check — `StiefelProjector.P() = Q Q^T` never produces one, so this
    constructs a fake stand-in object to exercise the rejection path."""

    class _ObliqueProjector:
        enabled = True

        def __init__(self, dim):
            # P = v w^T / (w^T v), a rank-1 idempotent-but-not-symmetric projector when v != w
            v = torch.tensor([1.0] + [0.0] * (dim - 1))
            w = torch.tensor([1.0, 1.0] + [0.0] * (dim - 2))
            self._P = torch.outer(v, w) / torch.dot(w, v)

        def P(self):
            return self._P

        def isometry_residual(self):
            return 0.0

        def idempotent_residual(self):
            return float(torch.linalg.norm(self._P @ self._P - self._P).item())

    oblique = _ObliqueProjector(dim=4)
    assert oblique.idempotent_residual() < 1e-6  # IS idempotent
    checks = check_projector_gate1(oblique)
    symmetry_check = next(c for c in checks if c.name == "projector_symmetric")
    assert not symmetry_check.passed, "an oblique (non-symmetric) projector was NOT rejected"


def test_negative_control_learned_topk_is_not_supported_for_certification():
    """`BatchedPathReasoner` already rejects `learned_topk` at
    construction (Gate 13.2's scope cut) — this test documents that
    certification therefore can never be attempted against it either,
    closing the loop rather than leaving it merely implicit."""
    import pytest
    with pytest.raises(ValueError, match="learned_topk"):
        BatchedPathReasoner(dim=8, rank=4, num_layers=1, max_neighbors=8, proj_rank=2, selector_mode="learned_topk")
