# software/ — pointer, not a duplicate copy

The full codebase (`src/seion_core/`, `spectral/`, `applications/`,
`scripts/`) is not duplicated in this package — it is the actual source
tree of the integrated repository this package was built from, tracked
in git at the commit recorded in `../provenance.md`. Duplicating it here
would create a second copy that could silently drift from the real
source of truth.

What IS included directly in this package (because it is new,
self-contained work product, not pre-existing infrastructure):

- `scripts/math_closure_m1_gji_symbolic.py` — the M1 GJI verification
  driver (also referenced from `mathematical_certificates/math_closure/gji/`).
- `mathematical_certificates/math_closure/` — every M1-M7 script and its
  output, in full.
- `ai_benchmarks/adaptive_tensor_network/` — the full applied-benchmark
  codebase, in full (src/, experiments/, tests/, results/).

For everything else (the finite-core math library, the spectral
certification suite, governance/CLI code), see the repository itself at
the commit in `provenance.md`.
