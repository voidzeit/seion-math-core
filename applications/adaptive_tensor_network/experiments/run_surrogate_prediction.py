"""M32: does the second-order surrogate predict held-out multi-node bundles?

EXPLORATORY, NOT CONFIRMATORY.

The discrete second-order expansion is

    E(r + D) - E(r) ~ -sum_v U_v D_v
                      + sum_v H_vv * C(D_v, 2)
                      + sum_{u<v} I_uv D_u D_v,     C(n,2) = n(n-1)/2.

At D = e_v this returns exactly -U_v, and at D = 2 e_v exactly -2 U_v + H_vv,
matching both definitions. Note C(D_v, 2) = 0 when D_v is 0 or 1: the diagonal
does not participate in one-unit-per-node bundles, so writing the diagonal as
(1/2) D^T diag(H) D would add a spurious (1/2) H_vv per selected node.

Two experiments:

M32A  binary bundles, D_v in {0,1}. The diagonal is inert here, so this
      isolates the pairwise interaction and its low-rank compression.
        L    = -U^T D
        P    = L + sum_{u<v} I_uv D_u D_v          (full pairwise)
        P_q  = L + low-rank pairwise
M32B  multi-unit bundles, D_v in {0,1,2}, every bundle containing at least one
      2 so the diagonal is active.
        L, D2 = L + sum_v H_vv C(D_v,2), F2 = D2 + full pairwise,
        F_q = D2 + low-rank pairwise

The low-rank pairwise term needs care. Truncating I to Q Lam Q^T generally
produces a nonzero diagonal even though I has none, which would silently
reintroduce a self term. It is therefore evaluated as

    (1/2) [ D^T (Q Lam Q^T) D - sum_v (Q Lam Q^T)_vv D_v^2 ],

which equals sum_{u<v} (Q Lam Q^T)_uv D_u D_v exactly and stays O(mq).

Held-out means ||D||_0 >= 3: singles and pairs were consumed to estimate U, I
and H_vv, so anything smaller is training data.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import (  # noqa: E402
    EVAL_BATCH, FIT_BATCH, SEEDS, heterogeneous_network, topology_for,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIMENSIONS = [6, 16]
FAMILIES = ("chain", "balanced")
BUDGET_FRACTIONS = (0.30, 0.50)
BUNDLE_SIZES = (3, 4, 6, 8)
BUNDLES_PER_SIZE = 40
Q_MODES = 4


def low_rank_pair_term(interaction: np.ndarray, q: int):
    """Return a callable giving sum_{u<v} (Q Lam Q^T)_uv D_u D_v."""
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    diagonal = np.diag(approx).copy()

    def term(delta: np.ndarray) -> float:
        quadratic = float(delta @ approx @ delta)
        return 0.5 * (quadratic - float(np.sum(diagonal * delta**2)))

    return term


def full_pair_term(interaction: np.ndarray):
    def term(delta: np.ndarray) -> float:
        return 0.5 * float(delta @ interaction @ delta)   # I has zero diagonal
    return term


def run_one_trial(family: str, dim: int, regime: str, seed: int) -> list[dict]:
    topology = topology_for(family, dim)
    net = (TensorNetwork.random(topology, seed=seed) if regime == "iid"
           else heterogeneous_network(topology, dim, seed=seed))

    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [node.node_id for node in topology.nodes_postorder]

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    records: list[dict] = []
    for fraction in BUDGET_FRACTIONS:
        budget = max(len(node_ids), int(round(fraction * len(node_ids) * dim)))
        base = uniform_allocation(net, budget)
        eligible = [nid for nid in node_ids
                    if nid != root_id and base.get(nid, dim) + 2 <= dim]
        if len(eligible) < max(BUNDLE_SIZES) + 1:
            continue
        m = len(eligible)
        rng = np.random.default_rng(seed * 7919 + int(fraction * 100))

        e_base = root_error(base)
        singles = {nid: root_error({**base, nid: base[nid] + 1}) for nid in eligible}
        doubles = {nid: root_error({**base, nid: base[nid] + 2}) for nid in eligible}
        utility = np.array([e_base - singles[nid] for nid in eligible])
        diagonal = np.array([doubles[nid] - 2 * singles[nid] + e_base for nid in eligible])

        interaction = np.zeros((m, m))
        for i in range(m):
            for j in range(i + 1, m):
                u, v = eligible[i], eligible[j]
                value = (root_error({**base, u: base[u] + 1, v: base[v] + 1})
                         - singles[u] - singles[v] + e_base)
                interaction[i, j] = interaction[j, i] = value

        pair_full = full_pair_term(interaction)
        pair_low = low_rank_pair_term(interaction, min(Q_MODES, m))

        def apply(delta: np.ndarray) -> dict:
            ranks = dict(base)
            for index, nid in enumerate(eligible):
                ranks[nid] = base[nid] + int(delta[index])
            truth = root_error(ranks) - e_base
            linear = -float(utility @ delta)
            binom = np.array([d * (d - 1) / 2.0 for d in delta])
            diag_term = float(diagonal @ binom)
            return {
                "true": truth,
                "L": linear,
                "P": linear + pair_full(delta),
                "Pq": linear + pair_low(delta),
                "D2": linear + diag_term,
                "F2": linear + diag_term + pair_full(delta),
                "Fq": linear + diag_term + pair_low(delta),
                "nnz": int(np.count_nonzero(delta)),
                "max_step": int(delta.max()),
            }

        for size in BUNDLE_SIZES:
            for _ in range(BUNDLES_PER_SIZE):
                chosen = rng.choice(m, size=size, replace=False)
                binary = np.zeros(m, dtype=int)
                binary[chosen] = 1
                records.append({
                    "experiment": "A_binary", "family": family, "dim": dim,
                    "regime": regime, "seed": seed, "budget_fraction": fraction,
                    "size": size, **apply(binary),
                })

                multi = binary.copy()
                # at least one node receives two units, so the diagonal is active
                multi[rng.choice(chosen, size=max(1, size // 2), replace=False)] = 2
                records.append({
                    "experiment": "B_multi", "family": family, "dim": dim,
                    "regime": regime, "seed": seed, "budget_fraction": fraction,
                    "size": size, **apply(multi),
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

    out_path = RESULTS_DIR / "surrogate_prediction_raw.json"
    out_path.write_text(json.dumps(all_records), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
