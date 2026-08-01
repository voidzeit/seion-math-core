"""Mission Section VI: "configuration/execution identity", "deterministic
artifact generation" - applied to the Level 1 AI campaign's raw results.
Checks the actual committed results/level1_raw.json rather than
re-running the full campaign (which the experiment scripts already do
and which is covered by applications/adaptive_tensor_network/tests/)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEVEL1_RAW = REPO_ROOT / "applications" / "adaptive_tensor_network" / "results" / "level1_raw.json"


def _load():
    return json.loads(LEVEL1_RAW.read_text(encoding="utf-8"))


def test_level1_raw_results_exist():
    assert LEVEL1_RAW.exists(), "Level 1 campaign must have been executed and its raw output committed"


def test_no_duplicate_config_execution_identity():
    """Every (topology, seed, budget, method) combination must appear
    exactly once - a duplicate would mean either a rerun was silently
    double-counted as an independent sample (forbidden by AI4) or the
    driver has a loop bug."""

    records = _load()
    keys = [(r["topology"], r["seed"], r["budget"], r["method"]) for r in records]
    counts = Counter(keys)
    duplicates = {k: c for k, c in counts.items() if c > 1}
    assert not duplicates, f"duplicate (topology,seed,budget,method) identities found: {duplicates}"


def test_all_declared_methods_present_for_every_config():
    records = _load()
    by_config = {}
    for r in records:
        key = (r["topology"], r["seed"], r["budget"])
        by_config.setdefault(key, set()).add(r["method"])
    method_sets = {frozenset(v) for v in by_config.values()}
    assert len(method_sets) == 1, "not every (topology,seed,budget) config ran the same set of methods"


def test_budget_and_rank_cost_consistent():
    records = _load()
    for r in records:
        assert r["rank_cost"] <= r["budget"], (
            f"rank_cost {r['rank_cost']} exceeds declared budget {r['budget']} for {r['method']}"
        )
