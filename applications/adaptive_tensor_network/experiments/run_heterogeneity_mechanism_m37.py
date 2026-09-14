"""M37: attempt to falsify the heterogeneity mechanism for low-rank interaction.

EXPERIMENTAL. This is a falsification campaign, not a confirmation campaign.

M31 observed r_eff(I) ~ 3.8-4.8 and R_4 ~ 0.95-0.98 in ONE structured
synthetic family (alpha_v ~ U[0.3, 2.0]), while the iid regime showed r_eff
growing with D and eigenspaces were not stable across instances. The only
supportable statement is that a particular regime showed spectral
concentration. M37 tests whether spectral heterogeneity is the cause.

CONTROL. The generator draws the random orthogonal factors from an RNG stream
that is INDEPENDENT of the alpha values, so two cells with the same seed differ
only in the imposed spectra. Without this, changing the alpha distribution
would also shift every subsequent random draw and no cell would be comparable
to another. This is Gate 1 and Gate 2.

r_eff DEFINITION. M31's code computes the participation ratio

    r_eff = (sum_i |lambda_i|)^2 / sum_i lambda_i^2

The M37 brief specifies an entropy form exp(-sum p_i log p_i). These are
different statistics. The frozen M31 definition is used for the Gate 0
reproduction and reported as `r_eff_participation`; the entropy form is
reported alongside as `r_eff_entropy`. Neither is silently substituted.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from network import NodeCore, TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
INTERNAL_NODES = 15
START_FRACTION = 0.40
FIT_BATCH = 200
EVAL_BATCH = 200
CALIBRATION_BATCH = 120
HELD_OUT_BUNDLES = 120
BUNDLE_SIZES = (3, 4, 6)


def git_state() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True,
            cwd=str(Path(__file__).resolve().parents[3]),
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def build_network(topology, dim: int, alphas, *, structure_seed: int) -> TensorNetwork:
    """Per-node power-law spectra with EXPLICIT alphas.

    `structure_seed` drives the orthogonal factors only. Alphas are supplied by
    the caller, so two configurations sharing a structure_seed have identical
    random bases and differ solely in the imposed spectra.
    """
    rng = np.random.default_rng(structure_seed)
    cores: dict[str, NodeCore] = {}
    net = TensorNetwork(topology=topology, cores=cores)
    probe = net.sample_leaf_batch(CALIBRATION_BATCH, seed=structure_seed * 977 + 13)

    def subtree_value(item):
        if isinstance(item, int):
            return probe[item]
        return cores[item.node_id].apply([subtree_value(c) for c in item.children])

    for node, alpha in zip(topology.nodes_postorder, alphas):
        child_dims = [topology.leaf_dims[c] if isinstance(c, int) else c.ambient_dim
                      for c in node.children]
        rows, cols = node.ambient_dim, int(np.prod(child_dims))
        spectrum = np.arange(1, min(rows, cols) + 1, dtype=float) ** (-float(alpha))
        k = len(spectrum)
        # Thin QR: only the first k columns are ever used, and the first k
        # columns of a Haar orthogonal matrix have the same distribution as a
        # thin QR factor of a (cols, k) Gaussian. At D = 32 this replaces a
        # 1024x1024 factorization per node with a 1024x32 one.
        left = np.linalg.qr(rng.standard_normal((rows, k)))[0]
        right = np.linalg.qr(rng.standard_normal((cols, k)))[0]
        unfolded = (left * spectrum) @ right.T
        cores[node.node_id] = NodeCore(tensor=unfolded.reshape(rows, *child_dims))

        child_vals = [subtree_value(c) for c in node.children]
        out = cores[node.node_id].apply(child_vals)
        out_rms = float(np.sqrt(np.mean(np.sum(out**2, axis=1))))
        in_rms = float(np.mean([np.sqrt(np.mean(np.sum(v**2, axis=1))) for v in child_vals]))
        if out_rms > 1e-12:
            cores[node.node_id] = NodeCore(
                tensor=cores[node.node_id].tensor * (in_rms / out_rms))
        net.cores = cores
    return net


def alpha_families(m: int, alpha_seed: int) -> dict[str, np.ndarray]:
    """All alpha vectors, drawn from a stream independent of the structure."""
    rng = np.random.default_rng(alpha_seed)
    families: dict[str, np.ndarray] = {}

    for a0 in (0.5, 1.0, 1.5):
        families[f"A0_degenerate_a{a0}"] = np.full(m, a0)

    for a0 in (0.5, 1.0, 1.5):
        for eps in (0.05, 0.15, 0.30):
            values = rng.uniform(a0 - eps, a0 + eps, size=m)
            families[f"A1_narrow_a{a0}_e{eps}"] = np.clip(values, 0.05, 3.0)

    for (low, high) in ((0.5, 1.5), (0.3, 2.0)):
        for p in (0.25, 0.5, 0.75):
            mask = rng.random(m) < p
            families[f"A2_bimodal_{low}_{high}_p{p}"] = np.where(mask, high, low)

    families["A3_baseline_U0.3_2.0"] = rng.uniform(0.3, 2.0, size=m)
    families["A4_wide_U0.2_2.5"] = rng.uniform(0.2, 2.5, size=m)
    families["A4_loguniform"] = np.exp(rng.uniform(np.log(0.2), np.log(2.5), size=m))
    return families


def spectral_metrics(interaction: np.ndarray) -> dict:
    eigenvalues = np.linalg.eigvalsh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues = eigenvalues[order]
    energy = float(np.sum(eigenvalues**2))
    m = len(eigenvalues)
    if energy <= 0:
        return {}
    weights = eigenvalues**2 / energy
    positive = weights[weights > 0]
    out = {
        # M31's frozen definition
        "r_eff_participation": float(np.sum(np.abs(eigenvalues)) ** 2 / energy),
        # the entropy form named in the M37 brief; a different statistic
        "r_eff_entropy": float(np.exp(-np.sum(positive * np.log(positive)))),
        "stable_rank": float(energy / eigenvalues[0] ** 2),
        "negative_energy_fraction": float(
            np.sum(eigenvalues[eigenvalues < 0] ** 2) / energy),
        "spectrum": [float(v) for v in eigenvalues],
    }
    cumulative = np.cumsum(weights)
    for q in (1, 2, 4, 8):
        out[f"R{q}"] = float(cumulative[min(q, m) - 1])
    for eps in (0.01, 0.05, 0.10):
        out[f"rank_eps{eps}"] = int(np.searchsorted(cumulative, 1.0 - eps) + 1)
    return out


def low_rank_matrix(interaction: np.ndarray, q: int) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues, eigenvectors = eigenvalues[order][:q], eigenvectors[:, order][:, :q]
    approx = (eigenvectors * eigenvalues) @ eigenvectors.T
    np.fill_diagonal(approx, 0.0)
    return approx


def leading_basis(interaction: np.ndarray, q: int) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(interaction)
    order = np.argsort(-np.abs(eigenvalues))
    return eigenvectors[:, order][:, :q]


def measure(topology, net, dim: int, seed: int) -> dict:
    fit_batch = net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    eval_batch = net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
    net.fit_projectors(net.ambient_forward(fit_batch))
    root_id = topology.root.node_id
    root_ambient = net.ambient_forward(eval_batch)[root_id]
    node_ids = [n.node_id for n in topology.nodes_postorder]

    def error(ranks) -> float:
        reduced = net.reduced_forward(eval_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    budget = max(len(node_ids), int(round(START_FRACTION * len(node_ids) * dim)))
    base = uniform_allocation(net, budget)
    eligible = [n for n in node_ids if n != root_id and base.get(n, dim) < dim]
    if len(eligible) < 9:
        return {}
    m = len(eligible)

    e_base = error(base)
    singles = {n: error({**base, n: base[n] + 1}) for n in eligible}
    utility = np.array([e_base - singles[n] for n in eligible])
    interaction = np.zeros((m, m))
    for i in range(m):
        for j in range(i + 1, m):
            u, v = eligible[i], eligible[j]
            value = (error({**base, u: base[u] + 1, v: base[v] + 1})
                     - singles[u] - singles[v] + e_base)
            interaction[i, j] = interaction[j, i] = value

    result = {"m": m, "base_error": e_base}
    result.update(spectral_metrics(interaction))
    norm_u = float(np.linalg.norm(utility))
    result["interaction_over_first_order"] = (
        float(np.linalg.norm(interaction) / norm_u) if norm_u > 0 else float("nan"))
    result["leading_basis"] = leading_basis(interaction, min(4, m)).tolist()

    # Gate 3: operational value on held-out bundles (||Delta||_0 >= 3, so the
    # singles and pairs that built U and I are not scored against themselves).
    rng = np.random.default_rng(seed * 31337 + 7)
    surrogates = {"first_order": None, "full": interaction}
    for q in (1, 2, 4, 8):
        if q < m:
            surrogates[f"lowrank_q{q}"] = low_rank_matrix(interaction, q)
    truth, predictions = [], {name: [] for name in surrogates}
    for _ in range(HELD_OUT_BUNDLES):
        size = int(rng.choice(BUNDLE_SIZES))
        combo = rng.choice(m, size=size, replace=False)
        delta = np.zeros(m)
        delta[combo] = 1.0
        candidate = dict(base)
        for index in combo:
            candidate[eligible[index]] += 1
        truth.append(error(candidate) - e_base)
        linear = -float(utility @ delta)
        for name, matrix in surrogates.items():
            predictions[name].append(
                linear if matrix is None
                else linear + 0.5 * float(delta @ matrix @ delta))

    truth = np.array(truth)
    spread = float(truth.max() - truth.min())
    best = int(np.argmin(truth))
    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    operational = {}
    for name, values in predictions.items():
        values = np.array(values)
        picked = int(np.argmin(values))
        ranking = np.argsort(values)
        operational[name] = {
            "r2": 1.0 - float(np.sum((truth - values) ** 2)) / ss_tot if ss_tot > 0 else float("nan"),
            "spearman": float(np.corrcoef(
                np.argsort(np.argsort(values)),
                np.argsort(np.argsort(truth)))[0, 1]),
            "decision_regret": (truth[picked] - truth[best]) / spread if spread > 0 else 0.0,
            "top3_overlap": len(set(ranking[:3]) & set(np.argsort(truth)[:3])) / 3.0,
        }
    result["operational"] = operational
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[8, 16, 32])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--out", type=str, default="m37_raw.json")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / args.out
    payload = {
        "config": {
            "internal_nodes": INTERNAL_NODES, "start_fraction": START_FRACTION,
            "fit_batch": FIT_BATCH, "eval_batch": EVAL_BATCH,
            "held_out_bundles": HELD_OUT_BUNDLES, "bundle_sizes": list(BUNDLE_SIZES),
            "dims": args.dims, "seeds": args.seeds, "dtype": "float64",
            "topology": "chain", "command": " ".join(sys.argv),
            "git": git_state(), "platform": platform.platform(),
            "python": sys.version.split()[0], "numpy": np.__version__,
            "r_eff_note": "r_eff_participation is M31's frozen definition; "
                          "r_eff_entropy is the M37 brief's formula",
        },
        "runs": [],
    }

    start = time.time()
    for dim in args.dims:
        topology = chain_topology(depth=INTERNAL_NODES, leaf_dim=dim, ambient_dim=dim)
        for seed in args.seeds:
            families = alpha_families(INTERNAL_NODES, alpha_seed=500000 + seed)
            for name, alphas in families.items():
                net = build_network(topology, dim, alphas, structure_seed=seed)
                record = measure(topology, net, dim, seed)
                if not record:
                    continue
                record.update({
                    "family": name, "dim": dim, "seed": seed,
                    "alpha_mean": float(np.mean(alphas)),
                    "alpha_std": float(np.std(alphas)),
                    "alpha_min": float(np.min(alphas)),
                    "alpha_max": float(np.max(alphas)),
                    "n_distinct_alpha": int(len(np.unique(np.round(alphas, 6)))),
                })
                payload["runs"].append(record)
            out_path.write_text(json.dumps(payload), encoding="utf-8")
            print(f"D={dim} seed={seed}: {len(payload['runs'])} runs, "
                  f"elapsed={time.time() - start:.0f}s", flush=True)

    print(f"\nWrote {len(payload['runs'])} runs to {out_path}")


if __name__ == "__main__":
    main()
