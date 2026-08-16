"""M34: when does coupling become DECISIONALLY important, not just predictive?

EXPLORATORY, NOT CONFIRMATORY.

M32 showed the pairwise term greatly improves prediction of E(r+D) across the
whole bundle distribution (R^2 0.767 -> 0.970). M33 showed that at m = 14 it
barely improves the argmin: measured first order captured essentially all of
the achievable gain, and the pairwise correction recovered only ~24% of the
0.8% headroom remaining above it, at 7x the acquisition cost.

Those are compatible: a model can be far more accurate across a range while
selecting the same optimum, because near the top the leading candidates are
close and first order already orders them. The question this pass answers is
whether that is structural or an artifact of m = 14.

Measured at a single base state (not a trajectory, which would confound the
comparison with divergent histories), over a shared candidate pool so every
method searches the same set:

    H(m,b)   = E_FO - E_oracle          headroom left after measured first order
    G_I(m,b) = E_FO - E_pair            what the pairwise term recovers
    C_I(m,b) = G_I / H                  fraction of the headroom captured

plus the decision-level statistics M33 could not distinguish:

    flip     P(argmin_FO != argmin_oracle)
    rank_FO  where first order's pick sits in the oracle's true ordering
    R_flip   |I(D_1) - I(D_2)| / (L_2 - L_1) for the top two bundles by first
             order -- below 1 the interaction cannot reorder the leaders,
             at or above 1 it can. This is the mechanism behind M33's result.

Two sweeps: m at fixed b = 3 (isolating the number of available decisions),
and b at fixed m (a bundle of size b contains C(b,2) interacting pairs, so the
value of I may depend more on b than on m).

Only the heterogeneous regime is run. M33 established that the i.i.d. operating
point is inert -- 18 units of rank move the error by ~5e-6 relative -- so it
cannot discriminate allocation policies and is not a meaningful control here.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import (  # noqa: E402
    EVAL_BATCH, FIT_BATCH, heterogeneous_network,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
SEEDS = [0, 1, 2]
BUDGET_FRACTIONS = (0.30, 0.45)
POOL = 1500
Q_MODES = 4

M_SWEEP = [(8, 3), (14, 3), (23, 3), (31, 3)]
B_SWEEP = [(23, 2), (23, 5), (23, 8)]


def low_rank_matrix(interaction: np.ndarray, q: int) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    np.fill_diagonal(approx, 0.0)
    return approx


def candidate_pool(m: int, b: int, rng) -> list[tuple[int, ...]]:
    total = 1
    for i in range(b):
        total = total * (m - i) // (i + 1)
    if total <= POOL:
        return list(itertools.combinations(range(m), b))
    seen = set()
    while len(seen) < POOL:
        seen.add(tuple(sorted(rng.choice(m, size=b, replace=False).tolist())))
    return sorted(seen)


def run_one_state(m_target: int, b: int, seed: int, fraction: float) -> dict | None:
    topology = chain_topology(depth=m_target + 1, leaf_dim=DIM, ambient_dim=DIM)
    net = heterogeneous_network(topology, DIM, seed=seed)
    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))

    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [n.node_id for n in topology.nodes_postorder]

    def root_error(ranks: dict[str, int]) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    budget = max(len(node_ids), int(round(fraction * len(node_ids) * DIM)))
    base = uniform_allocation(net, budget)
    eligible = [nid for nid in node_ids if nid != root_id and base.get(nid, DIM) < DIM]
    if len(eligible) < b + 2:
        return None
    m = len(eligible)

    e_base = root_error(base)
    singles = {nid: root_error({**base, nid: base[nid] + 1}) for nid in eligible}
    utility = np.array([e_base - singles[nid] for nid in eligible])

    interaction = np.zeros((m, m))
    for i in range(m):
        for j in range(i + 1, m):
            u, v = eligible[i], eligible[j]
            value = (root_error({**base, u: base[u] + 1, v: base[v] + 1})
                     - singles[u] - singles[v] + e_base)
            interaction[i, j] = interaction[j, i] = value
    low_rank = low_rank_matrix(interaction, min(Q_MODES, m))

    rng = np.random.default_rng(seed * 7919 + int(fraction * 1000) + b)
    pool = candidate_pool(m, b, rng)

    def delta_of(combo):
        delta = np.zeros(m)
        delta[list(combo)] = 1.0
        return delta

    linear, pair, lowr, truth = [], [], [], []
    for combo in pool:
        delta = delta_of(combo)
        base_linear = -float(utility @ delta)
        linear.append(base_linear)
        pair.append(base_linear + 0.5 * float(delta @ interaction @ delta))
        lowr.append(base_linear + 0.5 * float(delta @ low_rank @ delta))
        candidate = dict(base)
        for index in combo:
            candidate[eligible[index]] += 1
        truth.append(root_error(candidate))

    linear = np.array(linear)
    pair = np.array(pair)
    lowr = np.array(lowr)
    truth = np.array(truth)

    pick_fo, pick_pair = int(np.argmin(linear)), int(np.argmin(pair))
    pick_lr, pick_oracle = int(np.argmin(lowr)), int(np.argmin(truth))
    order = np.argsort(truth)
    oracle_rank = {int(index): position for position, index in enumerate(order)}

    # R_flip on the top two bundles by first order
    top_two = np.argsort(linear)[:2]
    gamma = float(linear[top_two[1]] - linear[top_two[0]])
    interaction_gap = abs(
        0.5 * float(delta_of(pool[top_two[0]]) @ interaction @ delta_of(pool[top_two[0]]))
        - 0.5 * float(delta_of(pool[top_two[1]]) @ interaction @ delta_of(pool[top_two[1]]))
    )

    return {
        "m": m, "b": b, "seed": seed, "budget_fraction": fraction,
        "pool_size": len(pool), "base_error": e_base,
        "E_FO": float(truth[pick_fo]), "E_pair": float(truth[pick_pair]),
        "E_LR": float(truth[pick_lr]), "E_oracle": float(truth[pick_oracle]),
        "flip_FO": bool(pick_fo != pick_oracle),
        "flip_pair": bool(pick_pair != pick_oracle),
        "oracle_rank_FO": oracle_rank[pick_fo],
        "oracle_rank_pair": oracle_rank[pick_pair],
        "gamma_FO": gamma,
        "interaction_gap": interaction_gap,
        "R_flip": interaction_gap / gamma if gamma > 0 else float("nan"),
        "evals_FO": m + 1,
        "evals_pair": m + 1 + m * (m - 1) // 2,
        "evals_oracle": len(pool),
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    start = time.time()
    for sweep_name, configs in (("m_sweep", M_SWEEP), ("b_sweep", B_SWEEP)):
        for m_target, b in configs:
            for seed in SEEDS:
                for fraction in BUDGET_FRACTIONS:
                    result = run_one_state(m_target, b, seed, fraction)
                    if result:
                        result["sweep"] = sweep_name
                        records.append(result)
            print(f"{sweep_name} m~{m_target} b={b}: {len(records)} records, "
                  f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "interaction_decision_value_raw.json"
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
