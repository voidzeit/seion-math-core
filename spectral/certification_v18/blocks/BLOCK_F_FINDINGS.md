# Block F (rigidity) — v18 findings

Three curvature objects, named explicitly and never conflated (n=6,
rank=2, seed=1, closure-residual loss at a random, non-optimal point):

- **Exact Hessian** (`torch.autograd.functional.hessian`): eigenvalues
  range from -0.53 to +0.42 — genuinely indefinite, as expected away from
  a minimum. Cross-checked against a central finite-difference second
  derivative along a random direction: relative error **2.6e-8**.
- **Generalized Gauss-Newton** (`2 J^T J`): eigenvalues range from ~0 to
  0.63, **all non-negative by construction** (confirmed, not assumed) —
  the legacy "hessian_condition_proxy" most likely corresponds to
  something GGN-like, not the true Hessian, precisely because a true
  Hessian at a non-minimum need not be PSD while GGN always is.

**A real methodological catch during development**: the first version of
the closure-residual loss fixed a single column of `U` (`x1 = U @ e_0`) to
build a scalar loss for the gauge-invariance test. That loss is **not**
actually gauge-invariant (`test_gauge_rotation_leaves_loss_invariant`
failed at 0.9% relative difference on the first attempt) — `U @ e_0`
picks out a specific column, which changes under `U -> U@Q`. Fixed by
summing the residual over *every* column of `U` (equivalent to a
Frobenius-norm quantity, which genuinely is invariant under
right-multiplication by a unitary — verified algebraically and
numerically to machine precision, 6e-16, after the fix). The corresponding
infinitesimal-gauge-rotation direction shows Hessian curvature
**-3.5e-18** (numerically exactly flat), confirming identifiability only
modulo gauge, as expected.

**Basin/seed stability — a genuine and notable finding**: three
independent seeds all converge to near-zero closure loss (1e-6 to 1e-7),
but the **pairwise max principal angle between their converged subspaces
is 1.55 rad (~89 degrees) — essentially orthogonal**. The closure
objective alone is severely non-identifying: many very different
subspaces achieve equally good loss. This is consistent with (and adds
independent support to) Block B's finding that the real training regime's
behavior is governed by the *interaction* of many simultaneous objectives,
not any single one in isolation — closure alone does not pin down a
unique (even gauge-equivalent) subspace.

## Gate status

`mathematical_proof_gate` contribution: `EXACT_CERTIFICATE` for the
Hessian/GGN distinction and the gauge-flat-direction identity (both
verified to machine precision); `EMPIRICAL_SCREENING_PASS` only for basin
stability, with the explicit, informative negative result that
single-objective basin stability does NOT hold (subspaces from different
seeds are essentially unrelated).
