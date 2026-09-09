"""Canonical finite-dimensional Projected Multilinear Trees (PMT) API.

The :mod:`seion_core.research_v3` namespace contains the original research
implementation and remains supported.  This namespace is the small, explicit
contract layer for the PMT mathematics: leaves receive ambient vectors,
internal vertices apply a typed multilinear law followed by an orthogonal
projector, and all root errors are reported separately.

The package deliberately does not turn numerical optimization into a proof.
The exact ``k=1``, ``k=2`` and ``k=3`` constants are exposed as theorem
contracts, while the fixed-eta ``k>=4`` interface reports an open problem.
"""

from .bounds import (
    W3_BREAKPOINT,
    ambient_root_bound,
    projected_root_bound,
    w3,
    w3_absolute,
    w3_sos_residual,
)
from .certificates import (
    AdmissibilityBracket,
    LocalDefectBracket,
    admissibility_bracket,
    projected_closure_bracket,
)
from .evaluation import (
    PMTEvaluation,
    RootErrorDecomposition,
    evaluate_ambient,
    evaluate_projected,
    evaluate_pmt,
)
from .extremizers import (
    W3Extremizer,
    branching_w3_extremizer,
    chain_w3_extremizer,
)
from .frontier import K4_FRONTIER, K4Frontier, k4_frontier
from .model import PMTModel
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.typed_tree import Leaf, Node, Tree
from seion_core.research_v3.types import TypeSystem, TypedSpace

__all__ = [
    "AdmissibilityBracket",
    "K4_FRONTIER",
    "K4Frontier",
    "Leaf",
    "LocalDefectBracket",
    "Node",
    "PMTEvaluation",
    "PMTModel",
    "RootErrorDecomposition",
    "Tree",
    "TypeSystem",
    "TypedLaw",
    "TypedSpace",
    "W3_BREAKPOINT",
    "W3Extremizer",
    "admissibility_bracket",
    "ambient_root_bound",
    "branching_w3_extremizer",
    "chain_w3_extremizer",
    "evaluate_ambient",
    "evaluate_pmt",
    "evaluate_projected",
    "k4_frontier",
    "projected_closure_bracket",
    "projected_root_bound",
    "w3",
    "w3_absolute",
    "w3_sos_residual",
]
