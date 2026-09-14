"""Exact ambient/projected PMT evaluation and root error decomposition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from seion_core.research_v3.typed_tree import Leaf, Tree

from .model import PMTModel


def _ambient_leaf_inputs(model: PMTModel, leaf_inputs: Mapping[int, np.ndarray]) -> dict[int, np.ndarray]:
    expected = model.leaf_dimensions()
    missing = sorted(set(expected) - set(leaf_inputs))
    extra = sorted(set(leaf_inputs) - set(expected))
    if missing or extra:
        raise ValueError(f"leaf input labels mismatch: missing={missing}, extra={extra}")
    values: dict[int, np.ndarray] = {}
    for label, dimension in expected.items():
        value = np.asarray(leaf_inputs[label])
        if value.shape != (dimension,):
            raise ValueError(
                f"leaf {label} needs an ambient vector of shape ({dimension},), got {value.shape}"
            )
        values[label] = value
    return values


def _visit_ambient(item: Tree, model: PMTModel, leaves: Mapping[int, np.ndarray], path: tuple[int, ...], values: dict):
    if isinstance(item, Leaf):
        value = leaves[item.label]
    else:
        children = [_visit_ambient(child, model, leaves, (*path, slot), values) for slot, child in enumerate(item.children)]
        value = model.laws[item.law_id].apply(children)
    values[path] = np.asarray(value)
    return values[path]


def _visit_projected(item: Tree, model: PMTModel, leaves: Mapping[int, np.ndarray], path: tuple[int, ...], values: dict):
    if isinstance(item, Leaf):
        value = leaves[item.label]
    else:
        children = [_visit_projected(child, model, leaves, (*path, slot), values) for slot, child in enumerate(item.children)]
        law = model.laws[item.law_id]
        value = model.types[item.output_type].project(law.apply(children))
    values[path] = np.asarray(value)
    return values[path]


@dataclass(frozen=True, slots=True)
class RootErrorDecomposition:
    """The three root errors and exact Hilbert identities."""

    ambient: float
    projected: float
    normal: float
    pythagorean_residual: float

    @property
    def projected_plus_normal_squared(self) -> float:
        return self.projected**2 + self.normal**2


@dataclass(frozen=True, slots=True)
class PMTEvaluation:
    """Ambient and recursively projected traces for one leaf assignment."""

    ambient_values: Mapping[tuple[int, ...], np.ndarray]
    projected_values: Mapping[tuple[int, ...], np.ndarray]
    ambient_root: np.ndarray
    projected_root: np.ndarray
    errors: RootErrorDecomposition


def evaluate_ambient(model: PMTModel, leaf_inputs: Mapping[int, np.ndarray]) -> Mapping[tuple[int, ...], np.ndarray]:
    leaves = _ambient_leaf_inputs(model, leaf_inputs)
    values: dict[tuple[int, ...], np.ndarray] = {}
    _visit_ambient(model.tree, model, leaves, (), values)
    return values


def evaluate_projected(model: PMTModel, leaf_inputs: Mapping[int, np.ndarray]) -> Mapping[tuple[int, ...], np.ndarray]:
    leaves = _ambient_leaf_inputs(model, leaf_inputs)
    values: dict[tuple[int, ...], np.ndarray] = {}
    _visit_projected(model.tree, model, leaves, (), values)
    return values


def evaluate_pmt(model: PMTModel, leaf_inputs: Mapping[int, np.ndarray]) -> PMTEvaluation:
    leaves = _ambient_leaf_inputs(model, leaf_inputs)
    ambient_values: dict[tuple[int, ...], np.ndarray] = {}
    projected_values: dict[tuple[int, ...], np.ndarray] = {}
    ambient_root = _visit_ambient(model.tree, model, leaves, (), ambient_values)
    projected_root = _visit_projected(model.tree, model, leaves, (), projected_values)
    ambient_delta = ambient_root - projected_root
    if isinstance(model.tree, Leaf):
        # Leaves use the extended convention P^ell = I, not the typed-space
        # reduction projector.  This keeps a leaf-only tree a zero-error
        # identity evaluation even when its ambient rank is not full.
        projected_delta = ambient_delta
        normal_delta = np.zeros_like(ambient_root)
    else:
        space = model.types[model.tree.output_type]
        projected_delta = space.project(ambient_root) - projected_root
        normal_delta = space.complement_projector @ ambient_root
    ambient_error = float(np.linalg.norm(ambient_delta))
    projected_error = float(np.linalg.norm(projected_delta))
    normal_error = float(np.linalg.norm(normal_delta))
    residual = abs(ambient_error**2 - projected_error**2 - normal_error**2)
    return PMTEvaluation(
        ambient_values=ambient_values,
        projected_values=projected_values,
        ambient_root=np.asarray(ambient_root),
        projected_root=np.asarray(projected_root),
        errors=RootErrorDecomposition(
            ambient=ambient_error,
            projected=projected_error,
            normal=normal_error,
            pythagorean_residual=residual,
        ),
    )
