"""Finite typed Hilbert spaces and orthogonal projectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np


def _adjoint(value: np.ndarray) -> np.ndarray:
    return np.asarray(value).conj().T


@dataclass(frozen=True, slots=True)
class TypedSpace:
    """A finite-dimensional Hilbert-space color with ``P = Q Q*``.

    ``q`` has orthonormal columns and therefore supplies both the orthogonal
    projector and reduced coordinates.  The constructor validates this
    contract instead of silently orthogonalizing user data.
    """

    name: str
    dimension: int
    q: np.ndarray
    field: str = "real"
    tolerance: float = 1.0e-12

    def __post_init__(self) -> None:
        q = np.asarray(self.q)
        if not self.name:
            raise ValueError("a type name must be nonempty")
        if self.dimension < 1:
            raise ValueError("dimension must be positive")
        if q.ndim != 2 or q.shape[0] != self.dimension:
            raise ValueError(
                f"Q for {self.name!r} must have shape ({self.dimension}, rank), got {q.shape}"
            )
        if not 0 < q.shape[1] <= self.dimension:
            raise ValueError("the reduced rank must lie between one and the ambient dimension")
        if self.field not in {"real", "complex"}:
            raise ValueError("field must be 'real' or 'complex'")
        if self.field == "real" and np.iscomplexobj(q) and np.max(np.abs(q.imag)) > self.tolerance:
            raise ValueError("a real typed space cannot use a genuinely complex embedding")
        gram = _adjoint(q) @ q
        if not np.allclose(gram, np.eye(q.shape[1]), atol=self.tolerance, rtol=0.0):
            raise ValueError("Q must have orthonormal columns")
        object.__setattr__(self, "q", np.array(q, copy=True))

    @classmethod
    def coordinate(
        cls, name: str, dimension: int, rank: int, *, field: str = "real"
    ) -> "TypedSpace":
        """Create the coordinate subspace spanned by the first ``rank`` axes."""

        if not 0 < rank <= dimension:
            raise ValueError("rank must satisfy 1 <= rank <= dimension")
        dtype = complex if field == "complex" else float
        return cls(name, dimension, np.eye(dimension, rank, dtype=dtype), field=field)

    @property
    def rank(self) -> int:
        return int(self.q.shape[1])

    @property
    def projector(self) -> np.ndarray:
        return self.q @ _adjoint(self.q)

    @property
    def complement_projector(self) -> np.ndarray:
        return np.eye(self.dimension, dtype=self.q.dtype) - self.projector

    def lift(self, reduced: np.ndarray) -> np.ndarray:
        value = np.asarray(reduced)
        if value.shape != (self.rank,):
            raise ValueError(f"reduced vector for {self.name} must have shape ({self.rank},)")
        return self.q @ value

    def reduce(self, ambient: np.ndarray) -> np.ndarray:
        value = np.asarray(ambient)
        if value.shape != (self.dimension,):
            raise ValueError(
                f"ambient vector for {self.name} must have shape ({self.dimension},)"
            )
        return _adjoint(self.q) @ value

    def project(self, ambient: np.ndarray) -> np.ndarray:
        value = np.asarray(ambient)
        if value.shape != (self.dimension,):
            raise ValueError(
                f"ambient vector for {self.name} must have shape ({self.dimension},)"
            )
        return self.projector @ value


class TypeSystem(Mapping[str, TypedSpace]):
    """Immutable name-indexed finite type set ``Tau``."""

    def __init__(self, spaces: Iterable[TypedSpace]):
        index: dict[str, TypedSpace] = {}
        for space in spaces:
            if space.name in index:
                raise ValueError(f"duplicate type {space.name!r}")
            index[space.name] = space
        if not index:
            raise ValueError("a type system must contain at least one type")
        self._spaces = index

    def __getitem__(self, key: str) -> TypedSpace:
        return self._spaces[key]

    def __iter__(self):
        return iter(self._spaces)

    def __len__(self) -> int:
        return len(self._spaces)

    def signature(self) -> tuple[tuple[str, int, int, str], ...]:
        return tuple(
            (name, space.dimension, space.rank, space.field)
            for name, space in sorted(self._spaces.items())
        )
