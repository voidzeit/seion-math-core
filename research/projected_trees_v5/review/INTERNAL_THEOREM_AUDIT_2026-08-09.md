# Internal theorem audit — 2026-08-09

This is an agent-generated pre-review audit. It is evidence preparation, not
independent human review, novelty approval, or publication approval. The
mathematical authority remains the proof files and theorem registry; executable
checks are supplementary.

## Audit scope

The audit checked the universal typed-tree definitions in the main manuscript,
M8, M14--M23 proof dossiers, their registered hypotheses, witness evaluators,
and focused tests. The questions were:

- Are the normalization and class definitions stated consistently?
- Do the displayed witnesses satisfy the operator and local-defect budgets?
- Do reductions preserve the norm and closure budgets?
- Does the manuscript distinguish independent laws, repeated laws, tags,
  rank-one/common-leaf restrictions, fixed topology, and asymptotic limits?

## Findings

| Item | Internal finding | Evidence | External status |
|---|---|---|---|
| Universal `k-1` bound | Consistent under the finite typed Hilbert-space convention, orthogonal output projectors, projected-input closure maps, and identical leaf lift/reduced values. The root residual is removed only after applying the root projector. | `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`, §Typed projected trees / §Universal coefficients | Human proof review pending |
| M8 | The iff proof is a complete equality-of-endpoints argument for the declared binary chain. Its essential convention is that leaves have no separate reduction projector and that `rho` bounds the inner closure map on clean leaf inputs. | `research/math_closure/k2/saturation_iff_theorem.tex`; `tests/math_closure/test_k2_k3_exact_forms.py` | Human proof review pending |
| M14 | The two-dimensional witness uses distinct laws, has operator norm one, and has first/second/root defects bounded by `eta`; M13 supplies the matching upper bound. | `research/math_closure/k3/m14_exact_chain_constant.tex/.py`; `tests/math_closure/test_m14_exact_chain_constant.py` | Human proof review pending |
| M15 | The upper argument is a nuclear/operator-norm duality reduction; the polar-factor witness has the stated norm and exact value. | `research/math_closure/k3/m15_exact_branching_constant.tex/.py`; `tests/math_closure/test_m15_exact_branching_constant.py` | Human proof review pending |
| M16 | Correct corollary of M14/M15 for independently selectable node laws; it does not assert repeated-law sharpness. | `research/math_closure/k3/m16_general_binary_class_corollary.tex` | Human proof review pending |
| M17 | The explicit gated contraction class has the exact `k=2` value one; the canonical orthogonal rotation remains a narrower `eta^2` family. | `research/math_closure/k2/m17_broader_gated_contraction_exact.tex` | Human proof review pending |
| M18/M19 | The complex-plane witnesses prove only fixed-topology asymptotic sharpness. The root law is real-valued and has zero root closure defect; no growing-tree limit is inferred. | `research/math_closure/k3/m18_*.tex`, `m19_*.tex` | Human proof review pending |
| M20 | The finite-arity reduction is now explicit: freezing unit projected leaf slots defines an effective law whose operator norm and projected-input closure residual cannot increase. The internal-child skeleton for three internal nodes is chain or branching. | `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex` | Human proof review pending |
| M21 | The tagged same-law construction is a direct sum of orthogonal input/output blocks. The executable certificate now computes the largest block norm and closure-defect cap instead of returning them as constants. | `research/math_closure/k3/m21_same_law_tagged_exact_constant.py/.tex`; `tests/math_closure/test_m21_same_law_tagged_exact_constant.py` | Human proof review pending |
| M22 | The repeated rank-one/common-leaf rotation attains `W_3` only for `eta >= sqrt(2/3)`; the low-eta and branching classes remain open. | `research/math_closure/k3/m22_same_law_rank_one_high_eta.tex` | Human proof review pending |
| M23 | The tree-to-unary-operator identity and converse gated realization are exact for the stated real, repeated-law, common-leaf, rank-one chain. The optimization value is intentionally not claimed. | `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.tex` | Human proof review pending |

## Scope and normalization checks

The common normalization is
\[
 C_T^P(\eta)=\sup E^P/(\rho M^{k-1}L_T),
 \qquad \eta=\rho/M,
\]
with the appropriate topology/class subscript. The main manuscript now states
that “independent laws” means freely selectable node laws, while “same law”
means one reused bilinear map and does not imply rank-one projectors or common
leaves. “Fixed tree” and “finite arity” are single finite ordered topologies;
limits are taken only after topology is fixed.

The audit found no internal contradiction in these definitions. The following
items remain review questions rather than resolved facts:

1. whether every theorem's closure-defect convention exactly matches the
   intended admissible class in the external literature;
2. whether the M13 Gram-matrix optimization and M15 nuclear-norm reduction
   have any hidden real/complex or zero-vector edge cases;
3. whether the direct-sum tags in M21 are acceptable under the intended
   interpretation of “same law”;
4. whether the effective-map argument in M20 should be stated for arbitrary
   fixed leaf vectors or only the unit projected leaves used here;
5. whether any theorem is already known in equivalent form.

## Verdict

The internal audit supports the labels `PROVED_UNDER_ASSUMPTIONS` and
`PENDING_HUMAN_REVIEW` already recorded in the registries. It does not upgrade
any novelty field, does not certify independent review, and does not support a
release or applied-superiority claim.
