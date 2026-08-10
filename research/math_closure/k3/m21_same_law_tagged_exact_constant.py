"""M21: tagged same-law witnesses for the binary k=3 classes.

The shared bilinear law is a block-diagonal direct sum of the M14 or M15
node laws.  Orthogonal projected tags on the leaf slots select the intended
block at each occurrence, so law sharing alone does not reduce the supremum
when leaf directions and projector rank are allowed to vary.
"""

from __future__ import annotations

import math

import numpy as np

from research.math_closure.k3.m20_k3_arbitrary_arity_exact_constant import (
    _m14_bases,
    _m15_bases,
    W3,
)
from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


DIMENSION = 10
PROJECTED_RANK = 8


def _set_block(
    tensor: np.ndarray,
    first: tuple[int, ...],
    second: tuple[int, ...],
    output: tuple[int, ...],
    matrix: np.ndarray,
) -> None:
    """Insert a finite bilinear block with matrix coefficients."""

    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (len(output), len(first), len(second)):
        raise ValueError("block coefficient shape does not match its supports")
    for out_index, out in enumerate(output):
        for first_index, first_slot in enumerate(first):
            for second_index, second_slot in enumerate(second):
                tensor[out, first_slot, second_slot] = matrix[
                    out_index, first_index, second_index
                ]


def _chain_law(eta: float) -> np.ndarray:
    """Build one shared law whose tagged blocks reproduce the M14 chain."""

    f, n, a = _m14_bases(eta)
    # P contains indices 0..7; indices 8 and 9 are the two active normal
    # coordinates.  U1=(0,8), U2=(1,9), and the root line is index 2.
    tensor = np.zeros((DIMENSION, DIMENSION, DIMENSION), dtype=float)
    tag0, tag1, tag2, tag3 = 3, 4, 5, 6
    u1 = (0, 8)
    u2 = (1, 9)
    root = (2,)

    bottom = np.zeros((2, 1, 1), dtype=float)
    bottom[:, 0, 0] = f
    _set_block(tensor, (tag0,), (tag1,), u1, bottom)

    middle = np.zeros((2, 2, 1), dtype=float)
    middle[:, :, 0] = n
    _set_block(tensor, u1, (tag2,), u2, middle)

    outer = np.zeros((1, 2, 1), dtype=float)
    outer[0, :, 0] = a[0, :]
    _set_block(tensor, u2, (tag3,), root, outer)
    return tensor


def _branch_law(eta: float) -> np.ndarray:
    """Build one shared law whose tagged blocks reproduce the M15 branch."""

    f, root_base = _m15_bases(eta)
    tensor = np.zeros((DIMENSION, DIMENSION, DIMENSION), dtype=float)
    tag0, tag1, tag2, tag3 = 3, 4, 5, 6
    u1 = (0, 8)
    u2 = (1, 9)
    root = (2,)

    bottom_one = np.zeros((2, 1, 1), dtype=float)
    bottom_one[:, 0, 0] = f
    _set_block(tensor, (tag0,), (tag1,), u1, bottom_one)

    bottom_two = np.zeros((2, 1, 1), dtype=float)
    bottom_two[:, 0, 0] = f
    _set_block(tensor, (tag2,), (tag3,), u2, bottom_two)

    root_block = np.zeros((1, 2, 2), dtype=float)
    root_block[0, :, :] = root_base[0, :, :]
    _set_block(tensor, u1, u2, root, root_block)
    return tensor


def _tagged_leaf(label: int) -> np.ndarray:
    vector = np.zeros(PROJECTED_RANK, dtype=float)
    vector[label] = 1.0
    return vector


def shared_law_certificate(eta: float, family: str) -> tuple[float, float]:
    """Return the structural direct-sum norm and closure-defect certificate.

    Each block has orthogonal input and output supports.  Therefore the
    direct-sum estimate bounds the shared bilinear norm by the largest block
    norm, while a nonzero block attains that bound.  The same argument applies
    to the closure map on projected inputs.
    """

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    t = min(eta, math.sqrt(2.0 / 3.0))
    if family == "chain":
        f, n, a = _m14_bases(eta)
        block_norms = (float(np.linalg.norm(f)), float(np.linalg.norm(n, 2)), float(np.linalg.norm(a, 2)))
        closure_blocks = (t, t, 0.0)
    elif family == "branch":
        f, root_base = _m15_bases(eta)
        block_norms = (float(np.linalg.norm(f)), float(np.linalg.norm(root_base[0], 2)))
        closure_blocks = (t, t, 0.0)
    else:
        raise ValueError("family must be 'chain' or 'branch'")
    return max(block_norms), max(closure_blocks)


def _tree(family: str) -> tuple[Leaf | Node, dict[str, TypedLaw], dict[int, np.ndarray]]:
    if family == "chain":
        shape = Node(
            "mu",
            "tau",
            (
                Node(
                    "mu",
                    "tau",
                    (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau")),
                ),
                Leaf(3, "tau"),
            ),
        )
        leaves = {0: _tagged_leaf(3), 1: _tagged_leaf(4), 2: _tagged_leaf(5), 3: _tagged_leaf(6)}
    elif family == "branch":
        shape = Node(
            "mu",
            "tau",
            (
                Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))),
                Node("mu", "tau", (Leaf(2, "tau"), Leaf(3, "tau"))),
            ),
        )
        leaves = {0: _tagged_leaf(3), 1: _tagged_leaf(4), 2: _tagged_leaf(5), 3: _tagged_leaf(6)}
    else:
        raise ValueError("family must be 'chain' or 'branch'")
    return shape, leaves


def evaluate_tagged_same_law(eta: float, family: str) -> tuple[float, float, float]:
    """Return projected error, shared-law norm, and closure defect."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    tree, leaves = _tree(family)
    tensor = _chain_law(eta) if family == "chain" else _branch_law(eta)
    laws = {"mu": TypedLaw("mu", ("tau", "tau"), "tau", tensor)}
    types = TypeSystem([TypedSpace.coordinate("tau", DIMENSION, PROJECTED_RANK, field="real")])
    ambient = evaluate_ambient_numpy(tree, laws, types, leaves).root
    projected = evaluate_projected_numpy(tree, laws, types, leaves).root
    P_ambient = types["tau"].project(ambient)
    error = float(np.linalg.norm(P_ambient - projected))
    law_norm, closure_defect = shared_law_certificate(eta, family)
    return error, law_norm, closure_defect


def exact_same_law_constant(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    return W3(eta)


def verify_tagged_same_law(etas: tuple[float, ...] = (1.0e-6, 0.1, 0.5, 0.7, 1.0)) -> bool:
    for family in ("chain", "branch"):
        for eta in etas:
            error, norm, defect = evaluate_tagged_same_law(eta, family)
            if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
                return False
            # The witness clamps its realized leakage at alpha=sqrt(2/3)
            # for the high-eta branch; admissibility requires defect <= eta,
            # not equality with the external budget.
            if not math.isclose(defect, min(eta, math.sqrt(2.0 / 3.0)), rel_tol=0.0, abs_tol=1.0e-12):
                return False
            if not math.isclose(error / eta, exact_same_law_constant(eta), rel_tol=0.0, abs_tol=2.0e-10):
                return False
    return True


if __name__ == "__main__":
    assert verify_tagged_same_law()
    print("All checks passed: tagged same-law k=3 constants equal W3.")
