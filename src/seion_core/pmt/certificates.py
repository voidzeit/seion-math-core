"""Finite-dimensional local defect brackets for PMT laws.

An operator norm of a general multilinear law is not silently treated as an
exactly computable quantity.  The bracket records an attained lower value and
the Frobenius upper certificate.  The upper endpoint is safe; the lower
endpoint is evidence, not a global optimum claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from seion_core.research_v3.operator_norms import OperatorNormBracket, multilinear_power_lower_bound
from seion_core.research_v3.typed_tree import Leaf, Node

from .model import PMTModel


@dataclass(frozen=True, slots=True)
class LocalDefectBracket:
    """Bracket for ``||(I-P_v) mu_v(P_children .)||_op``."""

    node_path: tuple[int, ...]
    law_id: str
    operator: OperatorNormBracket
    semantics: str = "projected_input_closure_defect"

    @property
    def lower(self) -> float:
        return self.operator.lower

    @property
    def upper(self) -> float:
        return self.operator.upper


@dataclass(frozen=True, slots=True)
class AdmissibilityBracket:
    """Nodewise brackets plus a fail-closed admissibility interpretation."""

    ambient: Mapping[tuple[int, ...], OperatorNormBracket]
    projected_closure: Mapping[tuple[int, ...], LocalDefectBracket]
    M_upper: float
    rho_upper: float
    status: str


def _identity(space) -> np.ndarray:
    return np.eye(space.dimension, dtype=space.q.dtype)


def _input_projector(model: PMTModel, child) -> np.ndarray:
    if isinstance(child, Leaf):
        return _identity(model.types[child.type_name])
    return model.types[child.output_type].projector


def _restricted_tensor(model: PMTModel, node: Node, *, output: str) -> np.ndarray:
    law = model.laws[node.law_id]
    data = np.asarray(law.tensor)
    # Contract input axes with the child projectors one at a time.  The
    # projectors are self-adjoint, so this is exactly mu(P_1 ., ..., P_a .).
    for slot, child in enumerate(node.children):
        projector = _input_projector(model, child)
        data = np.tensordot(data, projector, axes=([1 + slot], [0]))
        data = np.moveaxis(data, -1, 1 + slot)
    if output == "N":
        data = np.tensordot(model.types[node.output_type].complement_projector, data, axes=([1], [0]))
    elif output != "F":
        raise ValueError("output must be 'F' or 'N'")
    return np.asarray(data)


def _bracket(tensor: np.ndarray, *, seed: int) -> OperatorNormBracket:
    return multilinear_power_lower_bound(tensor, restarts=12, maximum_iterations=300, seed=seed)


def projected_closure_bracket(model: PMTModel, node_path: tuple[int, ...], node: Node | None = None) -> LocalDefectBracket:
    """Compute a safe numerical bracket for one projected-input closure defect."""

    if node is None:
        node = _node_at_path(model.tree, node_path)
    if not isinstance(node, Node):
        raise ValueError("node_path must identify an internal node")
    tensor = _restricted_tensor(model, node, output="N")
    return LocalDefectBracket(
        node_path=node_path,
        law_id=node.law_id,
        operator=_bracket(tensor, seed=sum(node_path) + len(node_path) + 1),
    )


def admissibility_bracket(model: PMTModel) -> AdmissibilityBracket:
    """Return nodewise ambient/closure brackets without upgrading them to proof."""

    ambient: dict[tuple[int, ...], OperatorNormBracket] = {}
    closure: dict[tuple[int, ...], LocalDefectBracket] = {}

    def visit(item, path: tuple[int, ...]) -> None:
        if isinstance(item, Leaf):
            return
        ambient[path] = _bracket(model.laws[item.law_id].tensor, seed=len(path) + 11)
        closure[path] = projected_closure_bracket(model, path, item)
        for slot, child in enumerate(item.children):
            visit(child, (*path, slot))

    visit(model.tree, ())
    M_upper = max((value.upper for value in ambient.values()), default=0.0)
    rho_upper = max((value.upper for value in closure.values()), default=0.0)
    status = "NUMERICAL_BRACKET_ONLY"
    return AdmissibilityBracket(ambient, closure, M_upper, rho_upper, status)


def _node_at_path(tree, path: tuple[int, ...]):
    item = tree
    for slot in path:
        if isinstance(item, Leaf):
            raise ValueError("path enters a leaf")
        item = item.children[slot]
    return item
