# Proof dependencies — math_closure campaign

Tracks what each closed item in `status_registry.yaml` actually depends on
(source code, prior theorems, prior numerical evidence), so a later
session can tell what breaks if an upstream assumption changes.

## M1_gji_six_term_general / M1_gji_six_term_collinear_subcase

- Depends on the exact tree/coefficient definition of
  `ternary_declared_gji()` in
  `src/seion_core/research_v3/polynomial_forests.py` — if that function's
  permutations or signs change, both verdicts must be re-run
  (`scripts/math_closure_m1_gji_symbolic.py` re-derives everything from
  the live function, not a frozen transcription, so re-running is
  sufficient; no manual re-derivation needed).
- Depends on the contraction convention in
  `src/seion_core/research_v3/local_constants.py::TypedLaw.apply`
  (positional `einsum`, no assumed symmetry) — cross-checked directly
  against `exact_evaluation.py::evaluate_ambient_numpy` on concrete data
  before trusting the symbolic result; if that convention changes, the
  cross-check step in `scripts/math_closure_m1_gji_symbolic.py` should be
  rerun to catch the mismatch (it is designed to fail loudly, not
  silently, if the conventions diverge).
- Does NOT depend on any prior theorem in `docs/theorems_v3/` — this is a
  self-contained combinatorial/multilinear-algebra fact about one named
  construction, independent of the k/(k-1) projected-error theorem or any
  other result in this repository.
- The root-cause explanation for the prior session's numerical finding
  depends on `scripts/signed_forest_adversarial_search_v5.py::forest_ratio`
  specifically using `TypedSpace.coordinate("tau", DIMENSION=2,
  PROJECTOR_RANK=1)` — if that script is later changed to use a
  higher-rank projector, its future numerical output would no longer
  match the collinear regime and should stop showing exact zero (a
  falsifiable, checkable consequence of this session's finding).
