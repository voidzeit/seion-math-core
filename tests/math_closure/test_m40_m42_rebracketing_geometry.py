"""M40-M42: the k=2 rebracketing constants J_2 = 2, H_2 = 2, S_2 = Sigma_2(eta).

Theorems in research/rebracketing_geometry/RG_CANONICAL.md. These tests are
implementation controls for the witnesses plus randomized falsification of the
three ceilings; they do not stand in for the proofs.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "rebracketing_geometry"))

from rg_witnesses import (  # noqa: E402
    audit, contract3, evaluate_pair, op_norm, sigma2, witness_j2_dim2,
    witness_j2_dim3, witness_s2,
)

ETAS = [0.05, 0.2, 0.5, 1 / math.sqrt(2), 0.9, 1.0]


# --------------------------------------------------------------------------
# Sigma_2 itself
# --------------------------------------------------------------------------

@pytest.mark.parametrize("eta", ETAS)
def test_sigma2_matches_the_piecewise_closed_form(eta):
    expected = 2 * math.sqrt(1 - eta**2) if eta <= 1 / math.sqrt(2) else 1 / eta
    assert sigma2(eta) == pytest.approx(expected, abs=1e-14)


def test_sigma2_is_continuous_at_the_crossover_and_strictly_below_two():
    crossover = 1 / math.sqrt(2)
    assert sigma2(crossover) == pytest.approx(math.sqrt(2), abs=1e-14)
    assert sigma2(crossover - 1e-9) == pytest.approx(math.sqrt(2), abs=1e-7)
    assert sigma2(crossover + 1e-9) == pytest.approx(math.sqrt(2), abs=1e-7)
    for eta in ETAS:
        assert sigma2(eta) < 2.0
    assert sigma2(1e-6) == pytest.approx(2.0, abs=1e-10)   # -> 2 only as eta->0


# --------------------------------------------------------------------------
# the witnesses
# --------------------------------------------------------------------------

@pytest.mark.parametrize("eta", ETAS)
@pytest.mark.parametrize("builder",
                         [witness_j2_dim3, witness_j2_dim2, witness_s2])
def test_witnesses_are_admissible_and_attain_their_constants(eta, builder):
    report = audit(builder(eta))
    failed = [name for name, ok in report["checks"].items() if not ok]
    assert not failed, f"{report['name']} at eta={eta}: {failed}"


@pytest.mark.parametrize("eta", ETAS)
def test_j2_witness_saturates_both_trees_and_conceals_completely(eta):
    """M40 + M41: two maximal, exactly anti-aligned errors, and Ahat = 0."""
    witness = witness_j2_dim3(eta)
    values = evaluate_pair(
        witness["mu_inner_L"], witness["P_inner_L"], witness["mu_root_L"],
        witness["mu_inner_M"], witness["P_inner_M"], witness["mu_root_M"],
        witness["P_root"], witness["leaves"])

    # each tree separately saturates C_2^P = 1
    assert np.linalg.norm(values["e_L"]) == pytest.approx(eta, abs=1e-14)
    assert np.linalg.norm(values["e_M"]) == pytest.approx(eta, abs=1e-14)
    # exactly anti-aligned: chi = -1
    assert values["e_L"] @ values["e_M"] == pytest.approx(-eta**2, abs=1e-14)
    # the compressed computation reports literal associativity
    assert np.linalg.norm(values["A_hat"]) == pytest.approx(0.0, abs=1e-14)
    # while the ambient one is maximally non-associative
    assert np.linalg.norm(values["PA"]) == pytest.approx(2 * eta, abs=1e-14)
    assert np.linalg.norm(values["D"]) == pytest.approx(2 * eta, abs=1e-14)


@pytest.mark.parametrize("eta", ETAS)
def test_s2_witness_fabricates_exactly_sigma2_from_nothing(eta):
    """M42: A = 0 exactly, yet the compressed computation reports a defect."""
    witness = witness_s2(eta)
    values = evaluate_pair(
        witness["mu_inner_L"], witness["P_inner_L"], witness["mu_root_L"],
        witness["mu_inner_M"], witness["P_inner_M"], witness["mu_root_M"],
        witness["P_root"], witness["leaves"])
    assert np.linalg.norm(values["A"]) == pytest.approx(0.0, abs=1e-14)
    assert np.linalg.norm(values["A_hat"]) == pytest.approx(
        sigma2(eta) * eta, abs=1e-14)


@pytest.mark.parametrize("eta", ETAS)
def test_the_shared_law_witness_really_shares_one_law_and_one_projector(eta):
    """M40's class claim: the hierarchy of Definition 1.5 collapses at k=2."""
    witness = witness_j2_dim3(eta)
    laws = [witness[key] for key in
            ("mu_inner_L", "mu_root_L", "mu_inner_M", "mu_root_M")]
    for law in laws[1:]:
        assert np.array_equal(law, laws[0])
    projectors = [witness[key] for key in
                  ("P_inner_L", "P_inner_M", "P_root")]
    for projector in projectors[1:]:
        assert np.array_equal(projector, projectors[0])
    # and every leaf lies in Ran(P), so the witness survives the stricter
    # reading in which leaf data must already be reduced
    P = witness["P_root"]
    for leaf in witness["leaves"]:
        assert np.allclose(P @ leaf, leaf, atol=1e-14)


def test_witness_operator_norms_are_exactly_one_not_merely_below_one():
    """An inadmissible law proves nothing; a slack one proves less."""
    for builder in (witness_j2_dim3, witness_j2_dim2, witness_s2):
        witness = builder(0.4)
        for key in ("mu_inner_L", "mu_root_L", "mu_root_M"):
            measured = op_norm(witness[key], restarts=200, iters=40, seed=5)
            assert measured["value"] == pytest.approx(1.0, abs=1e-9)
            assert measured["no_stall"]


# --------------------------------------------------------------------------
# randomized falsification of the three ceilings
# --------------------------------------------------------------------------

def _random_admissible_pair(rng, dim, eta):
    """A random admissible k=2 pair, in the free class.

    Root laws are taken P-valued (Lemma 2.2); inner laws are scaled to
    operator norm 1 and then have their normal component shrunk until the
    closure budget holds. The closure norm is measured, not assumed.
    """
    rank = int(rng.integers(1, dim))
    P_root = np.diag([1.0] * rank + [0.0] * (dim - rank))
    projectors = []
    for _ in range(2):
        inner_rank = int(rng.integers(1, dim))
        projectors.append(np.diag([1.0] * inner_rank + [0.0] *
                                  (dim - inner_rank)))

    def inner_law(projector):
        raw = rng.standard_normal((dim,) * 4)
        raw /= op_norm(raw, restarts=60, iters=40, seed=int(rng.integers(1e6))
                       )["value"]
        normal = np.eye(dim) - projector
        defect = op_norm(np.einsum("qo,oacd->qacd", normal, raw), restarts=60,
                         iters=40, seed=int(rng.integers(1e6)))["value"]
        if defect > eta:
            raw = (np.einsum("qo,oacd->qacd", projector, raw)
                   + (eta / defect) * np.einsum("qo,oacd->qacd", normal, raw))
        return raw

    def root_law():
        raw = np.einsum("qo,oacd->qacd", P_root, rng.standard_normal((dim,) * 4))
        return raw / op_norm(raw, restarts=60, iters=40,
                             seed=int(rng.integers(1e6)))["value"]

    leaves = rng.standard_normal((5, dim))
    leaves /= np.linalg.norm(leaves, axis=1, keepdims=True)
    return (inner_law(projectors[0]), projectors[0], root_law(),
            inner_law(projectors[1]), projectors[1], root_law(),
            P_root, list(leaves))


@pytest.mark.parametrize("eta", [0.2, 1 / math.sqrt(2), 0.95])
def test_random_admissible_pairs_never_exceed_the_three_ceilings(eta):
    rng = np.random.default_rng(20260816)
    for _ in range(40):
        configuration = _random_admissible_pair(rng, int(rng.integers(2, 5)),
                                                eta)
        values = evaluate_pair(*configuration)
        A_hat = np.linalg.norm(values["A_hat"])
        PA = np.linalg.norm(values["PA"])
        assert np.linalg.norm(values["D"]) <= 2 * eta + 1e-9          # J_2
        assert PA - A_hat <= 2 * eta + 1e-9                           # H_2
        assert A_hat - PA <= sigma2(eta) * eta + 1e-9                 # S_2
        # and the bridge identity, which the ceilings are derived from
        assert values["D"] == pytest.approx(-values["e_L"] + values["e_M"],
                                            abs=1e-12)


@pytest.mark.parametrize("eta", [0.2, 1 / math.sqrt(2), 0.95])
def test_each_tree_alone_obeys_c2_equals_one(eta):
    """The single-tree constant the pair constants are built on."""
    rng = np.random.default_rng(4242)
    for _ in range(25):
        configuration = _random_admissible_pair(rng, 3, eta)
        values = evaluate_pair(*configuration)
        assert np.linalg.norm(values["e_L"]) <= eta + 1e-9
        assert np.linalg.norm(values["e_M"]) <= eta + 1e-9


# --------------------------------------------------------------------------
# Theorem 5.1's optimization, checked without tensors or an operator-norm
# estimator. This is the one verification of Sigma_2 that is immune to the
# estimator convergence defect recorded in RG_CANONICAL.md section 9.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("eta", [0.2, 0.45, 1 / math.sqrt(2), 1.0])
def test_scalar_optimum_never_exceeds_sigma2(eta):
    """Sampling the raw feasible set must approach eta*Sigma_2 from within."""
    sys.path.insert(0, str(ROOT / "research" / "rebracketing_geometry"))
    from rg_scalar_verification import best_for_cell

    result = best_for_cell((17, eta, 20_000, 21))
    predicted = math.sin(min(2 * math.asin(min(eta, 1.0)), math.pi / 2))
    assert result["predicted"] == pytest.approx(predicted, abs=1e-14)
    assert result["found"] <= predicted + 1e-12       # a breach refutes Thm 5.1
    assert result["found"] >= 0.90 * predicted        # and the search must bite


def test_scalar_extremizer_switches_active_constraint_at_the_crossover():
    """Below eta_c the closure budget binds; above it the norm budget does."""
    sys.path.insert(0, str(ROOT / "research" / "rebracketing_geometry"))
    from rg_scalar_verification import best_for_cell

    low = best_for_cell((23, 0.45, 40_000, 41))["state"]
    high = best_for_cell((23, 1.0, 40_000, 41))["state"]
    # below the crossover both defects sit exactly on the closure budget
    assert low["d"] == pytest.approx(0.45, abs=0.03)
    assert low["d_prime"] == pytest.approx(0.45, abs=0.03)
    # above it they move interior, onto d^2 + d'^2 = 1
    assert high["d"] ** 2 + high["d_prime"] ** 2 == pytest.approx(1.0, abs=0.1)
