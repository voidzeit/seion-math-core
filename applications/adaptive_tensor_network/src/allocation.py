"""Rank-allocation algorithms (mission AI2).

All algorithms have the same signature: given the network, a total rank
budget B, and (for methods that use it) the fitted singular spectra /
pathwise scores, return {node_id: rank} with sum(ranks) <= B and
1 <= rank <= ambient_dim for every node. No method uses test-set
information (all inputs are training/validation-batch statistics
computed once, up front).
"""

from __future__ import annotations

import itertools
from typing import Callable

import numpy as np

from network import TensorNetwork


def threshold_ranks_from_spectra(
    spectra: dict[str, np.ndarray],
    budget: int,
    *,
    minimum_ranks: dict[str, int] | None = None,
    maximum_ranks: dict[str, int] | None = None,
) -> tuple[dict[str, int], float]:
    """Choose a common tail-energy threshold under an exact rank budget.

    For each node ``i`` and common ``tau`` the selected rank is

    ``min {r >= minimum_ranks[i] : sum_{j>r} sigma[i,j]^2 <= tau}``.

    With distinct floating-point tail energies, lowering ``tau`` crosses one
    rank boundary at a time, so every integer budget between the minimum and
    maximum is attained.  Exact attainment is required deliberately: silently
    rounding a threshold allocation would confound a same-rank comparison.
    """

    if not spectra:
        raise ValueError("at least one spectrum is required")
    node_ids = sorted(spectra)
    minimum_ranks = minimum_ranks or {node_id: 1 for node_id in node_ids}
    maximum_ranks = maximum_ranks or {
        node_id: len(np.asarray(spectra[node_id])) for node_id in node_ids
    }
    if set(minimum_ranks) != set(node_ids) or set(maximum_ranks) != set(node_ids):
        raise ValueError("rank bounds must have exactly the spectrum node ids")

    tails: dict[str, dict[int, float]] = {}
    boundaries: set[float] = set()
    for node_id in node_ids:
        singular = np.asarray(spectra[node_id], dtype=float)
        minimum = int(minimum_ranks[node_id])
        maximum = int(maximum_ranks[node_id])
        if minimum < 0 or maximum < minimum or maximum > singular.size:
            raise ValueError(f"invalid rank bounds for {node_id}")
        node_tails = {
            rank: float(np.sum(singular[rank:] ** 2))
            for rank in range(minimum, maximum + 1)
        }
        tails[node_id] = node_tails
        boundaries.update(node_tails.values())

    minimum_total = sum(int(minimum_ranks[node_id]) for node_id in node_ids)
    maximum_total = sum(int(maximum_ranks[node_id]) for node_id in node_ids)
    if budget < minimum_total or budget > maximum_total:
        raise ValueError(
            f"budget {budget} is outside feasible [{minimum_total}, {maximum_total}]"
        )

    # At a tail-energy boundary, <= makes the corresponding rank feasible.
    # Search from loose to strict thresholds and require exact budget equality.
    for tau in sorted(boundaries, reverse=True):
        ranks = {}
        for node_id in node_ids:
            feasible = [
                rank for rank, tail in tails[node_id].items() if tail <= tau
            ]
            ranks[node_id] = min(feasible) if feasible else int(maximum_ranks[node_id])
        if sum(ranks.values()) == budget:
            return ranks, float(tau)

    raise RuntimeError(
        "no common threshold attains the exact budget; use an explicitly "
        "declared boundary-tie policy rather than silent rounding"
    )


def threshold_static_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    node_ids: list[str],
    minimum_ranks: dict[str, int],
) -> tuple[dict[str, int], float]:
    """One-shot common-cutoff allocation from the fitted singular spectra."""

    spectra = {
        node_id: np.asarray(net.projectors[node_id].singular_values, dtype=float)
        for node_id in node_ids
    }
    maximum = {
        node_id: int(net.projectors[node_id].ambient_dim) for node_id in node_ids
    }
    return threshold_ranks_from_spectra(
        spectra,
        budget,
        minimum_ranks=minimum_ranks,
        maximum_ranks=maximum,
    )


def threshold_adaptive_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    node_ids: list[str],
    minimum_ranks: dict[str, int],
    current_values: dict[str, np.ndarray],
) -> tuple[dict[str, int], float]:
    """Recompute fixed-basis discarded energy on the current reduced state.

    The projector bases remain frozen, preserving terminal-state sufficiency
    and the exact M8/M10 oracle.  What adapts is the energy present in each
    fitted basis direction after upstream truncations have propagated through
    the calibration pipeline.  This is the strongest path-dependent cutoff
    signal compatible with that oracle; it is not a basis-refitting method.
    """

    spectra = {}
    maximum = {}
    for node_id in node_ids:
        projector = net.projectors[node_id]
        coordinates = np.asarray(current_values[node_id]) @ projector.basis
        # The threshold rule depends only on squared values.  sqrt(sum x^2)
        # gives one energy-equivalent coefficient per frozen basis direction.
        spectra[node_id] = np.sqrt(np.sum(coordinates**2, axis=0))
        maximum[node_id] = int(projector.ambient_dim)
    return threshold_ranks_from_spectra(
        spectra,
        budget,
        minimum_ranks=minimum_ranks,
        maximum_ranks=maximum,
    )


def _node_ids(net: TensorNetwork) -> list[str]:
    return [node.node_id for node in net.topology.nodes_postorder]


def _ambient_dims(net: TensorNetwork) -> dict[str, int]:
    return {node.node_id: node.ambient_dim for node in net.topology.nodes_postorder}


def _clip_to_budget(ranks: dict[str, int], budget: int, ambient_dims: dict[str, int]) -> dict[str, int]:
    """Ensure every rank is >=1, <=ambient_dim, and the total is <= budget
    by proportionally shrinking (largest-first) if needed."""

    ranks = {k: max(1, min(v, ambient_dims[k])) for k, v in ranks.items()}
    total = sum(ranks.values())
    if total <= budget:
        return ranks
    # shrink largest ranks first until within budget
    order = sorted(ranks, key=lambda k: -ranks[k])
    idx = 0
    while total > budget:
        k = order[idx % len(order)]
        if ranks[k] > 1:
            ranks[k] -= 1
            total -= 1
        idx += 1
        if idx > 10000 * len(order):
            break
    return ranks


def uniform_allocation(net: TensorNetwork, budget: int, **_ignored) -> dict[str, int]:
    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    base = max(1, budget // len(ids))
    ranks = {node_id: base for node_id in ids}
    return _clip_to_budget(ranks, budget, ambient)


def singular_energy_allocation(net: TensorNetwork, budget: int, **_ignored) -> dict[str, int]:
    """Allocate rank at each node to retain a fixed fraction of that
    node's singular-value energy, then rescale to hit the budget."""

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    target_energy = 0.9
    ranks = {}
    for node_id in ids:
        sv = net.projectors[node_id].singular_values
        energy = sv**2
        total_energy = energy.sum()
        if total_energy <= 0:
            ranks[node_id] = 1
            continue
        cumulative = np.cumsum(energy) / total_energy
        rank = int(np.searchsorted(cumulative, target_energy) + 1)
        ranks[node_id] = min(rank, ambient[node_id])
    return _clip_to_budget(ranks, budget, ambient)


def local_error_greedy_allocation(net: TensorNetwork, budget: int, *, ambient_values, **_ignored) -> dict[str, int]:
    """Greedily increase rank, one unit at a time, at whichever node has
    the largest LOCAL truncation error per unit of additional rank
    (marginal benefit estimated via the node's own singular-value
    spectrum, not global propagated error - hence "local")."""

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    ranks = {node_id: 1 for node_id in ids}
    remaining = budget - len(ids)
    if remaining < 0:
        return _clip_to_budget(ranks, budget, ambient)

    def marginal_gain(node_id: str, current_rank: int) -> float:
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        return float(sv[current_rank] ** 2)  # energy captured by the NEXT singular direction

    for _ in range(remaining):
        candidates = [nid for nid in ids if ranks[nid] < ambient[nid]]
        if not candidates:
            break
        gains = {nid: marginal_gain(nid, ranks[nid]) for nid in candidates}
        best = max(gains, key=gains.get)
        ranks[best] += 1
    return ranks


def random_allocation(net: TensorNetwork, budget: int, *, seed: int = 0, **_ignored) -> dict[str, int]:
    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    rng = np.random.default_rng(seed)
    ranks = {node_id: 1 for node_id in ids}
    remaining = budget - len(ids)
    if remaining < 0:
        return _clip_to_budget(ranks, budget, ambient)
    for _ in range(remaining):
        candidates = [nid for nid in ids if ranks[nid] < ambient[nid]]
        if not candidates:
            break
        choice = rng.choice(candidates)
        ranks[choice] += 1
    return ranks


def gradient_based_allocation(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, **_ignored
) -> dict[str, int]:
    """Continuous relaxation: assign a soft "importance weight" per node
    from the local singular-energy AND the empirical path amplification
    (a cheap proxy for a true gradient w.r.t. a continuous rank
    parameter), then round proportionally to the budget - "gradient-
    based" in the sense of using a first-order sensitivity signal, not a
    full differentiable-rank relaxation (out of scope for this budget of
    effort; the pathwise method below is the mission's actual proposed
    algorithm and gets the full path-product treatment)."""

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    amplifications = net.path_amplification(ambient_values, leaf_batch)
    weights = {}
    for node_id in ids:
        sv = net.projectors[node_id].singular_values
        energy = float((sv**2).sum())
        weights[node_id] = energy * amplifications.get(node_id, 1.0)
    total_weight = sum(weights.values()) or 1.0
    ranks = {
        node_id: max(1, int(round(budget * weights[node_id] / total_weight)))
        for node_id in ids
    }
    return _clip_to_budget(ranks, budget, ambient)


def pathwise_global_allocation(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, **_ignored
) -> dict[str, int]:
    """The mission's proposed algorithm: greedy marginal benefit per cost,
    using the FULL pathwise score (local error x product of path
    amplification factors to the root), re-evaluated after each rank
    increment (since increasing a node's rank changes its own local
    error, hence its own score, though NOT its neighbors' local errors
    or the path amplification factors under this network's frozen-core
    convention)."""

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    amplifications = net.path_amplification(ambient_values, leaf_batch)
    ranks = {node_id: 1 for node_id in ids}
    remaining = budget - len(ids)
    if remaining < 0:
        return _clip_to_budget(ranks, budget, ambient)

    def path_product(node_id: str) -> float:
        path = net.topology.path_to_root(node_id)
        product = 1.0
        for step in path[:-1]:
            product *= amplifications.get(step, 1.0)
        return product

    path_products = {node_id: path_product(node_id) for node_id in ids}

    def marginal_benefit_per_cost(node_id: str, current_rank: int) -> float:
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        local_error_reduction = float(sv[current_rank])  # sqrt-energy reduction from adding this direction
        return local_error_reduction * path_products[node_id]  # cost of +1 rank is uniform (1 unit)

    for _ in range(remaining):
        candidates = [nid for nid in ids if ranks[nid] < ambient[nid]]
        if not candidates:
            break
        gains = {nid: marginal_benefit_per_cost(nid, ranks[nid]) for nid in candidates}
        best = max(gains, key=gains.get)
        ranks[best] += 1
    return ranks


def _path_products(net: TensorNetwork, ambient_values, leaf_batch) -> dict[str, float]:
    """Return the declared empirical path products for every internal node."""

    amplifications = net.path_amplification(ambient_values, leaf_batch)
    products = {}
    for node_id in _node_ids(net):
        path = net.topology.path_to_root(node_id)
        product = 1.0
        for step in path[:-1]:
            product *= amplifications.get(step, 1.0)
        products[node_id] = product
    return products


def pathwise_majorant_value(
    net: TensorNetwork,
    ranks: dict[str, int],
    *,
    ambient_values,
    leaf_batch,
    include_root: bool = False,
) -> float:
    """Evaluate the fitted-data pathwise majorant for a rank allocation.

    The local residual is computed exactly from the fitted singular spectrum:
    ``sqrt(sum_{j>=r} s_j^2 / batch_size)``.  The root is excluded by default
    because ``TensorNetwork.reduced_forward`` does not project the root.  The
    path factors are the same empirical factors used by ``pathwise_global``;
    this function is therefore an exact optimizer objective, not a claim that
    those empirical factors are universal operator-norm certificates.
    """

    products = _path_products(net, ambient_values, leaf_batch)
    root_id = net.topology.root.node_id
    sample_count = next(iter(ambient_values.values())).shape[0]
    total = 0.0
    for node in net.topology.nodes_postorder:
        if not include_root and node.node_id == root_id:
            continue
        rank = max(1, min(int(ranks.get(node.node_id, node.ambient_dim)), node.ambient_dim))
        singular_values = net.projectors[node.node_id].singular_values
        tail = float(np.sqrt(np.sum(singular_values[rank:] ** 2) / sample_count))
        total += products[node.node_id] * tail
    return total


def pathwise_majorant_optimal_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    ambient_values,
    leaf_batch,
    include_root: bool = False,
    **_ignored,
) -> dict[str, int]:
    """Minimize the declared pathwise majorant exactly under a rank budget.

    Once the fitted spectra and path products are fixed, the objective is a
    sum of independent node tails.  The finite dynamic program below therefore
    finds the global minimizer of that *certificate objective* in
    ``O(|V| B d_max^2)`` time, rather than relying on the singular-value
    marginal heuristic in ``pathwise_global_allocation``.  It does not use
    held-out root errors and it does not establish an allocator-optimality
    theorem for the true reconstruction error.
    """

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    root_id = net.topology.root.node_id
    decision_ids = [node_id for node_id in ids if include_root or node_id != root_id]
    fixed_ranks = {root_id: 1} if not include_root else {}
    if not decision_ids:
        return _clip_to_budget(fixed_ranks, budget, ambient)
    if budget < len(decision_ids) + len(fixed_ranks):
        return _clip_to_budget(
            {node_id: 1 for node_id in ids}, budget, ambient
        )

    products = _path_products(net, ambient_values, leaf_batch)
    sample_count = next(iter(ambient_values.values())).shape[0]
    usable_budget = min(budget - len(fixed_ranks), sum(ambient[node_id] for node_id in decision_ids))
    infinity = float("inf")
    dynamic = [infinity] * (usable_budget + 1)
    dynamic[0] = 0.0
    parents: list[list[tuple[int, int] | None]] = []

    for node_id in decision_ids:
        singular_values = net.projectors[node_id].singular_values
        max_rank = min(ambient[node_id], usable_budget)
        tails = {
            rank: products[node_id]
            * float(np.sqrt(np.sum(singular_values[rank:] ** 2) / sample_count))
            for rank in range(1, max_rank + 1)
        }
        next_dynamic = [infinity] * (usable_budget + 1)
        parent = [None] * (usable_budget + 1)
        for used, current in enumerate(dynamic):
            if not np.isfinite(current):
                continue
            for rank, cost in tails.items():
                new_used = used + rank
                if new_used > usable_budget:
                    break
                candidate = current + cost
                if candidate < next_dynamic[new_used]:
                    next_dynamic[new_used] = candidate
                    parent[new_used] = (used, rank)
        dynamic = next_dynamic
        parents.append(parent)

    final_used = min(
        (used for used, value in enumerate(dynamic) if np.isfinite(value)),
        key=lambda used: (dynamic[used], -used),
    )
    ranks = dict(fixed_ranks)
    for index in range(len(decision_ids) - 1, -1, -1):
        previous = parents[index][final_used]
        if previous is None:
            raise RuntimeError("majorant dynamic program lost a feasible parent")
        previous_used, rank = previous
        ranks[decision_ids[index]] = rank
        final_used = previous_used
    return _clip_to_budget(ranks, budget, ambient)


def small_case_oracle_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    evaluate_fn: Callable[[dict[str, int]], float],
    max_combinations: int = 2000,
    **_ignored,
) -> dict[str, int]:
    """Exhaustive (or bounded-sample, if the true combinatorial space is
    too large) search over rank allocations, evaluated with the REAL
    objective (`evaluate_fn`, e.g. true reconstruction error) - the
    ground-truth best achievable allocation at this budget, used to
    compute regret for the other 6 methods. Never uses test-set data
    (evaluate_fn must be called with validation, not test, data by the
    caller)."""

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    n = len(ids)
    # enumerate all rank vectors with 1<=r_i<=ambient_i and sum<=budget,
    # bounded by max_combinations (small trees / small ambient dims only)
    ranges = [range(1, ambient[node_id] + 1) for node_id in ids]
    best_ranks = None
    best_value = float("inf")
    count = 0
    for combo in itertools.product(*ranges):
        if sum(combo) > budget:
            continue
        count += 1
        if count > max_combinations:
            break
        candidate = dict(zip(ids, combo))
        value = evaluate_fn(candidate)
        if value < best_value:
            best_value = value
            best_ranks = candidate
    if best_ranks is None:
        # budget too tight for any valid combination within the cap;
        # fall back to uniform (still budget-feasible by construction)
        return uniform_allocation(net, budget)
    return best_ranks


def small_case_validated_certificate_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    leaf_batch,
    max_combinations: int = 2000,
    **_ignored,
) -> dict[str, int]:
    """Minimize the finite-batch validated root bound for small networks.

    This is deliberately an optional small-case policy: it evaluates the
    sound sup-norm certificate from ``TensorNetwork.validated_error_certificate``
    for each candidate allocation, so its cost is combinatorial.  It uses only
    the supplied fitting/validation batch and must not be compared to held-out
    performance as if it were a preregistered allocator.
    """

    return small_case_oracle_allocation(
        net,
        budget,
        evaluate_fn=lambda ranks: float(
            net.validated_error_certificate(leaf_batch, ranks)["root_bound"]
        ),
        max_combinations=max_combinations,
    )


def global_certificate_optimal_allocation(
    net: TensorNetwork,
    budget: int,
    *,
    leaf_norm_bounds,
    **_ignored,
) -> dict[str, int]:
    """Globally minimize the bounded-domain certificate by dynamic programming.

    The operator-norm recurrence exposes a fixed downstream gain and a local
    rank cost at every non-root node.  The resulting separable integer problem
    is solved exactly in ``O(|V| B d_max^2)`` worst-case time, without
    held-out data or exhaustive rank-vector enumeration.
    """

    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    root_id = net.topology.root.node_id
    decision_ids = [node_id for node_id in ids if node_id != root_id]
    fixed = {root_id: 1}
    if budget < len(decision_ids) + 1:
        return _clip_to_budget({node_id: 1 for node_id in ids}, budget, ambient)
    components = net.global_error_certificate(leaf_norm_bounds)
    rank_costs = components["rank_costs"]
    usable_budget = min(budget - 1, sum(ambient[node_id] for node_id in decision_ids))
    infinity = float("inf")
    dynamic = [infinity] * (usable_budget + 1)
    dynamic[0] = 0.0
    parents: list[list[tuple[int, int] | None]] = []
    for node_id in decision_ids:
        costs = rank_costs[node_id]
        next_dynamic = [infinity] * (usable_budget + 1)
        parent = [None] * (usable_budget + 1)
        for used, current in enumerate(dynamic):
            if not np.isfinite(current):
                continue
            for rank in range(1, min(ambient[node_id], usable_budget - used) + 1):
                candidate = current + costs[rank]
                new_used = used + rank
                if candidate < next_dynamic[new_used]:
                    next_dynamic[new_used] = candidate
                    parent[new_used] = (used, rank)
        dynamic = next_dynamic
        parents.append(parent)
    final_used = min(
        (used for used, value in enumerate(dynamic) if np.isfinite(value)),
        key=lambda used: (dynamic[used], -used),
    )
    ranks = dict(fixed)
    for index in range(len(decision_ids) - 1, -1, -1):
        previous = parents[index][final_used]
        if previous is None:
            raise RuntimeError("global certificate dynamic program lost a feasible parent")
        final_used, rank = previous
        ranks[decision_ids[index]] = rank
    return _clip_to_budget(ranks, budget, ambient)


def _greedy_by_score(
    net: TensorNetwork,
    budget: int,
    *,
    marginal_benefit_per_cost: Callable[[str, int], float],
) -> dict[str, int]:
    ids = _node_ids(net)
    ambient = _ambient_dims(net)
    ranks = {node_id: 1 for node_id in ids}
    remaining = budget - len(ids)
    if remaining < 0:
        return _clip_to_budget(ranks, budget, ambient)
    for _ in range(remaining):
        candidates = [nid for nid in ids if ranks[nid] < ambient[nid]]
        if not candidates:
            break
        gains = {nid: marginal_benefit_per_cost(nid, ranks[nid]) for nid in candidates}
        best = max(gains, key=gains.get)
        ranks[best] += 1
    return ranks


def ablation_local_source_only(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, **_ignored
) -> dict[str, int]:
    """AI6 ablation: local truncation error only, path amplification set
    to 1 everywhere (ignores how errors propagate to the root)."""

    ids = _node_ids(net)

    def gain(node_id: str, current_rank: int) -> float:
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        return float(sv[current_rank])

    return _greedy_by_score(net, budget, marginal_benefit_per_cost=gain)


def ablation_path_amplification_only(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, **_ignored
) -> dict[str, int]:
    """AI6 ablation: path amplification only, local error set to a
    constant 1 everywhere (allocates purely by tree position/depth,
    ignoring how much each node's own truncation actually loses)."""

    ids = _node_ids(net)
    amplifications = net.path_amplification(ambient_values, leaf_batch)

    def path_product(node_id: str) -> float:
        path = net.topology.path_to_root(node_id)
        product = 1.0
        for step in path[:-1]:
            product *= amplifications.get(step, 1.0)
        return product

    path_products = {node_id: path_product(node_id) for node_id in ids}

    def gain(node_id: str, current_rank: int) -> float:
        ambient_dim = net.topology.leaf_dims[0] if False else None  # unused, kept for signature symmetry
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        return path_products[node_id]  # constant per node regardless of current rank -> depth-only ordering

    return _greedy_by_score(net, budget, marginal_benefit_per_cost=gain)


def ablation_universal_coarse_k_minus_1(net: TensorNetwork, budget: int, **_ignored) -> dict[str, int]:
    """AI6 ablation: the proved-but-coarse universal (k-1) bound, applied
    naively as "every node contributes equally, scaled only by (k-1)
    where k = distance from root" - i.e. allocate uniformly regardless
    of any data-dependent signal, matching what using ONLY the universal
    worst-case constant (ignoring all local structure) would prescribe."""

    return uniform_allocation(net, budget)


def ablation_root_residual_negative_control(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, **_ignored
) -> dict[str, int]:
    """AI6 deliberately-incorrect negative control: includes the root's
    own truncation "residual" in its score as if the root itself were
    truncated (it is not, by this network's convention - the root is
    never projected), inflating the apparent importance of nodes closest
    to the root for a reason that should not apply. Expected to
    underperform pathwise_global at equal budget."""

    ids = _node_ids(net)
    amplifications = net.path_amplification(ambient_values, leaf_batch)
    root_id = net.topology.root.node_id

    def path_product_including_root_residual(node_id: str) -> float:
        path = net.topology.path_to_root(node_id)
        product = 1.0
        for step in path[:-1]:
            product *= amplifications.get(step, 1.0)
        # Incorrect extra factor: double-count the LAST hop's amplification
        # again, as if the root itself also leaked a residual through that
        # same edge (it does not - the root is never truncated by this
        # network's convention). This factor is genuinely node-dependent
        # (it uses the specific last edge on each node's own path, which
        # differs by branch), unlike a single tree-wide constant, so it can
        # actually perturb the greedy ranking rather than being a no-op.
        last_edge = path[-2] if len(path) >= 2 else node_id
        spurious_root_factor = 1.0 + amplifications.get(last_edge, 1.0)
        return product * spurious_root_factor

    path_products = {node_id: path_product_including_root_residual(node_id) for node_id in ids}

    def gain(node_id: str, current_rank: int) -> float:
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        return float(sv[current_rank]) * path_products[node_id]

    return _greedy_by_score(net, budget, marginal_benefit_per_cost=gain)


def ablation_random_path_coefficients(
    net: TensorNetwork, budget: int, *, ambient_values, leaf_batch, seed: int = 0, **_ignored
) -> dict[str, int]:
    """AI6 ablation: replace the real, measured path-amplification
    factors with independent random positive coefficients (destroys the
    causal signal while keeping the same greedy-allocation machinery, to
    check the REAL amplification factors are doing real work, not just
    "any weighting improves on uniform")."""

    ids = _node_ids(net)
    rng = np.random.default_rng(seed)
    random_path_products = {node_id: float(rng.uniform(0.1, 2.0)) for node_id in ids}

    def gain(node_id: str, current_rank: int) -> float:
        sv = net.projectors[node_id].singular_values
        if current_rank >= len(sv):
            return 0.0
        return float(sv[current_rank]) * random_path_products[node_id]

    return _greedy_by_score(net, budget, marginal_benefit_per_cost=gain)


ALLOCATION_METHODS: dict[str, Callable] = {
    "uniform": uniform_allocation,
    "singular_energy": singular_energy_allocation,
    "local_error_greedy": local_error_greedy_allocation,
    "random": random_allocation,
    "gradient_based": gradient_based_allocation,
    "pathwise_global": pathwise_global_allocation,
    # "oracle" intentionally excluded from this dict: it needs an
    # evaluate_fn and is only tractable for small trees, so it is invoked
    # explicitly by the experiment driver, not iterated over generically.
}

ABLATION_METHODS: dict[str, Callable] = {
    "local_source_only": ablation_local_source_only,
    "path_amplification_only": ablation_path_amplification_only,
    "universal_coarse_k_minus_1": ablation_universal_coarse_k_minus_1,
    "root_residual_negative_control": ablation_root_residual_negative_control,
    "random_path_coefficients": ablation_random_path_coefficients,
}
