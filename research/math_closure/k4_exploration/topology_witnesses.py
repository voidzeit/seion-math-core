"""Analytic k4 lower witnesses; equality for mixed has a separate proof draft.

The branch-below family is real bilinear complex multiplication on R^2;
its naive complexification is NOT asserted contractive.
"""

import math
import numpy as np

from seion_core.pmt import PMTModel, TypedLaw, evaluate_pmt
from seion_core.pmt.phase import gated_phase_tree


def k4_topology_witness(topology, eta):
    if not 0 < eta <= 1:
        raise ValueError("require 0 < eta <= 1")
    if topology == "mixed":
        shape = (((None, None), None), (None, None))
    elif topology == "branch_below":
        shape = (((None, None), (None, None)), None)
    else:
        raise ValueError("topology must be mixed or branch_below")
    t = min(eta, math.sqrt(3/7))
    model, leaves = gated_phase_tree(shape, t)
    ev = evaluate_pmt(model, leaves)
    root = model.tree
    tensor = np.zeros((2,2,2))
    if topology == "mixed":
        k = np.outer(ev.ambient_values[(0,)], ev.ambient_values[(1,)])
        k -= np.outer(ev.projected_values[(0,)], ev.projected_values[(1,)])
        u, _, vh = np.linalg.svd(k)
        tensor[0] = u@vh
    else:
        error = ev.ambient_values[(0,)]-ev.projected_values[(0,)]
        tensor[0, :, 0] = error/np.linalg.norm(error)
    laws = dict(model.laws)
    laws[root.law_id] = TypedLaw(root.law_id, ("plane", "plane"), "plane", tensor)
    return PMTModel(root, model.types, laws), leaves
