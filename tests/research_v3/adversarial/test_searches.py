import pytest

from seion_core.research_v3.adversarial_search import (
    SearchConfig,
    derivative_free_search,
    gradient_search,
)
from seion_core.research_v3.typed_tree import Leaf, Node


def _tree():
    inner = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    return Node("mu", "tau", (inner, Leaf(2, "tau")))


def test_tiny_gradient_search_is_explicitly_empirical():
    pytest.importorskip("torch")
    result = gradient_search(
        _tree(),
        SearchConfig(
            eta=0.1,
            seeds=(0,),
            restarts_per_seed=1,
            adam_steps=3,
            lbfgs_steps=1,
            device="cpu",
        ),
    )
    assert result.best_lower_bound >= 0.0
    assert result.status == "EMPIRICAL_LOWER_BOUND"
    assert not result.globally_certified


@pytest.mark.slow
def test_tiny_derivative_free_search_is_independent_and_empirical():
    result = derivative_free_search(
        _tree(), eta=0.1, maximum_iterations=1, population_size=2, seed=1
    )
    assert result.best_lower_bound >= 0.0
    assert "differential" in result.optimizer.lower()
    assert not result.globally_certified
