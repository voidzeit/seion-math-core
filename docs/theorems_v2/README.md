# Structure-preserving reduction v2

This directory contains the proof ledger for the research-v2 branch. The
results are stated for finite-dimensional Hilbert spaces and make every
projection and norm convention explicit.

The status labels are intentionally conservative:

- ESTABLISHED_KNOWN_RESULT: a standard restriction, operadic, or spectral
  perturbation fact. It is included to make the implementation auditable, not
  claimed as a new theorem.
- PROVED_AUXILIARY: proved here in the finite-dimensional model and useful for
  the experiments, but not by itself a novelty claim.
- COUNTEREXAMPLE: a registered exact construction showing that a hypothesis
  cannot be silently removed.
- OPEN_OR_BLOCKED: a proposed extension for which this repository does not yet
  provide a proof.

The main conclusion of the v2 audit is that the exact reduction and snapping
statements are standard consequences of subalgebra restriction and spectral
projector perturbation theory. The explicit tree recurrence is a useful
computable certificate, but it is not advertised as a major novelty without a
more complete comparison against the literature.

Files:

- exact_reduction.md: exact typed reduction and partial composition.
- approximate_closure.md: explicit tree recurrence and polynomial residual
  corollaries.
- spectral_snapping.md: gap-dependent snapping bound and no-gap example.
- polynomial_identities.md: inheritance of operadic identities.
