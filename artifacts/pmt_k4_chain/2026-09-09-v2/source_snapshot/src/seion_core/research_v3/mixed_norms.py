"""Projected/normal mask restrictions and slot-sensitive gains."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Mapping

import numpy as np
from scipy.linalg import null_space

from .local_constants import TypedLaw
from .operator_norms import frobenius_upper_bound, multilinear_power_lower_bound
from .types import TypeSystem


Mask = tuple[str, ...]


def complement_basis(q: np.ndarray, tolerance: float = 1.0e-12) -> np.ndarray:
    basis = null_space(np.asarray(q).conj().T, rcond=tolerance)
    return np.asarray(basis)


def restrict_tensor(
    law: TypedLaw,
    types: TypeSystem,
    mask: Mask,
    *,
    output_component: str = "F",
) -> np.ndarray:
    """Restrict input slots to projected (``P``) or normal (``N``) bases.

    Output component ``F`` retains ambient coordinates, ``P`` uses reduced
    projected coordinates, and ``N`` uses an orthonormal complement basis.
    """

    if len(mask) != law.arity or any(item not in {"P", "N"} for item in mask):
        raise ValueError("a mixed mask must contain one P/N symbol per input slot")
    data = np.asarray(law.tensor)
    output_space = types[law.output_type]
    if output_component == "P":
        data = np.tensordot(output_space.q.conj().T, data, axes=([1], [0]))
    elif output_component == "N":
        normal = complement_basis(output_space.q, output_space.tolerance)
        data = np.tensordot(normal.conj().T, data, axes=([1], [0]))
    elif output_component != "F":
        raise ValueError("output_component must be F, P, or N")
    for axis, (type_name, symbol) in enumerate(zip(law.input_types, mask), start=1):
        space = types[type_name]
        basis = space.q if symbol == "P" else complement_basis(space.q, space.tolerance)
        data = np.tensordot(data, basis, axes=([axis], [0]))
        data = np.moveaxis(data, -1, axis)
    return np.asarray(data)


@dataclass(frozen=True, slots=True)
class MixedNormTable:
    """Certified upper summaries plus attained lower diagnostics."""

    full: Mapping[Mask, float]
    projected: Mapping[Mask, float]
    normal: Mapping[Mask, float]
    lower_full: Mapping[Mask, float]
    method: str = "Frobenius upper / alternating lower"

    def norm(self, output: str, mask: Mask) -> float:
        table = {"F": self.full, "P": self.projected, "N": self.normal}.get(output)
        if table is None:
            raise ValueError("output must be F, P, or N")
        return float(table[mask])


def compute_mixed_norms(
    law: TypedLaw,
    types: TypeSystem,
    *,
    lower_restarts: int = 4,
    seed: int = 0,
) -> MixedNormTable:
    masks = list(product(("P", "N"), repeat=law.arity))
    full: dict[Mask, float] = {}
    projected: dict[Mask, float] = {}
    normal: dict[Mask, float] = {}
    lower: dict[Mask, float] = {}
    for index, mask in enumerate(masks):
        full_tensor = restrict_tensor(law, types, mask, output_component="F")
        projected_tensor = restrict_tensor(law, types, mask, output_component="P")
        normal_tensor = restrict_tensor(law, types, mask, output_component="N")
        full[mask] = frobenius_upper_bound(full_tensor)
        projected[mask] = frobenius_upper_bound(projected_tensor)
        normal[mask] = frobenius_upper_bound(normal_tensor)
        if all(dimension > 0 for dimension in full_tensor.shape):
            lower[mask] = multilinear_power_lower_bound(
                full_tensor, restarts=lower_restarts, seed=seed + index
            ).lower
        else:
            lower[mask] = 0.0
    return MixedNormTable(full=full, projected=projected, normal=normal, lower_full=lower)


def slot_gains(table: MixedNormTable, *, output: str = "F") -> tuple[float, ...]:
    """Best available one-normal-slot gains with all siblings projected."""

    if not table.full:
        return ()
    arity = len(next(iter(table.full)))
    gains: list[float] = []
    for slot in range(arity):
        mask = tuple("N" if index == slot else "P" for index in range(arity))
        gains.append(table.norm(output, mask))
    return tuple(gains)
