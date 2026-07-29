"""Multisorted/typed n-ary laws."""

from __future__ import annotations

import numpy as np

from ..typing import VectorSpace
from .nary_law import NaryLaw


class TypedNaryLaw:
    def __init__(
        self, law: NaryLaw, inputs: tuple[VectorSpace, ...], output: VectorSpace
    ) -> None:
        if len(inputs) != law.arity:
            raise ValueError("number of input spaces must equal law arity")
        if tuple(s.dimension for s in inputs) != law.input_dims:
            raise ValueError("input space dimensions do not match law tensor")
        if output.dimension != law.output_dim:
            raise ValueError("output space dimension does not match law tensor")
        self.law = law
        self.inputs = inputs
        self.output = output

    @property
    def arity(self) -> int:
        return self.law.arity

    def __call__(self, *vectors: np.ndarray) -> np.ndarray:
        return self.law(*vectors)

