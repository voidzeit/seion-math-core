"""Gate 7: controls that must fail/degrade, not pass.

A test suite that only ever asserts "PASS" cannot distinguish a correct
implementation from one that is vacuously permissive. Each test here
constructs a case designed to violate an identity or invariant and
checks that the code correctly detects or reflects the violation.
"""
import math

import pytest
import torch

from seion_kgr_reference_fp64 import (
    CPTernaryLaw,
    Projector,
    brute_force_filtered_rank,
    build_reciprocal_kg,
    margin_preserves_order,
)

pytestmark = pytest.mark.symbolic


def test_oblique_projector_is_flagged_by_isometry_residual():
    """A non-orthonormal 'Q' must show a large isometry residual —
    Gate 0/1's 'oblique projector must fail' control."""
    Q_bad = torch.tensor([[1.0, 1.0], [0.0, 1.0], [0.0, 0.0]], dtype=torch.float64)  # not orthonormal columns
    proj = Projector(Q_bad)
    assert proj.isometry_residual() > 1e-3


def test_zero_cp_law_produces_zero_output():
    """Gate 7 'kernel zero' control: O=0 must force the law output to be
    identically zero regardless of A, B, C or the inputs."""
    dim, rank = 3, 2
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.zeros(dim, rank, dtype=torch.float64),
    )
    x, a, q = (torch.randn(dim, dtype=torch.float64) for _ in range(3))
    out = cp.forward(x, a, q)
    assert torch.linalg.norm(out).item() == 0.0


def test_random_cp_law_differs_from_zero_law_almost_surely():
    """Complements the zero-kernel control: a random CP law must NOT
    collapse to zero output (otherwise the zero-law control above would
    be trivially indistinguishable from the general case)."""
    dim, rank = 3, 2
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.randn(dim, rank, dtype=torch.float64),
    )
    x, a, q = (torch.randn(dim, dtype=torch.float64) for _ in range(3))
    out = cp.forward(x, a, q)
    assert torch.linalg.norm(out).item() > 1e-6


def test_filter_removal_must_never_improve_gold_rank():
    """Gate 7: disabling evaluation filters must never make the gold
    entity's rank better (lower) than the filtered rank, since filtering
    only removes *other* true answers from competition."""
    kg = build_reciprocal_kg([(0, 0, 1), (0, 0, 2), (0, 0, 3)], num_entities=6, num_relations=1)
    scores = {0: -1.0, 1: 5.0, 2: 4.0, 3: 3.0, 4: 2.0, 5: 1.0}

    def scorer_fn(h, r, t):
        return scores[t]

    filtered = brute_force_filtered_rank(scorer_fn, kg, h=0, r=0, t=3, mode="tail")

    def unfiltered_rank(h, r, t):
        gold = scorer_fn(h, r, t)
        others = [scorer_fn(h, r, c) for c in range(kg.num_entities) if c != t]
        better = sum(1 for s in others if s > gold + 1e-9)
        ties = sum(1 for s in others if abs(s - gold) <= 1e-9)
        return 1.0 + better + 0.5 * ties

    unfiltered = unfiltered_rank(0, 0, 3)
    assert unfiltered >= filtered, (unfiltered, filtered)
    assert unfiltered > filtered  # in this constructed example it is strictly worse


def test_margin_negative_control_order_can_flip_below_threshold():
    """Gate 7: an insufficient margin (<= 2*epsilon) must NOT be reported
    as certifying order preservation, and a concrete adversarial
    perturbation within epsilon must actually flip the order."""
    s_i, s_j, eps = 1.0, 0.9, 0.2  # gap 0.1 <= 2*0.2
    assert not margin_preserves_order(s_i, s_j, eps)
    s_tilde_i, s_tilde_j = s_i - eps, s_j + eps
    assert s_tilde_i < s_tilde_j  # order really did flip


def test_margin_positive_control_worst_case_perturbation_cannot_flip_order():
    s_i, s_j, eps = 1.0, 0.3, 0.2  # gap 0.7 > 2*0.2
    assert margin_preserves_order(s_i, s_j, eps)
    for sign_i in (-1, 1):
        for sign_j in (-1, 1):
            s_tilde_i = s_i + sign_i * eps
            s_tilde_j = s_j + sign_j * eps
            assert s_tilde_i > s_tilde_j, (sign_i, sign_j, s_tilde_i, s_tilde_j)


def test_asymmetric_cp_law_head_and_tail_predictions_can_differ():
    """Documents (does not 'fix') the v25 finding that a directional
    ternary law is not automatically symmetric between the first slot
    (head-like) and the third slot (tail-like) — regression guard so a
    future accidental symmetrization is not silently assumed."""
    dim, rank = 3, 2
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.randn(dim, rank, dtype=torch.float64),
    )
    x, a, q = (torch.randn(dim, dtype=torch.float64) for _ in range(3))
    forward = cp.forward(x, a, q)
    swapped = cp.forward(q, a, x)  # swap first/third slot
    assert not torch.allclose(forward, swapped, atol=1e-6)
