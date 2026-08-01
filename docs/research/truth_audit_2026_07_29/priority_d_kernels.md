# Priority D audit — kernel-integrated laws

Scope: `src/seion_core/kernels/` — one of three tracks
`docs/mathematical_scope.md` declares first-class in-scope (alongside the
tree-projection and finite-cohomology tracks already audited).

## What's implemented

Every module is a finite/discrete construction, and every module says so
in its own docstring:

- `integral_kernel.py` — `IntegralKernelDefinition` is pure metadata
  (name/arity/domain/measure strings); `quadrature_apply` (:26-45) is a
  finite tensor contraction over a `FiniteMeasureSpace`. Docstring (:34):
  "This is an exact finite model, not a continuous theorem."
- `discrete_kernel.py` — `DiscreteKernel` wraps a finite array as an
  `NaryLaw`. Docstring (:10): "its finite sum is exact for the declared
  grid."
- `measure_space.py` — `FiniteMeasureSpace`, a finite point/weight pair
  with nonnegativity validation. Docstring (:10): "Exact finite discrete
  measure used as a kernel approximation." No continuum measure object
  exists here at all — sigma-finiteness/measurability machinery is simply
  absent, not silently assumed.
- `boundedness.py` — `hilbert_schmidt_bound` (:6-17) computes a finite
  Frobenius norm times a weight factor. Docstring (:9-10): "It is not an
  assertion about an unbounded continuous operator."
- `convergence.py` — `convergence_errors` and `loglog_slope` (log-log
  regression) — a numerical-observation utility, no error-bound proof, no
  attached theorem.
- `quadrature.py` — `periodic_grid`, `trapezoidal_interval`: standard
  finite quadrature grid constructors.
- `compositions.py` — re-exports `partial_compose`; nothing kernel-
  specific.

## Registry / docs

Zero matches for kernel/Hilbert-Schmidt/quadrature/compact/Sobolev across
`claims/theorem_registry*.yaml` and `docs/theorems*/` — **no theorem is
registered for this track at all**. `claims/claims_registry.yaml` registers
the continuum-limit question as an open conjecture
(`CONJ_CONTINUUM_LIMIT_V1`: "this repository does not prove a general
theorem"), and `docs/open_problems/index.md` item 3 lists "prove
quadrature convergence under explicit kernel regularity assumptions" as
open. `docs/mathematical_scope.md:11` and `docs/architecture.md:3`
independently confirm no continuum claim is made.

## Tests — the real gap

Only `tests/convergence/test_convergence.py` touches this package, and
only `loglog_slope` (validated against a synthetic `1/n**2` sequence).
`DiscreteKernel`, `quadrature_apply`, `hilbert_schmidt_bound`,
`FiniteMeasureSpace`, `periodic_grid`, and `trapezoidal_interval` have
**no test coverage anywhere** in `tests/unit`, `tests/numerical`, or
`tests/property`, despite `kernels/__init__.py` exporting all of them as
public API.

## Verdict

No overclaim, no missing-hypothesis red flag, no finite-to-continuum
upgrade — because the code never asserts a continuum operator-theory
result to begin with; every relevant docstring is self-limiting and the
open-problem docs correctly flag continuum convergence as unproved. The
one real, actionable gap: this is a declared first-class track shipping in
the public API with essentially no test coverage. Recommend adding direct
unit tests for `quadrature_apply`, `hilbert_schmidt_bound`, and
`DiscreteKernel` before treating this track as production-quality, even
though no false mathematical claim currently rides on it.
