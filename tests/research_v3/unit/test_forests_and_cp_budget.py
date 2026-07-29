from seion_core.research_v3.cp_projection_budget import homogeneous_cp_projection_budget
from seion_core.research_v3.polynomial_forests import (
    ForestTerm,
    SignedForest,
    ternary_associator,
)
from seion_core.research_v3.typed_tree import Leaf, Node


def test_signed_forest_exactly_cancels_identical_terms():
    tree = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    forest = SignedForest("zero", (ForestTerm(1.0, tree), ForestTerm(-1.0, tree)))
    assert forest.combined_terms() == ()


def test_ternary_associator_has_two_five_input_trees():
    forest = ternary_associator()
    assert len(forest.terms) == 2
    assert [len(list(_leaves(term.tree))) for term in forest.terms] == [5, 5]


def _leaves(tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _leaves(child)


def test_cp_projection_budget_exposes_interaction_instead_of_hiding_it():
    budget = homogeneous_cp_projection_budget(
        internal_nodes=4,
        exact_norm=1.0,
        representation_error=0.1,
        closure_residual=0.02,
        projected_root=True,
    )
    assert budget.representation > 0
    assert budget.projection_and_closure > 0
    assert budget.interaction > 0
    assert budget.total == budget.recursive_amplification
