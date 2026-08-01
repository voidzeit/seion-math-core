# Priority A audit — finite canonical core

Scope: typed n-ary laws, exact restriction/projector closure, reduced laws,
composition trees, nodewise/mixed-mask/path-sum error certificates,
telescoping order, signed forests — the `research_v3` track, since it is the
most mature and the one `claims/scope_registry_v4.yaml` marks
`ACTIVE_RESEARCH_TRACK`.

Method: read `claims/theorem_registry.yaml` (v1/v2/v3), `claims/claims_registry.yaml`,
`claims/claim_evidence_matrix_v3.csv`, `claims/theorem_dependency_matrix_v3.csv`,
`docs/theorems_v3/`, the referenced modules in `src/seion_core/research_v3/`
and `src/seion_core/projectors/`, and the corresponding tests. Ran
`pytest tests/research_v3 -q` directly (30 passed, no skips/xfails).

## Findings table

| ID | Claim | Registry status | Evidence found | Verdict |
|---|---|---|---|---|
| THM_V3_ROOT_ERROR_ORTHOGONALITY | E_amb²=E_proj²+E_norm², E_red=E_proj | PROVED_UNDER_ASSUMPTIONS | Exact Hilbert-space orthogonality argument; `projected_evaluation.py:71-96` computes all four errors, checked ≈0 in `tests/research_v3/unit/test_evaluation.py` | Matches — genuine identity under the stated Hilbert-space assumptions |
| THM_V3_EXACT_SUBSET_EXPANSION | Δv = local residual + sum over nonempty child-error subsets | PROVED | Pure multilinear algebra, no inequality; `error_expansion.py:34-75`, symbolic test in `tests/research_v3/symbolic/test_error_expansion.py` | Matches — fair to label PROVED, it's an algebraic identity |
| THM_V3_HOMOGENEOUS_AMBIENT_K | E_amb ≤ k·ρ·M^(k−1)·L | PROVED_UNDER_ASSUMPTIONS; sharpness explicitly `OPEN_AT_FIXED_ETA` | Induction proof matches `certificates.py:358-363` | Matches, honestly hedged |
| THM_V3_PROJECTED_ROOT_K_MINUS_ONE | E_proj = E_red ≤ (k−1)·ρ·M^(k−1)·L | PROVED_UNDER_ASSUMPTIONS; sharpness `CERTIFIED_UPPER_BOUND_NOT_FIXED_ETA_OPTIMALITY` | Same induction; `certificates.py:366-375`; regression-tested against a rotation extremizer over all 196 binary tree shapes for k=1..6 | Matches — the best-evidenced claim in the set |
| THM_V3_OPTIMAL_TELESCOPING_ORDER | Sign-partitioned ratio order minimizes the scalar telescoping certificate | PROVED_UNDER_ASSUMPTIONS | Standard adjacent-exchange argument, `telescoping_order.py`; brute-force validator to arity 7/8 | Matches |
| THM_V3_NODEWISE_MIXED_CERTIFICATE | Five mixed-mask bounds computable in polynomial subset-mask time | PROVED_UNDER_ASSUMPTIONS | `certificates.py::certify_tree`; tested against observed rotation-family errors | Matches |
| THM_V3_NODEWISE_PATH_SUM | Path-sum decomposition drops the root source under projection | PROVED_UNDER_ASSUMPTIONS | `_propagate_contributions`; test asserts root excluded from `projected_contributions` | Matches |
| COR_V3_PROJECTED_TERNARY_ASSOCIATOR_TWO | Projected 5-input ternary associator bounded by 2ρML | PROVED_UNDER_ASSUMPTIONS; sharpness OPEN | Arithmetic corollary of the k−1 theorem; see finding 1 below | **Weakly evidenced — flagged** |

Sharpness/optimality language was checked across the whole registry: no
instance was found where a constant is called optimal without a matching
lower-bound construction. `CLM_V3_007`/`CLM_V3_008` (lower-bound
constructions) are correctly labeled `CERTIFIED_LOWER_BOUND` /
`EMPIRICAL_LOWER_BOUND`, never "optimal."

## Concrete mismatch found

**Finding 1 — evidence-matrix citation overstates what its cited test checks.**

`COR_V3_PROJECTED_TERNARY_ASSOCIATOR_TWO` (`claims/theorem_registry_v3.yaml:96-108`)
is the only v3 theorem with no `tests:` key. `claims/claim_evidence_matrix_v3.csv`
(row `CLM_V3_009`) nonetheless cites `tests/research_v3/unit/test_forests_and_cp_budget.py`
as its "numerical_or_exact_evidence." Reading that file:
`test_ternary_associator_has_two_five_input_trees` (lines 16-19) only checks
that the forest has 2 terms of 5 leaves each — it never calls
`triangle_certificate` or `certify_tree`, and never checks the constant "2"
against anything. `triangle_certificate` (`polynomial_forests.py:87-97`) is
called from no test file in the repository. The constant is correct by hand
arithmetic (two copies of the already-proved k−1 bound at k=2, so
2·ρ·M·L) — this is not a false claim — but the evidence-matrix row cites a
test as support that does not in fact exercise the number.

**Recommended fix** (not applied by this audit — advisory only): either add
a direct numerical test that calls `triangle_certificate`/`certify_tree` on
the two five-leaf trees and checks the value 2ρML, or correct the evidence
matrix to cite "arithmetic corollary of THM_V3_PROJECTED_ROOT_K_MINUS_ONE"
rather than a test file.

## Secondary, low-severity observation

`theorem_dependency_matrix_v3.csv` marks dependency edges with a "PROVED"
status column that just restates the dependency's own registry status
rather than certifying the edge itself (e.g. row 4,
`THM_V3_HOMOGENEOUS_AMBIENT_K → THM_V3_EXACT_SUBSET_EXPANSION`). Harmless
bookkeeping, not a mismatch — flagged for completeness only.

## Bottom line

The v3 finite-canonical-core claims are unusually well-hedged, and in eight
of nine checked claims the evidence matches the stated status exactly,
including a genuinely strong numerical stress test (196 tree shapes,
k=1..6) behind the strongest claim. The one gap (finding 1) is a citation
accuracy issue, not a false theorem.
