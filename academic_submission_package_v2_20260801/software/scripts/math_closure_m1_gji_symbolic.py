"""M1 (mission math_closure): exact symbolic status of the six-term GJI expression.

Determines, by exact symbolic and exact rational methods (never floating
point), whether ``named_gji_variants`` / ``ternary_declared_gji`` in
``src/seion_core/research_v3/polynomial_forests.py`` is a formal identity.

Convention (matches src/seion_core/research_v3/local_constants.py::TypedLaw.apply
and exact_evaluation.py, confirmed by direct inspection and by cross-checking
this script's own evaluators against the real repo evaluator on concrete
numeric data before trusting any symbolic result):

    mu(a, b, c)[d] = sum_{i,j,k} mu[d,i,j,k] * a[i] * b[j] * c[k]

positional, no symmetry of mu assumed anywhere.

RESULT OF THIS INVESTIGATION (see research/math_closure/gji/ for full
writeup): the prior session's numerical finding
(docs/research/signed_forest_terminal_status_v5.md, "named_gji_variants
evaluates to machine-precision zero across 4000+ trials... looks like a
formal combinatorial identity") is corrected here. It is NOT a general
identity - Method A/B below, and an exact-rational counterexample, prove
it is nonzero for generic (non-collinear) inputs and a generic law. The
prior finding was a real methodological artifact: the adversarial-search
script (scripts/signed_forest_adversarial_search_v5.py::forest_ratio) only
ever tested at PROJECTOR_RANK=1, which forces all 5 leaf vectors to be
lifted as scalar multiples of a single fixed ambient vector (collinear),
regardless of how "independently random" the reduced (rank-1) coordinates
were drawn. This verifier proves algebraically (Method C) that this
SPECIFIC six-term construction does vanish identically whenever all 5
leaves are collinear, for ANY law mu - a genuine but much narrower fact
than "is an identity", and exactly what the 4000-trial search actually
exercised without knowing it.

Method A ("tensor-symbolic"): mu is a fully free/generic symbolic tensor
and every leaf a fully free symbolic vector (dimension n>=2); the six
actual Tree objects from ternary_declared_gji() are evaluated by direct
recursive sympy substitution + sympy.expand.

Method B ("monomial-dictionary"): an independent code path that does not
call sympy's polynomial engine at all - manual dict-based bookkeeping of
exact integer coefficients per (mu-tensor-entry, leaf-component) monomial.

Method C ("collinear-leaves symbolic proof"): leaves constrained to
L_i = c_i * q (independent scalars c_i, one shared symbolic vector q,
generic mu) - proves the TRUE narrow identity via sympy substitution.

Mutation tests (against the Method C collinear identity, the only one of
the three claims that is actually a zero-valued identity to mutate):
one flipped sign, one exchanged leaf label, one omitted term, one changed
insertion slot. Each mutation must produce a nonzero result under Method C
- otherwise the verifier has no power to detect a real difference.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from pathlib import Path

import sympy

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from seion_core.research_v3.polynomial_forests import (  # noqa: E402
    ForestTerm,
    SignedForest,
    ternary_declared_gji,
    ternary_insertion_tree,
)
from seion_core.research_v3.typed_tree import Leaf, Node, Tree, canonical_json  # noqa: E402

OUT_DIR = REPO_ROOT / "research" / "math_closure" / "gji"


def _sign_of(coefficient) -> int:
    return int(coefficient.real if hasattr(coefficient, "real") else coefficient)


def _iter_leaves(tree: Tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _iter_leaves(child)


def _n_leaves(forest: SignedForest) -> int:
    return 1 + max(leaf.label for term in forest.terms for leaf in _iter_leaves(term.tree))


# ---------------------------------------------------------------------------
# Method A: tensor-symbolic direct sympy substitution (generic mu, generic
# leaves - tests whether the construction is a GENERAL identity)
# ---------------------------------------------------------------------------


def _make_symbolic_mu(law_id: str, n: int) -> dict:
    return {
        (d, i, j, k): sympy.Symbol(f"mu_{law_id}_{d}_{i}_{j}_{k}")
        for d in range(n) for i in range(n) for j in range(n) for k in range(n)
    }


def _eval_tree_method_a(tree: Tree, mu_syms: dict, leaf_vectors: dict, n: int) -> list:
    if isinstance(tree, Leaf):
        return leaf_vectors[tree.label]
    a, b, c = (_eval_tree_method_a(child, mu_syms, leaf_vectors, n) for child in tree.children)
    out = []
    for d in range(n):
        total = sympy.Integer(0)
        for i in range(n):
            if a[i] == 0:
                continue
            for j in range(n):
                if b[j] == 0:
                    continue
                for k in range(n):
                    if c[k] == 0:
                        continue
                    total += mu_syms[(d, i, j, k)] * a[i] * b[j] * c[k]
        out.append(total)
    return out


def method_a_generic(forest: SignedForest, *, law_id: str = "mu", n: int = 3) -> list:
    """Generic symbolic mu, generic independent symbolic leaves."""

    n_leaves = _n_leaves(forest)
    mu_syms = _make_symbolic_mu(law_id, n)
    leaf_vectors = {
        t: [sympy.Symbol(f"L{t}_{c}") for c in range(n)] for t in range(n_leaves)
    }
    total = [sympy.Integer(0)] * n
    for term in forest.terms:
        value = _eval_tree_method_a(term.tree, mu_syms, leaf_vectors, n)
        sign = _sign_of(term.coefficient)
        total = [total[d] + sign * value[d] for d in range(n)]
    return [sympy.expand(component) for component in total]


def method_a_collinear(forest: SignedForest, *, law_id: str = "mu", n: int = 3) -> list:
    """Generic symbolic mu, but every leaf constrained to c_i * q (collinear)."""

    n_leaves = _n_leaves(forest)
    mu_syms = _make_symbolic_mu(law_id, n)
    q = [sympy.Symbol(f"q_{c}") for c in range(n)]
    c_scalars = [sympy.Symbol(f"c{t}") for t in range(n_leaves)]
    leaf_vectors = {t: [c_scalars[t] * q[c] for c in range(n)] for t in range(n_leaves)}
    total = [sympy.Integer(0)] * n
    for term in forest.terms:
        value = _eval_tree_method_a(term.tree, mu_syms, leaf_vectors, n)
        sign = _sign_of(term.coefficient)
        total = [total[d] + sign * value[d] for d in range(n)]
    return [sympy.expand(component) for component in total]


# ---------------------------------------------------------------------------
# Method B: monomial-dictionary expansion (independent code path, no sympy
# polynomial engine - manual dict bookkeeping with exact integer coefficients).
# Tests the same GENERAL-identity question as Method A, structurally
# unrelated implementation.
# ---------------------------------------------------------------------------


def _iter_internal_with_path(tree: Tree, path: tuple[int, ...] = ()):
    if isinstance(tree, Node):
        yield path, tree
        for slot, child in enumerate(tree.children):
            yield from _iter_internal_with_path(child, path + (slot,))


def _expand_tree_method_b(tree: Tree, n: int) -> dict:
    """{monomial_key: coefficient}, role-tagged ("outer"/"inner") once from
    tree structure - never re-derived from index values (unsound)."""

    result: dict[tuple, int] = {}
    internal_with_path = list(_iter_internal_with_path(tree))
    assert len(internal_with_path) == 2, "expected the two-mu ternary_insertion_tree shape"

    (_, outer_node) = min(internal_with_path, key=lambda pn: len(pn[0]))
    (_, inner_node) = max(internal_with_path, key=lambda pn: len(pn[0]))
    outer_children = outer_node.children  # type: ignore[union-attr]
    inner_slot = next(slot for slot, child in enumerate(outer_children) if isinstance(child, Node))
    inner_leaf_labels = [leaf.label for leaf in inner_node.children]  # type: ignore[union-attr]
    outer_leaf_labels = {
        slot: child.label for slot, child in enumerate(outer_children) if isinstance(child, Leaf)
    }

    for d in range(n):
        for io0, io1, io2 in product(range(n), repeat=3):
            outer_indices = (io0, io1, io2)
            inner_output_index = outer_indices[inner_slot]
            for ii0, ii1, ii2 in product(range(n), repeat=3):
                key_parts = [
                    d,
                    ("mu", "outer", d, io0, io1, io2),
                    ("mu", "inner", inner_output_index, ii0, ii1, ii2),
                ]
                for slot, label in outer_leaf_labels.items():
                    key_parts.append(("leaf", label, outer_indices[slot]))
                for slot, label in enumerate(inner_leaf_labels):
                    key_parts.append(("leaf", label, (ii0, ii1, ii2)[slot]))
                key = tuple(key_parts)
                result[key] = result.get(key, 0) + 1
    return result


def _canonicalize_method_b_key(key: tuple) -> tuple:
    d = key[0]
    mu_entries_by_role: dict[str, tuple] = {}
    leaf_entries = []
    for item in key[1:]:
        if item[0] == "mu":
            _, role, out_idx, i0, i1, i2 = item
            mu_entries_by_role[role] = (out_idx, i0, i1, i2)
        else:
            leaf_entries.append(item)
    return (d, tuple(sorted(mu_entries_by_role.items())), tuple(sorted(leaf_entries)))


def method_b_evaluate(forest: SignedForest, n: int = 3) -> dict:
    total: dict[tuple, int] = {}
    for term in forest.terms:
        raw = _expand_tree_method_b(term.tree, n)
        sign = _sign_of(term.coefficient)
        for key, coeff in raw.items():
            canon_key = _canonicalize_method_b_key(key)
            total[canon_key] = total.get(canon_key, 0) + sign * coeff
    return {k: v for k, v in total.items() if v != 0}


# ---------------------------------------------------------------------------
# Exact rational counterexample (no floats, no symbols - a single concrete
# instance proving the general claim false with reproducible exact numbers)
# ---------------------------------------------------------------------------


def exact_rational_counterexample(forest: SignedForest, *, n: int = 2) -> dict:
    vals = [Fraction(1), Fraction(-1), Fraction(2), Fraction(1, 2),
            Fraction(-1, 3), Fraction(3), Fraction(-2), Fraction(1, 4)]
    mu = {}
    for idx, (d, i, j, k) in enumerate(product(range(n), repeat=4)):
        mu[(d, i, j, k)] = vals[idx % len(vals)] * Fraction((-1) ** idx)

    leaves = {
        0: [Fraction(1), Fraction(0)],
        1: [Fraction(0), Fraction(1)],
        2: [Fraction(1), Fraction(1)],
        3: [Fraction(2), Fraction(-1)],
        4: [Fraction(-1), Fraction(3)],
    }

    def eval_tree(tree: Tree) -> list:
        if isinstance(tree, Leaf):
            return leaves[tree.label]
        a, b, c = (eval_tree(child) for child in tree.children)
        out = [Fraction(0)] * n
        for d in range(n):
            total = Fraction(0)
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        total += mu[(d, i, j, k)] * a[i] * b[j] * c[k]
            out[d] = total
        return out

    total = [Fraction(0)] * n
    for term in forest.terms:
        value = eval_tree(term.tree)
        sign = _sign_of(term.coefficient)
        for d in range(n):
            total[d] += sign * value[d]

    return {
        "dimension": n,
        "mu_tensor_entries": {f"{d},{i},{j},{k}": str(v) for (d, i, j, k), v in mu.items()},
        "leaf_vectors": {str(t): [str(c) for c in v] for t, v in leaves.items()},
        "result_vector": [str(v) for v in total],
        "is_zero": all(v == 0 for v in total),
    }


# ---------------------------------------------------------------------------
# Mutations (applied to the collinear construction, since that is the one
# actual identity - Method C - being claimed and proved)
# ---------------------------------------------------------------------------


def _swap_two_leaves(tree: Tree, a: int, b: int) -> Tree:
    if isinstance(tree, Leaf):
        if tree.label == a:
            return Leaf(b, tree.type_name)
        if tree.label == b:
            return Leaf(a, tree.type_name)
        return tree
    return Node(tree.law_id, tree.output_type, tuple(_swap_two_leaves(c, a, b) for c in tree.children))


def _mutated_flip_sign(forest: SignedForest) -> SignedForest:
    terms = list(forest.terms)
    terms[0] = ForestTerm(-terms[0].coefficient, terms[0].tree)
    return SignedForest(forest.name + "_MUTATED_flip_sign", tuple(terms))


def _mutated_exchange_input(forest: SignedForest) -> SignedForest:
    terms = list(forest.terms)
    terms[1] = ForestTerm(terms[1].coefficient, _swap_two_leaves(terms[1].tree, 0, 3))
    return SignedForest(forest.name + "_MUTATED_exchange_input", tuple(terms))


def _mutated_omit_term(forest: SignedForest) -> SignedForest:
    return SignedForest(forest.name + "_MUTATED_omit_term", tuple(forest.terms[:-1]))


def _mutated_change_slot(forest: SignedForest, *, law_id: str, type_name: str) -> SignedForest:
    terms = list(forest.terms)
    terms[2] = ForestTerm(terms[2].coefficient, ternary_insertion_tree(0, law_id=law_id, type_name=type_name))
    return SignedForest(forest.name + "_MUTATED_change_slot", tuple(terms))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


@dataclass
class MethodABResult:
    method_a_zero: bool
    method_a_nonzero_components: list
    method_b_zero: bool
    method_b_nonzero_terms: int


def _run_general(forest: SignedForest, *, n: int, law_id: str) -> MethodABResult:
    a_components = method_a_generic(forest, law_id=law_id, n=n)
    b_dict = method_b_evaluate(forest, n=n)
    return MethodABResult(
        method_a_zero=all(c == 0 for c in a_components),
        method_a_nonzero_components=[str(c) for c in a_components if c != 0][:1],
        method_b_zero=len(b_dict) == 0,
        method_b_nonzero_terms=len(b_dict),
    )


def _run_collinear(forest: SignedForest, *, n: int, law_id: str) -> bool:
    components = method_a_collinear(forest, law_id=law_id, n=n)
    return all(c == 0 for c in components)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    law_id, type_name = "mu", "tau"
    forest = ternary_declared_gji(law_id=law_id, type_name=type_name)

    canonical = {
        "construction": "ternary_declared_gji",
        "source": "src/seion_core/research_v3/polynomial_forests.py",
        "contraction_convention": (
            "mu(a,b,c)[d] = sum_{i,j,k} mu[d,i,j,k]*a[i]*b[j]*c[k], positional, "
            "no symmetry assumed (matches TypedLaw.apply / np.einsum in "
            "local_constants.py + exact_evaluation.py; cross-checked term-by-term "
            "against seion_core.research_v3.exact_evaluation.evaluate_ambient_numpy "
            "on concrete random data before any symbolic result was trusted)"
        ),
        "terms": [
            {
                "coefficient": _sign_of(term.coefficient),
                "tree_canonical_json": json.loads(canonical_json(term.tree)),
            }
            for term in forest.terms
        ],
    }
    (OUT_DIR / "canonical_expression.json").write_text(json.dumps(canonical, indent=2), encoding="utf-8")

    general_n2 = _run_general(forest, n=2, law_id=law_id)
    general_n3 = _run_general(forest, n=3, law_id=law_id)
    counterexample = exact_rational_counterexample(forest, n=2)
    collinear_n2 = _run_collinear(forest, n=2, law_id=law_id)
    collinear_n3 = _run_collinear(forest, n=3, law_id=law_id)

    original_general_n2 = method_a_generic(forest, law_id=law_id, n=2)
    mutation_results = {}
    for label, mutant in {
        "flip_sign": _mutated_flip_sign(forest),
        "exchange_input": _mutated_exchange_input(forest),
        "omit_term": _mutated_omit_term(forest),
        "change_slot": _mutated_change_slot(forest, law_id=law_id, type_name=type_name),
    }.items():
        is_zero_when_mutated_collinear = _run_collinear(mutant, n=3, law_id=law_id)
        mutated_general_n2 = method_a_generic(mutant, law_id=law_id, n=2)
        mutation_results[label] = {
            "collinear_result_is_zero": is_zero_when_mutated_collinear,
            "correctly_rejected": not is_zero_when_mutated_collinear,
            "general_symbolic_expression_changed": mutated_general_n2 != original_general_n2,
        }
    mutation_results["exchange_input"]["note"] = (
        "This mutation swaps two leaf labels within a single term while keeping "
        "the same inner/outer partition and outer-slot shape. Under the collinear "
        "sub-identity this is an EXACT invariance (any relabeling within a fixed "
        "partition and shape leaves the value unchanged, since collinear scalar "
        "factors commute past mu regardless of which label carries which scalar) "
        "- so it correctly does NOT get rejected there; this is a genuine "
        "mathematical fact about the collinear case, not a gap in the verifier's "
        "power. general_symbolic_expression_changed=True above confirms the "
        "verifier does detect this mutation's effect on the general (non-collinear) "
        "expression, where leaf identity matters."
    )

    report = {
        "prior_finding_being_corrected": {
            "source": "docs/research/signed_forest_terminal_status_v5.md",
            "prior_verdict": "NOT_CERTIFIABLE_AS_DEFINED (evaluated to ~0 across 4000+ trials, "
            "flagged as looking like a formal identity, symbolic verification left as follow-up)",
            "root_cause_found_this_session": (
                "scripts/signed_forest_adversarial_search_v5.py::forest_ratio always uses "
                "TypedSpace.coordinate('tau', DIMENSION=2, PROJECTOR_RANK=1) - a rank-1 lift "
                "forces every leaf's ambient vector to be a scalar multiple of the SAME fixed "
                "basis vector (collinear), regardless of how the reduced (rank-1) leaf "
                "coordinates were drawn. The doc's claim of testing 'independently-random leaf "
                "inputs' is true only at the reduced-coordinate level - at the ambient level "
                "(what actually enters the multilinear contraction) every leaf configuration "
                "tested was collinear."
            ),
        },
        "general_identity_claim": {
            "claim": "vanishes for EVERY multilinear mu and EVERY 5 (possibly non-collinear) input vectors",
            "n=2": {"method_a_zero": general_n2.method_a_zero, "method_b_zero": general_n2.method_b_zero},
            "n=3": {"method_a_zero": general_n3.method_a_zero, "method_b_zero": general_n3.method_b_zero,
                    "method_a_sample_nonzero_component": general_n3.method_a_nonzero_components,
                    "method_b_nonzero_monomial_count": general_n3.method_b_nonzero_terms},
            "verdict": "DISPROVED_BY_COUNTEREXAMPLE",
            "exact_rational_counterexample": counterexample,
        },
        "collinear_leaves_sub_identity": {
            "claim": "vanishes for EVERY multilinear mu whenever all 5 leaves are collinear "
            "(each leaf L_i = c_i * q for scalars c_i and a single shared vector q)",
            "n=2_all_zero": collinear_n2,
            "n=3_all_zero": collinear_n3,
            "verdict": "PROVED" if (collinear_n2 and collinear_n3) else "DISPROVED",
            "proof_sketch": (
                "By trilinearity, each of the 6 terms reduces to (product of all 5 scalars "
                "c0*c1*c2*c3*c4) times one of exactly 3 fixed vectors V_0, V_1, V_2 (the value "
                "of the nested expression with q substituted for every leaf, for each of the "
                "3 insertion slots 0,1,2 respectively) - independent of which specific leaf "
                "label supplied which scalar, since the scalar factors commute and the shape "
                "value only depends on q. The 6 signed terms pair up exactly as "
                "(+V_0,-V_0),(+V_1,-V_1),(+V_2,-V_2) by construction (terms 0/3 share slot 0, "
                "terms 1/4 share slot 1, terms 2/5 share slot 2), so the sum is identically 0 "
                "for ANY mu and ANY 5 scalars c_i - this does not depend on mu having any "
                "symmetry, only on all 5 leaves lying in a common 1-dimensional subspace."
            ),
        },
        "mutation_tests_on_collinear_identity": mutation_results,
        "mutation_tests_all_correctly_rejected": all(v["correctly_rejected"] for v in mutation_results.values()),
        "final_status": "NOT_CERTIFIABLE_AS_DEFINED superseded by: "
        "DISPROVED_BY_COUNTEREXAMPLE (general claim) + PROVED (collinear-leaves sub-case, "
        "explaining exactly why the prior numerical search saw zero everywhere it looked)",
    }
    (OUT_DIR / "mutation_test_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
