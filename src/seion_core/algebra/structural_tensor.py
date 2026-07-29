"""Dense structural tensors with explicit coordinate conventions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..exceptions import ShapeError


@dataclass
class StructuralTensor:
    """Tensor with shape ``(output, input_1, ..., input_n)``."""

    data: np.ndarray
    arity: int

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data)
        if self.arity < 2:
            raise ValueError("arity must be at least two")
        if self.data.ndim != self.arity + 1:
            raise ShapeError(
                f"expected rank {self.arity + 1} structural tensor, got {self.data.ndim}"
            )
        if any(dim <= 0 for dim in self.data.shape):
            raise ShapeError("all structural tensor dimensions must be positive")

    @property
    def output_dim(self) -> int:
        return int(self.data.shape[0])

    @property
    def input_dims(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.data.shape[1:])

    def contract(self, *vectors: np.ndarray) -> np.ndarray:
        if len(vectors) != self.arity:
            raise ShapeError(f"expected {self.arity} vectors, got {len(vectors)}")
        out = self.data
        for axis, vector in enumerate(vectors):
            vec = np.asarray(vector)
            expected = self.input_dims[axis]
            if vec.ndim != 1 or vec.shape[0] != expected:
                raise ShapeError(f"input {axis} must have shape ({expected},), got {vec.shape}")
            out = np.tensordot(out, vec, axes=([1], [0]))
        return np.asarray(out)

    def frobenius_norm(self) -> float:
        return float(np.linalg.norm(self.data.ravel()))

    def copy(self) -> "StructuralTensor":
        return StructuralTensor(self.data.copy(), self.arity)

