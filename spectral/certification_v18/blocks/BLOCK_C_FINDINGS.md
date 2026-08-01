# Block C (FINITE_BEALS_PROXY) — v18 findings

Renamed explicitly to `FINITE_BEALS_PROXY` per mission section 2C; this
block reports finite nested-commutator Frobenius norms ONLY and makes no
claim about PsiDO membership, microlocal regularity, or any continuum
Beals criterion.

Scaling with dimension (rank=3, order<=2, diag-cosine + shift observables):
max norm grows from 3.02 (n=8) to 4.12 (n=64) — growing but saturating,
not blowing up, over a 8x dimension increase (mild log-like growth, not
tested against a fitted asymptotic form this pass). Scaling with
commutator order: 1.73 (order 0, `= sqrt(rank)` exactly, an algebraic
identity for a rank-3 projector) -> 1.83 (order 1) -> 3.02 (order 2) —
noticeably faster growth at order 2 than order 1.

**Projector-family comparison** (n=16, rank=3): random=3.84,
smooth(low-frequency)=2.85, localized(spatial basis)=2.00,
**adversarially-optimized=4.35**. The adversarial search (gradient ascent
directly maximizing the order-1 commutator sum) beats every hand-picked
family, confirming the reported numbers are not cherry-picked in the
suite's favor — the adversarial control is required by mission section 8
and is verified to actually win here.

## Gate status

`dynamic_explanation_gate` contribution: `NUMERICAL_SANITY_PASS` only — all
values are finite, ordered sensibly (adversarial >= all hand-picked
families), and the block's own non-implications are enforced by never
producing a status stronger than this. No PsiDO/microlocal claim is made
anywhere in this module.
