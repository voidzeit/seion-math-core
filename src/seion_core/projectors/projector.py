from __future__ import annotations

import numpy as np


class Projector:
    """Orthogonal projector represented by an orthonormal basis ``Q``."""

    def __init__(self, q: np.ndarray, method: str = "orthogonal_basis") -> None:
        q = np.asarray(q)
        if q.ndim != 2 or q.shape[1] < 1 or q.shape[0] < q.shape[1]:
            raise ValueError("Q must be a 2-D basis with 1 <= rank <= dimension")
        self.q = q
        self.method = method

    @classmethod
    def from_matrix(cls, matrix: np.ndarray, rank: int | None = None, method: str = "qr") -> "Projector":
        q, _ = np.linalg.qr(np.asarray(matrix))
        if rank is not None:
            q = q[:, :rank]
        return cls(q, method=method)

    @property
    def dimension(self) -> int:
        return int(self.q.shape[0])

    @property
    def rank(self) -> int:
        return int(self.q.shape[1])

    @property
    def matrix(self) -> np.ndarray:
        return self.q @ self.q.conj().T

    def apply(self, vector: np.ndarray) -> np.ndarray:
        vector = np.asarray(vector)
        if vector.shape != (self.dimension,):
            raise ValueError(f"vector must have shape ({self.dimension},)")
        return self.matrix @ vector

    def diagnostics(self, eps: float = 1e-15) -> dict[str, float | int | str]:
        p = self.matrix
        scale = max(float(np.linalg.norm(p)), eps)
        return {
            "idempotence_error": float(np.linalg.norm(p @ p - p) / scale),
            "selfadjoint_error": float(np.linalg.norm(p.conj().T - p) / scale),
            "dimension": self.dimension,
            "rank": self.rank,
            "method": self.method,
        }

    def complementary(self) -> np.ndarray:
        return np.eye(self.dimension, dtype=self.q.dtype) - self.matrix

