"""Numerical tensor-network evaluator for finite DAGs with shared nodes."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dag import DAGTopology
from network import NodeCore, NodeProjector
from seion_core.research_v5.dag_domain_certificate import (
    DAGDomainNode,
    certify_dag_domain,
    certify_dag_domain_rank_aware,
    optimal_dag_domain_ranks,
    optimal_rank_aware_dag_domain_ranks,
)


@dataclass
class DAGTensorNetwork:
    topology: DAGTopology
    cores: dict[str, NodeCore]
    projectors: dict[str, NodeProjector] = field(default_factory=dict)

    @classmethod
    def random(cls, topology: DAGTopology, *, seed: int) -> "DAGTensorNetwork":
        rng = np.random.default_rng(seed)
        cores: dict[str, NodeCore] = {}
        for node_id in topology.topological_order:
            node = topology.nodes[node_id]
            child_dims = [
                topology.leaf_dims[ref] if isinstance(ref, int) else topology.nodes[ref].ambient_dim
                for ref in node.inputs
            ]
            tensor = rng.standard_normal((node.ambient_dim, *child_dims)) / np.sqrt(np.prod(child_dims))
            cores[node_id] = NodeCore(tensor=tensor)
        return cls(topology=topology, cores=cores)

    def sample_leaf_batch(self, batch_size: int, *, seed: int) -> list[np.ndarray]:
        rng = np.random.default_rng(seed)
        return [rng.standard_normal((batch_size, dim)) for dim in self.topology.leaf_dims]

    def _children(self, node_id: str, values: dict[str, np.ndarray], leaf_batch: list[np.ndarray]) -> list[np.ndarray]:
        return [leaf_batch[ref] if isinstance(ref, int) else values[ref] for ref in self.topology.nodes[node_id].inputs]

    def ambient_forward(self, leaf_batch: list[np.ndarray]) -> dict[str, np.ndarray]:
        self._validate_leaf_batch(leaf_batch)
        values: dict[str, np.ndarray] = {}
        for node_id in self.topology.topological_order:
            values[node_id] = self.cores[node_id].apply(self._children(node_id, values, leaf_batch))
        return values

    def fit_projectors(self, ambient_values: dict[str, np.ndarray]) -> None:
        projectors: dict[str, NodeProjector] = {}
        for node_id in self.topology.topological_order:
            node = self.topology.nodes[node_id]
            batch = ambient_values[node_id]
            _, singular_values, vt = np.linalg.svd(batch, full_matrices=True)
            basis = vt.T
            singular = np.zeros(node.ambient_dim)
            singular[: len(singular_values)] = singular_values
            projectors[node_id] = NodeProjector(basis=basis, singular_values=singular)
        self.projectors = projectors

    def reduced_forward(self, leaf_batch: list[np.ndarray], ranks: dict[str, int]) -> dict[str, np.ndarray]:
        self._validate_leaf_batch(leaf_batch)
        if not self.projectors:
            raise RuntimeError("fit_projectors must be called before reduced_forward")
        raw_values: dict[str, np.ndarray] = {}
        reduced_values: dict[str, np.ndarray] = {}
        for node_id in self.topology.topological_order:
            raw = self.cores[node_id].apply(self._children(node_id, reduced_values, leaf_batch))
            raw_values[node_id] = raw
            if node_id == self.topology.root_id:
                reduced_values[node_id] = raw
            else:
                rank = ranks.get(node_id, self.topology.nodes[node_id].ambient_dim)
                reduced_values[node_id] = self.projectors[node_id].project(raw, rank)
        return raw_values

    def _rank_dimension(self, node_id: str, ranks: dict[str, int]) -> int:
        """Return the materialized dimension of an internal node.

        The root is deliberately unprojected in this backend, so its
        materialized output always has the ambient dimension.  Non-root
        outputs are stored in the first ``rank`` projector coordinates.
        """

        node = self.topology.nodes[node_id]
        if node_id == self.topology.root_id:
            return node.ambient_dim
        return max(0, min(int(ranks.get(node_id, node.ambient_dim)), node.ambient_dim))

    def _compressed_core(self, node_id: str, ranks: dict[str, int]) -> np.ndarray:
        """Transform one ambient core to exact projected coordinates.

        For every non-root child, the corresponding input mode is contracted
        with that child's fitted basis.  For every non-root output, the output
        mode is contracted with the transpose of the local basis.  Thus this
        is an algebraic change of coordinates, not an approximation beyond
        the projections already used by :meth:`reduced_forward`.
        """

        node = self.topology.nodes[node_id]
        tensor = self.cores[node_id].tensor
        for axis, ref in enumerate(node.inputs, start=1):
            if not isinstance(ref, str):
                continue
            rank = self._rank_dimension(ref, ranks)
            basis = self.projectors[ref].basis[:, :rank]
            tensor = np.tensordot(tensor, basis, axes=([axis], [0]))
            tensor = np.moveaxis(tensor, -1, axis)
        if node_id != self.topology.root_id:
            rank = self._rank_dimension(node_id, ranks)
            basis = self.projectors[node_id].basis[:, :rank]
            tensor = np.tensordot(basis.T, tensor, axes=([1], [0]))
        return tensor

    def compressed_forward(
        self, leaf_batch: list[np.ndarray], ranks: dict[str, int]
    ) -> dict[str, np.ndarray]:
        """Evaluate the projected network using materialized rank coordinates.

        The returned value at each non-root node is a coordinate matrix of
        width equal to its assigned rank; the root remains in ambient
        coordinates.  Lifting these coordinates gives exactly the values
        produced by ``reduced_forward`` under the same ranks.
        """

        self._validate_leaf_batch(leaf_batch)
        if not self.projectors:
            raise RuntimeError("fit_projectors must be called before compressed_forward")
        values: dict[str, np.ndarray] = {}
        for node_id in self.topology.topological_order:
            node = self.topology.nodes[node_id]
            children = [
                leaf_batch[ref] if isinstance(ref, int) else values[ref]
                for ref in node.inputs
            ]
            values[node_id] = NodeCore(tensor=self._compressed_core(node_id, ranks)).apply(children)
        return values

    def resource_proxy(self, ranks: dict[str, int], *, dtype_bytes: int = 8) -> dict[str, int]:
        """Return a deterministic compressed-execution resource proxy.

        ``contraction_units_per_sample`` counts one output-input multilinear
        product per transformed-core entry.  ``core_storage_units`` counts
        transformed-core entries and ``basis_storage_units`` counts fitted
        basis entries.  ``peak_activation_units_per_sample`` follows the
        declared topological schedule, freeing a value after its last input
        slot is consumed; shared DAG nodes are therefore materialized once.
        These are analytical units, not wall-clock FLOPs or a hardware
        benchmark.
        """

        if dtype_bytes <= 0:
            raise ValueError("dtype_bytes must be positive")
        if not self.projectors:
            raise RuntimeError("fit_projectors must be called before resource_proxy")

        def output_dim(node_id: str) -> int:
            return self._rank_dimension(node_id, ranks)

        core_storage = 0
        contraction_units = 0
        basis_storage = 0
        node_units: dict[str, int] = {}
        for node_id in self.topology.topological_order:
            node = self.topology.nodes[node_id]
            input_dims = [
                self.topology.leaf_dims[ref] if isinstance(ref, int) else output_dim(ref)
                for ref in node.inputs
            ]
            units = output_dim(node_id) * int(np.prod(input_dims, dtype=int))
            node_units[node_id] = units
            core_storage += units
            contraction_units += units
            if node_id != self.topology.root_id:
                basis_storage += node.ambient_dim * output_dim(node_id)

        remaining: dict[tuple[str, int], int] = {}
        for index in range(len(self.topology.leaf_dims)):
            remaining[("leaf", index)] = 0
        for node_id in self.topology.topological_order:
            remaining[("node", node_id)] = 0
        for node in self.topology.nodes.values():
            for ref in node.inputs:
                key = ("leaf", ref) if isinstance(ref, int) else ("node", ref)
                remaining[key] += 1

        live: dict[tuple[str, int] | tuple[str, str], int] = {
            ("leaf", index): dim
            for index, dim in enumerate(self.topology.leaf_dims)
            if remaining[("leaf", index)] > 0
        }
        peak = sum(live.values())
        for node_id in self.topology.topological_order:
            live[("node", node_id)] = output_dim(node_id)
            peak = max(peak, sum(live.values()))
            for ref in self.topology.nodes[node_id].inputs:
                key = ("leaf", ref) if isinstance(ref, int) else ("node", ref)
                remaining[key] -= 1
                if remaining[key] == 0:
                    live.pop(key, None)

        return {
            "rank_budget": int(sum(int(ranks.get(node_id, output_dim(node_id))) for node_id in self.topology.topological_order)),
            "core_storage_units": int(core_storage),
            "basis_storage_units": int(basis_storage),
            "parameter_storage_bytes": int((core_storage + basis_storage) * dtype_bytes),
            "contraction_units_per_sample": int(contraction_units),
            "peak_activation_units_per_sample": int(peak),
            "node_contraction_units": {key: int(value) for key, value in node_units.items()},
        }

    def _certificate_nodes(self, leaf_norm_bounds: list[float] | tuple[float, ...]) -> tuple[dict[str, DAGDomainNode], dict[str, str]]:
        if len(leaf_norm_bounds) != len(self.topology.leaf_dims):
            raise ValueError("one norm bound is required for every leaf")
        leaf_ids = {index: f"leaf:{index}" for index in range(len(self.topology.leaf_dims))}
        nodes: dict[str, DAGDomainNode] = {
            leaf_id: DAGDomainNode(leaf_id) for leaf_id in leaf_ids.values()
        }
        for node_id in self.topology.topological_order:
            node = self.topology.nodes[node_id]
            core_flat = self.cores[node_id].tensor.reshape(node.ambient_dim, -1)
            if node_id == self.topology.root_id:
                normal_bounds = (0.0,) * (node.ambient_dim + 1)
                projected_bounds = (float(np.linalg.norm(core_flat)),) * (node.ambient_dim + 1)
            else:
                projector = self.projectors[node_id]
                identity = np.eye(node.ambient_dim)
                normal_bounds = []
                projected_bounds = []
                for rank in range(node.ambient_dim + 1):
                    basis = projector.basis[:, :rank]
                    residual = identity - basis @ basis.T
                    normal_bounds.append(float(np.linalg.norm(residual @ core_flat)))
                    projected_bounds.append(float(np.linalg.norm((basis @ basis.T) @ core_flat)))
                normal_bounds = tuple(normal_bounds)
                projected_bounds = tuple(projected_bounds)
            nodes[node_id] = DAGDomainNode(
                node_id=node_id,
                inputs=tuple(leaf_ids[ref] if isinstance(ref, int) else ref for ref in node.inputs),
                operator_bound=float(np.linalg.norm(self.cores[node_id].tensor.reshape(node.ambient_dim, -1))),
                normal_bounds=normal_bounds,
                projected_operator_bounds=projected_bounds,
            )
        return nodes, leaf_ids

    def global_error_certificate(
        self,
        leaf_norm_bounds: list[float] | tuple[float, ...],
        ranks: dict[str, int] | None = None,
    ) -> dict[str, object]:
        """Return the global domain certificate and its DAG diagnostics."""

        nodes, leaf_ids = self._certificate_nodes(leaf_norm_bounds)
        if ranks is None:
            ranks = {
                node_id: self.topology.nodes[node_id].ambient_dim
                for node_id in self.topology.topological_order
            }
        certificate = certify_dag_domain(
            nodes,
            self.topology.root_id,
            leaf_norm_bounds={leaf_id: bound for (leaf_id, bound) in zip(leaf_ids.values(), leaf_norm_bounds)},
            ranks=ranks,
        )
        return {
            "root_bound": certificate.root_bound,
            "value_bounds": certificate.value_bounds,
            "error_bounds": certificate.error_bounds,
            "downstream_gains": certificate.downstream_gains,
            "rank_costs": certificate.rank_costs,
            "operator_norm_enclosures": {
                node_id: nodes[node_id].operator_bound
                for node_id in self.topology.topological_order
            },
            "normal_norm_enclosures": {
                node_id: nodes[node_id].normal_bounds
                for node_id in self.topology.topological_order
            },
            "projected_operator_enclosures": {
                node_id: nodes[node_id].projected_operator_bounds
                for node_id in self.topology.topological_order
            },
        }

    def rank_aware_error_certificate(
        self,
        leaf_norm_bounds: list[float] | tuple[float, ...],
        ranks: dict[str, int],
    ) -> dict[str, object]:
        """Return the fixed-assignment rank-aware domain certificate."""

        nodes, leaf_ids = self._certificate_nodes(leaf_norm_bounds)
        leaf_bounds = {
            leaf_id: bound for leaf_id, bound in zip(leaf_ids.values(), leaf_norm_bounds)
        }
        certificate = certify_dag_domain_rank_aware(
            nodes,
            self.topology.root_id,
            leaf_norm_bounds=leaf_bounds,
            ranks=ranks,
        )
        return {
            "root_bound": certificate.root_bound,
            "exact_value_bounds": certificate.exact_value_bounds,
            "approximate_value_bounds": certificate.approximate_value_bounds,
            "mixed_value_bounds": certificate.mixed_value_bounds,
            "error_bounds": certificate.error_bounds,
            "ranks": certificate.ranks,
        }

    def optimal_certificate_allocation(
        self,
        budget: int,
        *,
        leaf_norm_bounds: list[float] | tuple[float, ...],
    ) -> dict[str, int]:
        """Allocate ranks by the exact finite DAG certificate objective."""

        nodes, leaf_ids = self._certificate_nodes(leaf_norm_bounds)
        leaf_bounds = {
            leaf_id: bound for leaf_id, bound in zip(leaf_ids.values(), leaf_norm_bounds)
        }
        internal_count = self.topology.internal_node_count
        if budget < internal_count:
            raise ValueError("budget must allow rank one at every internal node")
        allocation, _ = optimal_dag_domain_ranks(
            nodes,
            self.topology.root_id,
            leaf_norm_bounds=leaf_bounds,
            budget=budget - 1,
        )
        return {self.topology.root_id: 1, **allocation}

    def optimal_rank_aware_certificate_allocation(
        self,
        budget: int,
        *,
        leaf_norm_bounds: list[float] | tuple[float, ...],
    ) -> dict[str, int]:
        """Small-DAG oracle for the rank-aware certificate objective."""

        nodes, leaf_ids = self._certificate_nodes(leaf_norm_bounds)
        leaf_bounds = {
            leaf_id: bound for leaf_id, bound in zip(leaf_ids.values(), leaf_norm_bounds)
        }
        if budget < self.topology.internal_node_count:
            raise ValueError("budget must allow rank one at every internal node")
        allocation, _ = optimal_rank_aware_dag_domain_ranks(
            nodes,
            self.topology.root_id,
            leaf_norm_bounds=leaf_bounds,
            budget=budget - 1,
        )
        return {self.topology.root_id: 1, **allocation}

    def root_error_sup(self, leaf_batch: list[np.ndarray], ranks: dict[str, int]) -> float:
        ambient = self.ambient_forward(leaf_batch)
        reduced = self.reduced_forward(leaf_batch, ranks)
        root_id = self.topology.root_id
        return float(np.max(np.linalg.norm(ambient[root_id] - reduced[root_id], axis=1)))

    def _validate_leaf_batch(self, leaf_batch: list[np.ndarray]) -> None:
        if len(leaf_batch) != len(self.topology.leaf_dims):
            raise ValueError("one batch is required for every leaf")
        batch_size = None
        for values, dim in zip(leaf_batch, self.topology.leaf_dims):
            if values.ndim != 2 or values.shape[1] != dim:
                raise ValueError("leaf batches must have shape (batch, leaf_dim)")
            if batch_size is None:
                batch_size = values.shape[0]
            elif values.shape[0] != batch_size:
                raise ValueError("all leaf batches must have the same batch size")
