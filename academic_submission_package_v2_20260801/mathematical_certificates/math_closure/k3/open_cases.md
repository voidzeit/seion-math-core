# M3 — open cases (k=3)

## Closed this pass

- **Chain topology, gated-planar-rotation law**: exact closed form
  $E_T^{\mathrm{proj}}(\eta) = 3\eta^2\sqrt{1-\eta^2}$, exact optimal
  point $\eta^\star=1/\sqrt2$, exact best ratio $3/4$ (min relative gap
  $1/4$). `PROVED` for this admissible class.
- **Branching topology, same law**: exact closed form
  $E_T^{\mathrm{proj}}(\eta) = \eta^2\sqrt{1-\eta^2}$, same
  $\eta^\star=1/\sqrt2$, exact best ratio $1/4$ (min relative gap $3/4$).
  `PROVED` for this admissible class.
- Both closed forms **correct and sharpen** (not merely reproduce) the
  prior session's discretely-sampled atlas finding (min relative gap
  $0.350$ at the sampled $\eta=0.5$) — the true continuous minimum gap is
  $1/4$ at $\eta^\star=1/\sqrt2$, a point the discrete grid never tested.
- Confirms **topology-dependence** of the k=3 gap floor: chain is exactly
  3x more efficient than branching for this law family, at the identical
  optimal $\eta$.

## Still open

- **Neither topology saturates the k=3 universal bound at any $\eta$**
  (best ratios $3/4$ and $1/4$, both $<1$) — unlike k=2's chain, which
  saturates exactly at $\eta=1$ (`research/math_closure/k2/`). Whether
  *some* law/topology saturates the k=3 bound at some $\eta$ remains
  open.
- Only 2 of the topologies the mission names were treated (chain,
  branching); a full enumeration of nonisomorphic k=3 topologies
  (mixed arity, heterogeneous laws, more leaves) was not attempted —
  same gap the prior terminal-status document already flagged.
- Independent (non-repeated) laws per node, complex field, and
  non-coordinate projectors: not attempted (same scope limits as M2).
- The general class-A (arbitrary law) upper bound for k=3 remains
  `OPEN_WITH_CERTIFIED_GAP` — this pass only closes specific
  constructions within one law family, not the general extremal problem.
