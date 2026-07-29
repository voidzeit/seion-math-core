"""SEION Math Core.

The public API is intentionally finite-dimensional and explicit.  Objects in
this package carry their arity, dimensions, field/dtype, and conventions so
that a certificate can distinguish a definition from an observed residual.
"""

from .algebra.nary_law import NaryLaw, SparseNaryLaw
from .algebra.ternary_law import TernaryLaw
from .algebra.cp_law import CPLaw
from .projectors.projector import Projector

__all__ = ["NaryLaw", "SparseNaryLaw", "TernaryLaw", "CPLaw", "Projector"]
__version__ = "0.1.0"

