from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ChainComplex:
    """Finite cochain complex with matrices ``d_k: C^k -> C^(k+1)``."""

    differentials: list[np.ndarray]
    dimensions: tuple[int, ...] | None = None
    name: str = "finite_complex"

    def __post_init__(self) -> None:
        self.differentials = [np.asarray(d) for d in self.differentials]
        if self.dimensions is None:
            if self.differentials:
                dims = [self.differentials[0].shape[1]] + [d.shape[0] for d in self.differentials]
                self.dimensions = tuple(dims)
            else:
                self.dimensions = (0,)
        if len(self.dimensions) != len(self.differentials) + 1:
            raise ValueError("dimensions must describe every cochain space")
        for k, d in enumerate(self.differentials):
            if d.shape != (self.dimensions[k + 1], self.dimensions[k]):
                raise ValueError("differential shape does not match dimensions")

    def verify_d_squared_zero(self, tolerance: float = 1e-10) -> dict:
        residuals = [float(np.linalg.norm(self.differentials[k + 1] @ self.differentials[k])) for k in range(len(self.differentials) - 1)]
        return {"residuals": residuals, "passed": bool(all(r <= tolerance for r in residuals)), "tolerance": tolerance}

    def cohomology_dimension(self, degree: int, tolerance: float = 1e-10) -> int:
        if not 0 <= degree < len(self.dimensions):
            raise IndexError(degree)
        kernel_dim = self.dimensions[degree] - (np.linalg.matrix_rank(self.differentials[degree], tol=tolerance) if degree < len(self.differentials) else 0)
        image_rank = np.linalg.matrix_rank(self.differentials[degree - 1], tol=tolerance) if degree > 0 else 0
        return int(kernel_dim - image_rank)

    def harmonic_basis(self, degree: int, tolerance: float = 1e-10) -> np.ndarray:
        incoming = self.differentials[degree - 1] if degree > 0 else np.zeros((self.dimensions[degree], 0))
        outgoing = self.differentials[degree] if degree < len(self.differentials) else np.zeros((0, self.dimensions[degree]))
        lap = incoming @ incoming.conj().T + outgoing.conj().T @ outgoing
        values, vectors = np.linalg.eigh(0.5 * (lap + lap.conj().T))
        return vectors[:, values <= tolerance]

