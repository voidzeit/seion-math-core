"""Hierarchical tensor network core (mission AI1).

Every internal vertex performs: multilinear contraction (a random or
fitted "core tensor") -> orthogonal projection / truncation to a chosen
rank. This directly reuses the SEION finite-core math theory's structure
(mu_v = local law, P_v = local orthogonal projector) in a data-driven
setting: projectors are fit via PCA/SVD on a batch of ambient outputs at
each node, giving genuine, controllable singular-value decay (not a
synthetic placeholder), and the ambient-vs-reduced (truncated) evaluation
distinction gives an EXACTLY computable local truncation error and global
propagated error, matching AI1's "exact dense reference evaluation"/
"reduced evaluation"/"nodewise discrepancy extraction" requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from tree import NodeSpec, TreeTopology


@dataclass
class NodeCore:
    """The fixed (untrained, randomly generated) multilinear law at one
    internal vertex: a tensor of shape (ambient_dim, *child_dims)."""

    tensor: np.ndarray

    def apply(self, child_values: list[np.ndarray]) -> np.ndarray:
        """child_values[i] has shape (batch, child_dims[i]); returns
        shape (batch, ambient_dim)."""

        result = self.tensor
        # contract each child dimension against the batch of child vectors
        # result axes: [ambient_dim, child_dim_0, child_dim_1, ...]
        out = np.einsum(_einsum_expr(len(child_values)), self.tensor, *child_values)
        return out


def _einsum_expr(n_children: int) -> str:
    # tensor axes: out, c0, c1, ..., c_{n-1}
    # each child value axes: batch, c_i
    letters = "abcdefghij"
    out_letter = "Z"
    child_letters = letters[:n_children]
    batch_letter = "N"
    tensor_spec = out_letter + child_letters
    child_specs = ",".join(f"{batch_letter}{c}" for c in child_letters)
    return f"{tensor_spec},{child_specs}->{batch_letter}{out_letter}"


@dataclass
class NodeProjector:
    """Rank-r orthonormal projector fit from a batch of ambient outputs
    at this node (top-r left singular vectors -> genuine, data-driven
    singular-value decay, not a synthetic placeholder)."""

    basis: np.ndarray  # shape (ambient_dim, ambient_dim), columns = singular vectors, sorted by decreasing singular value
    singular_values: np.ndarray  # shape (ambient_dim,)

    @property
    def ambient_dim(self) -> int:
        return self.basis.shape[0]

    def project(self, values: np.ndarray, rank: int) -> np.ndarray:
        """values: shape (batch, ambient_dim). Returns the rank-`rank`
        truncated reconstruction, same shape."""

        if rank <= 0:
            return np.zeros_like(values)
        if rank >= self.ambient_dim:
            return values
        U = self.basis[:, :rank]
        return values @ U @ U.T

    def reduced_coordinates(self, values: np.ndarray, rank: int) -> np.ndarray:
        """values: shape (batch, ambient_dim). Returns shape (batch, rank)."""

        if rank <= 0:
            return np.zeros((values.shape[0], 0))
        U = self.basis[:, :rank]
        return values @ U

    def lift(self, reduced: np.ndarray, rank: int) -> np.ndarray:
        if rank <= 0:
            return np.zeros((reduced.shape[0], self.ambient_dim))
        U = self.basis[:, :rank]
        return reduced @ U.T


@dataclass
class TensorNetwork:
    topology: TreeTopology
    cores: dict[str, NodeCore]
    projectors: dict[str, NodeProjector] = field(default_factory=dict)

    @classmethod
    def random(cls, topology: TreeTopology, *, seed: int) -> "TensorNetwork":
        rng = np.random.default_rng(seed)
        cores = {}
        for node in topology.nodes_postorder:
            child_dims = [
                topology.leaf_dims[c] if isinstance(c, int) else c.ambient_dim
                for c in node.children
            ]
            shape = (node.ambient_dim, *child_dims)
            tensor = rng.standard_normal(shape) / np.sqrt(np.prod(child_dims))
            cores[node.node_id] = NodeCore(tensor=tensor)
        return cls(topology=topology, cores=cores)

    def sample_leaf_batch(self, batch_size: int, *, seed: int) -> list[np.ndarray]:
        rng = np.random.default_rng(seed)
        return [rng.standard_normal((batch_size, dim)) for dim in self.topology.leaf_dims]

    def ambient_forward(self, leaf_batch: list[np.ndarray]) -> dict[str, np.ndarray]:
        """Full, untruncated evaluation at every node. Returns {node_id:
        (batch, ambient_dim) array}, plus implicit leaf values (not
        stored, caller already has them)."""

        values: dict[str, np.ndarray] = {}

        def visit(node_or_leaf) -> np.ndarray:
            if isinstance(node_or_leaf, int):
                return leaf_batch[node_or_leaf]
            child_values = [visit(c) for c in node_or_leaf.children]
            out = self.cores[node_or_leaf.node_id].apply(child_values)
            values[node_or_leaf.node_id] = out
            return out

        visit(self.topology.root)
        return values

    def fit_projectors(self, ambient_values: dict[str, np.ndarray]) -> None:
        """PCA/SVD-fit a rank-`ambient_dim` orthonormal basis per node
        from a batch of ambient outputs (genuine, data-driven singular
        spectrum)."""

        projectors = {}
        for node in self.topology.nodes_postorder:
            batch = ambient_values[node.node_id]
            centered = batch  # no centering: this is a subspace-energy
            # decomposition, not a classical PCA - the "mean" direction is
            # itself part of the signal this network needs to reproduce.
            u, s, _ = np.linalg.svd(centered, full_matrices=False)
            # basis columns = right singular vectors of the (batch x dim)
            # matrix's *column space* -> use SVD of centered.T for that
            _, s2, vt = np.linalg.svd(centered, full_matrices=True)
            basis = vt.T  # shape (ambient_dim, ambient_dim)
            singular_values = np.zeros(node.ambient_dim)
            singular_values[: len(s2)] = s2
            projectors[node.node_id] = NodeProjector(basis=basis, singular_values=singular_values)
        self.projectors = projectors

    def reduced_forward(
        self, leaf_batch: list[np.ndarray], ranks: dict[str, int]
    ) -> dict[str, np.ndarray]:
        """Evaluation where every internal node's OUTPUT is truncated to
        rank ranks[node_id] before being used by its parent (errors
        propagate). Returns {node_id: (batch, ambient_dim) reduced-then-
        lifted-back array} plus the root's untruncated-at-itself output
        (root is not projected, matching the math theory's E_T^proj
        convention: the discrepancy of interest is in the root's OWN
        space, not a further-projected root)."""

        values: dict[str, np.ndarray] = {}

        def visit(node_or_leaf) -> np.ndarray:
            if isinstance(node_or_leaf, int):
                return leaf_batch[node_or_leaf]
            child_values = [visit(c) for c in node_or_leaf.children]
            out = self.cores[node_or_leaf.node_id].apply(child_values)
            values[node_or_leaf.node_id] = out
            if node_or_leaf.node_id == self.topology.root.node_id:
                return out  # root itself is not truncated
            rank = ranks.get(node_or_leaf.node_id, node_or_leaf.ambient_dim)
            projector = self.projectors[node_or_leaf.node_id]
            return projector.project(out, rank)

        visit(self.topology.root)
        return values

    def local_truncation_error(
        self, ambient_values: dict[str, np.ndarray], ranks: dict[str, int]
    ) -> dict[str, float]:
        """lambda_v = RMS norm of (ambient_output_v - rank-r_v projection
        of ambient_output_v), measured on the CLEAN ambient pipeline (not
        the already-degraded reduced pipeline) - isolates v's own
        truncation loss from propagated error, matching the theory's
        local closure-leakage rho_v."""

        errors = {}
        for node in self.topology.nodes_postorder:
            batch = ambient_values[node.node_id]
            rank = ranks.get(node.node_id, node.ambient_dim)
            projected = self.projectors[node.node_id].project(batch, rank)
            diff = batch - projected
            errors[node.node_id] = float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))
        return errors

    def path_amplification(
        self, ambient_values: dict[str, np.ndarray], leaf_batch: list[np.ndarray]
    ) -> dict[str, float]:
        """h_v = an empirical Lipschitz/operator-norm estimate of the
        PARENT's core tensor with respect to the v-th child slot,
        evaluated at the batch's typical operating point (finite-
        difference directional-derivative norm, averaged over the
        batch and over random perturbation directions)."""

        parent_of: dict[str, tuple[NodeSpec, int]] = {}
        for node in self.topology.nodes_postorder:
            for slot, child in enumerate(node.children):
                child_id = child if isinstance(child, int) else child.node_id
                parent_of[str(child_id)] = (node, slot)

        rng = np.random.default_rng(0)
        h = {}
        # build a lookup from node/leaf id (str) -> value batch
        all_values: dict[str, np.ndarray] = dict(ambient_values)
        for i, leaf_val in enumerate(leaf_batch):
            all_values[str(i)] = leaf_val

        def child_values_of(node: NodeSpec) -> list[np.ndarray]:
            return [
                leaf_batch[c] if isinstance(c, int) else ambient_values[c.node_id]
                for c in node.children
            ]

        for key, (parent, slot) in parent_of.items():
            core = self.cores[parent.node_id]
            children_vals = child_values_of(parent)
            base = children_vals[slot]
            eps = 1e-4
            direction = rng.standard_normal(base.shape)
            direction /= np.linalg.norm(direction, axis=1, keepdims=True) + 1e-30
            perturbed_children = list(children_vals)
            perturbed_children[slot] = base + eps * direction
            out_base = core.apply(children_vals)
            out_perturbed = core.apply(perturbed_children)
            directional_deriv = np.linalg.norm(out_perturbed - out_base, axis=1) / eps
            h[key] = float(np.mean(directional_deriv))
        return h

    def pathwise_score(
        self, local_errors: dict[str, float], amplifications: dict[str, float]
    ) -> dict[str, float]:
        """score_v = lambda_v * product of amplification factors along
        path(v, root), exactly the mission's AI1 formula."""

        scores = {}
        for node in self.topology.nodes_postorder:
            path = self.topology.path_to_root(node.node_id)
            # path = [node_id, ..., root_id]; amplification factors are
            # attached to each edge (child_id -> parent), i.e. one factor
            # per step from node up to (but not including) the root.
            product = 1.0
            for step_node_id in path[:-1]:
                product *= amplifications.get(step_node_id, 1.0)
            scores[node.node_id] = local_errors[node.node_id] * product
        return scores

    def rank_cost(self, ranks: dict[str, int]) -> int:
        """Total parameter-equivalent cost: sum of ranks (the mission's
        simplest declared budget unit)."""

        return sum(ranks.get(node.node_id, node.ambient_dim) for node in self.topology.nodes_postorder)
