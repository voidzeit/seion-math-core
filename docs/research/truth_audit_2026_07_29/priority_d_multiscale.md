# Priority D audit — multiscale structure

Scope: `src/seion_core/multiscale/`, checked specifically against the
mission's sharpest warning here: "Never claim a continuum limit from two
or three finite resolutions."

## What's implemented

All five files are small (9-22 lines):

- `alignment.py:6-11` — `align_bases`: orthogonal Procrustes alignment via
  SVD. Principal-angle/gauge machinery, no limit-taking.
- `transport.py:6-16` — `projector_transport_error`,
  `law_transport_error`: scalar residuals for a *pair* of resolutions
  given explicit restrict/prolong maps. No limit is taken or claimed.
- `persistence.py:6-9` — `basis_persistence`: Frobenius distance between a
  basis and its Procrustes-aligned counterpart — this is the
  "gauge-aligned persistence" object. Tensor/CP-factor/spectral-gap
  persistence variants named in the mission do not appear in this
  directory.
- `resolution.py:6-21` — pure data containers. `ResolutionFamily` carries
  `topology: str = "finite-dimensional operator norm"` and
  `uniform_estimates_available: bool = False` as defaults — an honest
  scaffold that flags its own missing ingredient rather than asserting one.
- `convergence.py:6-12` — `convergence_summary(resolutions, errors)`:
  **if `len(resolutions) < 3` it returns
  `status: "insufficient_sequence_for_limit_claim"` and refuses to fit a
  slope; with ≥3 points it returns `status: "finite_sequence_observation"`**
  — a self-gating disclaimer built directly into the return contract, not
  just prose.

## The conjecture (verbatim)

`claims/conjecture_registry.yaml`:
```
- id: CONJ_MULTISCALE_PERSISTENCE
  statement: "Gauge-aligned finite tensor features may persist across a
    suitable resolution sequence."
  status: CONJECTURE
  blockers: [choice of maps, topology, uniform estimates]
```
Correctly `CONJECTURE`, with blockers naming exactly the missing
ingredients (topology of convergence, uniform bounds) the mission demands
before a continuum claim would be admissible.

## Registry / docs search

Zero hits for "multiscale"/"resolution" combined with a continuum claim
across all three theorem registries and `papers/foundations_v2/main.tex`.
`docs/mathematical_scope.md:11` disclaims a continuum limit outright.

## Tests — the real gap

`tests/convergence/test_convergence.py` exercises
`seion_core.kernels.convergence.loglog_slope` — a **different module** —
not anything under `multiscale/`. A repository-wide grep for
`from seion_core.multiscale` / `import seion_core.multiscale` in `tests/`
returns **zero matches**. `alignment.py`, `persistence.py`,
`resolution.py`, `transport.py`, and `multiscale/convergence.py` itself
are entirely untested.

## Verdict

No red flag found — if anything the module is defensively under-claiming:
`convergence_summary` structurally refuses to label a &lt;3-point sequence
a limit, `uniform_estimates_available` defaults to `False`, and the one
relevant claim is correctly registered as a conjecture with named
blockers. The real gap is test coverage, not overclaim: none of these five
files is exercised by any test, so their numerical *correctness* (as
opposed to their epistemic framing, which is fine) is currently
unverified.
