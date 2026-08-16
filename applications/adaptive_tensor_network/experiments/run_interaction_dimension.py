"""M31: is the low rank real, is the subspace stable, and what spans it?

EXPLORATORY, NOT CONFIRMATORY.

M30 showed the interaction spectrum is nearly invariant across four topology
families, but every configuration there had ambient dimension D = 6 while the
measured r_eff was 4.6-6.3 -- the same order as D. The interaction could look
low-rank simply because the whole phenomenon is mediated by a small vector
space. Three questions, one campaign:

M31A  dimension scaling. Sweep D and track r_eff/D. If r_eff grows
      proportionally to D, "rank 4" was mostly a consequence of D = 6. If it
      saturates, there is a genuine latent interaction dimension.

M31B  mode stability. "There are always four modes" and "they are the same
      four modes" are different claims; only the first was tested. Compare
      leading subspaces via the chordal overlap

          S_q(A, B) = ||Q_A^T Q_B||_F^2 / q,

      which is 1 when the subspaces coincide and q/m for random subspaces.
      Compared across budgets (same instance, different base state) and across
      seeds (different instance, same architecture).

M31C  what spans the subspace. Eigenvectors have arbitrary sign, can swap
      order, and rotate freely inside near-degenerate eigenspaces, so
      correlating them one by one is unstable. Instead measure how much of a
      node-indexed feature vector x lies in the leading subspace,

          R2_Q(x) = ||Q Q^T x||^2 / ||x||^2,

      against a random-vector baseline of q/m.

Also recorded: the SIGNED inertia of I. I is symmetric, so the quadratic form
depends on eigenvalue signs, not on singular values. A surrogate with large
negative modes is non-convex, and mixed signs would bear directly on M27's
non-monotonicity.

Raw records go to results/interaction_dimension_raw.json.
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
from network import NodeCore, TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

DIMENSIONS = [4, 6, 8, 12, 16, 24, 32]
FAMILIES = ("chain", "balanced")
SEEDS = list(range(5))
BUDGET_FRACTIONS = (0.25, 0.40, 0.55)
INTERNAL_NODES = 15
FIT_BATCH = 200
EVAL_BATCH = 200
Q_MODES = 4


def topology_for(family: str, dim: int):
    if family == "chain":
        return chain_topology(depth=INTERNAL_NODES, leaf_dim=dim, ambient_dim=dim)
    return balanced_binary_topology(16, leaf_dim=dim, ambient_dim=dim)


def heterogeneous_network(topology, dim: int, *, seed: int) -> TensorNetwork:
    """Per-node power-law spectra, norm-calibrated. Same construction as the
    depth sweep's, re-expressed for an arbitrary ambient dimension."""
    rng = np.random.default_rng(seed)
    cores: dict[str, NodeCore] = {}
    net = TensorNetwork(topology=topology, cores=cores)
    probe = net.sample_leaf_batch(120, seed=seed * 977 + 13)

    def subtree_value(item):
        if isinstance(item, int):
            return probe[item]
        return cores[item.node_id].apply([subtree_value(c) for c in item.children])

    for node in topology.nodes_postorder:
        child_dims = [
            topology.leaf_dims[c] if isinstance(c, int) else c.ambient_dim
            for c in node.children
        ]
        rows, cols = node.ambient_dim, int(np.prod(child_dims))
        alpha = float(rng.uniform(0.3, 2.0))
        spectrum = np.arange(1, min(rows, cols) + 1, dtype=float) ** (-alpha)
        left = np.linalg.qr(rng.standard_normal((rows, rows)))[0]
        right = np.linalg.qr(rng.standard_normal((cols, cols)))[0]
        unfolded = (left[:, : len(spectrum)] * spectrum) @ right[:, : len(spectrum)].T
        cores[node.node_id] = NodeCore(tensor=unfolded.reshape(rows, *child_dims))

        child_vals = [subtree_value(c) for c in node.children]
        out = cores[node.node_id].apply(child_vals)
        out_rms = float(np.sqrt(np.mean(np.sum(out**2, axis=1))))
        in_rms = float(np.mean([np.sqrt(np.mean(np.sum(v**2, axis=1))) for v in child_vals]))
        if out_rms > 1e-12:
            cores[node.node_id] = NodeCore(
                tensor=cores[node.node_id].tensor * (in_rms / out_rms)
            )
        net.cores = cores
    return net


def run_one_trial(family: str, dim: int, regime: str, seed: int) -> list[dict]:
    topology = topology_for(family, dim)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, dim, seed=seed))

    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    fit_ambient = net.ambient_forward(fit_batch)
    net.fit_projectors(fit_ambient)

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [node.node_id for node in topology.nodes_postorder]
    amplifications = net.path_amplification(fit_ambient, fit_batch)

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    records: list[dict] = []
    for fraction in BUDGET_FRACTIONS:
        budget = max(len(node_ids), int(round(fraction * len(node_ids) * dim)))
        base = uniform_allocation(net, budget)
        eligible = [
            nid for nid in node_ids
            if nid != root_id and base.get(nid, dim) < dim
        ]
        if len(eligible) < Q_MODES + 2:
            continue

        e_base = root_error(base)
        singles = {nid: root_error({**base, nid: base[nid] + 1}) for nid in eligible}
        utility = {nid: e_base - singles[nid] for nid in eligible}

        m = len(eligible)
        interaction = np.zeros((m, m))
        for i in range(m):
            for j in range(i + 1, m):
                u, v = eligible[i], eligible[j]
                value = (root_error({**base, u: base[u] + 1, v: base[v] + 1})
                         - singles[u] - singles[v] + e_base)
                interaction[i, j] = interaction[j, i] = value

        local_errors = net.local_truncation_error(fit_ambient, base)
        features = {
            "constant": [1.0] * m,
            "depth": [float(len(topology.path_to_root(nid)) - 1) for nid in eligible],
            "local_error": [float(local_errors[nid]) for nid in eligible],
            "path_weight": [
                float(np.prod([amplifications.get(s, 1.0)
                               for s in topology.path_to_root(nid)[:-1]]))
                for nid in eligible
            ],
            "rank": [float(base[nid]) for nid in eligible],
            "abs_utility": [abs(utility[nid]) for nid in eligible],
        }

        records.append({
            "family": family,
            "dim": dim,
            "regime": regime,
            "seed": seed,
            "budget_fraction": fraction,
            "eligible": eligible,
            "m": m,
            "base_root_error": e_base,
            "utility": [utility[nid] for nid in eligible],
            "interaction": interaction.tolist(),
            "features": features,
        })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    start = time.time()
    for dim in DIMENSIONS:
        for family in FAMILIES:
            for regime in ("iid", "heterogeneous"):
                for seed in SEEDS:
                    all_records.extend(run_one_trial(family, dim, regime, seed))
        print(f"D={dim}: {len(all_records)} records so far, "
              f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "interaction_dimension_raw.json"
    out_path.write_text(json.dumps(all_records), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
