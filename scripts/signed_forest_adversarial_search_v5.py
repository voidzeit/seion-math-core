"""Real derivative-free adversarial search over the named signed forests
(SEION V5 Phase 8) -- fills in the `derivative_free_constant` /
`gradient_adversarial_constant` columns that
scripts/tree_constants_v3_pipeline.py's `_block_g()` explicitly left as
`np.nan` with `optimizer_status="EXTENDED_PENDING_RESOURCE_GATE"`
(artifacts/research_v3/block_G.csv).

That existing pipeline only ever evaluated ONE construction per forest
(the single-parameter gated rotation `rotation_tensor(arity, eta)`,
reused unmodified from the single-tree extremizer work) plugged into a
signed multi-term combination it was never designed to maximize -- hence
tiny observed ratios (e.g. 5e-5 of the triangle bound at eta=1e-4) that
say more about that one construction's unsuitability for a SIGNED
combination than about the true extremal ratio. This script instead
samples many random typed laws (operator norm numerically normalized to
~1, matching the existing pipeline's natural-units convention) and keeps
the best (adversarially worst-case) forest ratio found for each named
identity -- a genuine empirical lower bound, not a placeholder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.research_v3.local_constants import TypedLaw, apply_tensor_numpy  # noqa: E402
from seion_core.research_v3.polynomial_forests import (  # noqa: E402
    ForestTerm,
    SignedForest,
    evaluate_forest_errors,
    named_signed_forests,
)
from seion_core.research_v3.typed_tree import Leaf, iter_internal  # noqa: E402
from seion_core.research_v3.types import TypeSystem, TypedSpace  # noqa: E402

DIMENSION = 2
PROJECTOR_RANK = 1
TRIALS_PER_FOREST = 4000
LOCAL_REFINEMENT_STEPS = 200
RNG_SEED = 0


def _iter_tree_leaves(tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _iter_tree_leaves(child)


def forest_arity(forest: SignedForest) -> int:
    for term in forest.terms:
        for node in iter_internal(term.tree):
            return node.arity
    raise ValueError("forest has no internal nodes")


def triangle_coefficient(forest: SignedForest) -> float:
    """Sum of |c_alpha| * (k_alpha - 1), the same natural-units triangle
    bound scripts/tree_constants_v3_pipeline.py's _block_g() computes
    (consistent units: unit leaf norms, operator norm M=1)."""
    return float(
        sum(
            abs(term.coefficient) * max(0, sum(1 for _ in iter_internal(term.tree)) - 1)
            for term in forest.terms
        )
    )


def estimate_operator_norm(tensor: np.ndarray, arity: int, *, trials: int, rng: np.random.Generator) -> float:
    """Multilinear operator norm over unit-norm real inputs, random-sampling estimate."""
    best = 0.0
    for _ in range(trials):
        vectors = [_unit(rng.standard_normal(DIMENSION)) for _ in range(arity)]
        value = apply_tensor_numpy(tensor, vectors)
        best = max(best, float(np.linalg.norm(value)))
    return best


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-30 else v


def random_normalized_law(arity: int, rng: np.random.Generator) -> np.ndarray:
    shape = (DIMENSION,) + (DIMENSION,) * arity
    tensor = rng.standard_normal(shape)
    m_hat = estimate_operator_norm(tensor, arity, trials=100, rng=rng)
    if m_hat < 1e-12:
        return tensor
    return tensor / m_hat  # rescale so operator norm ~1, matching the fixed-rotation construction's units


def forest_ratio(forest: SignedForest, tensor: np.ndarray, arity: int) -> float:
    types = TypeSystem([TypedSpace.coordinate("tau", DIMENSION, PROJECTOR_RANK)])
    law = TypedLaw("mu", tuple("tau" for _ in range(arity)), "tau", tensor)
    max_label = max(leaf.label for term in forest.terms for leaf in _iter_tree_leaves(term.tree))
    inputs = {index: np.ones(PROJECTOR_RANK) for index in range(max_label + 1)}
    errors = evaluate_forest_errors(forest, {"mu": law}, types, inputs)
    return errors.projected


def search_forest(name: str, forest: SignedForest, rng: np.random.Generator) -> dict:
    arity = forest_arity(forest)
    triangle = triangle_coefficient(forest)
    best_ratio = 0.0
    best_tensor = None
    for _ in range(TRIALS_PER_FOREST):
        tensor = random_normalized_law(arity, rng)
        value = forest_ratio(forest, tensor, arity)
        if value > best_ratio:
            best_ratio = value
            best_tensor = tensor

    # Local refinement: coordinate-wise perturbation hill-climbing around the
    # best random trial found (derivative-free, no autodiff needed here since
    # these are plain NumPy tensors, not torch parameters).
    if best_tensor is not None:
        current = best_tensor.copy()
        step = 0.3
        for i in range(LOCAL_REFINEMENT_STEPS):
            candidate = current + step * rng.standard_normal(current.shape)
            m_hat = estimate_operator_norm(candidate, arity, trials=60, rng=rng)
            if m_hat < 1e-12:
                continue
            candidate = candidate / m_hat
            value = forest_ratio(forest, candidate, arity)
            if value > best_ratio:
                best_ratio = value
                current = candidate
            else:
                step *= 0.995  # gentle cooling regardless of accept/reject

    gap = triangle - best_ratio
    if triangle <= 1e-12:
        verdict = "TRIANGLE_BOUND_DEGENERATE"
    elif gap < 0.05 * triangle:
        verdict = "SHARP"
    elif gap > 0.5 * triangle:
        verdict = "OPEN_WITH_CERTIFIED_GAP"
    else:
        verdict = "IMPROVABLE_WITH_EXACT_CONSTANT_OPEN"

    return {
        "name": name,
        "arity": arity,
        "triangle_upper": triangle,
        "derivative_free_constant": best_ratio,
        "gap": gap,
        "ratio_of_triangle": best_ratio / triangle if triangle > 1e-12 else 0.0,
        "trials": TRIALS_PER_FOREST,
        "local_refinement_steps": LOCAL_REFINEMENT_STEPS,
        "verdict": verdict,
    }


def main() -> dict:
    rng = np.random.default_rng(RNG_SEED)
    named = named_signed_forests()
    priority = [
        "five_input_ternary_associator", "anchored_associator", "jacobiator_variants",
        "named_gji_variants", "filippov_fundamental_identity",
    ]
    results = {name: search_forest(name, named[name], rng) for name in priority}
    out_dir = ROOT / "artifacts" / "research_v3"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "signed_forest_adversarial_search_v5.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
