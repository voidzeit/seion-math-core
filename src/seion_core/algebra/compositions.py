"""Explicit operadic partial compositions."""

from __future__ import annotations

import numpy as np

from ..exceptions import ShapeError
from .nary_law import NaryLaw


def partial_compose(outer: NaryLaw, inner: NaryLaw, slot: int) -> NaryLaw:
    if not 0 <= slot < outer.arity:
        raise ValueError("slot outside outer arity")
    if outer.input_dims[slot] != inner.output_dim:
        raise ShapeError("inner output dimension must equal inserted outer input dimension")
    input_dims = outer.input_dims[:slot] + inner.input_dims + outer.input_dims[slot + 1 :]
    result = np.zeros((outer.output_dim, *input_dims), dtype=np.result_type(outer.tensor, inner.tensor))
    for full_index in np.ndindex(result.shape):
        output_index = full_index[0]
        inner_indices = full_index[1 + slot : 1 + slot + inner.arity]
        outer_inputs = []
        cursor = 1
        for j, dim in enumerate(outer.input_dims):
            if j == slot:
                cursor += inner.arity
                continue
            outer_inputs.append(np.eye(dim, dtype=result.dtype)[full_index[cursor]])
            cursor += 1
        inner_inputs = [np.eye(dim, dtype=result.dtype)[i] for dim, i in zip(inner.input_dims, inner_indices)]
        inserted = inner(*inner_inputs)
        ordered = outer_inputs[:slot] + [inserted] + outer_inputs[slot:]
        result[full_index] = outer(*ordered)[output_index]
    return NaryLaw(result, outer.arity + inner.arity - 1, name=f"{outer.name}_circ_{slot}_{inner.name}")

