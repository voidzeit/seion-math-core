"""M35c: exact rollout calibration at m = 8 against the true terminal optimum.

EXPERIMENTAL. Nothing here is a theorem.

M35b established that better approximation of the IMMEDIATE objective does not
give a better TERMINAL policy: full pairwise and exhaustive step-greedy reach
identical terminal profiles, and both sit around the 17th percentile of the
admissible terminal landscape while the exact optimum is known. Every policy in
the campaign so far optimizes E(r + a). Rollout is the first that does not.

Rollout uses a base policy pi_0 and scores each candidate action by the
outcome of CONTINUING with pi_0, rather than by its immediate cost:

    Q_t^{pi_0,h}(r, a) = E( state reached by taking a at r,
                            then h-1 further rounds under pi_0 )

    pi_rollout(r) = argmin_a Q_t^{pi_0,h}(r, a)

The lookahead depth h interpolates: h = 1 evaluates E(r + a) and is exactly
step-greedy; h = T - t continues to the horizon. Sweeping h measures how much
lookahead is actually needed, which is more useful operationally than solving
the dynamic program.

Because m = 8 has an exact E_terminal_star from run_terminal_oracle_m8.py, the
natural normalization is available without inventing a metric:

    Gamma = R_T^rollout / R_T^base,     R_T^pi = E_T^pi - E_terminal_star

Gamma < 1 means lookahead improved on the base policy; Gamma ~ 0 means it
recovered nearly all the gap to the true optimum; Gamma = 1 means lookahead
bought nothing. Both regrets share the same valid reference, so the ratio is
well posed -- unlike M35's discarded A_T.

Also recorded: A_action, the per-step action-agreement rate between policy
pairs. M35b observed identical TERMINAL PROFILES for full_pairwise and
step_greedy, but E is path-independent, so identical profiles do not imply
identical action sequences. A_action settles that.
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
from tree import chain_topology  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_interaction_dimension import EVAL_BATCH, FIT_BATCH, heterogeneous_network  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DIM = 16
BUNDLE = 3
ROUNDS = 6
START_FRACTION = 0.25


class Instance:
    def __init__(self, seed: int, m: int) -> None:
        self.m = m
        self.topology = chain_topology(depth=m + 1, leaf_dim=DIM, ambient_dim=DIM)
        self.net = heterogeneous_network(self.topology, DIM, seed=seed)
        fit_batch = self.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
        self.eval_batch = self.net.sample_leaf_batch(EVAL_BATCH, seed=seed * 1000 + 2)
        self.fit_ambient = self.net.ambient_forward(fit_batch)
        self.net.fit_projectors(self.fit_ambient)
        self.nodes = [n.node_id for n in self.topology.nodes_postorder]
        self.root_id = self.topology.root.node_id
        self.allocatable = [n for n in self.nodes if n != self.root_id]
        self.root_ambient = self.net.ambient_forward(self.eval_batch)[self.root_id]
        budget = int(round(START_FRACTION * len(self.nodes) * DIM))
        self.base = uniform_allocation(self.net, max(len(self.nodes), budget))
        self.evaluations = 0

    def error(self, ranks) -> float:
        self.evaluations += 1
        reduced = self.net.reduced_forward(self.eval_batch, ranks)
        diff = self.root_ambient - reduced[self.root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    def eligible(self, ranks):
        return [n for n in self.allocatable if ranks[n] < DIM]


def base_action(instance: "Instance", ranks, policy: str):
    """One action of a base policy. Returns a tuple of allocatable node ids."""
    eligible = instance.eligible(ranks)
    if len(eligible) < BUNDLE:
        return None
    if policy == "local_greedy":
        local = instance.net.local_truncation_error(instance.fit_ambient, ranks)
        order = sorted(eligible, key=lambda n: -local[n])
        return tuple(order[:BUNDLE])
    if policy == "measured_first_order":
        e_base = instance.error(ranks)
        utility = {n: e_base - instance.error({**ranks, n: ranks[n] + 1})
                   for n in eligible}
        order = sorted(eligible, key=lambda n: -utility[n])
        return tuple(order[:BUNDLE])
    raise ValueError(policy)


def continue_with(instance: Instance, ranks, policy: str, steps: int):
    """Advance `steps` rounds under a base policy; return the final ranks."""
    current = dict(ranks)
    for _ in range(steps):
        action = base_action(instance, current, policy)
        if action is None:
            break
        for node in action:
            current[node] += 1
    return current


def run_rollout(instance: Instance, base_policy: str, lookahead: int) -> dict:
    ranks = dict(instance.base)
    instance.evaluations = 0
    actions = []
    start = time.time()

    for step in range(ROUNDS):
        eligible = instance.eligible(ranks)
        if len(eligible) < BUNDLE:
            break
        remaining = ROUNDS - step
        depth = min(lookahead, remaining)
        best, best_value = None, float("inf")
        for combo in itertools.combinations(range(len(eligible)), BUNDLE):
            candidate = dict(ranks)
            for index in combo:
                candidate[eligible[index]] += 1
            # h = 1 evaluates the immediate objective: exactly step-greedy.
            final = continue_with(instance, candidate, base_policy, depth - 1)
            value = instance.error(final)
            if value < best_value:
                best, best_value = combo, value
        chosen = tuple(sorted(eligible[i] for i in best))
        actions.append(chosen)
        for node in chosen:
            ranks[node] += 1

    return {
        "policy": f"rollout_{base_policy}_h{lookahead}",
        "base_policy": base_policy,
        "lookahead": lookahead,
        "terminal_error": instance.error(ranks),
        "terminal_profile": [ranks[n] - instance.base[n] for n in instance.allocatable],
        "actions": [list(a) for a in actions],
        "evaluations": instance.evaluations,
        "wall_seconds": time.time() - start,
    }


def run_base(instance: Instance, policy: str) -> dict:
    ranks = dict(instance.base)
    instance.evaluations = 0
    actions = []
    start = time.time()
    for _ in range(ROUNDS):
        action = base_action(instance, ranks, policy)
        if action is None:
            break
        actions.append(action)
        for node in action:
            ranks[node] += 1
    return {
        "policy": policy,
        "base_policy": policy,
        "lookahead": 0,
        "terminal_error": instance.error(ranks),
        "terminal_profile": [ranks[n] - instance.base[n] for n in instance.allocatable],
        "actions": [list(a) for a in actions],
        "evaluations": instance.evaluations,
        "wall_seconds": time.time() - start,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=8)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--lookahead", type=int, nargs="+", default=[1, 2, 3, 6])
    parser.add_argument("--bases", type=str, nargs="+",
                        default=["local_greedy", "measured_first_order"])
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"rollout_calibration_m{args.m}_raw.json"
    payload = {
        "config": {
            "m": args.m, "dim": DIM, "bundle": BUNDLE, "rounds": ROUNDS,
            "start_fraction": START_FRACTION, "eval_batch": EVAL_BATCH,
            "fit_batch": FIT_BATCH, "regime": "heterogeneous", "dtype": "float64",
            "seeds": args.seeds, "lookahead": args.lookahead, "bases": args.bases,
            "command": " ".join(sys.argv), "platform": platform.platform(),
            "numpy": np.__version__,
            "note": "h=1 rollout is exactly step-greedy over the full 56-bundle set",
        },
        "runs": [],
    }

    start = time.time()
    for seed in args.seeds:
        instance = Instance(seed, args.m)
        base_error = instance.error(instance.base)
        for policy in args.bases:
            result = run_base(instance, policy)
            result.update({"seed": seed, "base_error": base_error})
            payload["runs"].append(result)
        for policy in args.bases:
            for lookahead in args.lookahead:
                result = run_rollout(instance, policy, lookahead)
                result.update({"seed": seed, "base_error": base_error})
                payload["runs"].append(result)
                print(f"seed={seed} {result['policy']}: "
                      f"E_T={result['terminal_error']:.6f} "
                      f"evals={result['evaluations']} "
                      f"elapsed={time.time() - start:.0f}s", flush=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\nWrote {len(payload['runs'])} runs to {out_path}")


if __name__ == "__main__":
    main()
