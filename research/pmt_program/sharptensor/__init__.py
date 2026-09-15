"""SharpTensor 0.1 — certified orthogonal truncation of tree tensor computations.

Scope (see ``research/pmt_program/paper/APPLICATIONS_BOUNDARY.md`` and
``research/pmt_program/sharptensor/CERTIFIED_ADAPTIVE_TENSOR_COMPRESSION.md``):
contract-then-truncate tree computations with exact orthogonal truncations. No quantisation, no
approximate projectors, no gradient compression.
"""

from .gbox import (
    GBoxEnclosure,
    additive_bound,
    capped_value,
    gbox_certified,
    gbox_float,
    uniform_fallback,
)

__all__ = [
    "GBoxEnclosure",
    "additive_bound",
    "capped_value",
    "gbox_certified",
    "gbox_float",
    "uniform_fallback",
]
