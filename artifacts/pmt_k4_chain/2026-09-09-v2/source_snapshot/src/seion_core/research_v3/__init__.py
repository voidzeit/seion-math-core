"""Nodewise stability tools for typed recursively projected trees.

The v3 namespace is intentionally independent of :mod:`research_v2`.  Its
public objects distinguish ambient, projected-root, normal, and reduced
coordinate errors and never attach an optimality claim to an uncertified
numerical search.
"""

from .certificates import BoundCertificate, LocalSummary, certify_tree
from .local_constants import TypedLaw
from .typed_tree import Leaf, Node, Tree, validate_tree
from .types import TypeSystem, TypedSpace

__all__ = [
    "BoundCertificate",
    "Leaf",
    "LocalSummary",
    "Node",
    "Tree",
    "TypeSystem",
    "TypedLaw",
    "TypedSpace",
    "certify_tree",
    "validate_tree",
]
