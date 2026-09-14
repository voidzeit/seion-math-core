# Projected Graphs V5 — independent-review packet

Canonical review hub: `research/projected_trees_v5/review/README.md`.

Date: 2026-08-08  
Repository: `seion-math-core`  
Scientific scope: finite-dimensional projected multilinear trees and source-resolved DAG error calculus

## Purpose and authority

This packet is a bounded handoff for an independent mathematical reviewer. It is
not an approval, novelty determination, or publication recommendation. The
repository remains governed by `PENDING_HUMAN_REVIEW` and
`NOVELTY_NOT_ESTABLISHED` statuses.

The current theorem-level spine is:

1. the universal projected-root bound with coefficient `k-1`;
2. the k=2 necessary-and-sufficient saturation conditions EQ1–EQ3;
3. the k=3 lower curve and tightened unconditional envelope `U_3(eta)`;
4. M10 pointwise non-attainment of `U_3(eta)`;
5. fixed-tree support compression and the resulting global strict gap
   `C_3,ind^P(eta) < U_3(eta)` for `0 < eta < 1`;
6. the exact M20 fixed-eta closure for every finite k=3 arity profile;
7. the M21 tagged same-law direct-sum closure for binary k=3;
8. the M22 high-eta rank-one/common-leaf same-law chain closure;
9. the M23 exact unary-operator reduction for the remaining strict
   rank-one/common-leaf same-law chain;
10. the finite-tree continuum theorem and the corrected growing-tree theorem
    under weighted summability.

## Primary review targets

| ID | Claim | Current status | Primary proof/evidence |
|---|---|---|---|
| M8 | EQ1–EQ3 characterize k=2 equality for arbitrary finite dimension/rank and independent or repeated laws | `PROVED`, approval pending | `research/math_closure/k2/saturation_iff_theorem.tex`; `src/seion_core/research_v5/k2_characterization.py` |
| M2 | Declared gated-planar rotation has exact k=2 value `E_proj=eta^2`, saturating the universal bound iff `eta=1` | `PROVED_UNDER_STATED_ASSUMPTIONS`, approval pending | `research/math_closure/k2/classification_theorem.tex`; `tests/math_closure/test_k2_k3_exact_forms.py` |
| M9 | `C_{3,ind}^P(eta) <= U_3(eta) < 2` for the declared chain/branching class | `PROVED`, approval pending | `research/math_closure/k3/general_upper_envelope.tex`; `src/seion_core/research_v5/k3_upper_bound.py` |
| M10 | No individual admissible chain configuration attains `U_3(eta)` | `PROVED_NON_ATTAINMENT`, approval pending | `research/math_closure/k3/m10_non_sharpness_of_m9.tex`; `src/seion_core/research_v5/k3_non_sharpness.py` |
| M10b | For each fixed finite dimension/rank class, compactness gives a class-dependent strict gap below `U_3(eta)` | `PROVED_UNDER_STATED_ASSUMPTIONS`, approval pending | `research/math_closure/k3/fixed_dimension_compactness_gap.tex` |
| M10c | Fixed finite-tree support compression reduces the declared k=3 global supremum to finitely many compact classes, giving a strict gap for `0 < eta < 1` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/dimension_rank/fixed_tree_support_compression.tex` |
| M10d | At `eta=1`, M10 non-attainment plus finite support compactness gives `C_3,ind^P(1) < U_3(1)=sqrt(2)` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m10_endpoint_eta_one.tex` |
| M13 | For the independent-law binary chain, the contraction Gram-matrix bound gives an unconditional `W_3(eta)` envelope and explicit gap below `U_3(eta)` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m13_unconditional_chain_envelope.tex` |
| M14 | The M13 envelope is attained: `C_3,ind,chain^P(eta)=W_3(eta)` for every fixed `eta` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m14_exact_chain_constant.tex`; `research/math_closure/k3/m14_exact_chain_constant.py`; `tests/math_closure/test_m14_exact_chain_constant.py` |
| M15 | The independent-law branching constant is exactly `W_3(eta)` by nuclear/operator-norm duality and an explicit polar-factor witness | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m15_exact_branching_constant.tex`; `research/math_closure/k3/m15_exact_branching_constant.py`; `tests/math_closure/test_m15_exact_branching_constant.py` |
| M16 | “Independent-law” means independently selectable node laws; therefore M14/M15 close the arbitrary-node-law binary k=3 class for chain and branching | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m16_general_binary_class_corollary.tex`; `research/math_closure/k3/m16_general_binary_class_corollary.py`; `tests/math_closure/test_m16_general_binary_class_corollary.py` |
| M17 | Contractive gated-planar repeated law has exact normalized k=2 constant `1`; the canonical orthogonal rotation is a narrower non-saturating subfamily | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k2/m17_broader_gated_contraction_exact.tex`; `research/math_closure/k2/m17_broader_gated_contraction_exact.py`; `tests/math_closure/test_m17_broader_gated_contraction_exact.py` |
| M18 | Every fixed finite ordered full-binary topology has asymptotic independent-law sharpness `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.tex`; `research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.py`; `tests/math_closure/test_m18_binary_tree_asymptotic_sharpness.py` |
| M19 | Every fixed finite ordered rooted topology with arities at least two has asymptotic independent-law sharpness `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.tex`; `research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.py`; `tests/math_closure/test_m19_finite_arity_asymptotic_sharpness.py` |
| M20 | Every finite ordered rooted k=3 topology with arities at least two has exact independent-law fixed-eta constant `C_{T,ind}^P(eta)=W_3(eta)` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex`; `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.py`; `tests/math_closure/test_m20_k3_arbitrary_arity_exact_constant.py` |
| M21 | A repeated bilinear law with finite orthogonal projected leaf tags has exact fixed-eta constant `W_3(eta)` for binary chain and branching | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m21_same_law_tagged_exact_constant.tex`; `research/math_closure/k3/m21_same_law_tagged_exact_constant.py`; `tests/math_closure/test_m21_same_law_tagged_exact_constant.py` |
| M22 | The strict rank-one/common-leaf repeated-rotation chain has exact constant `W_3(eta)` for `sqrt(2/3) <= eta <= 1` | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m22_same_law_rank_one_high_eta.tex`; `research/math_closure/k3/m22_same_law_rank_one_high_eta.py`; `tests/math_closure/test_m22_same_law_rank_one_high_eta.py` |
| M23 | The remaining strict rank-one/common-leaf same-law chain reduces exactly to the contraction problem `|<e0,A^3e0>-<e0,Ae0>^3|` with `||Q A e0||<=eta`; the value remains open | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.tex`; `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.py`; `tests/math_closure/test_m23_rank_one_same_law_chain_operator_reduction.py` |
| DAG calculus | Finite source-resolved theorem package consolidating exact multi-index propagation, first-order source recombination, truncation, and signed bounds | `PROVED_UNDER_ASSUMPTIONS`, approval pending | `research/math_closure/dag/source_resolved_error_calculus.tex` |
| M5b | Growing-tree convergence under explicit downstream-gain weighted summability | `PROVED_UNDER_STATED_ASSUMPTIONS`, approval pending | `research/math_closure/continuum/growing_tree_summability.tex` |
| DAG | Exact source-polynomial provenance and signed cancellation inequalities | implementation/theorem consolidation | `research/projected_trees_v5/manuscript/SOURCE_RESOLVED_ERROR_CALCULUS.md`; `papers/projected_graphs_v5/source_resolved_error_calculus_v5.tex` |

## Addendum — 2026-08-08 restricted topology-wide formula

The declared homogeneous gated-planar rotation family is now closed for every
finite ordered full-binary topology by the recursive `a(T),d(T)` formula in
`research/math_closure/k3/gated_rotation_full_binary.tex`. This does not close
same-law/gated extremal subclasses, higher-arity or arbitrary finite topologies,
or a uniform reduction theorem for unbounded tree size/arity. The exact evaluator checks all
ordered shapes through four internal nodes at several dimension/rank pairs.

The same restricted closure extends to variable arity: the arity-compatible
law `mu_m(x1,...,xm)=R_theta*x1` times the secondary `e0` gates has the same
recursive formula for every finite ordered rooted tree with arity at least
two. Primary evidence is
`research/math_closure/k3/gated_rotation_general_arity.tex`,
`research/math_closure/k3/gated_rotation_general_arity.py`, and
`tests/math_closure/test_gated_rotation_general_arity.py`. This remains a
restricted family result and does not alter the open global extremal claims.

M11 adds a conditional quantitative target for review:
`research/math_closure/k3/m11_conditional_quantitative_gap.tex`. Under exact
first-propagator norm saturation, it gives the explicit normalized bound
`sqrt(4-3 eta^2)` / `2/(sqrt(3) eta)` across the two regimes. The hypothesis
is essential; this is not a global strict-supremum result.

The Route-A dimension/rank blocker is now resolved for fixed finite trees by
the support-compression theorem in
`research/math_closure/dimension_rank/fixed_tree_support_compression.tex`.
For the binary `k=3` chain and branching classes it gives a dimension bound
of `20` per one-type support (or `22` with proper-projector padding), and M10
therefore yields a fixed-class gap for the chain; M15 supplies the branching
bound directly. The current M14/M15 results determine the exact independent-
law constants for both binary topologies as `W_3(eta)`, including the
endpoint. Same-law/gated sharpness and uniform growing-tree bounds remain
open.

## Required checks

The reviewer should independently verify:

- every hypothesis in the universal projection theorem, especially typing,
  contraction, and the final `P(I-P)=0` step;
- that EQ1–EQ3 are both necessary and sufficient, including zero or degenerate
  cases and repeated-law compatibility;
- the M9 piecewise optimizer, breakpoint
  `eta_* = sqrt((sqrt(5)-1)/2)`, and the normalization of `U_3`;
- that M10 proves only pointwise non-attainment, and that the separate
  support-compression/compactness argument is what upgrades this to a strict
  supremum gap for `0 < eta < 1`;
- that M10b gives only a fixed-class gap and no dimension/rank-uniform
  `delta(eta)`;
- whether the growing-tree assumptions are stated at the correct level of
  uniformity and are sufficient for the claimed limsup passage;
- that source-aware and signed bounds combine coefficients before taking norms;
- that the finite source-resolved proof covers repeated-source multiplicities,
  recursive/topological agreement, and the truncation remainder without
  silently discarding terms;
- whether any theorem or source-calculus component is already present in the
  adjacent literature listed in the novelty audit.
- that M23's tree-to-operator identity is exact under the declared common-leaf,
  rank-one, repeated-law hypotheses, and that its converse gated realization
  preserves the stated contraction and closure budgets;
- that M23 makes no claim about the open low-eta extremal value, branching, or
  broader same-law/gated classes.

## Falsification and reproducibility entry points

The agent's pre-review consistency audit is recorded in
`research/projected_trees_v5/review/INTERNAL_THEOREM_AUDIT_2026-08-09.md`.
It is not independent approval and should be treated as a checklist for the
external reviewer.

The requirement-by-requirement completion audit is recorded in
`research/projected_trees_v5/review/OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md`.
It identifies the exact evidence that remains external: a named mathematical
reviewer and an independent theorem-by-theorem novelty determination.

The novelty record now includes a systematic category pass and comparator
matrix for tree projection/truncation, tensor-manifold step truncation,
rank-adaptive TTN integration, bilinear MOR, semiring provenance, and current
adaptive-rank HT work. It remains a bounded search record; no novelty status
has been upgraded.

The ready-to-send review request is recorded in
`research/projected_trees_v5/review/EXTERNAL_REVIEW_REQUEST_TEMPLATE.md`.
It contains the minimum reading set, theorem-by-theorem questions, verdict
vocabulary, and a separate novelty-review form.

The compact normalization and scope sheet is recorded in
`research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md`.
It is intended to prevent the common review failure in which a fixed-tree,
independent-law, or projected-input statement is silently read as a broader
same-law, ambient-error, or growing-tree claim.

The exact review-input hashes are recorded in
`research/projected_trees_v5/review/REVIEW_ARTIFACT_MANIFEST_2026-08-09.md`.
The manifest is the snapshot identifier for an external review; it does not
freeze the dirty worktree or constitute approval.

Focused V5 tests currently pass. Re-run:

```powershell
python -m pytest tests/research_v5_test_equality_conditions.py tests/research_v5_test_k2_characterization.py tests/research_v5_test_k2_sharpness.py tests/research_v5_test_k3_independent_candidates.py tests/research_v5_test_k3_non_sharpness.py tests/research_v5_test_k3_upper_bound.py tests/research_v5_test_v5b_extremal.py -q
```

The paper build and render audit are deterministic entry points:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_projected_graphs_v5_papers.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify_projected_graphs_v5_papers.ps1
```

The current postflight records 493 collected tests, with 60 math-closure tests
and 16 adaptive-application tests passing in their focused runs. The main
mathematical PDF is now 9 pages and contains the analytic M13--M15/M20 proof
spine; the evaluator remains supplementary. Historical run counts remain
provenance, not fresh evidence; the governance run index separately retains
all historical executions and duplicate groups.

## Explicitly unresolved

- low-eta rank-one/common-leaf same-law chain, rank-one/common-leaf branching
  and gated k=3 sharpness, plus fixed-eta independent-law sharpness for
  `k>=4` (M20--M22 close the stated broader regimes);
- a dimension/rank bound uniform over unbounded tree size/arity or beyond the
  typed-projector convention;
- variable-gate, arbitrary-leaf, and non-planar shared-law variants beyond
  the explicitly defined M17 contractive gated-planar subclass;
- fixed-eta independent-law sharpness beyond M20's k=3 closure;
- globally tight multilinear spectral norms;
- theorem-level novelty and independent human approval;
- Lean/lake formalization, blocked because the toolchain is not installed;
- resource-gated V3 extended experiments.

M19 closes the finite-tree asymptotic `k-1` statement, while M20 closes the
fixed-eta independent-law k=3 arity frontier. The earlier M10/M10d rows and
addenda are retained as provenance. M14 and M15 remain the binary components
of M20; M10 is not used as a branching proof.

## Reviewer decision fields

These fields are intentionally left unfilled by the agent:

```yaml
independent_math_review: PENDING_HUMAN_REVIEW
novelty_decision: NOVELTY_NOT_ESTABLISHED
publication_recommendation: PENDING_HUMAN_REVIEW
reviewer: null
review_date: null
```
