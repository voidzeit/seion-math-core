"""Analysis for M34, from results/interaction_decision_value_raw.json.

The central curve is C_I(m,b) = G_I / H, the fraction of the post-first-order
headroom that the pairwise term recovers.

  C_I -> 0        interaction exists but is not needed for allocation;
                  an O(m) measured-marginal allocator is the answer
  C_I ~ constant  interaction has value; whether it justifies O(m^2) is a
                  cost question
  C_I grows       coupling becomes decisionally important at scale, and cheap
                  recovery of Q becomes the priority

R_flip is the mechanism: below 1 the interaction cannot reorder the two
leading first-order candidates, so it cannot change the decision.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def summarize(rows: list[dict]) -> dict:
    headroom, gain_pair, gain_lr, captured, captured_lr = [], [], [], [], []
    for r in rows:
        h = r["E_FO"] - r["E_oracle"]
        gp = r["E_FO"] - r["E_pair"]
        gl = r["E_FO"] - r["E_LR"]
        scale = max(r["base_error"], 1e-30)
        headroom.append(h / scale)
        gain_pair.append(gp / scale)
        gain_lr.append(gl / scale)
        if h > 1e-12:
            captured.append(gp / h)
            captured_lr.append(gl / h)
    finite = [r["R_flip"] for r in rows if r["R_flip"] == r["R_flip"]]
    return {
        "n": len(rows),
        "m": statistics.fmean([r["m"] for r in rows]),
        "headroom_rel": statistics.fmean(headroom),
        "gain_pair_rel": statistics.fmean(gain_pair),
        "C_I": statistics.fmean(captured) if captured else float("nan"),
        "C_I_lowrank": statistics.fmean(captured_lr) if captured_lr else float("nan"),
        "flip_FO": statistics.fmean([float(r["flip_FO"]) for r in rows]),
        "flip_pair": statistics.fmean([float(r["flip_pair"]) for r in rows]),
        "oracle_rank_FO": statistics.fmean([r["oracle_rank_FO"] for r in rows]),
        "oracle_rank_pair": statistics.fmean([r["oracle_rank_pair"] for r in rows]),
        "R_flip_median": statistics.median(finite) if finite else float("nan"),
        "R_flip_p90": float(np.percentile(finite, 90)) if finite else float("nan"),
        "pool": statistics.fmean([r["pool_size"] for r in rows]),
        "evals_FO": statistics.fmean([r["evals_FO"] for r in rows]),
        "evals_pair": statistics.fmean([r["evals_pair"] for r in rows]),
    }


def main() -> None:
    records = json.loads((RESULTS_DIR / "interaction_decision_value_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} states.\n")

    report = {}
    for sweep in ("m_sweep", "b_sweep"):
        rows = [r for r in records if r["sweep"] == sweep]
        if not rows:
            continue
        groups = defaultdict(list)
        for r in rows:
            groups[(r["m"], r["b"])].append(r)
        print(f"=== {sweep} ===")
        print(f"{'m':>4} {'b':>3} {'pool':>6} | {'headroom':>9} {'gain_pair':>10} "
              f"{'C_I':>7} {'C_I(LR)':>8} | {'flipFO':>7} {'flipPair':>9} "
              f"{'rankFO':>7} | {'R_flip':>7} {'p90':>7} | {'evFO':>6} {'evPair':>7}")
        for key in sorted(groups):
            entry = summarize(groups[key])
            report[f"{sweep}_m{key[0]}_b{key[1]}"] = entry
            print(f"{key[0]:4d} {key[1]:3d} {entry['pool']:6.0f} | "
                  f"{entry['headroom_rel']:9.5f} {entry['gain_pair_rel']:10.5f} "
                  f"{entry['C_I']:7.3f} {entry['C_I_lowrank']:8.3f} | "
                  f"{entry['flip_FO']:7.2f} {entry['flip_pair']:9.2f} "
                  f"{entry['oracle_rank_FO']:7.1f} | "
                  f"{entry['R_flip_median']:7.3f} {entry['R_flip_p90']:7.3f} | "
                  f"{entry['evals_FO']:6.0f} {entry['evals_pair']:7.0f}")
        print()

    print("headroom/gain are relative to the base error;  C_I = gain_pair / headroom")
    print("rankFO = position of first order's pick in the oracle's true ordering (0 = optimal)")
    print("R_flip = |interaction gap| / |first-order margin| on the top two candidates")

    (RESULTS_DIR / "interaction_decision_value_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/interaction_decision_value_analysis.json")


if __name__ == "__main__":
    main()
