"""M31 correction: the full discrete Hessian, diagonal included.

EXPLORATORY, NOT CONFIRMATORY.

The M31 pass reported the signed inertia of the off-diagonal interaction matrix
I and concluded from it that the quadratic surrogate is non-convex. That
conclusion does not follow. I has ZERO DIAGONAL by construction, so tr(I) = 0,
so its eigenvalues sum to zero, so any nonzero I is indefinite with
n_+ ~ n_- and roughly half its spectral energy negative. The reported inertia
was forced by the design, not measured from the problem.

Convexity is a property of the full discrete Hessian

    H = I + diag(H_vv),    H_vv = E(r + 2 e_v) - 2 E(r + e_v) + E(r),

whose diagonal is the second difference in a single coordinate. A strongly
positive diagonal can dominate the off-diagonal terms and make H positive
definite despite I being indefinite; a negative diagonal would compound the
problem. Only H decides.

This measures H_vv on the M31 configurations and reports the inertia of I and
of H side by side. Nodes are eligible only when r_v + 2 <= D, since the
diagonal difference needs two increments of headroom.
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
    BUDGET_FRACTIONS, EVAL_BATCH, FIT_BATCH, SEEDS,
    heterogeneous_network, topology_for,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIMENSIONS = [6, 16, 32]
FAMILIES = ("chain", "balanced")


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
        # Two increments of headroom are needed for the diagonal difference.
        eligible = [nid for nid in node_ids
                    if nid != root_id and base.get(nid, dim) + 2 <= dim]
        if len(eligible) < 6:
            continue

        e_base = root_error(base)
        singles = {nid: root_error({**base, nid: base[nid] + 1}) for nid in eligible}
        doubles = {nid: root_error({**base, nid: base[nid] + 2}) for nid in eligible}

        m = len(eligible)
        hessian = np.zeros((m, m))
        for i, nid in enumerate(eligible):
            hessian[i, i] = doubles[nid] - 2.0 * singles[nid] + e_base
        for i in range(m):
            for j in range(i + 1, m):
                u, v = eligible[i], eligible[j]
                value = (root_error({**base, u: base[u] + 1, v: base[v] + 1})
                         - singles[u] - singles[v] + e_base)
                hessian[i, j] = hessian[j, i] = value

        records.append({
            "family": family,
            "dim": dim,
            "regime": regime,
            "seed": seed,
            "budget_fraction": fraction,
            "m": m,
            "base_root_error": e_base,
            "utility": [e_base - singles[nid] for nid in eligible],
            "hessian": hessian.tolist(),
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

    out_path = RESULTS_DIR / "discrete_hessian_raw.json"
    out_path.write_text(json.dumps(all_records), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
