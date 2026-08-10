# External mathematical review request — Projected Graphs V5

This document is a handoff template for a named independent mathematician. It
must be completed by a human reviewer; an agent must not fill the verdict
fields or convert a software pass into approval.

## Requested review scope

Please review the finite-dimensional projected multilinear-tree paper and the
following minimum theorem spine:

1. the universal projected-root coefficient `k-1`;
2. M8, the necessary-and-sufficient `k=2` equality characterization;
3. M14 and M15, the exact independent-law `k=3` chain and branching constants;
4. M16, the independent-law class corollary;
5. M18 and M19, fixed-topology asymptotic sharpness;
6. M20, the exact fixed-eta constant for every finite `k=3` arity profile.

M21--M23 are optional for the first-paper decision and may be reviewed as a
separate shared-operator addendum:

- M21: tagged same-law direct-sum simulation;
- M22: high-eta rank-one/common-leaf same-law chain;
- M23: exact unary-operator reduction, with the value intentionally open.

## Minimal reading set

- Main mathematical draft:
  `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`
- Theorem registry:
  `claims/theorem_registry_v5.yaml`
- Review packet:
  `research/projected_trees_v5/review/REVIEW_PACKET_2026-08-08.md`
- Internal consistency audit (context only, not approval):
  `research/projected_trees_v5/review/INTERNAL_THEOREM_AUDIT_2026-08-09.md`
- Requirement audit (context only, not approval):
  `research/projected_trees_v5/review/OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md`
- Compact normalization/scope sheet:
  `research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md`
- Frozen review-input hashes:
  `research/projected_trees_v5/review/REVIEW_ARTIFACT_MANIFEST_2026-08-09.md`
- Optional neutral reviewer-profile shortlist:
  `research/projected_trees_v5/review/EXTERNAL_REVIEWER_SHORTLIST_2026-08-09.md`

The individual theorem dossiers are listed in the review packet. Python
implementations and tests are supplementary checks, not premises of the
mathematical proofs.

## Questions for each theorem

For every reviewed item, please answer:

1. Are the ambient/reduced spaces, projectors, leaf convention, arity, field,
   and operator/closure-defect hypotheses stated exactly enough?
2. Is the normalization of `C_T^P(eta)` and the relation `eta=rho/M`
   consistent throughout the proof and witness?
3. Does every displayed witness belong to the declared class, including law
   sharing, rank, leaf tags, topology, and fixed-tree restrictions?
4. Do the upper-bound and reduction steps preserve operator norms and local
   closure-defect budgets, including zero or boundary cases?
5. Is the conclusion no stronger than the proof (fixed topology versus growing
   trees, independent laws versus same law, asymptotic versus fixed eta)?

## Verdict vocabulary

Use one verdict per theorem:

- `ACCEPT`: proof is correct under the stated hypotheses;
- `ACCEPT_WITH_CORRECTION`: correct after specified changes;
- `REJECT`: a substantive mathematical gap or false statement was found;
- `INCOMPLETE`: insufficient detail or evidence to decide.

Please list exact file/section references for every correction or unresolved
point. A computational reproduction may support a verdict but cannot replace a
proof check.

## Novelty review

Independently compare the theorem statements, not the project name, against
hierarchical tensor approximation, tensor-network truncation and dynamics,
multilinear perturbation, projection-based model reduction, recursive
projection, and graph/source error propagation. In particular, search for an
equivalent combination of:

- local projected-input multilinear closure residual;
- recursively projected finite tree/DAG evaluation;
- the same `rho M^(k-1) L_T` normalization;
- exact fixed-eta `W_3(eta)` constants and admissible extremizers.

Return one of:

- `NO_MATCH_FOUND_IN_REVIEWED_SOURCES`;
- `ADJACENT_PRIOR_ART_FOUND`;
- `SUBSTANTIAL_OR_EXACT_PRIOR_ART_FOUND`.

This repository currently records only `NOVELTY_NOT_ESTABLISHED`; the reviewer
must supply the evidence and reasoning before any change is considered.

## Reviewer record

```yaml
reviewer_name: null
affiliation: null
expertise: null
review_date: null
theorem_verdicts: {}
novelty_verdict: null
publication_recommendation: null
required_corrections: []
```
