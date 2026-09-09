import math

import numpy as np
import pytest

from seion_core.pmt import (
    K4_FRONTIER,
    Leaf,
    Node,
    PMTModel,
    TypedLaw,
    TypeSystem,
    TypedSpace,
    ambient_root_bound,
    branching_w3_extremizer,
    chain_w3_extremizer,
    evaluate_pmt,
    projected_closure_bracket,
    projected_root_bound,
    w3,
    w3_absolute,
    w3_sos_residual,
)


def _simple_model():
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    tensor = np.zeros((2, 2, 2), dtype=float)
    tensor[0, 0, 0] = 1.0
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    tree = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    return PMTModel(tree, types, {"mu": law})


def test_pmt_evaluator_accepts_ambient_leaf_vectors_and_separates_root_errors():
    model = _simple_model()
    result = evaluate_pmt(
        model,
        {0: np.array([0.0, 1.0]), 1: np.array([0.0, 1.0])},
    )
    assert np.isclose(result.errors.ambient, 0.0)
    assert np.isclose(result.errors.projected, 0.0)
    assert np.isclose(result.errors.normal, 0.0)
    assert result.errors.pythagorean_residual < 1e-14


def test_pmt_evaluator_reports_a_nonzero_normal_root_component():
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    tensor = np.zeros((2, 2, 2), dtype=float)
    tensor[1, 1, 1] = 1.0
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    model = PMTModel(Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), types, {"mu": law})

    result = evaluate_pmt(model, {0: np.array([0.0, 1.0]), 1: np.array([0.0, 1.0])})

    assert result.errors.ambient == pytest.approx(1.0)
    assert result.errors.projected == pytest.approx(0.0)
    assert result.errors.normal == pytest.approx(1.0)
    assert result.errors.pythagorean_residual < 1e-14


def test_leaf_root_uses_the_identity_projector_convention():
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    model = PMTModel(Leaf(0, "tau"), types, {})

    result = evaluate_pmt(model, {0: np.array([0.0, 1.0])})

    assert result.errors.ambient == pytest.approx(0.0)
    assert result.errors.projected == pytest.approx(0.0)
    assert result.errors.normal == pytest.approx(0.0)
    assert np.array_equal(model.input_projector(model.tree), np.eye(2))


def test_complex_typed_laws_are_evaluated_in_the_declared_hilbert_field():
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field="complex")])
    tensor = np.zeros((2, 2, 2), dtype=complex)
    tensor[1, 1, 1] = 1j
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    model = PMTModel(Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), types, {"mu": law})

    result = evaluate_pmt(
        model,
        {0: np.array([0.0, 1.0]), 1: np.array([0.0, 1.0])},
    )

    assert result.ambient_root[1] == pytest.approx(1j)
    assert result.errors.ambient == pytest.approx(1.0)
    assert result.errors.normal == pytest.approx(1.0)


def test_w3_formula_and_sum_of_squares_contract():
    eta_c = math.sqrt(2.0 / 3.0)
    assert np.isclose(w3(eta_c), math.sqrt(2.0))
    assert np.isclose(w3_absolute(eta_c), 2.0 / math.sqrt(3.0))
    assert w3_sos_residual(math.sqrt(2.0), math.sqrt(2.0)) == pytest.approx(0.0)
    assert w3_sos_residual(0.3, 0.7) >= -1e-14
    assert projected_root_bound(1, 1.0, 0.3) == 0.0
    assert projected_root_bound(3, 2.0, 0.5, 4.0) == pytest.approx(16.0)
    assert ambient_root_bound(3, 2.0, 0.5, 4.0) == pytest.approx(24.0)


@pytest.mark.parametrize("factory", [chain_w3_extremizer, branching_w3_extremizer])
@pytest.mark.parametrize("eta", [0.2, math.sqrt(2.0 / 3.0), 0.9])
def test_w3_extremizers_hit_the_declared_constant(factory, eta):
    construction = factory(eta)
    result = construction.evaluate()
    assert result.errors.projected == pytest.approx(construction.target_projected_error, abs=2e-12)
    assert result.errors.projected / eta == pytest.approx(w3(eta), abs=2e-12)
    assert result.errors.pythagorean_residual < 2e-12


def test_projected_closure_bracket_has_explicit_semantics():
    construction = chain_w3_extremizer(0.25)
    bracket = projected_closure_bracket(construction.model, (0, 0), construction.model.tree.children[0].children[0])
    assert bracket.semantics == "projected_input_closure_defect"
    assert bracket.lower <= bracket.upper + 1e-12
    assert bracket.upper <= 0.25 + 1e-12


def test_k4_frontier_is_open_and_never_returns_a_constant():
    assert K4_FRONTIER.status == "OPEN_PROBLEM"
    from seion_core.pmt import k4_frontier

    record = k4_frontier(observation={"eta": 0.2, "candidate_ratio": 2.7})
    assert record["exact_constant"] is None
    assert record["observation_status"] == "NUMERICAL_OBSERVATION"
