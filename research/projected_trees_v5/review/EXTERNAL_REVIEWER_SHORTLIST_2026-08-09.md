# Projected Graphs V5 — neutral external-reviewer shortlist

This is a research-profile shortlist, not an outreach record or endorsement.
The people below were identified because their published work overlaps a
specific part of the review scope. Availability, conflicts of interest, and
willingness to review must be confirmed by the project owner. No person listed
here has reviewed or approved SEION V5.

## Candidate profiles

| Profile | Relevant expertise | Best review target | Primary public basis |
|---|---|---|---|
| Anthony Nouy | Tree-based low-rank tensor approximation, hierarchical subspaces, interpolation/projection error | Universal bound, M18--M20, finite-arity reduction, tensor prior art | [Higher-order principal component analysis for tree-based low-rank formats](https://arxiv.org/abs/1705.00880) |
| Christian Lubich | Rank-adaptive time integration of tree tensor networks, Galerkin updates, rank truncation | Recursive projection interpretation, M18--M20, distinction from TTN truncation theory | [Rank-adaptive time integration of tree tensor networks](https://arxiv.org/abs/2201.10291) |
| Gianluca Ceruti / Dominik Sulz | Tree-tensor numerical analysis and leaves-to-root rank-adaptive algorithms | Technical comparison of recursive tree projection and truncation error | [Rank-adaptive time integration of tree tensor networks](https://arxiv.org/abs/2201.10291) |
| Martin Hackbusch | Hierarchical tensor formats and truncation theory | Prior-art audit for tree projections, orthogonal truncation, and error constants | [Truncation of tensors in the hierarchical format](https://link.springer.com/article/10.1007/s40324-018-00184-5) |
| Martin Redmann / Igor Pontes Duff | Galerkin projection and error bounds for bilinear reduced-order models | Projection-based MOR comparison and multilinear-dynamics scope | [Full state approximation by Galerkin projection reduced order models](https://arxiv.org/abs/2102.07534) |
| Erich Grädel / Val Tannen | Semiring provenance and multivariate polynomial dependency tracking | Source-resolved DAG polynomial and signed-provenance novelty comparison | [Provenance Analysis and Semiring Semantics for First-Order Logic](https://arxiv.org/abs/2412.07986) |

## Recommended independent-review configuration

The minimum paper decision needs one reviewer who can inspect the mathematical
proofs and one who can inspect prior art. A practical routing is:

1. **Core theorem reviewer:** review the universal theorem, M8, M14--M20,
   normalization, witness admissibility, and the effective-law reduction.
2. **Prior-art reviewer:** independently search HT/TTN truncation, multilinear
   MOR, recursive projection, and source/DAG error analysis.
3. **Optional specialist:** review M21--M23 and the source-resolved calculus.

The same person may cover all roles only if they have the required expertise and
declare no conflict. The request should include the frozen
`REVIEW_ARTIFACT_MANIFEST_2026-08-09.md`, not an unlabelled mutable checkout.

## Outreach safeguards

- Do not describe any candidate as an approver before a signed review exists.
- Do not send private contact information through repository artifacts.
- Ask for theorem verdicts and prior-art reasoning separately.
- Preserve a negative or incomplete review as evidence; do not overwrite it with
  a later favorable summary.
- Keep `PENDING_HUMAN_REVIEW` and `NOVELTY_NOT_ESTABLISHED` until the reviewer
  supplies an explicit, attributable decision.

## Status

This shortlist improves review readiness only. It does not satisfy the
independent-review requirement.
