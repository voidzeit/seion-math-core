# Projected graphs v5 truth ledger

## Baseline

The finite v4 core is frozen at scientific commit
`1f4984ec8e741049789e0035c7a3ba84c86d3f29`. The operational branch later
contains governance-only postflight commit `f88f75bdf3f44407392d6c55dd2affb37d3185ab`.
V5 does not modify `research_projected_trees_v4`, Gate 13.5, Gate 14, KGR, or
historical artifacts.

## V5 theorem target

For the general real binary k=2 chain with independent node laws, define

```text
C_2^P(eta) = sup E_proj / (rho M L),   eta=rho/M.
```

The universal projected-root theorem gives `C_2^P(eta) <= 1`.

## Closed result: independent-law saturation

For every `0 < eta <= 1`, the explicit two-dimensional construction in
`src/seion_core/research_v5/k2_sharpness.py` has:

```text
||mu_inner|| = ||mu_outer|| = M
rho_inner = eta*M
rho_outer = 0
E_proj = eta*M^2 = rho*M.
```

Therefore:

```text
C_2^P(eta) = 1
```

for this declared general class with independent node laws. This does not
contradict the earlier `E_proj=eta^2` result: that result is for the narrower
repeated gated-planar law family, not the general independent-law class.

## Remaining open questions

- repeated-law/shared-map k=2 sharpness;
- higher-arity k=2 sharpness;
- universal dimension/rank reduction;
- k=3 topology-specific global constants;
- globally tight multilinear spectral norms;
- theorem-level novelty.

## Equality/slack conclusion

The simultaneous equality conditions are compatible for independent node laws,
as witnessed by the exact construction. The additional same-law constraint is
not resolved: the repeated-law equality system remains `OPEN`.

## V5-A: independent-law k=3 lower witnesses

The chain and branching constructions in
`src/seion_core/research_v5/k3_independent_candidates.py` are certified lower
witnesses, not global sharpness results. With a defect budget `rho=eta*M`,
they choose

```text
q = min(rho, M/sqrt(2))
E_proj = 2*M*q*sqrt(M^2-q^2)
```

For `0 < eta <= 1/sqrt(2)`, the realized defect equals the budget and the
normalized lower bound is `2*sqrt(1-eta^2)`. For larger eta, the witness uses
the budget maximum of its family and reports the realized defect separately.
The global independent-law constants for `k=3` remain `OPEN`.

## V5-B: scalar extremal reduction and asymptotic sharpness

The V5-A family reduces to the exact scalar problem

```text
maximize 2*M*q*sqrt(M^2-q^2)
subject to 0 <= q <= rho=eta*M.
```

The exact scalar optimizer is `q*=min(rho,M/sqrt(2))`, yielding the
normalized lower curve

```text
L3(eta) = 2*sqrt(1-eta^2),  0 < eta <= 1/sqrt(2)
L3(eta) = 1/eta,              1/sqrt(2) < eta <= 1.
```

This is a certified lower bound for the declared V5-A witness family. It is
not a fixed-eta global upper bound. The proposed matching upper envelope is
recorded only conditionally on proving a universal scalar reduction of the
form `E_proj <= 2*A*B`, `A^2+B^2 <= M^2`, and `A <= rho`.

Combining `L3(eta) <= C_3,ind^P(eta) <= 2` gives the proved asymptotic result

```text
lim_{eta downarrow 0} C_3,ind^P(eta) = 2.
```

The fixed-eta k=3 constant remains `OPEN`.

## V5-B: repeated-law k=2 status

The broader explicitly declared same-map class is now sharp:

```text
C_2,same-law^P(eta) = 1.
```

The same bilinear law `mu(x,y)=M*x1*y0*e0+rho*x0*y0*e1` is used at both
internal nodes and attains `E_proj=rho*M` for every `0<eta<=1`. The earlier
gated-planar repeated-law family remains narrower, with exact projected error
`eta^2` and normalized value `eta`. Sharpness for that restricted subclass
remains open.

## Theorem-closure campaign (2026-08-08): k=2 iff characterization and k=3 upper envelope

Two new theorem-level results close the campaign's two highest-priority
open targets to the extent tractable in a single pass:

1. **k=2 saturation is now characterized, not just witnessed.** For the
   binary k=2 chain (any dimension, any projector rank, laws independent or
   repeated), `E_proj=rho*M*L_T` holds iff three explicit local conditions
   (EQ1: outer-law operator-norm saturation, EQ2: closure-map saturation,
   EQ3: root-projection alignment) hold simultaneously. Proved by an
   elementary chain-of-inequalities argument. Both prior witnesses verified
   as instances; a third, independently constructed witness (not matching
   either prior form) predicted and verified to saturate.
   `research/math_closure/k2/saturation_iff_theorem.tex`.
2. **The k=3 upper bound is now tightened unconditionally.** The
   `CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION` bookkeeping entry above is
   superseded by a proved envelope `U_3(eta)` (chain and branching, any
   dimension/rank), strictly below the trivial bound `2` for every `eta>0`.
   `research/math_closure/k3/general_upper_envelope.tex`.

Fixed-eta k=3 sharpness remains open; the certified gap narrowed but did
not close. See `V5B_EXTREMAL_STATUS.md`'s "Superseded" section for the
exact numbers.

**M10 (same-day follow-up, then revised after review found two errors):
no single configuration attains U_3(eta).** Deriving the equality
conditions of M9 uncovered a genuine structural obstruction, but the
first write-up had two bugs an external review caught: (1) it claimed
`S1 perp S2` from a lemma step that doesn't actually survive an arbitrary
projection -- repaired with a projector-independent self-adjointness
argument giving the weaker, sufficient fact "`S2` is never a nonzero
multiple of `S1`"; (2) it concluded the strict supremum inequality
`C_3,ind^P(eta) < U_3(eta)` from mere non-attainment, which is an invalid
inference (a supremum can be approached without being attained). The
corrected result is `PROVED_NON_ATTAINMENT` only: no single admissible
configuration reaches `U_3(eta)` exactly. Whether the *supremum* itself
is strictly below `U_3(eta)`, or merely unreachable pointwise while still
equal to it in the limit, is now tracked as a separate, explicitly open
question (`OPEN_V5_K3_STRICT_SUPREMUM_GAP`) requiring either a
compactness argument or an explicit quantitative gap -- neither
completed. A separate gradient-based numerical search attempt failed to
even recover the known `L_3(eta)` witness and was discarded as
methodologically unreliable, not as evidence.
`research/math_closure/k3/m10_non_sharpness_of_m9.tex`.

## Conjectural direction

The finite-tree independent-law statement
`C_{T,ind}^P(eta)=k(T)-1` for sufficiently free laws is recorded as an open
conjecture only. No theorem or numerical construction in this repository
establishes it beyond the exact k=2 independent-law class.
