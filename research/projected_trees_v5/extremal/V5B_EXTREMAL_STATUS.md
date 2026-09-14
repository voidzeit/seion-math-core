# V5-B — fixed-eta extremal tightening

## Scope

V5-B separates the exact one-variable optimization exposed by the V5-A
construction from the unresolved global tree problem. The declared V5-A
class is real, binary, rank-one, orthogonally projected, and independently
parameterized at each internal node.

## Closed scalar result

For

\[
  f(q)=2Mq\sqrt{M^2-q^2},\qquad 0\le q\le \rho,
\]

calculus gives the unconstrained maximizer `q=M/sqrt(2)`. Therefore the
family optimizer is

\[
  q_*=\min(\rho,M/\sqrt2).
\]

With `rho=eta M`, the normalized V5-A lower curve is

\[
L_3(\eta)=
\begin{cases}
2\sqrt{1-\eta^2}, & 0<\eta\le1/\sqrt2,\\
1/\eta, & 1/\sqrt2<\eta\le1.
\end{cases}
\]

This is an exact optimization of the declared witness family and hence a
`CERTIFIED_LOWER_BOUND` for the independent-law `k=3` constants. It is not a
global fixed-eta sharpness theorem.

## Asymptotic consequence

The universal projected-root theorem supplies `C_3,ind^P(eta) <= 2`, while
the witness supplies `C_3,ind^P(eta) >= L_3(eta)`. Since

\[
  \lim_{\eta\downarrow0}L_3(\eta)=2,
\]

the squeeze theorem gives

\[
  \lim_{\eta\downarrow0}C_{3,\mathrm{ind}}^P(\eta)=2.
\]

This closes asymptotic sharpness at `eta -> 0` for the declared class, while
fixed-eta global sharpness remains open.

## Conditional upper-bound attempt

The candidate upper envelope is the same piecewise curve if every admissible
candidate can be reduced to scalars `A,B` satisfying

\[
  E_{\rm proj}\le2AB,\qquad A^2+B^2\le M^2,qquad 0\le A\le\rho.
\]

The repository records this as
`CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION`; it is not registered as a global
upper bound. Proving these reduction inequalities for the full declared class
is the next theorem-level target.

## Repeated/shared-law `k=2`

The broader same-map class is now closed at the universal value. With the
single repeated law

```text
mu(x,y) = M*x1*y0*e0 + rho*x0*y0*e1,
```

the two-node chain attains `E_proj=rho*M` for every `0<eta<=1`. Combined
with the universal upper bound, this gives

\[
  C_{2,\mathrm{same\ law}}^P(\eta)=1.
\]

This does not change the narrower historical gated-planar result: its exact
projected error is `eta^2` and its normalized value is `eta`. Thus the
remaining open problem is restricted repeated-law subclasses (for example,
the gated-planar family), not the explicitly declared same-map class above.

## Superseded: unconditional k=3 upper envelope (2026-08-08 theorem-closure campaign)

The "conditional upper-bound attempt" above is **superseded**. Its stated
assumptions (`E_proj<=2*A*B`, `A^2+B^2<=M^2`) were never proved and are
dimensionally inconsistent with the actual witness value
`2*M*q*sqrt(M^2-q^2)` (missing a factor of `M`). A correct, unconditional
proof is now available:

```text
U_3(eta) = 1 + sqrt(1-eta^2),   0 < eta <= eta_star
U_3(eta) = sqrt(1+eta^2)/eta,   eta_star < eta <= 1
eta_star = sqrt((sqrt(5)-1)/2) ~= 0.786151   (both branches equal the golden ratio there)
```

proved directly from the exact local-error telescoping identity plus a
Pythagorean coupling between the two propagated-error terms at the first
internal node (`research/math_closure/k3/general_upper_envelope.tex`,
`src/seion_core/research_v5/k3_upper_bound.py`). It applies unconditionally
(no rank-one restriction, arbitrary dimension/rank) and identically to both
chain and branching topologies. `U_3(eta)<2` strictly for every `eta>0`;
`U_3(1)=sqrt(2)~=1.41421`, a 29% reduction from the trivial bound.

```text
L3(eta) <= C_3,ind^P(eta) <= U_3(eta) < 2   for every eta in (0,1]
```

The gap narrowed substantially (e.g. at `eta=1`: relative gap `50%->29%`;
at `eta=0.9`: `44%->26%`) but did **not** close. Fixed-eta global sharpness
for k=3 remains `OPEN_WITH_CERTIFIED_GAP`.

## Reproducible execution

Run:

```powershell
python scripts/run_projected_graphs_v5b.py
pytest -q tests/research_v5_test_v5b_extremal.py
```

The generated JSON contains the source commit, transition regimes, analytic
values, repeated-law bands, and a finite grid sanity check. The grid check is
diagnostic only and does not replace the calculus argument.

## Current theorem-closure correction — 2026-08-09

The lower-witness and M9 sections above are preserved as provenance. The
independent-law binary `k=3` fixed-eta problem is now closed by the subsequent
M14/M15 proofs: both chain and branching constants equal `W_3(eta)`. The
M20 extends this exact closure to every finite `k=3` arity profile by reducing
extra leaf slots to effective linear/bilinear laws and embedding the M14/M15
witnesses. The remaining fixed-eta frontier is same-law/gated subclasses and
independent-law trees with `k>=4`; the historical lower curves remain valid
constructions but are no longer the best available global description for the
closed `k=3` classes.

The broader gated-planar boundary is now split explicitly. M17 closes the
contractive repeated law `mu_A(x,y)=A*x*<e0,y>` with fixed gate and active
planar contraction at normalized constant `1`, using the exact identity
`P*A*(I-P)*A*e0` and an off-diagonal witness. Variable-gate, arbitrary-leaf,
and non-planar shared-law variants remain open.
