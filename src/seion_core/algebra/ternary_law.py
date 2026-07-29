"""Ternary specialization and explicit composition conventions."""

from __future__ import annotations

import numpy as np

from ..exceptions import ConventionError, ShapeError
from .nary_law import NaryLaw


class TernaryLaw(NaryLaw):
    """A law ``mu: V_1 x V_2 x V_3 -> W`` with ternary conventions."""

    def __init__(self, tensor: np.ndarray, name: str = "ternary_law") -> None:
        super().__init__(np.asarray(tensor), arity=3, name=name)

    def astype(self, dtype: np.dtype | str) -> "TernaryLaw":
        return TernaryLaw(self.tensor.astype(dtype), name=self.name)

    def five_input_associator(
        self, x1: np.ndarray, x2: np.ndarray, x3: np.ndarray, x4: np.ndarray, x5: np.ndarray
    ) -> np.ndarray:
        """Return ``mu(mu(x1,x2,x3),x4,x5)-mu(x1,x2,mu(x3,x4,x5))``."""
        if self.input_dims != (self.output_dim,) * 3:
            raise ConventionError("five-input internal associator requires V -> V in every slot")
        return self(self(x1, x2, x3), x4, x5) - self(x1, x2, self(x3, x4, x5))

    def anchored_product(self, anchor: np.ndarray):
        anchor = np.asarray(anchor)
        if self.input_dims[2] != anchor.shape[0] or self.input_dims[:2] != (self.output_dim,) * 2:
            raise ConventionError("anchored binary reduction requires a common internal space")

        def product(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            return self(x, y, anchor)

        return product

    def anchored_associator(
        self, anchor: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray
    ) -> np.ndarray:
        product = self.anchored_product(anchor)
        return product(product(x, y), z) - product(x, product(y, z))

    def partial_composition(self, other: "TernaryLaw", slot: int) -> NaryLaw:
        """Return the 5-input operadic composition ``self o_slot other``."""
        if slot not in {0, 1, 2}:
            raise ValueError("slot must be 0, 1, or 2")
        from .compositions import partial_compose
        return partial_compose(self, other, slot)
