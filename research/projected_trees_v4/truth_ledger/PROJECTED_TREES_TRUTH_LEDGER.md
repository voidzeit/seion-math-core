# Projected Trees Truth Ledger

Status: P0 baseline frozen and reproduced locally; P1–P5 and P6A–P7A
implemented as bounded v4 extensions.

Observed on 2026-08-08 from branch `campaign/gate13-closeout` at commit
`c491c032579b9239f2c7216801d174f86c11c4de`.

## Scope

This ledger covers the finite-dimensional projected-tree theory only:
finite typed ordered trees, real or complex Hilbert spaces, orthogonal
projectors, bounded multilinear laws, ambient evaluation, and recursively
projected evaluation. It does not transfer claims to KGE, SEION scoring,
continuum limits, infinite trees, or general neural networks.

## Epistemic statuses

- `PROVED`: exact algebraic identity or proof valid in its declared scope.
- `PROVED_UNDER_ASSUMPTIONS`: theorem conditional on explicit hypotheses.
- `EXACT_CONSTRUCTION`: exact formula for a restricted admissible family.
- `CERTIFIED_LOWER_BOUND`: validated construction; not a supremum proof.
- `CERTIFIED_UPPER_BOUND`: rigorous upper bound; not fixed-parameter sharpness.
- `NUMERICAL_CONJECTURE`: computational evidence only.
- `DISPROVED`: counterexample to a statement outside its hypotheses.
- `OPEN`: no matching theorem/construction currently closes the question.
- `NOVELTY_NOT_ESTABLISHED`: mathematically supported but not a novelty claim.

## Current P0 reproduction

| Command | Result | Authority |
|---|---:|---|
| `python -m pytest tests/research_v3 -q` | 30 passed | current source/tests |
| `python research/math_closure/k2/exact_examples/chain_gated_rotation_eta_squared.py` | passed | exact restricted construction |
| `python research/math_closure/k3/certificates/chain_and_branching_closed_forms.py` | passed | exact restricted constructions |

The prior v3 technical audit remains historical evidence: 69 tests, 15,493
unique scientific instances, 81,445 tree occurrences, 80,870 unique tree
hashes, 1,530 leakage masks, zero bound-violation margin, and maximum recorded
CPU/GPU discrepancy `1.922112502494855e-08`. It was not re-executed as the
full 15-stage campaign in this P0 pass.

## Exact and conditional mathematical results

| ID | Statement | Status | Evidence |
|---|---|---|---|
| PT-001 | `E_amb^2 = E_proj^2 + E_normal^2` and `E_red = E_proj` at the root | `PROVED_UNDER_ASSUMPTIONS` | `docs/theorems_v3/typed_model.md`; `src/seion_core/research_v3/projected_evaluation.py` |
| PT-002 | Exact local subset expansion: local normal residual plus one term for every nonempty erroneous-child subset | `PROVED` | `docs/theorems_v3/exact_subset_expansion.md`; `src/seion_core/research_v3/error_expansion.py` |
| PT-003 | Ambient universal bound `E_amb <= k rho M^(k-1) L_T` | `CERTIFIED_UPPER_BOUND` | `docs/theorems_v3/homogeneous_constants.md` |
| PT-004 | Projected/reduced universal bound `E_proj = E_red <= (k-1) rho M^(k-1) L_T` | `CERTIFIED_UPPER_BOUND` | `docs/theorems_v3/homogeneous_constants.md`; `tests/research_v3/regression/test_projected_k_minus_one.py` |
| PT-005 | Root local residual is removed exactly by the final projection | `PROVED` | `docs/theorems_v3/exact_subset_expansion.md` |
| PT-006 | Sign-partitioned ratio ordering minimizes the declared scalar telescoping certificate | `PROVED_UNDER_ASSUMPTIONS` | `docs/theorems_v3/telescoping_order.md`; `src/seion_core/research_v3/telescoping_order.py` |
| PT-007 | Mixed-mask dynamic program is a valid typed-tree certificate with `O(|T| 3^a_max + |T| a_max log a_max)` declared complexity | `PROVED_UNDER_ASSUMPTIONS` | `docs/theorems_v3/nodewise_certificates.md` |
| PT-008 | Residual-source path-sum certificate is valid for the declared telescoping gains | `PROVED_UNDER_ASSUMPTIONS` | `docs/theorems_v3/nodewise_certificates.md` |
| PT-009 | Representation and projection/closure error can be separated under the declared operator perturbation hypotheses | `PROVED_UNDER_ASSUMPTIONS` | `docs/theorems_v3/cp_projection_budget.md` |
| PT-010 | Projected five-input ternary associator has triangle coefficient `2` under the declared conventions | `CERTIFIED_UPPER_BOUND` | `docs/theorems_v3/signed_forests.md`; `claims/theorem_registry_v3.yaml` |
| PT-011 | Scalar DAG recurrence admits an `O(|V|+|E|)` source-resolved reverse dynamic program without tree unrolling | `PROVED_UNDER_ASSUMPTIONS` | `research/projected_trees_v4/dag/proof/dag_native_source_resolved.md`; `src/seion_core/research_v4/dag_certificate.py` |
| PT-012 | First-order source-aware vector DAG coefficients aggregate all paths carrying the same source before norm; the resulting bound is no larger than the pathwise triangle certificate | `PROVED_UNDER_ASSUMPTIONS` | `research/projected_trees_v4/dag/source_aware/proof/P6A_first_order_source_aware.md`; `src/seion_core/research_v4/source_aware_dag.py`; `tests/research_v4/test_source_aware.py` |
| PT-013 | First-order signed source aggregation for a signed forest is no larger than the treewise triangle certificate and can be strictly smaller | `PROVED_UNDER_ASSUMPTIONS` | `research/projected_trees_v4/cancellation/associator/P7A_signed_source_certificate.md`; `src/seion_core/research_v4/signed_certificate.py`; `tests/research_v4/test_source_aware.py` |
| PT-014 | Finite multilinear DAG errors admit an exact finite source polynomial indexed by multi-indices; repeated source use is preserved and order truncation has an omitted-term norm bound | `PROVED_UNDER_ASSUMPTIONS` | `research/projected_trees_v4/dag/source_aware/proof/P6B_exact_source_polynomial.md`; `src/seion_core/research_v4/higher_order_source_polynomial.py`; `tests/research_v4/test_higher_order_source_polynomial.py` |

## Restricted exact constructions

| ID | Class | Exact result | Status | Evidence |
|---|---|---|---|---|
| PT-K2-B | Homogeneous k=2 chain, gated planar rotation | `E_proj(eta) = eta^2`, independent of tested dimension/rank class | `EXACT_CONSTRUCTION` | `research/math_closure/k2/classification_theorem.tex` |
| PT-K2-B-SAT | Same class | Saturates the universal k-1 bound only at `eta=1` | `PROVED_UNDER_ASSUMPTIONS` | `research/math_closure/k2/status.md` |
| PT-K3-CHAIN | k=3 chain, same restricted law | `E_proj(eta)=3 eta^2 sqrt(1-eta^2)`; best ratio `3/4` at `eta=1/sqrt(2)` | `EXACT_CONSTRUCTION` | `research/math_closure/k3/topology_chain.tex` |
| PT-K3-BRANCH | k=3 branching, same restricted law | `E_proj(eta)=eta^2 sqrt(1-eta^2)`; best ratio `1/4` at `eta=1/sqrt(2)` | `EXACT_CONSTRUCTION` | `research/math_closure/k3/topology_branching.tex` |

These formulas are exact for their restricted admissible families. They do
not determine the global fixed-eta extremal constants.

## Counterexamples and boundary results

| ID | Result | Status | Evidence |
|---|---|---|---|
| PT-CE-001 | Removing exact invariance can break composition/reduction commutation | `DISPROVED` | `claims/counterexample_registry_v2.yaml`; `artifacts/counterexamples_v2/no_invariance_composition.json` |
| PT-CE-002 | Removing a positive spectral gap can make snapping discontinuous under vanishing perturbations | `DISPROVED` | `claims/counterexample_registry_v2.yaml`; `artifacts/counterexamples_v2/spectral_gap_sweep.json` |
| PT-CE-003 | The named general six-term GJI identity is not universally zero; collinear-leaf subcase is separately proved zero | `DISPROVED` / `PROVED` by subcase | `research/math_closure/gji/` |
| PT-CE-004 | Historical duplicate run records are not independent scientific instances | `DISPROVED` as an aggregation assumption | `artifacts/index/run_index_deduplicated.csv` |

## Open theorem targets

| ID | Question | Status | Current boundary |
|---|---|---|---|
| PT-O-001 | Exact fixed-eta projected constant `C_T^P(eta)` for general k=2 | `OPEN` | Universal upper bound exists; no global matching construction/theorem |
| PT-O-002 | Whether dimension 2/rank 1 is universally sufficient for k=2 extremizers | `OPEN` | Restricted planar family is not a dimension-reduction theorem |
| PT-O-003 | General k=3 sharpness by topology, dimension, rank, field, and repeated-map policy | `OPEN` | Chain/branching restricted forms do not close class A |
| PT-O-004 | Exact nonlinear cancellation-aware constants for associator, Jacobiator, Filippov, and general GJI | `OPEN` | P7A closes only the first-order signed-source inequality; nonlinear sharp constants remain open |
| PT-O-005 | Scalable higher-order/correlation-aware vector DAG source expansion without tree unrolling | `OPEN` | P6B closes the exact finite polynomial layer for small declared DAGs; scalable tail envelopes and broader correlation theory remain open |
| PT-O-006 | Scalable shared-source/correlation-aware provenance polynomial for DAGs | `OPEN` | P6B exact finite multi-index propagation is implemented; scalable provenance compression remains open |
| PT-O-007 | Validated multilinear spectral/operator norm enclosures tighter than Frobenius fallback | `OPEN` | Existing numerical searches are lower-bound/conjecture engines |
| PT-O-008 | Universal dominance ordering among nodewise, pathwise, mixed-mask, and telescoping certificates | `OPEN` | Current documents explicitly avoid a universal dominance claim |
| PT-O-009 | Nonlinear Lipschitz envelope for LayerNorm, gates, top-k, and neural modules | `OPEN` | Outside the finite multilinear core theorem scope |
| PT-O-010 | Theorem-level novelty beyond standard finite-dimensional restriction and perturbation consequences | `NOVELTY_NOT_ESTABLISHED` | Independent human and theorem-to-theorem review pending |

## P0 conclusion

The baseline is technically reproducible and mathematically coherent in its
declared finite typed-tree scope. The strongest current results are the
projected-root `(k-1)` upper bound plus exact local expansion, the scalar
`O(|V|+|E|)` DAG recurrence, the P6A first-order source-aware vector
certificate, and the P7A first-order signed-source certificate. Fixed-eta
sharpness, dimension/rank universality, higher-order DAG provenance, and
nonlinear cancellation-aware constants remain open. No optimizer output or
finite atlas row is promoted to a sharpness theorem.

## Preservation boundary

Gate 13.5, Gate 14A, KGE artifacts, historical runs, failed runs, and prior
paper claims are not rewritten by this ledger.
