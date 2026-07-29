"""Explicit low-dimensional admissible lower-bound constructions."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

import numpy as np

from .local_constants import TypedLaw
from .projected_evaluation import TreeErrors, compute_tree_errors
from .typed_tree import Leaf, Node, Tree, iter_internal
from .types import TypeSystem, TypedSpace


@dataclass(frozen=True, slots=True)
class ExtremizerConstruction:
    name: str
    eta: float
    types: TypeSystem
    laws: Mapping[str, TypedLaw]
    reduced_inputs: Mapping[int, np.ndarray]
    full_norm_certificate: float
    closure_norm: float
    status: str
    mechanism: str


def rotation_tensor(
    arity: int, eta: float, *, dimension: int = 2, projector_rank: int = 1
) -> np.ndarray:
    """A norm-one gated rotation on ``R^2`` with rank-one leakage ``eta``.

    ``mu(x_1,...,x_a)=T_eta x_1 prod_{j>1}<e_0,x_j>`` and
    ``T_eta=[[sqrt(1-eta^2),-eta],[eta,sqrt(1-eta^2)]]``.
    Its multilinear operator norm is exactly one and the coordinate rank-one
    closure norm is exactly ``eta``.
    """

    if arity < 2 or not 0.0 <= eta <= 1.0:
        raise ValueError("arity >= 2 and 0 <= eta <= 1 are required")
    if not 0 < projector_rank < dimension:
        raise ValueError("the construction needs a nontrivial proper projector")
    tangent = math.sqrt(max(0.0, 1.0 - eta * eta))
    rotation = np.array([[tangent, -eta], [eta, tangent]], dtype=float)
    tensor = np.zeros((dimension, *(dimension for _ in range(arity))), dtype=float)
    active = (0, projector_rank)
    for out_local, out_index in enumerate(active):
        for first_local, first_index in enumerate(active):
            tensor[(out_index, first_index, *(0 for _ in range(arity - 1)))] = rotation[
                out_local, first_local
            ]
    return tensor


def rotation_extremizer(
    tree: Tree, eta: float, *, dimension: int = 2, projector_rank: int = 1
) -> ExtremizerConstruction:
    type_name = "tau"
    types = TypeSystem([TypedSpace.coordinate(type_name, dimension, projector_rank)])
    laws: dict[str, TypedLaw] = {}
    for node in iter_internal(tree):
        if node.output_type != type_name:
            raise ValueError("rotation extremizer requires a homogeneous tau tree")
        law = TypedLaw(
            node.law_id,
            tuple(type_name for _ in range(node.arity)),
            type_name,
            rotation_tensor(
                node.arity, eta, dimension=dimension, projector_rank=projector_rank
            ),
        )
        previous = laws.get(node.law_id)
        if previous is not None and previous.arity != law.arity:
            raise ValueError("one repeated law id cannot carry different arities")
        laws[node.law_id] = law
    leaves = {
        leaf.label: np.array([1.0, *(0.0 for _ in range(projector_rank - 1))])
        for leaf in _leaves(tree)
    }
    return ExtremizerConstruction(
        name="gated_planar_rotation",
        eta=eta,
        types=types,
        laws=laws,
        reduced_inputs=leaves,
        full_norm_certificate=1.0,
        closure_norm=eta,
        status="CERTIFIED_LOWER_BOUND",
        mechanism="Each node rotates tangent mass into the normal direction; later nodes gate on tangent coordinates.",
    )


def _leaves(tree: Tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _leaves(child)


def evaluate_extremizer(tree: Tree, construction: ExtremizerConstruction) -> TreeErrors:
    return compute_tree_errors(
        tree, construction.laws, construction.types, construction.reduced_inputs
    )


def normalized_ratios(tree: Tree, construction: ExtremizerConstruction) -> dict[str, float]:
    errors = evaluate_extremizer(tree, construction)
    k = sum(1 for _ in iter_internal(tree))
    if k == 0 or construction.eta == 0.0:
        return {"ambient": 0.0, "projected": 0.0, "normal": 0.0}
    denominator = construction.eta * construction.full_norm_certificate ** (k - 1)
    return {
        "ambient": errors.ambient / denominator,
        "projected": errors.projected_root / denominator,
        "normal": errors.normal_root / denominator,
    }
