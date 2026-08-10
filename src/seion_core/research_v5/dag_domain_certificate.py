"""Global bounded-domain certificates for finite multilinear DAGs.

The certificate is deliberately an enclosure calculus.  Each internal node is
given an operator-norm enclosure and a table of normal-residual enclosures,
indexed by the rank of its intermediate projection.  Shared subexpressions
are evaluated once in topological order; their error is then charged once per
edge (or input slot) in the downstream recurrence.  No tree unrolling is
needed, and no sharpness claim is implied by the supplied enclosures.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


@dataclass(frozen=True, slots=True)
class DAGDomainNode:
    """A node in a finite typed-by-bound multilinear DAG.

    ``normal_bounds[r]`` is the declared bound for the local projected normal
    residual at rank ``r``.  Index zero is reserved, so rank-one data lives at
    index one.  Leaves have no operator or projection role and use
    ``leaf_norm_bounds`` supplied to :func:`certify_dag_domain`.
    """

    node_id: str
    inputs: tuple[str, ...] = ()
    operator_bound: float = 0.0
    normal_bounds: tuple[float, ...] = ()
    projected_operator_bounds: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("DAG node ids must be nonempty")
        if self.operator_bound < 0.0 or not isfinite(float(self.operator_bound)):
            raise ValueError("operator_bound must be finite and nonnegative")
        if any(bound < 0.0 or not isfinite(float(bound)) for bound in self.normal_bounds):
            raise ValueError("normal_bounds must be finite and nonnegative")
        if any(bound < 0.0 or not isfinite(float(bound)) for bound in self.projected_operator_bounds):
            raise ValueError("projected_operator_bounds must be finite and nonnegative")
        if self.inputs and len(self.normal_bounds) < 2:
            raise ValueError("internal nodes need rank-one normal data at index 1")
        if self.inputs and self.projected_operator_bounds and len(self.projected_operator_bounds) < 2:
            raise ValueError("projected_operator_bounds need rank-one data at index 1")


@dataclass(frozen=True, slots=True)
class DAGDomainCertificate:
    """Forward and reverse data for a certified finite DAG enclosure."""

    root: str
    topological_order: tuple[str, ...]
    value_bounds: Mapping[str, float]
    error_bounds: Mapping[str, float]
    downstream_gains: Mapping[str, float]
    rank_costs: Mapping[str, tuple[float, ...]]
    root_bound: float
    project_root: bool
    complexity: str = "O(|V| + |E| + |V| d)"


@dataclass(frozen=True, slots=True)
class DAGRankAwareCertificate:
    """Certificate using rank-dependent projected values and operator bounds."""

    root: str
    topological_order: tuple[str, ...]
    exact_value_bounds: Mapping[str, float]
    approximate_value_bounds: Mapping[str, float]
    mixed_value_bounds: Mapping[str, float]
    error_bounds: Mapping[str, float]
    ranks: Mapping[str, int]
    root_bound: float
    complexity: str = "O(|V| + |E|) for a fixed rank assignment"


def _validate_graph(nodes: Mapping[str, DAGDomainNode], root: str) -> tuple[str, ...]:
    if not nodes:
        raise ValueError("DAG must contain at least one node")
    if root not in nodes:
        raise ValueError(f"unknown root {root!r}")
    indegree = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for node in nodes.values():
        for input_id in node.inputs:
            if input_id not in nodes:
                raise ValueError(f"unknown input node {input_id!r}")
            indegree[node.node_id] += 1
            outgoing[input_id].append(node.node_id)
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(nodes):
        raise ValueError("dependency graph contains a cycle")
    return tuple(order)


def _product(values: tuple[float, ...]) -> float:
    result = 1.0
    for value in values:
        result *= value
    return result


def _validate_leaf_bounds(nodes: Mapping[str, DAGDomainNode], leaf_norm_bounds: Mapping[str, float]) -> None:
    unknown = set(leaf_norm_bounds) - set(nodes)
    if unknown:
        raise ValueError(f"leaf_norm_bounds contains unknown nodes: {sorted(unknown)}")
    for node_id, node in nodes.items():
        if not node.inputs and node_id not in leaf_norm_bounds:
            raise ValueError(f"missing leaf norm bound for {node_id!r}")
    for node_id, bound in leaf_norm_bounds.items():
        if bound < 0.0 or not isfinite(float(bound)):
            raise ValueError(f"leaf norm bound for {node_id!r} must be finite and nonnegative")
        if nodes[node_id].inputs:
            raise ValueError(f"leaf norm bound supplied for internal node {node_id!r}")


def _rank_for(node_id: str, ranks: Mapping[str, int] | None) -> int:
    rank = 1 if ranks is None else ranks.get(node_id, 1)
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError(f"rank for {node_id!r} must be a positive integer")
    return rank


def certify_dag_domain(
    nodes: Mapping[str, DAGDomainNode],
    root: str,
    *,
    leaf_norm_bounds: Mapping[str, float],
    ranks: Mapping[str, int] | None = None,
    project_root: bool = False,
) -> DAGDomainCertificate:
    """Certify a finite multilinear DAG on a declared bounded leaf domain.

    For an internal node ``v`` with child value bounds ``U_i`` and error
    bounds ``D_i``, the recurrence is

    ``U_v <= M_v prod_i U_i`` and
    ``D_v <= rho_v(r) prod_i U_i +
    M_v sum_i(prod_{j != i} U_j) D_i``.

    The root is unprojected by default, matching the projected-intermediate
    setting.  Repeated input ids count as repeated slots, while a shared node
    is still represented only once in the returned maps.
    """

    order = _validate_graph(nodes, root)
    _validate_leaf_bounds(nodes, leaf_norm_bounds)
    value_bounds: dict[str, float] = {}
    error_bounds: dict[str, float] = {}

    for node_id in order:
        node = nodes[node_id]
        if not node.inputs:
            value_bounds[node_id] = float(leaf_norm_bounds[node_id])
            error_bounds[node_id] = 0.0
            continue
        child_values = tuple(value_bounds[input_id] for input_id in node.inputs)
        child_errors = tuple(error_bounds[input_id] for input_id in node.inputs)
        product_all = _product(child_values)
        value_bounds[node_id] = float(node.operator_bound) * product_all
        propagated = 0.0
        for slot, child_error in enumerate(child_errors):
            other_product = _product(child_values[:slot] + child_values[slot + 1 :])
            propagated += float(node.operator_bound) * other_product * child_error
        rank = _rank_for(node_id, ranks)
        if rank >= len(node.normal_bounds):
            raise ValueError(
                f"rank {rank} for {node_id!r} has no normal bound; "
                f"available ranks are 1..{len(node.normal_bounds) - 1}"
            )
        local = node.normal_bounds[rank] * product_all if (node_id != root or project_root) else 0.0
        error_bounds[node_id] = float(local + propagated)

    downstream_gains = {node_id: 0.0 for node_id in nodes}
    downstream_gains[root] = 1.0
    for parent in reversed(order):
        parent_gain = downstream_gains[parent]
        node = nodes[parent]
        if parent_gain == 0.0 or not node.inputs:
            continue
        child_values = tuple(value_bounds[input_id] for input_id in node.inputs)
        for slot, child_id in enumerate(node.inputs):
            other_product = _product(child_values[:slot] + child_values[slot + 1 :])
            downstream_gains[child_id] += parent_gain * float(node.operator_bound) * other_product

    rank_costs: dict[str, tuple[float, ...]] = {}
    for node_id, node in nodes.items():
        if not node.inputs or (node_id == root and not project_root) or downstream_gains[node_id] == 0.0:
            continue
        child_values = tuple(value_bounds[input_id] for input_id in node.inputs)
        local_scale = downstream_gains[node_id] * _product(child_values)
        rank_costs[node_id] = tuple(float(local_scale * bound) for bound in node.normal_bounds)

    return DAGDomainCertificate(
        root=root,
        topological_order=order,
        value_bounds=value_bounds,
        error_bounds=error_bounds,
        downstream_gains=downstream_gains,
        rank_costs=rank_costs,
        root_bound=error_bounds[root],
        project_root=project_root,
    )


def _projected_operator_bound(node: DAGDomainNode, rank: int) -> float:
    if node.projected_operator_bounds:
        if rank >= len(node.projected_operator_bounds):
            raise ValueError(
                f"rank {rank} for {node.node_id!r} has no projected operator bound; "
                f"available ranks are 1..{len(node.projected_operator_bounds) - 1}"
            )
        return float(node.projected_operator_bounds[rank])
    return float(node.operator_bound)


def certify_dag_domain_rank_aware(
    nodes: Mapping[str, DAGDomainNode],
    root: str,
    *,
    leaf_norm_bounds: Mapping[str, float],
    ranks: Mapping[str, int] | None = None,
    project_root: bool = False,
) -> DAGRankAwareCertificate:
    """Certify a fixed rank assignment with rank-dependent value enclosures.

    If ``X_v`` is the exact value and ``Y_v`` is the recursively projected
    value, the method tracks ``U_v >= ||X_v||``, ``A_v >= ||Y_v||`` and
    ``D_v >= ||X_v-Y_v||``.  The mixed factor
    ``max(U_i, A_i)`` makes the multilinear telescoping bound valid even when a
    projection reduces the child value.  Unlike :func:`certify_dag_domain`,
    this objective is generally coupled across ranks and is not assumed
    separable.
    """

    order = _validate_graph(nodes, root)
    _validate_leaf_bounds(nodes, leaf_norm_bounds)
    exact_values: dict[str, float] = {}
    approximate_values: dict[str, float] = {}
    mixed_values: dict[str, float] = {}
    error_bounds: dict[str, float] = {}

    for node_id in order:
        node = nodes[node_id]
        if not node.inputs:
            bound = float(leaf_norm_bounds[node_id])
            exact_values[node_id] = bound
            approximate_values[node_id] = bound
            mixed_values[node_id] = bound
            error_bounds[node_id] = 0.0
            continue
        exact_children = tuple(exact_values[input_id] for input_id in node.inputs)
        approximate_children = tuple(approximate_values[input_id] for input_id in node.inputs)
        mixed_children = tuple(mixed_values[input_id] for input_id in node.inputs)
        exact_product = _product(exact_children)
        approximate_product = _product(approximate_children)
        exact_values[node_id] = float(node.operator_bound) * exact_product
        rank = _rank_for(node_id, ranks)
        projected_bound = (
            float(node.operator_bound)
            if node_id == root and not project_root
            else _projected_operator_bound(node, rank)
        )
        approximate_values[node_id] = projected_bound * approximate_product
        propagated = 0.0
        child_errors = tuple(error_bounds[input_id] for input_id in node.inputs)
        for slot, child_error in enumerate(child_errors):
            other_product = _product(mixed_children[:slot] + mixed_children[slot + 1 :])
            propagated += other_product * child_error
        local = 0.0 if node_id == root and not project_root else node.normal_bounds[rank] * approximate_product
        error_bounds[node_id] = float(local + projected_bound * propagated)
        mixed_values[node_id] = max(exact_values[node_id], approximate_values[node_id])

    normalized_ranks = {
        node_id: _rank_for(node_id, ranks)
        for node_id, node in nodes.items()
        if node.inputs
    }
    return DAGRankAwareCertificate(
        root=root,
        topological_order=order,
        exact_value_bounds=exact_values,
        approximate_value_bounds=approximate_values,
        mixed_value_bounds=mixed_values,
        error_bounds=error_bounds,
        ranks=normalized_ranks,
        root_bound=error_bounds[root],
    )


def optimal_rank_aware_dag_domain_ranks(
    nodes: Mapping[str, DAGDomainNode],
    root: str,
    *,
    leaf_norm_bounds: Mapping[str, float],
    budget: int,
    project_root: bool = False,
) -> tuple[dict[str, int], float]:
    """Exhaustively optimize the rank-aware certificate for small DAGs.

    This is intentionally a small-case oracle.  The rank-aware value bounds
    couple ancestor and descendant choices, so the separable DP from
    :func:`optimal_dag_domain_ranks` is not silently reused.
    """

    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    order = _validate_graph(nodes, root)
    _validate_leaf_bounds(nodes, leaf_norm_bounds)
    projectable = tuple(
        node_id
        for node_id in order
        if nodes[node_id].inputs and (node_id != root or project_root)
    )
    if budget < len(projectable):
        raise ValueError("budget is too small to assign rank one to every projectable node")
    rank_ranges = []
    for node_id in projectable:
        node = nodes[node_id]
        maximum = len(node.normal_bounds) - 1
        if node.projected_operator_bounds:
            maximum = min(maximum, len(node.projected_operator_bounds) - 1)
        rank_ranges.append(range(1, maximum + 1))

    import itertools

    best: tuple[float, dict[str, int]] | None = None
    for values in itertools.product(*rank_ranges):
        if sum(values) > budget:
            continue
        candidate = dict(zip(projectable, values))
        certificate = certify_dag_domain_rank_aware(
            nodes,
            root,
            leaf_norm_bounds=leaf_norm_bounds,
            ranks=candidate,
            project_root=project_root,
        )
        state = (certificate.root_bound, candidate)
        if best is None or (state[0], sum(values)) < (best[0], sum(best[1].values())):
            best = state
    if best is None:
        raise ValueError("no rank-aware allocation fits budget")
    return dict(best[1]), float(best[0])


def optimal_dag_domain_ranks(
    nodes: Mapping[str, DAGDomainNode],
    root: str,
    *,
    leaf_norm_bounds: Mapping[str, float],
    budget: int,
    project_root: bool = False,
) -> tuple[dict[str, int], float]:
    """Find the exact discrete rank allocation for the supplied certificate.

    The objective is the certified root bound and the cost of a node at rank
    ``r`` is ``r``.  Since the operator/value enclosures are rank independent,
    reverse fan-out gains make the root bound separable across nodes, so a
    knapsack dynamic program is exact for this declared model.
    """

    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    base = certify_dag_domain(nodes, root, leaf_norm_bounds=leaf_norm_bounds, project_root=project_root)
    projectable = tuple(base.rank_costs)
    if budget < len(projectable):
        raise ValueError("budget is too small to assign rank one to every projectable node")
    dp: list[tuple[float, dict[str, int]] | None] = [None] * (budget + 1)
    dp[0] = (0.0, {})
    for node_id in projectable:
        next_dp: list[tuple[float, dict[str, int]] | None] = [None] * (budget + 1)
        costs = base.rank_costs[node_id]
        for spent, state in enumerate(dp):
            if state is None:
                continue
            prior_objective, prior = state
            for rank in range(1, len(costs)):
                new_spent = spent + rank
                if new_spent > budget:
                    break
                candidate = (prior_objective + costs[rank], {**prior, node_id: rank})
                current = next_dp[new_spent]
                if current is None or candidate[0] < current[0]:
                    next_dp[new_spent] = candidate
        dp = next_dp
    feasible = [(spent, state) for spent, state in enumerate(dp) if state is not None]
    if not feasible:
        raise ValueError("no rank allocation fits budget")
    spent, (objective, state) = min(feasible, key=lambda item: (item[1][0], item[0]))
    result = dict(state)
    return result, float(objective)
