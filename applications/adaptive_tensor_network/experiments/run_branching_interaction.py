"""M30: does the M29 interaction geometry survive branching?

EXPLORATORY, NOT CONFIRMATORY.

M29 measured the pairwise interaction matrix I on chains only. In a chain every
pair is ancestor/descendant and shares its ENTIRE transport path to the root,
so two candidate explanations of |I_uv| are perfectly confounded: topological
distance, and how much downstream the two nodes share. M29's "not local"
reading is therefore only established along chains.

This runs the identical measurement on four topology families holding the
internal-node count fixed at 15, so the spectra are directly comparable:

    chain           15 internal nodes, no branching at all
    balanced        balanced binary over 16 leaves
    asymmetric      root joining a depth-11 chain and a depth-3 chain
    random          random binary tree, 15 internal nodes

The critical gate is whether the low-rank structure survives. If R4 stays
around 0.9 on balanced and random trees, M29's finding is a property of the
problem; if it collapses once genuinely independent branches exist, the low
rank was an artifact of chains.

Each pair is classified and given four geometric coordinates, so distance and
shared downstream can be separated:

    relation           ancestor_descendant | different_branch
    d_T(u,v)           edge distance through the LCA
    d(u,LCA), d(v,LCA) the disjoint portions of the two transport paths
    shared_downstream  edges from the LCA to the root, i.e. the common part

Also measured, as the mechanism behind M27's negative marginals: a
single-source decomposition. c_v is the root error vector when ONLY node v is
truncated. Since c_u for u != v does not depend on r_v, bumping r_v splits the
change in squared error exactly into

    delta_self  = ||c_v'||^2 - ||c_v||^2
    delta_cross = 2 * sum_{u != v} ( <c_u, c_v'> - <c_u, c_v> )

and a negative marginal should show delta_self < 0 with
delta_cross > |delta_self| -- improving a node's own contribution while
destroying a cancellation. The linearity residual of the decomposition is
recorded rather than assumed.

Raw records go to results/branching_interaction_raw.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import NodeSpec, TreeTopology, balanced_binary_topology, chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_depth_sweep import (  # noqa: E402
    AMBIENT_DIM, EVAL_BATCH_SIZE, FIT_BATCH_SIZE, LEAF_DIM, SEEDS,
    budget_grid, heterogeneous_network,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
INTERNAL_NODES = 15


class _Leaves:
    def __init__(self) -> None:
        self.count = 0

    def next(self) -> int:
        value = self.count
        self.count += 1
        return value


def _chain_subtree(depth: int, leaves: _Leaves, prefix: str) -> NodeSpec:
    current: NodeSpec | int | None = None
    for i in range(depth):
        left = current if current is not None else leaves.next()
        node = NodeSpec(f"{prefix}{i}", (left, leaves.next()), AMBIENT_DIM)
        current = node
    return current


def asymmetric_topology() -> TreeTopology:
    """Root joining a long chain and a short one: branching, badly unbalanced."""
    leaves = _Leaves()
    long_arm = _chain_subtree(11, leaves, "L")
    short_arm = _chain_subtree(3, leaves, "S")
    root = NodeSpec("root", (long_arm, short_arm), AMBIENT_DIM)
    return TreeTopology(root=root, leaf_dims=tuple(LEAF_DIM for _ in range(leaves.count)))


def random_tree_topology(seed: int) -> TreeTopology:
    """Random binary tree, built by repeatedly splitting a random leaf slot."""
    rng = np.random.default_rng(10_000 + seed)
    root = NodeSpec("r0", (0, 1), AMBIENT_DIM)
    for index in range(1, INTERNAL_NODES):
        slots = []

        def collect(node: NodeSpec, path: tuple) -> None:
            for position, child in enumerate(node.children):
                if isinstance(child, int):
                    slots.append(path + (position,))
                else:
                    collect(child, path + (position,))

        collect(root, ())
        chosen = slots[int(rng.integers(len(slots)))]

        def rebuild(node: NodeSpec, path: tuple, depth: int) -> NodeSpec:
            children = list(node.children)
            position = path[depth]
            if depth == len(path) - 1:
                children[position] = NodeSpec(f"r{index}", (0, 0), AMBIENT_DIM)
            else:
                children[position] = rebuild(children[position], path, depth + 1)
            return NodeSpec(node.node_id, tuple(children), node.ambient_dim)

        root = rebuild(root, chosen, 0)

    # Renumber every leaf slot consecutively.
    leaves = _Leaves()

    def renumber(node: NodeSpec) -> NodeSpec:
        children = tuple(
            renumber(child) if isinstance(child, NodeSpec) else leaves.next()
            for child in node.children
        )
        return NodeSpec(node.node_id, children, node.ambient_dim)

    root = renumber(root)
    return TreeTopology(root=root, leaf_dims=tuple(LEAF_DIM for _ in range(leaves.count)))


def topology_for(family: str, seed: int) -> TreeTopology:
    if family == "chain":
        return chain_topology(depth=INTERNAL_NODES, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    if family == "balanced":
        return balanced_binary_topology(16, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    if family == "asymmetric":
        return asymmetric_topology()
    if family == "random":
        return random_tree_topology(seed)
    raise ValueError(family)


def pair_geometry(topology: TreeTopology, u: str, v: str) -> dict:
    path_u = topology.path_to_root(u)
    path_v = topology.path_to_root(v)
    index_v = {node_id: i for i, node_id in enumerate(path_v)}
    for i, node_id in enumerate(path_u):
        if node_id in index_v:
            lca, du, dv = node_id, i, index_v[node_id]
            break
    else:
        raise ValueError("no common ancestor")
    if lca == u or lca == v:
        relation = "ancestor_descendant"
    else:
        relation = "different_branch"
    return {
        "relation": relation,
        "distance": du + dv,
        "d_u_lca": du,
        "d_v_lca": dv,
        "shared_downstream": len(topology.path_to_root(lca)) - 1,
    }


def run_one_trial(family: str, regime: str, seed: int) -> list[dict]:
    topology = topology_for(family, seed)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, seed=seed))

    fit_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [node.node_id for node in topology.nodes_postorder]
    full = {nid: AMBIENT_DIM for nid in node_ids}

    def residual(ranks: dict[str, int]) -> np.ndarray:
        return root_ambient - net.reduced_forward(eval_batch, ranks)[root_id]

    def rms(vectors: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.sum(vectors**2, axis=1))))

    records: list[dict] = []
    for budget in budget_grid(topology.internal_node_count):
        base = uniform_allocation(net, budget)
        eligible = [
            nid for nid in node_ids
            if nid != root_id and base.get(nid, AMBIENT_DIM) < AMBIENT_DIM
        ]
        if len(eligible) < 3:
            continue

        total = residual(base)
        e_base = rms(total)
        singles = {nid: rms(residual({**base, nid: base[nid] + 1})) for nid in eligible}
        utility = {nid: e_base - singles[nid] for nid in eligible}

        m = len(eligible)
        interaction = np.zeros((m, m))
        geometry = []
        for i in range(m):
            for j in range(i + 1, m):
                u, v = eligible[i], eligible[j]
                both = {**base, u: base[u] + 1, v: base[v] + 1}
                value = rms(residual(both)) - singles[u] - singles[v] + e_base
                interaction[i, j] = interaction[j, i] = value
                geometry.append({"i": i, "j": j, "value": value, **pair_geometry(topology, u, v)})

        # Single-source decomposition: c_v is the root residual when only v is
        # truncated. c_u does not depend on r_v, so bumping r_v changes the
        # cross terms only through c_v.
        contributions = {nid: residual({**full, nid: base[nid]}) for nid in eligible}
        bumped_contributions = {
            nid: residual({**full, nid: base[nid] + 1}) for nid in eligible
        }
        stacked = np.stack([contributions[nid] for nid in eligible])
        linearity_residual = rms(stacked.sum(axis=0) - total) / max(e_base, 1e-30)

        mechanism = []
        for index, nid in enumerate(eligible):
            c_old, c_new = contributions[nid], bumped_contributions[nid]
            others = stacked.sum(axis=0) - c_old
            delta_self = float(np.mean(np.sum(c_new**2, axis=1) - np.sum(c_old**2, axis=1)))
            delta_cross = 2.0 * float(np.mean(np.sum(others * (c_new - c_old), axis=1)))
            mechanism.append({
                "node": nid,
                "utility": utility[nid],
                "delta_self": delta_self,
                "delta_cross": delta_cross,
            })

        records.append({
            "family": family,
            "regime": regime,
            "seed": seed,
            "budget": budget,
            "eligible": eligible,
            "base_root_error": e_base,
            "utility": utility,
            "interaction": interaction.tolist(),
            "pair_geometry": geometry,
            "linearity_residual": linearity_residual,
            "mechanism": mechanism,
        })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    start = time.time()
    for family in ("chain", "balanced", "asymmetric", "random"):
        for regime in ("iid", "heterogeneous"):
            for seed in SEEDS:
                all_records.extend(run_one_trial(family, regime, seed))
            print(f"{family}/{regime}: {len(all_records)} records so far, "
                  f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "branching_interaction_raw.json"
    out_path.write_text(json.dumps(all_records), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
