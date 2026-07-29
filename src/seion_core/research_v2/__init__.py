"""Research-v2 reference mathematics and reproducibility primitives.

This package is deliberately small and independent of the legacy experiment
drivers.  It contains the typed tree calculus used by the v2 proofs and the
slow/reference and vectorized evaluators used by the parity tests.
"""

from .reference import (
    Tree,
    apply_tensor_reference,
    compose_tensor_reference,
    evaluate_tree_reference,
    exact_reduction_tensor,
    project_tensor_inputs,
    tree_bound,
    tree_internal_nodes,
    tree_height,
)
from .accelerated import apply_tensor_einsum, compose_tensor_tensordot, evaluate_tree_einsum

__all__ = [
    "Tree",
    "apply_tensor_reference",
    "compose_tensor_reference",
    "evaluate_tree_reference",
    "exact_reduction_tensor",
    "project_tensor_inputs",
    "tree_bound",
    "tree_internal_nodes",
    "tree_height",
    "apply_tensor_einsum",
    "compose_tensor_tensordot",
    "evaluate_tree_einsum",
]
