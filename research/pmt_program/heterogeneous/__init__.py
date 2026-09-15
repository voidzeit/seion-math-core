"""Numerical and bookkeeping tools for the heterogeneous Theorem R program.

The scalar box maximum is an exploratory quantity until the heterogeneous
upper-bound theorem is proved.  The module therefore exposes both:

* a conservative uniform-Theorem-R certificate; and
* the heterogeneous box maximum as a lower-bound/candidate quantity.
"""

from .scalar_extremization import (
    BoxMaximum,
    capped_equal_angle,
    factor,
    heterogeneous_box_max,
    interval_box_max,
    uniform_G,
)
from .certificate import HeterogeneousCertificate, make_certificate
from .allocation import NodeChoice, AllocationResult, optimize_allocation

__all__ = [
    "AllocationResult",
    "BoxMaximum",
    "HeterogeneousCertificate",
    "NodeChoice",
    "capped_equal_angle",
    "factor",
    "heterogeneous_box_max",
    "interval_box_max",
    "make_certificate",
    "optimize_allocation",
    "uniform_G",
]
