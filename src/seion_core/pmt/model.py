"""Typed PMT model contract.

The model is intentionally thin: the established typed-tree classes remain
the source of truth for tree validation, while this object binds a tree,
finite Hilbert spaces, and dense multilinear laws into one validated PMT
instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from seion_core.research_v3.local_constants import TypedLaw, validate_law_family
from seion_core.research_v3.typed_tree import Leaf, Tree, iter_internal, iter_leaves, validate_tree
from seion_core.research_v3.types import TypeSystem


@dataclass(frozen=True, slots=True)
class PMTModel:
    """A finite typed projected multilinear tree.

    ``TypedLaw.tensor`` uses output-first coordinates
    ``(output, input_1, ..., input_a)``.  Every internal output is projected
    with the orthogonal projector attached to its declared output type.  A
    leaf has no reduction and therefore receives an ambient vector directly.
    """

    tree: Tree
    types: TypeSystem
    laws: Mapping[str, TypedLaw]

    def __post_init__(self) -> None:
        validate_law_family(self.laws, self.types)
        validate_tree(self.tree, self.types, self.laws)

    @property
    def internal_count(self) -> int:
        return sum(1 for _ in iter_internal(self.tree))

    @property
    def leaf_count(self) -> int:
        return sum(1 for _ in iter_leaves(self.tree))

    def leaf_dimensions(self) -> dict[int, int]:
        return {
            leaf.label: self.types[leaf.type_name].dimension
            for leaf in iter_leaves(self.tree)
        }

    def output_projector(self, type_name: str):
        return self.types[type_name].projector

    def input_projector(self, item: Tree):
        """Return ``I`` for a leaf and its output projector for an internal child."""

        if isinstance(item, Leaf):
            space = self.types[item.type_name]
            return np.eye(space.dimension, dtype=space.q.dtype)
        return self.types[item.output_type].projector
