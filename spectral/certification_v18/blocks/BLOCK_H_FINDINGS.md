# Block H (associator bound, constant-2 sharpness) — v18 findings

The constant "2" in `||A(x,y,z)|| <= 2 * M_hat^2 * ||x|| ||y|| ||z||` comes
from a plain triangle inequality on the associator's two terms
`T1=(x o y) o z`, `T2=x o (y o z)` — it assumes worst-case anti-alignment
(`cos(T1,T2) = -1`).

Empirical result (n=16, rank=4, cp_rank=4, seed=0, 300 random + 200
adversarial-gradient-ascent trials on a random `CyclicCPProduct` instance):
`M_hat` (adversarially-refined operator-norm estimate) = 0.535;
**max observed ratio = 0.452** against the triangle bound of 2.0 — a gap of
**1.55**. Mean `cos(T1,T2)` across trials = 0.067 (T1, T2 are close to
uncorrelated for this random law, not anti-aligned as the bound's worst
case assumes).

**Verdict: `CONSTANT_2_NOT_SHARP_TIGHTER_BOUND_AVAILABLE`.** For this
family of randomly-initialized cyclic CP laws, the constant 2 is a valid
but very loose upper bound; adversarial search across 500 total (random +
gradient-ascent) trials never got past 0.452. This does not prove a
universal tighter constant (that would need an analytic argument, which is
Track T territory and out of scope here per the deferred-Track-T
decision) — it is an empirical, adversarially-searched statement about
this law family and this ambient dimension, reported as such.

The mission's `2 rho M L` tree-bound notation belongs to the deferred
Track T (projected n-ary tree mathematics); this block operationalizes the
analogous "constant 2" question for the A-N audit's own associator
diagnostic using the law's own operator-norm estimate `M_hat`, not
Track T's `rho`/`L`, and does not claim to resolve Track T's own open
sharpness questions.

The Pythagorean identity `projected_norm^2 + normal_norm^2 = ambient_norm^2`
(orthogonal decomposition via `P` and `I-P`) is verified to 1e-8 relative
error — an exact algebraic sanity check, not an empirical claim.

## Gate status

`algebra_gate` contribution: `EMPIRICAL_SCREENING_PASS` for "the triangle
bound holds" (never violated in 500 trials, as required — a violation
would refute the bound, not just its sharpness) and
`STRUCTURAL_IDENTITY_PASS` for the Pythagorean ambient/projected/normal
split (exact, no fitting).
