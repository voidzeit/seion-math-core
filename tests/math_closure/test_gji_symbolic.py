"""Pytest wrapper for the M1 GJI symbolic verification (mission Section
VI: "GJI symbolic canonicalization", "mutation detection"). Runs the
same driver as scripts/math_closure_m1_gji_symbolic.py but asserts on
its output instead of just printing it, so `pytest` catches regressions
automatically rather than requiring a human to read console output.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

import math_closure_m1_gji_symbolic as m1  # noqa: E402
from seion_core.research_v3.polynomial_forests import ternary_declared_gji  # noqa: E402


def test_general_claim_disproved_with_exact_counterexample():
    forest = ternary_declared_gji(law_id="mu", type_name="tau")
    counterexample = m1.exact_rational_counterexample(forest, n=2)
    assert not counterexample["is_zero"], "the general (non-collinear) claim must be nonzero"
    assert counterexample["result_vector"] == ["97/3", "97/3"]


def test_general_claim_nonzero_both_methods_n2_and_n3():
    forest = ternary_declared_gji(law_id="mu", type_name="tau")
    for n in (2, 3):
        result = m1._run_general(forest, n=n, law_id="mu")
        assert not result.method_a_zero, f"Method A unexpectedly zero at n={n}"
        assert not result.method_b_zero, f"Method B unexpectedly zero at n={n}"


def test_collinear_sub_identity_proved_both_dimensions():
    forest = ternary_declared_gji(law_id="mu", type_name="tau")
    for n in (2, 3):
        assert m1._run_collinear(forest, n=n, law_id="mu"), f"collinear identity failed at n={n}"


def test_mutations_detected_except_documented_invariance():
    """3 of 4 mutations must be rejected under the collinear regime; the
    4th (exchange_input) is a documented, proved invariance of the
    collinear case, not a verifier weakness - covered separately below."""

    forest = ternary_declared_gji(law_id="mu", type_name="tau")
    flip_sign = m1._mutated_flip_sign(forest)
    omit_term = m1._mutated_omit_term(forest)
    change_slot = m1._mutated_change_slot(forest, law_id="mu", type_name="tau")

    assert not m1._run_collinear(flip_sign, n=3, law_id="mu")
    assert not m1._run_collinear(omit_term, n=3, law_id="mu")
    assert not m1._run_collinear(change_slot, n=3, law_id="mu")


def test_exchange_input_mutation_is_collinear_invariant_but_changes_general_case():
    forest = ternary_declared_gji(law_id="mu", type_name="tau")
    exchange = m1._mutated_exchange_input(forest)
    assert m1._run_collinear(exchange, n=3, law_id="mu"), (
        "expected this specific mutation to be invisible under collinearity (a proved fact, not a bug)"
    )
    original_general = m1.method_a_generic(forest, law_id="mu", n=2)
    mutated_general = m1.method_a_generic(exchange, law_id="mu", n=2)
    assert original_general != mutated_general, (
        "the mutation must still change the GENERAL (non-collinear) symbolic expression"
    )
