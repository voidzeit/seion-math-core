"""Finite-dimensional n-linear internal laws."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np

from ..exceptions import ShapeError
from .structural_tensor import StructuralTensor


@dataclass
class NaryLaw:
    """An n-linear map represented by a structural tensor.

    Coordinates always use ``K[a, i_1, ..., i_n]`` and vectors are one
    dimensional arrays.  Shape validation is strict by design.
    """

    tensor: np.ndarray
    arity: int
    name: str = "nary_law"

    def __post_init__(self) -> None:
        self.tensor = np.asarray(self.tensor)
        if self.arity < 2:
            raise ValueError("arity must satisfy n >= 2")
        if self.tensor.ndim != self.arity + 1:
            raise ShapeError(
                f"tensor for arity {self.arity} must have rank {self.arity + 1}; "
                f"got shape {self.tensor.shape}"
            )
        if any(d <= 0 for d in self.tensor.shape):
            raise ShapeError("law dimensions must be positive")
        if not np.issubdtype(self.tensor.dtype, np.number):
            raise TypeError("law tensor must have a numeric dtype")

    @classmethod
    def from_tensor(cls, tensor: np.ndarray, arity: int, name: str = "nary_law") -> "NaryLaw":
        return cls(np.asarray(tensor), arity=arity, name=name)

    @property
    def output_dim(self) -> int:
        return int(self.tensor.shape[0])

    @property
    def input_dims(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.tensor.shape[1:])

    @property
    def dtype(self) -> np.dtype:
        return self.tensor.dtype

    @property
    def field(self) -> str:
        return "complex" if np.iscomplexobj(self.tensor) else "real"

    def structural_tensor(self) -> StructuralTensor:
        return StructuralTensor(self.tensor, self.arity)

    def _validate_vectors(self, vectors: Iterable[np.ndarray]) -> tuple[np.ndarray, ...]:
        values = tuple(np.asarray(v) for v in vectors)
        if len(values) != self.arity:
            raise ShapeError(f"{self.name} expects {self.arity} inputs, got {len(values)}")
        for i, (value, dim) in enumerate(zip(values, self.input_dims)):
            if value.ndim != 1 or value.shape[0] != dim:
                raise ShapeError(
                    f"input {i} of {self.name} must have shape ({dim},), got {value.shape}"
                )
        return values

    def __call__(self, *vectors: np.ndarray) -> np.ndarray:
        values = self._validate_vectors(vectors)
        out = self.tensor
        for value in values:
            out = np.tensordot(out, value, axes=([1], [0]))
        return np.asarray(out)

    def batch(self, *vectors: np.ndarray) -> np.ndarray:
        """Evaluate batches with shape ``(batch, dimension)``."""
        if len(vectors) != self.arity:
            raise ShapeError(f"expected {self.arity} batched inputs")
        arrays = tuple(np.asarray(v) for v in vectors)
        batch_size = arrays[0].shape[0]
        for i, (value, dim) in enumerate(zip(arrays, self.input_dims)):
            if value.ndim != 2 or value.shape != (batch_size, dim):
                raise ShapeError(f"batch input {i} must have shape ({batch_size}, {dim})")
        # einsum labels are avoided so this remains valid for arbitrary arity.
        outputs = [self(*[value[j] for value in arrays]) for j in range(batch_size)]
        return np.stack(outputs, axis=0)

    def to_tensor(self) -> np.ndarray:
        return self.tensor.copy()

    def norm(self) -> float:
        return float(np.linalg.norm(self.tensor.ravel()))

    def scale(self, scalar: complex) -> "NaryLaw":
        return NaryLaw(self.tensor * scalar, self.arity, name=f"{scalar}*{self.name}")

    def astype(self, dtype: np.dtype | str) -> "NaryLaw":
        return NaryLaw(self.tensor.astype(dtype), self.arity, name=self.name)

    def multilinearity_residual(
        self, vectors: tuple[np.ndarray, ...], index: int, alpha: complex = 0.37
    ) -> float:
        if index < 0 or index >= self.arity:
            raise IndexError(index)
        values = self._validate_vectors(vectors)
        lhs = self(*values[:index], alpha * values[index], *values[index + 1 :])
        rhs = alpha * self(*values)
        return float(np.linalg.norm(lhs - rhs))

    def dense_entries(self, tolerance: float = 0.0) -> list[tuple[tuple[int, ...], complex]]:
        entries: list[tuple[tuple[int, ...], complex]] = []
        for index in product(*[range(d) for d in self.tensor.shape]):
            value = self.tensor[index]
            if abs(value) > tolerance:
                entries.append((index, value.item()))
        return entries


class SparseNaryLaw:
    """Sparse coordinate representation with the same strict call contract."""

    def __init__(
        self,
        output_dim: int,
        input_dims: tuple[int, ...],
        entries: dict[tuple[int, ...], complex],
        name: str = "sparse_nary_law",
    ) -> None:
        if len(input_dims) < 2 or output_dim <= 0 or any(d <= 0 for d in input_dims):
            raise ShapeError("invalid sparse law dimensions")
        self.output_dim = int(output_dim)
        self.input_dims = tuple(int(d) for d in input_dims)
        self.arity = len(input_dims)
        self.entries = dict(entries)
        self.name = name
        shape = (self.output_dim, *self.input_dims)
        for index in self.entries:
            if len(index) != self.arity + 1 or any(i < 0 or i >= shape[k] for k, i in enumerate(index)):
                raise ShapeError(f"sparse entry index {index} is outside shape {shape}")

    @property
    def dtype(self) -> np.dtype:
        return np.asarray(list(self.entries.values()) or [0.0]).dtype

    @property
    def field(self) -> str:
        return "complex" if any(np.iscomplexobj(v) for v in self.entries.values()) else "real"

    def __call__(self, *vectors: np.ndarray) -> np.ndarray:
        if len(vectors) != self.arity:
            raise ShapeError(f"{self.name} expects {self.arity} inputs")
        values = [np.asarray(v) for v in vectors]
        for i, (value, dim) in enumerate(zip(values, self.input_dims)):
            if value.ndim != 1 or value.shape[0] != dim:
                raise ShapeError(f"input {i} must have shape ({dim},), got {value.shape}")
        out = np.zeros(self.output_dim, dtype=np.result_type(self.dtype, *[v.dtype for v in values]))
        for index, coefficient in self.entries.items():
            out[index[0]] += coefficient * np.prod([values[j][index[j + 1]] for j in range(self.arity)])
        return out

    def to_dense(self) -> NaryLaw:
        tensor = np.zeros((self.output_dim, *self.input_dims), dtype=self.dtype)
        for index, value in self.entries.items():
            tensor[index] = value
        return NaryLaw(tensor, self.arity, self.name.replace("sparse", "dense"))


def zero_law(dimension: int, arity: int = 3, dtype: str | np.dtype = np.float64) -> NaryLaw:
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    return NaryLaw(np.zeros((dimension,) * (arity + 1), dtype=dtype), arity, name="zero_law")

