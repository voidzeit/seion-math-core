"""M37 Phase B: does WHERE the spectral scales sit matter, or only WHICH exist?

EXPERIMENTAL.

Gate 2 requires that placement variants share the exact same alpha multiset.
Each variant below is a permutation of one drawn multiset, so any difference in
the interaction spectrum is attributable to topological placement alone and not
to the values present.

Placements, on a chain where node index 0 is deepest and index m-1 feeds the
root:

    random          a fixed random permutation
    high_at_root    sorted ascending, so the largest alphas sit nearest the root
    low_at_root     sorted descending
    alternating     high/low interleaved by depth
    clustered       sorted, i.e. contiguous blocks of similar alpha
    dispersed       maximally interleaved (deck-shuffle of the sorted multiset)

If placement moves the spectrum materially, the mechanism is
topology x heterogeneity rather than heterogeneity alone.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_heterogeneity_mechanism_m37 import (  # noqa: E402
    INTERNAL_NODES, build_network, git_state, measure,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def placements(alphas: np.ndarray, rng) -> dict[str, np.ndarray]:
    ordered = np.sort(alphas)
    m = len(ordered)
    half = m // 2
    low, high = ordered[:half], ordered[half:]

    alternating = np.empty(m)
    alternating[0::2] = high[: len(alternating[0::2])]
    alternating[1::2] = low[: len(alternating[1::2])]

    dispersed = np.empty(m)
    dispersed[: len(high)] = high
    dispersed[len(high):] = low
    dispersed = dispersed.reshape(-1)[np.argsort(np.arange(m) % 2, kind="stable")]

    # Contiguous blocks of similar alpha, but with the BLOCK ORDER shuffled.
    # Sorting alone would coincide exactly with `high_at_root` on a chain, which
    # is what an earlier version did -- the two conditions were byte-identical
    # and therefore not a test of clustering at all.
    n_blocks = 3
    blocks = np.array_split(ordered, n_blocks)
    clustered = np.concatenate([blocks[i] for i in rng.permutation(n_blocks)])

    return {
        "random": rng.permutation(alphas),
        "high_at_root": ordered,               # index m-1 feeds the root
        "low_at_root": ordered[::-1],
        "alternating": alternating,
        "clustered": clustered,
        "dispersed": dispersed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dims", type=int, nargs="+", default=[16])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--multiset", type=str, default="baseline",
                        choices=["baseline", "bimodal"])
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "m37_placement_raw.json"
    payload = {
        "config": {
            "internal_nodes": INTERNAL_NODES, "dims": args.dims,
            "seeds": args.seeds, "multiset": args.multiset,
            "command": " ".join(sys.argv), "git": git_state(),
            "platform": platform.platform(), "numpy": np.__version__,
            "note": "every placement is a permutation of ONE drawn multiset",
        },
        "runs": [],
    }

    start = time.time()
    for dim in args.dims:
        topology = chain_topology(depth=INTERNAL_NODES, leaf_dim=dim, ambient_dim=dim)
        for seed in args.seeds:
            rng = np.random.default_rng(700000 + seed)
            if args.multiset == "baseline":
                multiset = rng.uniform(0.3, 2.0, size=INTERNAL_NODES)
            else:
                multiset = np.where(rng.random(INTERNAL_NODES) < 0.5, 0.3, 2.0)
            for name, alphas in placements(multiset, rng).items():
                net = build_network(topology, dim, alphas, structure_seed=seed)
                record = measure(topology, net, dim, seed)
                if not record:
                    continue
                record.update({
                    "placement": name, "dim": dim, "seed": seed,
                    "multiset": args.multiset,
                    "alpha_sorted": sorted(float(a) for a in alphas),
                    "alpha_mean": float(np.mean(alphas)),
                    "alpha_std": float(np.std(alphas)),
                })
                payload["runs"].append(record)
            out_path.write_text(json.dumps(payload), encoding="utf-8")
            print(f"D={dim} seed={seed}: {len(payload['runs'])} runs, "
                  f"elapsed={time.time() - start:.0f}s", flush=True)

    print(f"\nWrote {len(payload['runs'])} runs to {out_path}")


if __name__ == "__main__":
    main()
