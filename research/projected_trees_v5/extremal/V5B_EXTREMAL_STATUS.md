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

The currently certified band is

\[
  \eta\le C_{2,\mathrm{rep}}^P(\eta)\le1.
\]

The lower bound comes from the known repeated gated-planar construction,
whose exact projected error is `eta^2` and whose normalized value is `eta`.
The fixed-eta constant remains `OPEN_FIXED_ETA_SHARPNESS`.

## Reproducible execution

Run:

```powershell
python scripts/run_projected_graphs_v5b.py
pytest -q tests/research_v5_test_v5b_extremal.py
```

The generated JSON contains the source commit, transition regimes, analytic
values, repeated-law bands, and a finite grid sanity check. The grid check is
diagnostic only and does not replace the calculus argument.
