"""Signed tree forests, shared-term cancellation, and named identities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .certificates import BoundCertificate
from .exact_evaluation import evaluate_ambient_numpy
from .local_constants import TypedLaw
from .projected_evaluation import evaluate_projected_numpy
from .typed_tree import Leaf, Node, Tree, canonical_json
from .types import TypeSystem


@dataclass(frozen=True, slots=True)
class ForestTerm:
    coefficient: complex
    tree: Tree


@dataclass(frozen=True, slots=True)
class SignedForest:
    name: str
    terms: tuple[ForestTerm, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.terms:
            raise ValueError("a signed forest requires a name and at least one term")

    def combined_terms(self) -> tuple[ForestTerm, ...]:
        """Exactly cancel syntactically identical trees before inequalities."""

        grouped: dict[str, tuple[complex, Tree]] = {}
        for term in self.terms:
            key = canonical_json(term.tree)
            coefficient, tree = grouped.get(key, (0.0, term.tree))
            grouped[key] = (coefficient + term.coefficient, tree)
        return tuple(
            ForestTerm(coefficient, tree)
            for coefficient, tree in grouped.values()
            if abs(coefficient) > 0.0
        )


@dataclass(frozen=True, slots=True)
class ForestErrors:
    ambient: float
    projected: float
    normal: float


def evaluate_forest_errors(
    forest: SignedForest,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> ForestErrors:
    ambient_sum = None
    projected_sum = None
    root_space = None
    for term in forest.combined_terms():
        ambient = evaluate_ambient_numpy(term.tree, laws, types, reduced_inputs).root
        projected = evaluate_projected_numpy(term.tree, laws, types, reduced_inputs).root
        ambient_sum = term.coefficient * ambient if ambient_sum is None else ambient_sum + term.coefficient * ambient
        projected_sum = term.coefficient * projected if projected_sum is None else projected_sum + term.coefficient * projected
        root_type = term.tree.type_name if isinstance(term.tree, Leaf) else term.tree.output_type
        candidate = types[root_type]
        if root_space is not None and candidate.name != root_space.name:
            raise ValueError("all signed-forest terms must have the same output type")
        root_space = candidate
    if ambient_sum is None or projected_sum is None or root_space is None:
        zero = 0.0
        return ForestErrors(zero, zero, zero)
    difference = ambient_sum - projected_sum
    projected_difference = root_space.project(ambient_sum) - projected_sum
    normal = root_space.complement_projector @ ambient_sum
    return ForestErrors(
        ambient=float(np.linalg.norm(difference)),
        projected=float(np.linalg.norm(projected_difference)),
        normal=float(np.linalg.norm(normal)),
    )


def triangle_certificate(
    forest: SignedForest, certificates: Mapping[str, BoundCertificate], error: str = "projected"
) -> float:
    field = {"ambient": "B_A", "projected": "B_P", "normal": "B_N"}.get(error)
    if field is None:
        raise ValueError("error must be ambient, projected, or normal")
    total = 0.0
    for term in forest.terms:
        key = canonical_json(term.tree)
        total += abs(term.coefficient) * float(getattr(certificates[key].root, field))
    return float(total)


def cancellation_aware_certificate(
    forest: SignedForest, certificates: Mapping[str, BoundCertificate], error: str = "projected"
) -> float:
    simplified = SignedForest(forest.name, forest.combined_terms())
    return triangle_certificate(simplified, certificates, error=error)


def ternary_insertion_tree(slot: int, *, law_id: str = "mu", type_name: str = "tau") -> Tree:
    """Return ``mu o_slot mu`` on five canonically ordered leaves."""

    if slot not in {0, 1, 2}:
        raise ValueError("a ternary insertion slot is 0, 1, or 2")
    leaves = [Leaf(index, type_name) for index in range(5)]
    inner = Node(law_id, type_name, tuple(leaves[slot : slot + 3]))
    outer_children: list[Tree] = []
    cursor = 0
    for outer_slot in range(3):
        if outer_slot == slot:
            outer_children.append(inner)
            cursor += 3
        else:
            outer_children.append(leaves[cursor])
            cursor += 1
    return Node(law_id, type_name, tuple(outer_children))


def ternary_associator(
    left_slot: int = 0, right_slot: int = 2, *, law_id: str = "mu", type_name: str = "tau"
) -> SignedForest:
    return SignedForest(
        name=f"ternary_associator_{left_slot}_{right_slot}",
        terms=(
            ForestTerm(1.0, ternary_insertion_tree(left_slot, law_id=law_id, type_name=type_name)),
            ForestTerm(-1.0, ternary_insertion_tree(right_slot, law_id=law_id, type_name=type_name)),
        ),
    )


def anchored_binary_associator(*, law_id: str = "mu", type_name: str = "tau") -> SignedForest:
    leaves = [Leaf(index, type_name) for index in range(3)]
    left = Node(
        law_id,
        type_name,
        (Node(law_id, type_name, (leaves[0], leaves[1])), leaves[2]),
    )
    right = Node(
        law_id,
        type_name,
        (leaves[0], Node(law_id, type_name, (leaves[1], leaves[2]))),
    )
    return SignedForest("anchored_binary_associator", (ForestTerm(1.0, left), ForestTerm(-1.0, right)))


def binary_jacobiator(*, law_id: str = "mu", type_name: str = "tau") -> SignedForest:
    leaves = [Leaf(index, type_name) for index in range(3)]

    def bracket(left: Tree, right: Tree) -> Node:
        return Node(law_id, type_name, (left, right))

    terms = (
        ForestTerm(1.0, bracket(leaves[0], bracket(leaves[1], leaves[2]))),
        ForestTerm(1.0, bracket(leaves[1], bracket(leaves[2], leaves[0]))),
        ForestTerm(1.0, bracket(leaves[2], bracket(leaves[0], leaves[1]))),
    )
    return SignedForest("binary_jacobiator_declared_order", terms)


def filippov_fundamental_identity(
    *, law_id: str = "mu", type_name: str = "tau"
) -> SignedForest:
    """The declared five-input ternary Filippov residual, with fixed slots."""

    x1, x2, y1, y2, y3 = [Leaf(index, type_name) for index in range(5)]

    def mu(*children: Tree) -> Node:
        return Node(law_id, type_name, tuple(children))

    return SignedForest(
        "ternary_filippov_fundamental_identity",
        (
            ForestTerm(1.0, mu(x1, x2, mu(y1, y2, y3))),
            ForestTerm(-1.0, mu(mu(x1, x2, y1), y2, y3)),
            ForestTerm(-1.0, mu(y1, mu(x1, x2, y2), y3)),
            ForestTerm(-1.0, mu(y1, y2, mu(x1, x2, y3))),
        ),
    )


def ternary_declared_gji(*, law_id: str = "mu", type_name: str = "tau") -> SignedForest:
    """A fully explicit six-term alternating insertion convention.

    This is registered as a declared GJI *variant*; no equivalence to another
    author's convention is inferred without a permutation/sign comparison.
    """

    def relabel(item: Tree, permutation: tuple[int, ...]) -> Tree:
        if isinstance(item, Leaf):
            return Leaf(permutation[item.label], item.type_name)
        return Node(item.law_id, item.output_type, tuple(relabel(child, permutation) for child in item.children))

    permutations = (
        (0, 1, 2, 3, 4),
        (1, 2, 0, 3, 4),
        (2, 0, 1, 3, 4),
        (1, 0, 2, 3, 4),
        (2, 1, 0, 3, 4),
        (0, 2, 1, 3, 4),
    )
    signs = (1.0, 1.0, 1.0, -1.0, -1.0, -1.0)
    terms = [
        ForestTerm(
            sign,
            relabel(
                ternary_insertion_tree(index % 3, law_id=law_id, type_name=type_name),
                permutation,
            ),
        )
        for index, (sign, permutation) in enumerate(zip(signs, permutations))
    ]
    return SignedForest("ternary_gji_six_term_declared_variant", tuple(terms))


def named_signed_forests(*, law_id: str = "mu", type_name: str = "tau") -> dict[str, SignedForest]:
    insertion_differences = {
        f"ternary_insertion_{left}_{right}": ternary_associator(
            left, right, law_id=law_id, type_name=type_name
        )
        for left, right in ((0, 1), (0, 2), (1, 2))
    }
    base = {
        "five_input_ternary_associator": ternary_associator(
            0, 2, law_id=law_id, type_name=type_name
        ),
        "anchored_associator": anchored_binary_associator(
            law_id=law_id, type_name=type_name
        ),
        "jacobiator_variants": binary_jacobiator(law_id=law_id, type_name=type_name),
        "named_gji_variants": ternary_declared_gji(law_id=law_id, type_name=type_name),
        "filippov_fundamental_identity": filippov_fundamental_identity(
            law_id=law_id, type_name=type_name
        ),
    }
    base.update(insertion_differences)
    return base
