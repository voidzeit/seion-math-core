# Objective requirements audit — 2026-08-09

This matrix audits the six requirements in the project objective against the
current repository evidence. It is a completion audit, not a substitute for
independent review or a publication decision.

| Requirement | Current status | Authoritative evidence | What is still missing |
|---|---|---|---|
| 1. Independent mathematical review of the universal theorem, M8, M14--M20, and optionally M21--M23 | **NOT SATISFIED** | `research/projected_trees_v5/review/REVIEW_PACKET_2026-08-08.md`; `research/projected_trees_v5/review/INTERNAL_THEOREM_AUDIT_2026-08-09.md`; `research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md`; `research/projected_trees_v5/review/REVIEW_ARTIFACT_MANIFEST_2026-08-09.md` | A named external mathematician must verify hypotheses, normalization, admissibility of witnesses, and norm/closure-budget preservation. The internal audit, frozen manifest, and candidate shortlist are preparatory only. |
| 2. Exhaustive theorem-by-theorem novelty audit | **PARTIAL / NOT SATISFIED** | `research/projected_trees_v5/novelty/TARGETED_AUDIT_2026-08-08.md`; `research/projected_trees_v5/novelty/THEOREM_TO_THEOREM_MATRIX.md`; `claims/theorem_registry_v5.yaml` | The repository now contains a broader category-based primary-source pass and explicit theorem-family dispositions, but it is still bounded and has no independent exhaustive literature review or expert determination. |
| 3. Concentrated mathematical manuscript | **SATISFIED AS INTERNAL DRAFT** | `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`; `output/pdf/projected_multilinear_trees_v5.pdf`; `output/pdf/projected_graphs_v5_render_audit.json` | External mathematical review and final editorial revision remain. The draft's central spine is definitions → `k-1` → `k=2` → `W_3` → finite arity → asymptotic sharpness; M21--M23 are later scoped additions. |
| 4. Absolute scope clarity | **SATISFIED IN SOURCES; REVIEW PENDING** | Main paper scope paragraph; `research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md`; M20/M21/M22/M23 proof files; theorem registry scopes; truth ledger | A reviewer must confirm that the formal definitions match the intended mathematical class and that no theorem is read outside its declared topology, arity, law-sharing, rank, or leaf assumptions. |
| 5. Reproducibility as support, not proof substitute | **SATISFIED FOR CURRENT INTERNAL GATES** | `tests/math_closure`; focused V5 tests; M20/M21/M23 module entry points; build and render scripts; `scripts/verify_projected_trees_v5_review_manifest.ps1` (**19/19**); governance audit; deduplicated run index | Independent reproduction is not yet available. Executable checks remain supplementary and do not themselves establish theorem truth or novelty. |
| 6. Separate applied validation | **CORRECTLY LIMITED / NOT A SUPERIORITY RESULT** | `applications/adaptive_tensor_network/results/APPLIED_VALIDATION_STATUS_2026-08-09.md`; `LEVEL1_FINDINGS.md`; `CAMPAIGN_FINDINGS.md`; `DAG_MATCHED_TOLERANCE_PROBE_2026-08-09.md`; registered benchmark artifacts | A technology-impact claim would require multi-topology matched-error allocation experiments with hardware memory/runtime, uncertainty, and structured-network baselines. The current evidence includes a validation/test tolerance study but remains context-dependent and does not establish an optimal policy or industrial benefit. |

## Minimum-paper audit

The objective's minimum strong-paper conditions have the following status:

| Condition | Status |
|---|---|
| Proofs audited internally under explicit hypotheses | **INTERNAL / VERIFIED WITH LIMITATIONS** |
| Prior art compared conservatively | **BOUNDED / INCOMPLETE** |
| Concentrated manuscript | **READY AS DRAFT** |
| Independent review | **MISSING** |

Therefore the project must not be marked complete or release-ready. The
remaining blockers are external scientific review, exhaustive novelty
positioning, and (only if technological impact is claimed) a separate matched-
error applied superiority study. The unresolved mathematical cases explicitly
excluded by the objective—`k>=4`, M23 low-eta value, and Lean formalization—are
not required for the first paper and are not used as reasons to withhold the
internal draft status.

## Current verification snapshot

- `tests/math_closure`: 60 passed.
- Focused M20/M21/M23 tests: 6 passed.
- M20, M21, and M23 module entry points: passed.
- Three projected-graphs-v5 PDFs: rendered/audited successfully.
- Frozen review manifest: 19/19 SHA-256 inputs verified by the deterministic
  review-manifest gate.
- Neutral external-reviewer shortlist prepared; no outreach or approval has
  occurred.
- Governance: structurally passed with status `yellow`; required files present;
  historical duplicate groups retained and deduplicated views generated.

The status fields in the theorem and novelty registries remain unchanged:
mathematical statements are conditional on their recorded assumptions,
`NOVELTY_NOT_ESTABLISHED`, and `PENDING_HUMAN_REVIEW`.

## Blocking completion audit

The repository can no longer remove the remaining blockers by internal edits
without changing the meaning of the objective. Requirement 1 needs an
attributable human mathematical review; requirement 2 needs an independent
expert prior-art determination. The repository has a frozen, hash-verified
packet and a neutral candidate shortlist, but no reviewer response. Requirement
6 is intentionally limited because no technology-superiority claim is being
made. Until the external review state changes, the project must remain an
internal draft and must not be marked complete or release-ready.

## Addendum — shared-DAG validation, 2026-08-09

The application track now also contains a finite shared-subexpression DAG
backend and an exploratory held-out probe. The global domain certificate held
on 140/140 matched seed/budget cases, but its rank allocator beat uniform on
only 15.7% of sup-error comparisons and had mean reduction `-0.007571`.
This strengthens certificate-soundness evidence while confirming that the
technology-impact requirement remains unsatisfied: no universal allocator or
industrial-superiority claim is supported.

The theory track also now has an exact constant for the nonnegative
first-order DAG channel envelope: all source-to-root path products are summed
with multiplicity. This is a genuine sharpness result for the declared
envelope, while full multilinear DAG sharpness remains unverified.

The theory now also closes the asymptotic constant `4` for one fixed
independent-law shared-diamond multilinear DAG. This improves the DAG
sharpness coverage but does not establish fixed-`eta` or arbitrary-DAG
sharpness.

That result has now been generalized: for every fixed finite independent-law
multilinear DAG in the declared rank-one planar class, the asymptotic constant
is the total projected source-to-root slot-path multiplicity `K(G)`. Fixed-eta
and unbounded-family sharpness remain outside the verified scope.

The witness formula has also been checked with explicitly constructed real
tensor cores on chain, shared-diamond, and repeated-slot DAGs, providing a
numerical implementation check independent of the scalar path-count test.

Finally, the application track now includes a validation-selected,
independent-test matched-tolerance study. The compressed-coordinate evaluator
is algebraically equivalent to projected ambient evaluation; all selected
certificate cases held on the test batch. However, tolerance transfer was
partial and the certificate policies used more contraction units than uniform
on average in the matched pairs. This directly addresses the requested
error/resource tradeoff as a negative/context-dependent result, while leaving
hardware timing, multi-topology generalization, structured networks, and any
technology claim open.
