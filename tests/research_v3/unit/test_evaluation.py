import numpy as np

from seion_core.research_v3.exact_evaluation import (
    evaluate_ambient_numpy,
    evaluate_ambient_reference,
)
from seion_core.research_v3.local_constants import TypedLaw, apply_tensor_loops, apply_tensor_numpy
from seion_core.research_v3.projected_evaluation import (
    compute_tree_errors,
    evaluate_projected_numpy,
    evaluate_reduced_coordinates,
)
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


def _problem(seed=4):
    rng = np.random.default_rng(seed)
    types = TypeSystem([TypedSpace.coordinate("tau", 3, 2)])
    tensor_a = rng.normal(size=(3, 3, 3)) / 4
    tensor_b = rng.normal(size=(3, 3, 3)) / 4
    laws = {
        "a": TypedLaw("a", ("tau", "tau"), "tau", tensor_a),
        "b": TypedLaw("b", ("tau", "tau"), "tau", tensor_b),
    }
    tree = Node(
        "b",
        "tau",
        (Node("a", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau")),
    )
    leaves = {index: rng.normal(size=2) for index in range(3)}
    return types, laws, tree, leaves


def test_coordinate_loop_and_numpy_law_evaluators_agree():
    rng = np.random.default_rng(2)
    tensor = rng.normal(size=(3, 2, 4, 2))
    vectors = [rng.normal(size=2), rng.normal(size=4), rng.normal(size=2)]
    assert np.allclose(apply_tensor_loops(tensor, vectors), apply_tensor_numpy(tensor, vectors))


def test_full_tree_reference_and_numpy_agree():
    types, laws, tree, leaves = _problem()
    reference = evaluate_ambient_reference(tree, laws, types, leaves)
    accelerated = evaluate_ambient_numpy(tree, laws, types, leaves)
    assert np.allclose(reference.root, accelerated.root, atol=1e-13)
    assert reference.values.keys() == accelerated.values.keys()


def test_named_errors_obey_exact_hilbert_relationships():
    types, laws, tree, leaves = _problem()
    errors = compute_tree_errors(tree, laws, types, leaves)
    assert errors.pythagorean_residual < 1e-12
    assert errors.reduced_projected_residual < 1e-12
    projected = evaluate_projected_numpy(tree, laws, types, leaves)
    reduced = evaluate_reduced_coordinates(tree, laws, types, leaves)
    assert np.allclose(reduced, types["tau"].reduce(projected.root))
