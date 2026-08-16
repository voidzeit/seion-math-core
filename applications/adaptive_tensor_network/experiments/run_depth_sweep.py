"""Depth sweep: is there a usable window where pathwise allocation wins?

EXPLORATORY, NOT CONFIRMATORY. This design was written after Level 1's
results were known, so it carries the same epistemic label the Level 2/3
campaigns carry in CAMPAIGN_FINDINGS.md. It tests a hypothesis that
LEVEL1_FINDINGS.md itself raised but did not attempt ("deeper trees than
the depth-3/3-node topologies tested here, where propagation effects
compound more").

Level 1 tested only k=3: both `chain_depth3` and `balanced_binary_4leaf`
have exactly 3 internal nodes. A probe run before this sweep measured the
coefficient of variation of the pure path-transport weights w_v at
CV=0.077 for k=3 -- i.e. the weights were nearly constant, so
`pathwise_global` and `local_error_greedy` were scoring nodes almost
identically and the comparison had little signal to detect. That same
probe found CV rising to 0.589 by k=24.

Three curves are recorded, per the design agreed for this sweep:

  A(k) = E[local_error_greedy] - E[pathwise_global]   (paired, per config)
         > 0 means pathwise wins.
  T(k) = root_actual / root_certificate_bound          (certificate tightness)
  H(k) = CV(w) and N_eff(w) over the path-transport weights

A(k) and T(k) are independent questions: an allocator only needs the
relative ORDER of node scores, so it can win while the absolute
certificate is loose.

Two core regimes are run:

  `iid`           - reproduces Level 1's generator exactly
                    (TensorNetwork.random: i.i.d. Gaussian at every node).
                    Note that under this generator every node is
                    statistically identical, so `uniform` is optimal by
                    symmetry and heterogeneity in w_v can only come from
                    topology (differing path lengths).
  `heterogeneous` - each node gets its own power-law singular spectrum
                    (exponent drawn per node), so nodes genuinely differ
                    in how much rank they need. This is the condition
                    under which rank allocation is a real problem at all.

Raw, unaggregated records go to results/depth_sweep_raw.json. All
statistics are computed afterward by analyze_depth_sweep.py, never inline
here, so the raw record stays independently re-analyzable.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import ABLATION_METHODS, ALLOCATION_METHODS  # noqa: E402
from geometric_certificate import gram_aware_certificate, restricted_gain_certificate  # noqa: E402
from network import NodeCore, TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

DEPTHS = [3, 6, 10, 16, 24]
SEEDS = list(range(10))
LEAF_DIM = 6
AMBIENT_DIM = 6
FIT_BATCH_SIZE = 300
EVAL_BATCH_SIZE = 300
CALIBRATION_BATCH = 200

# Methods compared. The oracle is omitted: it is exhaustive over rank
# combinations and is not tractable at depth 24.
METHODS = dict(ALLOCATION_METHODS)
METHODS.update({
    f"ablation_{name}": fn
    for name, fn in ABLATION_METHODS.items()
    if name in ("local_source_only", "random_path_coefficients")
})


def heterogeneous_network(topology, *, seed: int) -> TensorNetwork:
    """Cores with a per-node power-law singular spectrum, norm-calibrated.

    Each node's core, unfolded to (ambient_dim, prod(child_dims)), is given
    singular values j**(-alpha_v) with alpha_v drawn per node in [0.3, 2.0].
    A small alpha means a flat spectrum (needs high rank); a large alpha
    means fast decay (a low rank suffices). That spread is what makes
    non-uniform allocation a well-posed problem -- Level 1's i.i.d.
    generator gives every node the same expected spectrum.

    After construction each core is rescaled so that its RMS output norm on
    a calibration batch matches its RMS input norm, keeping the forward
    pass numerically stable as depth grows (the role layer normalization
    plays in a trained network). Without this the value scale drifts by
    orders of magnitude across the depth range and the sweep would be
    measuring scale drift rather than geometry.
    """

    rng = np.random.default_rng(seed)
    cores: dict[str, NodeCore] = {}
    net = TensorNetwork(topology=topology, cores=cores)
    probe = net.sample_leaf_batch(CALIBRATION_BATCH, seed=seed * 977 + 13)

    def subtree_value(node_or_leaf):
        """Forward pass over one subtree only.

        The whole-network ambient_forward cannot be used here: cores are
        built in postorder, so the ancestors of the node being calibrated do
        not exist yet.
        """
        if isinstance(node_or_leaf, int):
            return probe[node_or_leaf]
        child_values = [subtree_value(c) for c in node_or_leaf.children]
        return cores[node_or_leaf.node_id].apply(child_values)

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

        # Calibrate this node's scale over its own subtree, which is fully
        # built at this point in the postorder.
        child_vals = [subtree_value(c) for c in node.children]
        out = cores[node.node_id].apply(child_vals)
        out_rms = float(np.sqrt(np.mean(np.sum(out**2, axis=1))))
        in_rms = float(np.mean([
            np.sqrt(np.mean(np.sum(v**2, axis=1))) for v in child_vals
        ]))
        if out_rms > 1e-12:
            cores[node.node_id] = NodeCore(
                tensor=cores[node.node_id].tensor * (in_rms / out_rms)
            )
        net.cores = cores

    return net


def transport_weights(net: TensorNetwork, amplifications: dict[str, float]) -> dict[str, float]:
    """w_v = product of amplification factors along path(v, root).

    This is the PURE transport factor of the pathwise score -- the local
    truncation error is deliberately excluded, so its dispersion measures
    how much the path structure alone discriminates between nodes.
    """

    weights = {}
    for node in net.topology.nodes_postorder:
        path = net.topology.path_to_root(node.node_id)
        product = 1.0
        for step_node_id in path[:-1]:
            product *= amplifications.get(step_node_id, 1.0)
        weights[node.node_id] = product
    return weights


def weight_dispersion(weights: dict[str, float]) -> dict[str, float]:
    values = np.asarray([v for v in weights.values()], dtype=float)
    values = values[np.isfinite(values) & (values > 0)]
    if values.size < 2:
        return {"cv": float("nan"), "n_eff": float("nan"), "n_nodes": int(values.size)}
    return {
        "cv": float(values.std() / values.mean()),
        "n_eff": float(values.sum() ** 2 / np.sum(values**2)),
        "n_nodes": int(values.size),
    }


def budget_grid(n_nodes: int) -> list[int]:
    lo = n_nodes                    # rank 1 everywhere
    hi = n_nodes * AMBIENT_DIM      # full rank everywhere
    return sorted(set(int(round(x)) for x in np.linspace(lo, hi, 6)))


def run_one_trial(depth: int, regime: str, seed: int) -> list[dict]:
    topology = chain_topology(depth=depth, leaf_dim=LEAF_DIM, ambient_dim=AMBIENT_DIM)
    if regime == "iid":
        net = TensorNetwork.random(topology, seed=seed)
    elif regime == "heterogeneous":
        net = heterogeneous_network(topology, seed=seed)
    else:
        raise ValueError(f"unknown regime {regime!r}")

    fit_leaf_batch = net.sample_leaf_batch(FIT_BATCH_SIZE, seed=seed * 1000 + 1)
    eval_leaf_batch = net.sample_leaf_batch(EVAL_BATCH_SIZE, seed=seed * 1000 + 2)

    fit_ambient_values = net.ambient_forward(fit_leaf_batch)
    net.fit_projectors(fit_ambient_values)

    eval_ambient_values = net.ambient_forward(eval_leaf_batch)
    root_id = net.topology.root.node_id
    root_ambient = eval_ambient_values[root_id]
    root_scale = float(np.sqrt(np.mean(np.sum(root_ambient**2, axis=1))))

    amplifications = net.path_amplification(fit_ambient_values, fit_leaf_batch)
    weights = transport_weights(net, amplifications)
    dispersion = weight_dispersion(weights)

    records: list[dict] = []
    for budget in budget_grid(net.topology.internal_node_count):
        for method_name, method_fn in METHODS.items():
            ranks = method_fn(
                net, budget,
                ambient_values=fit_ambient_values,
                leaf_batch=fit_leaf_batch,
                seed=seed,
            )
            reduced = net.reduced_forward(eval_leaf_batch, ranks)
            diff = root_ambient - reduced[root_id]
            true_error = float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

            local_errors = net.local_truncation_error(fit_ambient_values, ranks)
            majorant = float(sum(net.pathwise_score(local_errors, amplifications).values()))

            # Three composition rules on identical inputs: A = the existing
            # scalar/Frobenius certificate, B = M24 restricted gains, C = M25
            # Gram-aware. Only the composition differs, so any tightness
            # difference is attributable to it.
            certificate = net.validated_error_certificate(eval_leaf_batch, ranks)
            cert_b = restricted_gain_certificate(net, eval_leaf_batch, ranks)
            cert_c = gram_aware_certificate(net, eval_leaf_batch, ranks)
            bound = float(certificate["root_bound"])
            actual_sup = float(certificate["root_actual_sup"])

            records.append({
                "depth": depth,
                "regime": regime,
                "seed": seed,
                "budget": budget,
                "method": method_name,
                "ranks": ranks,
                "rank_cost": int(sum(ranks.values())),
                "true_root_error": true_error,
                # normalized so errors are comparable across depths, whose
                # root value scales differ
                "relative_root_error": true_error / root_scale if root_scale > 0 else float("nan"),
                "root_scale": root_scale,
                "predicted_majorant": majorant,
                "certificate_bound": bound,
                "certificate_actual_sup": actual_sup,
                "certificate_tightness": actual_sup / bound if bound > 0 and np.isfinite(bound) else float("nan"),
                "certificate_holds": bool(certificate["bound_holds"]),
                "cert_b_bound": float(cert_b["root_bound"]),
                "cert_b_tightness": float(cert_b["tightness"]),
                "cert_b_holds": bool(cert_b["bound_holds"]),
                "cert_c_bound": float(cert_c["root_bound"]),
                "cert_c_tightness": float(cert_c["tightness"]),
                "cert_c_holds": bool(cert_c["bound_holds"]),
                "w_cv": dispersion["cv"],
                "w_n_eff": dispersion["n_eff"],
                "n_nodes": dispersion["n_nodes"],
            })
    return records


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    start = time.time()
    for regime in ("iid", "heterogeneous"):
        for depth in DEPTHS:
            for seed in SEEDS:
                all_records.extend(run_one_trial(depth, regime, seed))
            print(f"{regime} k={depth}: {len(all_records)} records so far, "
                  f"elapsed={time.time() - start:.1f}s", flush=True)

    out_path = RESULTS_DIR / "depth_sweep_raw.json"
    out_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} raw records to {out_path}")
    print(f"Total wall time: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
