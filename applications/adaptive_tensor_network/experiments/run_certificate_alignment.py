"""M36: does a tighter certified bound carry usable allocation information?

EXPERIMENTAL. Nothing here is a theorem.

The certificates are proved upper bounds (M24/M25): E <= G <= B <= min(Bbar, A).
They claim nothing about argmin. This asks whether they nonetheless RANK
actions usefully, which is a different task from bounding.

The bet is asymmetric. A negative result does not weaken M24/M25 at all -- it
would only say that certification and decision ranking are distinct problems. A
positive result would turn an output of the certification theory into an input
of the allocation algorithm, which is the missing link between the two lines.

From a state r and the full 56-bundle candidate set, for each action a:

    dE(a) = E(r+a) - E(r)          true immediate change
    dA(a) = A(r+a) - A(r)          scalar/Frobenius certificate  (loosest)
    dB(a) = B(r+a) - B(r)          M24 restricted-gain
    dG(a) = G(r+a) - G(r)          M25 Gram-aware               (tightest)

Negative means improvement throughout. Monotonicity of the bounds in rank is
NOT assumed: raising a rank lowers the local residual but also changes the
effective slot maps M_{v,j}(r), so dB may take either sign. Whether the
sample-wise certificate inherits any of E's non-monotonicity is itself a
question here, not an assumption.

Four levels are measured, in increasing order of what an allocator needs:
  A. numeric prediction   R^2
  B. ranking              Spearman, Kendall
  C. decision             top-1 agreement, top-K overlap
  D. decision regret      dE(argmin dB) - min dE

Plus sign agreement, which asks directly whether a certificate can detect that
more rank may make the true objective worse.

At m = 8 the full terminal landscape is known, so each action is also scored by

    V(r+a) = min over terminal profiles still reachable from r+a

which tests a possibility M35c raises: a conservative bound might be
accidentally better aligned with terminal value than the one-step objective E
itself.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import uniform_allocation  # noqa: E402
from geometric_certificate import gram_aware_certificate, restricted_gain_certificate  # noqa: E402
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import EVAL_BATCH, FIT_BATCH, heterogeneous_network  # noqa: E402
from run_terminal_oracle_m8 import ChainEvaluator, count_profiles  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
M = 8
BUNDLE = 3
ROUNDS = 6


def enumerate_profiles(m: int, rounds: int, bundle: int) -> np.ndarray:
    """Terminal increment profiles in the SAME depth-first order the oracle used."""
    total = rounds * bundle
    out = []

    def walk(index, used, prefix):
        if index == m:
            if used == total:
                out.append(tuple(prefix))
            return
        remaining_slots = m - index - 1
        for increment in range(rounds + 1):
            if used + increment > total:
                break
            if used + increment + remaining_slots * rounds < total:
                continue
            prefix.append(increment)
            walk(index + 1, used + increment, prefix)
            prefix.pop()

    walk(0, 0, [])
    return np.asarray(out, dtype=np.int16)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--steps", type=int, nargs="+", default=[0, 2, 4])
    args = parser.parse_args()

    profiles = enumerate_profiles(M, ROUNDS, BUNDLE)
    expected = count_profiles(M, ROUNDS, BUNDLE)
    if len(profiles) != expected:
        raise RuntimeError(f"profile enumeration {len(profiles)} != {expected}")
    print(f"terminal profiles: {len(profiles)}")

    payload = {
        "config": {
            "m": M, "dim": DIM, "bundle": BUNDLE, "rounds": ROUNDS,
            "eval_batch": EVAL_BATCH, "fit_batch": FIT_BATCH,
            "regime": "heterogeneous", "dtype": "float64",
            "seeds": args.seeds, "states_at_steps": args.steps,
            "candidate_set": "all C(8,3)=56 bundles",
            "command": " ".join(sys.argv), "platform": platform.platform(),
        },
        "states": [],
    }

    start = time.time()
    for seed in args.seeds:
        evaluator = ChainEvaluator(seed)
        net, topology = evaluator.net, evaluator.topology
        eligible_all = evaluator.allocatable
        values_path = RESULTS_DIR / f"terminal_oracle_m8_values_seed{seed}.npy"
        landscape = np.load(values_path) if values_path.exists() else None

        # Walk a measured-first-order trajectory and probe at the chosen steps.
        ranks = dict(evaluator.base)
        for step in range(ROUNDS):
            if step in args.steps:
                current = np.array([ranks[n] - evaluator.base[n] for n in eligible_all],
                                   dtype=np.int16)
                remaining = ROUNDS - step - 1
                base_e = evaluator.direct(ranks)
                base_a = net.validated_error_certificate(evaluator.eval_batch, ranks)["root_bound"]
                base_b = restricted_gain_certificate(net, evaluator.eval_batch, ranks)["root_bound"]
                base_g = gram_aware_certificate(net, evaluator.eval_batch, ranks)["root_bound"]

                records = []
                for combo in itertools.combinations(range(len(eligible_all)), BUNDLE):
                    candidate = dict(ranks)
                    for index in combo:
                        candidate[eligible_all[index]] += 1
                    increment = current.copy()
                    for index in combo:
                        increment[index] += 1

                    entry = {
                        "action": list(combo),
                        "dE": evaluator.direct(candidate) - base_e,
                        "dA": net.validated_error_certificate(
                            evaluator.eval_batch, candidate)["root_bound"] - base_a,
                        "dB": restricted_gain_certificate(
                            net, evaluator.eval_batch, candidate)["root_bound"] - base_b,
                        "dG": gram_aware_certificate(
                            net, evaluator.eval_batch, candidate)["root_bound"] - base_g,
                    }
                    if landscape is not None:
                        reachable = np.all(profiles >= increment, axis=1) & \
                                    np.all(profiles - increment <= remaining, axis=1)
                        entry["V"] = (float(landscape[reachable].min())
                                      if reachable.any() else None)
                    records.append(entry)

                payload["states"].append({
                    "seed": seed, "step": step,
                    "base_error": base_e, "base_A": base_a,
                    "base_B": base_b, "base_G": base_g,
                    "remaining_rounds": remaining,
                    "candidates": records,
                })
                print(f"seed={seed} step={step}: {len(records)} candidates, "
                      f"elapsed={time.time() - start:.0f}s", flush=True)

            # advance with measured first order
            eligible = [n for n in eligible_all if ranks[n] < DIM]
            if len(eligible) < BUNDLE:
                break
            e_now = evaluator.direct(ranks)
            utility = {n: e_now - evaluator.direct({**ranks, n: ranks[n] + 1})
                       for n in eligible}
            for node in sorted(eligible, key=lambda n: -utility[n])[:BUNDLE]:
                ranks[node] += 1

        out_path = RESULTS_DIR / "certificate_alignment_raw.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\nWrote {len(payload['states'])} probed states to "
          f"{RESULTS_DIR / 'certificate_alignment_raw.json'}")


if __name__ == "__main__":
    main()
