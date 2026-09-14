"""Restricted-gain (M24) and Gram-aware (M25) finite-batch certificates.

Both are drop-in alternatives to `TensorNetwork.validated_error_certificate`
(certificate A) and are compared against it on identical inputs. All three
certify the same quantity: an upper bound on

    max_n || ambient_root(n) - reduced_root(n) ||

over the supplied finite leaf batch and rank assignment. None is a claim
about unbounded inputs.

The three differ ONLY in how they compose per-node information into a root
bound; what is measured locally is held fixed, so a tightness difference is
attributable to the composition rule.

Certificate A (existing, `network.validated_error_certificate`)
    value bound  U_v = ||K_v||_F * prod(U_children), propagated recursively
    slot gain    ||K_v||_F * prod_{j!=i} U_j
    combination  D_v <= C_v + sum_i gain_i * D_i        (triangle inequality)

Certificate B (M24, `restricted_gain_certificate`)
    slot gain    max_n || K_v(.., x_j!=i(n), ..) ||_op  -- the exact operator
                 norm of the slot-i linear map at each sample's own
                 operating point, maximized over the batch, instead of a
                 Frobenius surrogate times propagated value bounds.
    combination  unchanged (triangle inequality)

    A's value bounds compound multiplicatively and are the dominant source
    of looseness: with ||K_v||_F ~ 2.45 and a leaf norm bound ~4.5, A's U_v
    grows like 11^k while the measured values stay O(1). B never forms a
    propagated value bound at all.

Certificate C (M25, `gram_aware_certificate`)
    Everything in B, plus: at each projected node the total error splits as
    a propagated part `a` and a closure residual `b = raw - P_v raw`, with
    b in Ran(I-P_v) by construction. Instead of ||a+b|| <= ||a|| + ||b||,
    use

        ||a+b||^2 = ||a||^2 + ||b||^2 + 2<a,b>,
        <a,b> <= ||Proj_{Ran(I-P_v)} a|| * ||b||,

    and bound the projected part by its OWN restricted gain
    max_n ||(I-P_v) K_v(.., x_j!=i(n), ..)||_op, which is generally much
    smaller than the unrestricted gain. When the propagated error is mostly
    tangential to Ran(P_v) this approaches Pythagorean addition rather than
    linear accumulation -- the same mechanism as Lemma 12.1 (D_1 perp R_1)
    in the k=3 theory, applied at every level.

Soundness is not assumed: every returned dict carries `bound_holds`, and
the campaign asserts it across all records. A tighter bound that is ever
violated is wrong, not an improvement.
"""

from __future__ import annotations

import numpy as np

from network import TensorNetwork
from tree import NodeSpec

_LETTERS = "abcdefghij"


def _slot_maps(core: np.ndarray, child_values: list[np.ndarray], slot: int) -> np.ndarray:
    """Per-sample matrix of the linear map `delta -> K(.., delta, ..)`.

    Returns shape (batch, ambient_dim, child_dims[slot]): for each sample,
    the core contracted against every child value except `slot`.
    """
    arity = len(child_values)
    child_letters = _LETTERS[:arity]
    others = [j for j in range(arity) if j != slot]
    operands = [core]
    specs = ["Z" + child_letters]
    for j in others:
        specs.append("N" + child_letters[j])
        operands.append(child_values[j])
    expression = ",".join(specs) + f"->NZ{child_letters[slot]}"
    return np.einsum(expression, *operands)


def _operator_norms(maps: np.ndarray, post: np.ndarray | None = None) -> np.ndarray:
    """Per-sample operator norm of the slot map, optionally post-composed.

    Returns one norm per sample rather than a batch maximum. Bounds are
    propagated per sample and reduced with a single max at the root, so the
    certificate never pairs the worst sample's gain with a different
    sample's error -- a decoupling that costs a constant factor at every
    level and therefore compounds with depth.

    `post` is applied on the output side (used for I - P_v, which yields the
    gain into the normal space only).
    """
    if maps.size == 0:
        return np.zeros(maps.shape[0])
    matrices = maps if post is None else np.einsum("ZY,NYa->NZa", post, maps)
    singular = np.linalg.svd(matrices, compute_uv=False)
    return singular[:, 0] if singular.shape[-1] else np.zeros(maps.shape[0])


def _row_norms(values: np.ndarray) -> np.ndarray:
    return np.linalg.norm(values, axis=1)


def _pipelines(net: TensorNetwork, leaf_batch, ranks):
    """Ambient values, raw reduced outputs, and the value each parent is fed."""
    ambient = net.ambient_forward(leaf_batch)
    raw = net.reduced_forward(leaf_batch, ranks)
    root_id = net.topology.root.node_id
    used: dict[str, np.ndarray] = {}
    for node in net.topology.nodes_postorder:
        if node.node_id == root_id:
            used[node.node_id] = raw[node.node_id]
        else:
            rank = ranks.get(node.node_id, node.ambient_dim)
            used[node.node_id] = net.projectors[node.node_id].project(raw[node.node_id], rank)
    return ambient, raw, used


def _child_arrays(node: NodeSpec, leaf_batch, ambient, used):
    """Telescoping needs, per slot i, the `used` values for j<i and the
    exact `ambient` values for j>i, matching

        K(x_1..x_m) - K(y_1..y_m) = sum_i K(y_1..y_{i-1}, x_i-y_i, x_{i+1}..x_m).
    """
    exact, fed = [], []
    for child in node.children:
        if isinstance(child, int):
            exact.append(leaf_batch[child])
            fed.append(leaf_batch[child])          # leaves are never truncated
        else:
            exact.append(ambient[child.node_id])
            fed.append(used[child.node_id])
    return exact, fed


def _certificate(net: TensorNetwork, leaf_batch, ranks, *, gram_aware: bool) -> dict:
    ambient, raw, used = _pipelines(net, leaf_batch, ranks)
    root_id = net.topology.root.node_id

    batch_size = leaf_batch[0].shape[0]
    error_bounds: dict[str, np.ndarray] = {
        str(index): np.zeros(batch_size) for index in range(len(leaf_batch))
    }
    diagnostics: dict[str, dict] = {}

    for node in net.topology.nodes_postorder:
        core = net.cores[node.node_id].tensor
        exact, fed = _child_arrays(node, leaf_batch, ambient, used)

        normal = None
        if node.node_id != root_id:
            rank = max(0, min(int(ranks.get(node.node_id, node.ambient_dim)), node.ambient_dim))
            basis = net.projectors[node.node_id].basis[:, :rank]
            normal = np.eye(node.ambient_dim) - basis @ basis.T

        propagated = np.zeros(batch_size)
        propagated_normal = np.zeros(batch_size)
        for slot, child in enumerate(node.children):
            if isinstance(child, int):
                continue                            # leaves carry no error
            child_bound = error_bounds[child.node_id]
            if not np.any(child_bound > 0.0):
                continue
            slot_inputs = [fed[j] if j < slot else exact[j] for j in range(len(node.children))]
            maps = _slot_maps(core, slot_inputs, slot)
            propagated += _operator_norms(maps) * child_bound
            if normal is not None:
                propagated_normal += _operator_norms(maps, post=normal) * child_bound

        if node.node_id == root_id:
            closure = np.zeros(batch_size)
            bound = propagated
        else:
            closure = _row_norms(raw[node.node_id] - used[node.node_id])
            if gram_aware:
                # ||a + b||^2 with b in Ran(I-P_v): the cross term only sees
                # the normal component of the propagated error.
                cross = np.minimum(propagated_normal, propagated)
                bound = np.sqrt(propagated**2 + closure**2 + 2.0 * cross * closure)
            else:
                bound = propagated + closure

        error_bounds[node.node_id] = bound
        diagnostics[node.node_id] = {
            "closure": float(np.max(closure)),
            "propagated": float(np.max(propagated)),
            "propagated_normal": float(np.max(propagated_normal)),
            "bound": float(np.max(bound)),
        }

    actual = float(np.max(_row_norms(ambient[root_id] - raw[root_id])))
    root_bound = float(np.max(error_bounds[root_id]))
    return {
        "root_bound": root_bound,
        "root_actual_sup": actual,
        "bound_holds": bool(actual <= root_bound + 1.0e-9),
        "tightness": float(actual / root_bound) if root_bound > 0 else float("nan"),
        "error_bounds": {key: float(np.max(value)) for key, value in error_bounds.items()},
        "diagnostics": diagnostics,
    }


def restricted_gain_certificate(net: TensorNetwork, leaf_batch, ranks) -> dict:
    """Certificate B (M24): exact per-sample slot operator norms."""
    return _certificate(net, leaf_batch, ranks, gram_aware=False)


def gram_aware_certificate(net: TensorNetwork, leaf_batch, ranks) -> dict:
    """Certificate C (M25): B plus normal/tangential angle accounting."""
    return _certificate(net, leaf_batch, ranks, gram_aware=True)
