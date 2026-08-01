# Final truth report — 2026-07-29 (advisory, first pass)

This answers the mission's 22 closing questions using only evidence
gathered in this audit: the first pass (`priority_a_finite_core.md`,
`curvature_associator.md`, `frontier_scope.md`, `governance_and_novelty.md`)
plus a second pass covering the modules the first pass left unreviewed
(`priority_d_kernels.md`, `priority_c_operators_and_cohomology_remainder.md`,
`priority_d_multiscale.md`, `priority_c_variational_energies.md`), and
`mathematical_object_registry.yaml`, which reflects both passes. No new
proof work was attempted; unresolved items are marked open, not researched
fresh. Everything under `src/seion_core` has now been audited at least
once. The one substantive negative finding is the variational-energy
gradient gap (Q21 below); everything else found in the second pass was
honestly self-scoped and undertested rather than false.

**1. What are the primitive objects of SEION?**
Typed finite-dimensional vector spaces; n-ary (chiefly ternary) laws
`mu_n: V_1 x...x V_n -> V_0`; their structural tensors and CP
factorizations; finite typed composition trees; projectors `P=QQ*` and
reduced laws; associator/identity defects (five-input, anchored,
Jacobiator, Filippov, Akivis); nodewise/path-sum error certificates. See
`mathematical_object_registry.yaml` for the full inventory with code
locations.

**2. Which definitions are coherent?**
All definitions checked in this pass are internally coherent and
consistently typed: the n-ary law, exact restriction, projector closure,
tree evaluation states, and every named associator/identity convention
(five-input, anchored, Jacobiator/GJI, Filippov, Akivis) are each
implemented as distinct functions with an explicit repository policy
(`docs/definitions/associators.md:9`) against silently identifying them.

**3. Which historical definitions are malformed?**
None found in the audited scope. No instance was found of a ternary
operation applied to two arguments without a declared anchor/currying
convention, nor of mismatched input/output types.

**4. Which theorems are completely proved (unconditionally)?**
`THM_V3_EXACT_SUBSET_EXPANSION` (pure algebraic identity) and
`THM_STANDARD_CURVATURE_ASSOCIATOR_DIFFERENCE_V1` are the two audited
results closest to unconditional — both are finite algebraic expansions
with no analytic hypotheses beyond finite-dimensionality.

**5. Which results are standard?**
`THM_STANDARD_CURVATURE_ASSOCIATOR_DIFFERENCE_V1` (a difference-of-
associators identity, standard non-associative algebra); the discrete
Hodge Laplacian (`OBJ_DISCRETE_HODGE`, textbook combinatorial Hodge
theory); exact invariant-subspace restriction under an isometry (flagged
as standard by the project's own novelty registry, not a claim of this
audit).

**6. Which results may be new?**
The nodewise/mixed-mask path-sum certificate machinery and the exhaustive
196-tree-shape stress test behind `THM_V3_PROJECTED_ROOT_K_MINUS_ONE` are
the most distinctive artifacts found — but see Q7: the project's own
novelty registry does not yet claim theorem-level novelty for these, and
this audit did not perform an independent literature search to confirm or
deny it.

**7. Which novelty claims survived independent review?**
None were being claimed to survive — `claims/novelty_registry.yaml`
states "theorem_level_novelty: none currently claimed" across every
audited area, corroborated by `claims/prior_art_registry_v3.yaml`. This
audit did not find a contradiction and did not attempt the independent
expert literature search the project itself says is still pending.

**8. Which claims were refuted?**
Two, both correctly registered as refuted rather than deleted: unqualified
spectral-snapping continuity without a uniform gap (`REFUTED_SNAPPING_NO_GAP_V1`)
and curvature equal to a raw associator without the `A(y,x,z)=0` hypothesis
(`CE_CURVATURE_NOT_RAW_ASSOCIATOR`).

**9. Which assumptions are necessary?**
For the k/(k−1) tree bounds: uniform operator-norm bound `M` and uniform
closure residual `rho` across all nodes. For the standard curvature
identity: none beyond finite-dimensional bilinearity — and that is exactly
why it cannot be strengthened to "curvature = raw associator" without
adding `A(y,x,z)=0` (shown necessary by the counterexample in Q8).

**10. Which constants are optimal?**
None, by the registry's own explicit labeling — every sharpness field is
`OPEN`, `OPEN_AT_FIXED_ETA`, or `CERTIFIED_UPPER_BOUND_NOT_FIXED_ETA_OPTIMALITY`.
No optimal-constant claim was found anywhere in the audited scope.

**11. Which optimality gaps remain?**
Fixed-positive-eta sharpness for both the `k` and `(k−1)` bounds
(`BLOCK-V4-MATH-SHARPNESS`), and cancellation-aware sharp constants for
FI/GJI/Jacobiator/signed-forest bounds (`BLOCK-V4-MATH-CONSTANTS`) — both
explicitly open per `artifacts/release_v4/final_canonical_handoff.md`.

**12. Which algebraic identities truly hold?**
`THM_V3_EXACT_SUBSET_EXPANSION` (unconditionally, by multilinear algebra)
and `THM_STANDARD_CURVATURE_ASSOCIATOR_DIFFERENCE_V1` (unconditionally, for
any finite-dimensional bilinear product). The k/(k−1) bounds hold as
*inequalities* under the uniform-M/uniform-rho hypotheses. GJI, Filippov,
and Akivis identities are implemented as diagnostics, not claimed to hold
identically for arbitrary laws — they are measured, not assumed.

**13. Under exactly what hypotheses can curvature equal an associator?**
Only the narrow, already-registered case: `R_standard(x,y)z = A(y,x,z) −
A(x,y,z)` for any finite-dimensional bilinear product, and it equals a
*single* raw associator only if the extra hypothesis `A(y,x,z)=0` holds
(refuted in general — see Q8). No anchored/induced version exists in the
repository at all (see `curvature_associator.md`).

**14. Is the proposed cohomology valid?**
The only cohomology actually proposed and proved in the repository — a
finite cochain complex with `d²=0` and commuting-operator descent
(`THM_COHOMOLOGY_DESCENT_FINITE_V1`) — is valid under its stated
assumptions and correctly scoped to finite complexes with an explicit
disclaimer against continuum extension. The broader "associator as
cohomology class" program described in the mission's section 1.20 is not
present in this repository to be evaluated.

**15. Which projector and reduction results are canonical?**
Exact restriction (`P=QQ*`, invariant-subspace closure) and the
root-error orthogonality identity (`E_amb²=E_proj²+E_norm²`, `E_red=E_proj`)
are canonical within `CANONICAL_FINITE_CORE`
(`claims/scope_registry_v4.yaml`). Baseline comparisons against
PCA/SVD/random projectors exist in code (`projectors/baselines.py`) but
were not independently re-verified in this pass.

**16. Which continuum arrows are proved?**
None. `docs/mathematical_scope.md` states this outright: "The package does
not prove a continuum limit, a universal curvature equivalence, a physical
field theory, or any application claim." This audit found nothing that
contradicts that statement.

**17. Which SHP arrows remain conjectural?**
Not applicable — SHP as a named program does not exist in this repository
(see `frontier_scope.md`). The two registered conjectures
(`claims/conjecture_registry.yaml`) are closure recovery under spectral
separation and multiscale gauge-aligned persistence, neither SHP-related.

**18. What exactly does the Laurent artifact prove?**
Nothing — it does not exist in this repository. No Laurent-polynomial
algebraization artifact, over `(C*)^2` or otherwise, was found.

**19. What exactly does E8 contribute?**
Nothing — no exceptional Lie algebra code exists; the sole text match is
an unrelated CSS hex color.

**20. Which applications are mathematically relevant but non-probative?**
None exist in this repository to classify — all listed application
domains (KGE, LLM compression, NEC/BIM, hypergraph compilers, cosmology,
trading, polynomial roots) are explicit, enforced non-goals
(`README.md:104`), not implemented applications whose success or failure
could be mistakenly used as theorem evidence. No such misuse was found
(`governance_and_novelty.md`).

**21. What is the minimal true SEION framework, as of this audit?**
A finite-dimensional typed n-ary algebra library with: (a) an exact,
unconditionally-proved child-error subset expansion identity; (b) a
root-error orthogonality identity and matching k/(k−1) error bounds for
recursively projected tree evaluation, proved under uniform operator-norm
and closure-residual hypotheses and stress-tested against 196 tree shapes;
(c) a standard (non-anchored) curvature-minus-associator difference
identity; (d) a small, correctly-scoped finite cochain complex with
commuting-operator cohomology descent; (e) honestly self-limiting,
if largely untested, finite kernel, operator, and multiscale utilities
that make no continuum or canonicity claims beyond what they can support.
The one component that should **not** be counted as part of the working
framework yet is the variational-energy/gradient machinery
(`src/seion_core/variational/`): it is present in code but functionally
incomplete (two stub energies, an unwired trainable-combination
mechanism, no gradient path, zero tests) and should not be relied on as a
trainable regularizer suite until that gap is closed.

**22. What remains of the original grand vision after every false or
unsupported claim is removed?**
Very little of the "grand vision" (SHP, Hodge conjecture progress, E8,
G-ASUn, Laurent algebraization, physical/cognitive interpretation) was
ever actually asserted in this repository to begin with — it appears to
exist only as the mission prompt's own hypothesis space, not as content
this codebase currently contains or claims. What remains, and is
genuinely defensible, is the modest finite-dimensional core in Q21: real,
tested, conditionally proved, and honestly gated behind
`FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW` rather than oversold.

## What this audit still leaves open

- The evidence-matrix citation gap in `priority_a_finite_core.md`
  (finding 1) has not been fixed — this audit is advisory only, nothing
  in `claims/` or `governance/` was edited.
- The variational-energy gap in `priority_c_variational_energies.md` has
  not been fixed — recommend either implementing/testing real gradients
  for the intended-trainable energies, or relabeling `gji`/`fi`/
  `total_energy` explicitly as unimplemented in their own docstrings.
- No test-writing was performed for the several modules found to have
  zero coverage (kernels, operators, multiscale, variational) — this
  audit only characterizes the gap, it does not close it.
- No independent literature search was performed for Q6/Q7; the
  repository's own prior-art registries remain the only source, and they
  say the search is bounded, not exhaustive.
- `constraints.py` and `estimators.py` in `variational/` were located but
  not individually detailed above beyond their role in the energy/gradient
  picture — a finer-grained pass could still be useful there.
