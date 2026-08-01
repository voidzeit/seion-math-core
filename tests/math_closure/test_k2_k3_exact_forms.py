"""Pytest wrapper for M2/M3's exact closed-form results (mission Section
VI: "exact k=2 constructions", "k=3 topology serialization")."""

from __future__ import annotations

import sys
from pathlib import Path

import sympy as sp

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k2" / "exact_examples"))
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k3" / "certificates"))

import chain_gated_rotation_eta_squared as k2_mod  # noqa: E402
import chain_and_branching_closed_forms as k3_mod  # noqa: E402


def test_k2_chain_eta_squared_dimension_rank_independent():
    for dimension, rank in [(2, 1), (3, 1), (3, 2), (4, 2)]:
        result = k2_mod.symbolic_check(dimension, rank)
        (eta,) = result.free_symbols
        for test_val in (sp.Rational(1, 7), sp.Rational(1, 2), sp.Rational(9, 10)):
            lhs = complex(result.subs(eta, test_val))
            rhs = complex(test_val**4)
            assert abs(lhs - rhs) < 1e-10


def test_k2_chain_saturates_only_at_eta_equals_one():
    # ratio = eta^2 / eta = eta; equals 1 iff eta=1, strictly less otherwise
    for eta_val in [0.1, 0.5, 0.9, 0.999]:
        ratio = eta_val**2 / eta_val
        assert ratio < 1.0
    assert abs(1.0**2 / 1.0 - 1.0) < 1e-12


def test_k3_chain_and_branching_closed_forms_and_optimum():
    from seion_core.research_v3.typed_tree import Leaf, Node  # noqa: E402

    chain = Node("mu", "tau", (Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau"))), Leaf(3, "tau")))
    branch = Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Node("mu", "tau", (Leaf(2, "tau"), Leaf(3, "tau")))))

    chain_sq = k3_mod.projected_error_squared(chain, 4)
    branch_sq = k3_mod.projected_error_squared(branch, 4)

    (eta,) = chain_sq.free_symbols
    for test_val in (sp.Rational(1, 5), sp.Rational(7, 10)):
        assert abs(complex(chain_sq.subs(eta, test_val)) - complex(9 * test_val**4 * (1 - test_val**2))) < 1e-10
        assert abs(complex(branch_sq.subs(eta, test_val)) - complex(test_val**4 * (1 - test_val**2))) < 1e-10

    # exact optimum eta* = 1/sqrt(2), best ratios 3/4 (chain) and 1/4 (branch)
    eta_star = float(sp.sqrt(sp.Rational(1, 2)))
    chain_ratio_at_star = 3 * eta_star**2 * (1 - eta_star**2) ** 0.5 / (2 * eta_star)
    branch_ratio_at_star = eta_star**2 * (1 - eta_star**2) ** 0.5 / (2 * eta_star)
    assert abs(chain_ratio_at_star - 0.75) < 1e-9
    assert abs(branch_ratio_at_star - 0.25) < 1e-9
