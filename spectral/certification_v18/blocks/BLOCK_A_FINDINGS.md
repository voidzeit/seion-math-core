# Block A (projector validity) — v18 findings

`certify_projector` checks idempotence, self-adjointness, rank (trace), and
eigenvalue clustering at {0,1} for `P = U U*`. All four hold to machine
precision for any orthonormal `U` (5 random seeds tested, plus an exact
n=2 hand-computable case at tolerance 1e-14) — confirmed in
`test_block_a.py`. A perturbation sweep (`perturbation_stability_sweep`)
confirms QR re-orthonormalization absorbs any input perturbation, so these
residuals stay near machine epsilon regardless of how `U` was produced. A
negative control (real transpose instead of conjugate transpose) is
confirmed broken (self-adjointness residual > 1e-6), so the check is not
vacuous.

**Non-implication, enforced in code, not just prose**: `certify_projector`
never returns a status above `TypedStatus.STRUCTURAL_IDENTITY_PASS`. This
is deliberate — idempotence/self-adjointness of `P=UU*` is a fact about
the QR construction, true for any orthonormal `U` whatsoever, and says
nothing about whether the r-dimensional subspace `U` happens to span is
scientifically meaningful (that question belongs to whichever block
supplies the training objective that shaped `U`, e.g. blocks B, G, H, N).

## Gate status

`projector_gate` (shared with block D): `STRUCTURAL_IDENTITY_PASS` for the
construction claim. This block makes no claim about learned-subspace
relevance and none should be inferred from it.
