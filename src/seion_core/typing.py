"""Runtime-visible mathematical type metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np

Array: TypeAlias = np.ndarray
Scalar: TypeAlias = Any


@dataclass(frozen=True)
class VectorSpace:
    """A finite-dimensional vector space label used for runtime validation."""

    name: str
    dimension: int
    field: str = "real"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("VectorSpace.name must be non-empty")
        if self.dimension <= 0:
            raise ValueError("VectorSpace.dimension must be positive")
        if self.field not in {"real", "complex", "rational", "symbolic"}:
            raise ValueError(f"Unsupported field label: {self.field}")

    @property
    def dtype(self) -> np.dtype:
        return np.dtype(np.complex128 if self.field == "complex" else np.float64)

