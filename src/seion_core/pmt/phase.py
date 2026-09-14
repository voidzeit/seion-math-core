"""M18/M19 phase trajectories with canonical ambient-leaf admissibility.

Leaf arguments enter through norm-one coordinate functionals. Multiplication
is used only on internal-child slots; applying it to unrestricted leaf slots
would have projected closure one, not eta. This is an independent-law family
over REAL planes, not a complex multilinear multiplication claim.
"""

from itertools import product
import math

import numpy as np

from .model import PMTModel
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypedSpace, TypeSystem


def gated_phase_tree(shape, eta: float):
    """A shape is None for a leaf, otherwise a tuple of >=2 child shapes."""
    if not 0 < eta <= 1:
        raise ValueError("require 0 < eta <= 1")
    leaves, laws = {}, {}
    phase = complex(math.sqrt(1 - eta*eta), eta)

    def build(current, root=False):
        if current is None:
            label = len(leaves)
            leaves[label] = np.array([1., 0.])
            return Leaf(label, "plane")
        if not isinstance(current, tuple) or len(current) < 2:
            raise ValueError("each internal node needs at least two children")
        children = tuple(build(child) for child in current)
        law_id = f"phase{len(laws)}"
        tensor = np.zeros((2,) + (2,) * len(children))
        for bits in product((0, 1), repeat=len(children)):
            if any(isinstance(child, Leaf) and bit for child, bit in zip(children, bits)):
                continue
            z = (1j)**sum(bits)
            if root:
                tensor[(0, *bits)] = z.imag
            else:
                z *= phase
                tensor[(0, *bits)] = z.real
                tensor[(1, *bits)] = z.imag
        laws[law_id] = TypedLaw(law_id, ("plane",)*len(children), "plane", tensor)
        return Node(law_id, "plane", children)

    tree = build(shape, root=True)
    model = PMTModel(tree, TypeSystem([TypedSpace.coordinate("plane", 2, 1)]), laws)
    return model, leaves
