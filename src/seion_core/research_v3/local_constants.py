"""Typed multilinear laws and declared nodewise constants."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import string
from typing import Mapping, Sequence

import numpy as np

from .types import TypeSystem


def apply_tensor_loops(tensor: np.ndarray, vectors: Sequence[np.ndarray]) -> np.ndarray:
    """Coordinate-loop authority for a dense multilinear tensor."""

    data = np.asarray(tensor)
    values = tuple(np.asarray(value) for value in vectors)
    if data.ndim < 3:
        raise ValueError("a law must have one output and at least two input axes")
    if len(values) != data.ndim - 1:
        raise ValueError(f"expected {data.ndim - 1} inputs, got {len(values)}")
    for slot, (value, dimension) in enumerate(zip(values, data.shape[1:])):
        if value.shape != (dimension,):
            raise ValueError(f"slot {slot} must have shape ({dimension},), got {value.shape}")
    output = np.zeros(data.shape[0], dtype=np.result_type(data, *values))
    for out_index in range(data.shape[0]):
        for indices in product(*(range(dimension) for dimension in data.shape[1:])):
            term = data[(out_index, *indices)]
            for value, index in zip(values, indices):
                term = term * value[index]
            output[out_index] += term
    return output


def apply_tensor_numpy(tensor: np.ndarray, vectors: Sequence[np.ndarray]) -> np.ndarray:
    """Independent NumPy/Einsum evaluation."""

    data = np.asarray(tensor)
    values = tuple(np.asarray(value) for value in vectors)
    arity = data.ndim - 1
    if arity != len(values):
        raise ValueError(f"expected {arity} inputs, got {len(values)}")
    alphabet = string.ascii_letters
    if arity + 1 > len(alphabet):
        raise ValueError("arity exceeds the einsum label budget")
    out = alphabet[0]
    slots = alphabet[1 : arity + 1]
    expression = f"{out}{slots}," + ",".join(slots) + f"->{out}"
    return np.einsum(expression, data, *values, optimize=True)


@dataclass(frozen=True, slots=True)
class TypedLaw:
    """Dense typed law ``mu: V_tau1 x ... x V_taua -> V_tauout``."""

    law_id: str
    input_types: tuple[str, ...]
    output_type: str
    tensor: np.ndarray

    def __post_init__(self) -> None:
        data = np.asarray(self.tensor)
        if not self.law_id:
            raise ValueError("a law id must be nonempty")
        if len(self.input_types) < 2:
            raise ValueError("law arity must be at least two")
        if data.ndim != len(self.input_types) + 1:
            raise ValueError(
                f"tensor rank {data.ndim} does not match arity {len(self.input_types)}"
            )
        if not self.output_type or any(not item for item in self.input_types):
            raise ValueError("all law colors must be nonempty")
        object.__setattr__(self, "tensor", np.array(data, copy=True))

    @property
    def arity(self) -> int:
        return len(self.input_types)

    def validate_dimensions(self, types: TypeSystem) -> None:
        expected = (
            types[self.output_type].dimension,
            *(types[name].dimension for name in self.input_types),
        )
        if self.tensor.shape != expected:
            raise ValueError(
                f"law {self.law_id!r} tensor shape {self.tensor.shape} does not match {expected}"
            )

    def apply_reference(self, vectors: Sequence[np.ndarray]) -> np.ndarray:
        return apply_tensor_loops(self.tensor, vectors)

    def apply(self, vectors: Sequence[np.ndarray]) -> np.ndarray:
        return apply_tensor_numpy(self.tensor, vectors)


def validate_law_family(laws: Mapping[str, TypedLaw], types: TypeSystem) -> None:
    for key, law in laws.items():
        if key != law.law_id:
            raise ValueError(f"law map key {key!r} disagrees with id {law.law_id!r}")
        if law.output_type not in types or any(name not in types for name in law.input_types):
            raise ValueError(f"law {key!r} references an unknown type")
        law.validate_dimensions(types)
