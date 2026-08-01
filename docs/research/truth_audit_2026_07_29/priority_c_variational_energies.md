# Priority C audit — variational energies (mission §1.18)

This is the most substantive finding of the second audit pass. Unlike
kernels/operators/multiscale (honestly scoped, just undertested), this
track has a real, unguarded structural gap.

## Inventory (`src/seion_core/variational/energies.py:28-40`)

All energies are defined only inside `energy_components()` — no
standalone `E_*` functions exist elsewhere in `src/`.

| Component | Computation | Classification |
|---|---|---|
| `assoc` | `‖five_input_associator(...)‖²` | Diagnostic-only |
| `cyclic` | `cyclic_defect(law, sample[:3])` | Diagnostic-only |
| `closure` | `closure_leakage(law, projector, samples)` | **Trainable** — the only one wired into an optimizer |
| `gji` | hardcoded `0.0` | **Not implemented — stub** |
| `fi` | hardcoded `0.0` | **Not implemented — stub** |
| `regularity` | `‖law.tensor.ravel()‖²` | Diagnostic-only |
| `projector` | `projector.diagnostics()["idempotence_error"]` | Diagnostic/certificate metric |

`total_energy()` (`energies.py:43-45`) is a weighted sum via
`EnergyWeights` (defaults: `assoc=1.0, closure=1.0`, all others `0.0`),
but **nothing in the repository ever calls `total_energy`** outside its
own definition — it is dead code, exposed in the public API but unwired
from any optimizer.

## Gradient path — does not exist

`gradients.py` contains only `finite_difference_gradient` and
`gradient_check` (an analytic-vs-numeric comparator) — no analytic or
autodiff gradient is implemented anywhere in `src/`. Critically, **these
two functions are themselves never called** from `optimizers.py`,
`energies.py`, or anywhere else — orphaned utilities.

## The one real optimizer

`optimizers.py:10-31` (`optimize_projector_closure`) is a **zeroth-order
stochastic hill-climb** on the Stiefel manifold: random Gaussian
perturbation, accept-if-better, shrink step on rejection. It optimizes
only `closure_leakage` — never `gji`, `fi`, `regularity`,
`assoc`/`total_energy`. No gradient is computed or used anywhere in the
loop, so it is derivative-free by design; the docstring says exactly
that: "This is an empirical optimizer. It is intentionally not described
as a global minimization result." The registered claim,
`EMP_PROJECTOR_RECOVERY_V1` (`claims/claims_registry.yaml:35-40`, status
`empirical`), is correctly hedged ("no general recovery or superiority
claim is made") and is not undermined by the gradient gap since it never
claimed a gradient-based method.

## Test coverage

**Zero.** No file under `tests/` imports anything from
`seion_core.variational`. `energy_components`, `total_energy`,
`optimize_projector_closure`, `finite_difference_gradient`, and
`gradient_check` are all untested.

## Verdict — how this differs from the mission's named failure mode

Mission §1.18 specifically warns about "an algebraic diagnostic added to a
loss but independent of trainable parameters" — i.e. a structurally-zero
gradient masquerading as a working regularizer. What was found here is
adjacent but distinct and, in one sense, more basic: **no analytic
gradient path exists for any energy at all**, so there is no trained
regularizer to have a zero-gradient bug in the first place. `gji` and `fi`
are literal `0.0` placeholders (not computed-then-discovered-to-be-zero —
simply not implemented), `total_energy`/`EnergyWeights` (the only
mechanism that could make `assoc`/`regularity`/etc. trainable) is
unwired dead code, and the gradient-check utilities that would catch the
mission's exact failure mode are themselves never invoked by anything.

**This is the one place in the repository where this audit recommends not
relying on the code as-is**: if any future work treats `energy_components`
or `total_energy` as a working trainable-regularizer suite (rather than
what they currently are — mostly diagnostic scalars plus one gradient-free
empirical optimizer touching a single term), that would be an unguarded
instance of exactly the failure mode the mission describes. Recommend
either implementing and testing real gradients for the energies intended
to be trainable, or relabeling `gji`/`fi`/`total_energy` explicitly as
unimplemented placeholders in their own docstrings so a future reader
doesn't mistake presence-in-code for functioning machinery.
