import numpy as np

from seion_core.algebra.associators import sample_associator_defect
from seion_core.algebra.compositions import partial_compose
from seion_core.examples.associative import coordinatewise_associative_law
from seion_core.examples.random_laws import random_ternary_law


def test_associative_five_input_residual_is_zero():
    law = coordinatewise_associative_law(3)
    rng = np.random.default_rng(3)
    values = [rng.normal(size=3) for _ in range(5)]
    np.testing.assert_allclose(law.five_input_associator(*values), 0.0)


def test_conventions_are_named_and_random_is_not_assumed_zero():
    law = random_ternary_law(3, 4)
    result = sample_associator_defect(law, "five_input", samples=8, seed=5)
    assert result.convention == "five_input"
    assert result.exact is False
    assert result.squared_energy >= 0


def test_operadic_partial_composition_has_five_inputs():
    law = coordinatewise_associative_law(2)
    composed = partial_compose(law, law, 0)
    assert composed.arity == 5
    assert composed.input_dims == (2, 2, 2, 2, 2)

