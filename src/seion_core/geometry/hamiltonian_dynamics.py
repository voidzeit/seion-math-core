from __future__ import annotations

import numpy as np


def experimental_hamiltonian_step(position: np.ndarray, momentum: np.ndarray, step: float, gradient) -> tuple[np.ndarray, np.ndarray]:
    """A labeled experimental symplectic Euler step; no physical interpretation."""
    momentum_next = momentum - step * gradient(position)
    return position + step * momentum_next, momentum_next

