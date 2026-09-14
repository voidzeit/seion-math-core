"""Recursively projected NumPy/CUDA evaluation and named root errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .exact_evaluation import EvaluationTrace, Path, evaluate_ambient_numpy
from .local_constants import TypedLaw, validate_law_family
from .typed_tree import Leaf, Node, Tree, validate_tree
from .types import TypeSystem


@dataclass(frozen=True, slots=True)
class TreeErrors:
    ambient: float
    projected_root: float
    normal_root: float
    reduced_coordinate: float
    pythagorean_residual: float
    reduced_projected_residual: float


def _leaf_value(leaf: Leaf, inputs, types: TypeSystem) -> np.ndarray:
    try:
        reduced = inputs[leaf.label]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"missing reduced input for leaf {leaf.label}") from exc
    return types[leaf.type_name].lift(np.asarray(reduced))


def evaluate_projected_numpy(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> EvaluationTrace:
    """Evaluate ``R_v=P_v mu_v(R_children)`` recursively."""

    validate_law_family(laws, types)
    validate_tree(tree, types, laws)
    values: dict[Path, np.ndarray] = {}

    def visit(item: Tree, path: Path) -> np.ndarray:
        if isinstance(item, Leaf):
            value = _leaf_value(item, reduced_inputs, types)
        else:
            children = [visit(child, (*path, slot)) for slot, child in enumerate(item.children)]
            unprojected = laws[item.law_id].apply(children)
            value = types[item.output_type].project(unprojected)
        values[path] = np.asarray(value)
        return values[path]

    root = visit(tree, ())
    return EvaluationTrace(root=root, values=values)


def evaluate_reduced_coordinates(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> np.ndarray:
    projected = evaluate_projected_numpy(tree, laws, types, reduced_inputs)
    root_type = tree.type_name if isinstance(tree, Leaf) else tree.output_type
    return types[root_type].reduce(projected.root)


def compute_tree_errors(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> TreeErrors:
    ambient_trace = evaluate_ambient_numpy(tree, laws, types, reduced_inputs)
    projected_trace = evaluate_projected_numpy(tree, laws, types, reduced_inputs)
    root_type = tree.type_name if isinstance(tree, Leaf) else tree.output_type
    space = types[root_type]
    delta = ambient_trace.root - projected_trace.root
    projected_delta = space.project(ambient_trace.root) - projected_trace.root
    normal = space.complement_projector @ ambient_trace.root
    reduced_delta = space.reduce(ambient_trace.root) - space.reduce(projected_trace.root)
    ambient_error = float(np.linalg.norm(delta))
    projected_error = float(np.linalg.norm(projected_delta))
    normal_error = float(np.linalg.norm(normal))
    reduced_error = float(np.linalg.norm(reduced_delta))
    return TreeErrors(
        ambient=ambient_error,
        projected_root=projected_error,
        normal_root=normal_error,
        reduced_coordinate=reduced_error,
        pythagorean_residual=abs(ambient_error**2 - projected_error**2 - normal_error**2),
        reduced_projected_residual=abs(reduced_error - projected_error),
    )


def evaluate_projected_torch(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
    *,
    device: str = "cuda",
    dtype=None,
):
    """PyTorch reference for CPU/GPU parity; no TF32 or mixed precision."""

    import torch

    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    torch.backends.cuda.matmul.allow_tf32 = False
    if dtype is None:
        complex_data = any(np.iscomplexobj(law.tensor) for law in laws.values())
        dtype = torch.complex128 if complex_data else torch.float64

    def tensor(value):
        return torch.as_tensor(value, dtype=dtype, device=device)

    torch_laws = {key: tensor(law.tensor) for key, law in laws.items()}
    torch_q = {name: tensor(space.q) for name, space in types.items()}

    def apply(data, values):
        arity = data.ndim - 1
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        out = alphabet[0]
        slots = alphabet[1 : arity + 1]
        equation = f"{out}{slots}," + ",".join(slots) + f"->{out}"
        return torch.einsum(equation, data, *values)

    def visit(item: Tree):
        if isinstance(item, Leaf):
            return torch_q[item.type_name] @ tensor(reduced_inputs[item.label])
        children = [visit(child) for child in item.children]
        value = apply(torch_laws[item.law_id], children)
        q = torch_q[item.output_type]
        return q @ (q.mH @ value)

    return visit(tree)
