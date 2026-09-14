"""Explicit two-dimensional independent-law ``W_3`` extremizers."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace

from .evaluation import PMTEvaluation, evaluate_pmt
from .model import PMTModel


@dataclass(frozen=True, slots=True)
class W3Extremizer:
    """A construction with analytic norm/closure certificates."""

    model: PMTModel
    leaf_inputs: dict[int, np.ndarray]
    eta: float
    effective_leakage: float
    target_projected_error: float
    normalized_constant: float
    status: str = "CERTIFIED_ANALYTIC_CONSTRUCTION"

    def evaluate(self) -> PMTEvaluation:
        return evaluate_pmt(self.model, self.leaf_inputs)


def _space() -> TypeSystem:
    return TypeSystem([TypedSpace.coordinate("tau", 2, 1)])


def _first_law(law_id: str, t: float, p: float) -> TypedLaw:
    tensor = np.zeros((2, 2, 2), dtype=float)
    tensor[0, 0, 0] = p
    tensor[1, 0, 0] = t
    return TypedLaw(law_id, ("tau", "tau"), "tau", tensor)


def _middle_law(law_id: str, t: float, c: float) -> TypedLaw:
    # N e0 = t e1 - c e0 and N e1 = c e1 + t e0.
    N = np.array([[-c, t], [t, c]], dtype=float)
    tensor = np.zeros((2, 2, 2), dtype=float)
    tensor[:, :, 0] = N
    return TypedLaw(law_id, ("tau", "tau"), "tau", tensor)


def _root_readout(law_id: str, vector: np.ndarray) -> TypedLaw:
    vector = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError("root readout vector must be nonzero")
    tensor = np.zeros((2, 2, 2), dtype=float)
    tensor[0, :, 0] = vector / norm
    return TypedLaw(law_id, ("tau", "tau"), "tau", tensor)


def chain_w3_extremizer(eta: float) -> W3Extremizer:
    """Construct the dimension-two rank-one chain attaining ``W_3(eta)``."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must satisfy 0 < eta <= 1")
    t = min(eta, math.sqrt(2.0 / 3.0))
    p = math.sqrt(1.0 - t * t)
    c = p
    N = np.array([[-c, t], [t, c]], dtype=float)
    # The propagated discrepancy is t N e1 + p t e1.
    vector = t * (N @ np.array([0.0, 1.0])) + p * t * np.array([0.0, 1.0])
    tree = Node(
        "mu3",
        "tau",
        (Node("mu2", "tau", (Node("mu1", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau"))), Leaf(3, "tau")),
    )
    laws = {
        "mu1": _first_law("mu1", t, p),
        "mu2": _middle_law("mu2", t, c),
        "mu3": _root_readout("mu3", vector),
    }
    model = PMTModel(tree, _space(), laws)
    leaves = {label: np.array([1.0, 0.0]) for label in range(4)}
    target = t * math.sqrt(4.0 - 3.0 * t * t)
    return W3Extremizer(model, leaves, eta, t, target, target / eta)


def branching_w3_extremizer(eta: float) -> W3Extremizer:
    """Construct the dimension-two rank-one branching witness for ``W_3``."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must satisfy 0 < eta <= 1")
    t = min(eta, math.sqrt(2.0 / 3.0))
    p = math.sqrt(1.0 - t * t)
    A = np.array([[t * t, t * p], [p * t, 0.0]], dtype=float)
    left, _, right_t = np.linalg.svd(A)
    polar = left @ right_t
    # A is indexed by (e1,e0) in each child. Convert to the ambient (e0,e1) basis.
    B = np.array([[polar[1, 1], polar[1, 0]], [polar[0, 1], polar[0, 0]]], dtype=float)
    root_tensor = np.zeros((2, 2, 2), dtype=float)
    root_tensor[0] = B
    tree = Node(
        "mu3",
        "tau",
        (
            Node("mu1", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))),
            Node("mu2", "tau", (Leaf(2, "tau"), Leaf(3, "tau"))),
        ),
    )
    laws = {
        "mu1": _first_law("mu1", t, p),
        "mu2": _first_law("mu2", t, p),
        "mu3": TypedLaw("mu3", ("tau", "tau"), "tau", root_tensor),
    }
    model = PMTModel(tree, _space(), laws)
    leaves = {label: np.array([1.0, 0.0]) for label in range(4)}
    target = t * math.sqrt(4.0 - 3.0 * t * t)
    return W3Extremizer(model, leaves, eta, t, target, target / eta)
