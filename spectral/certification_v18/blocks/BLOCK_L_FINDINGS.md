# Block L (gauge canonicalization) — v18 findings

Canonicalization via Gram-matrix eigendecomposition now explicitly reports
its regime (`simple_spectrum` / `partially_degenerate` / `fully_degenerate`)
and residual gauge dimensions per cluster, using principal angles (not the
vacuous free-unitary Procrustes block M's development ruled out) to check
stability.

A random reduced tensor's Gram spectrum (n=12, rank=4, seed=0) is simple
and stable under a 1e-9 perturbation (`CANONICAL`/`CANONICAL_MODULO_RESIDUAL_GAUGE`,
max principal angle < 1e-2). A deliberately constructed exactly-degenerate
Gram matrix (eigenvalues 2,1,1) is correctly detected as
`partially_degenerate` with a 2-dimensional residual gauge. The decisive
test: an ARBITRARY (not infinitesimal) unitary rotation applied within
that 2-dim degenerate eigenspace produces a basis that differs from the
original by more than 0.1 in Frobenius norm pointwise, yet principal
angles between the two bases are < 1e-8 — i.e. they are exactly the same
subspace despite looking completely different vector-by-vector. This is
the concrete demonstration of what "canonical only modulo residual gauge"
means, and confirms the comparison tool correctly reports "same subspace"
rather than either falsely claiming instability (pointwise difference) or
silently picking one arbitrary representative and calling it canonical.

## Gate status

`gauge_gate`: `EXACT_CERTIFICATE` for the residual-gauge detection logic
itself (exact eigenvalue-degeneracy construction, exact principal-angle
identity check); `EMPIRICAL_SCREENING_PASS` for the simple-spectrum
stability claim (single seed, float64, small perturbation only).
