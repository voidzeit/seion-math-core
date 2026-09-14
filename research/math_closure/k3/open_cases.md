# M3 — open cases (k=3)

## Current global boundary — 2026-08-09

- **Fixed finite-tree support compression is proved** under the declared typed,
  type-indexed-projector convention. For a one-type binary tree with three
  internal nodes the support dimension is bounded by `20`, or `22` when two
  padding coordinates are required to make the projector proper.
- The independent-law chain and branching constants are now closed exactly by
  M14 and M15, respectively, and both satisfy `C_3^P(eta)<U_3(eta)` for
  `0 < eta <= 1`. The fixed-tree reduction and M10 remain useful provenance,
  but M10 itself is chain-only.
- The rank-one/common-leaf same-law and gated values, fixed-eta
  independent-law sharpness for `k>=4`, and uniform reduction for unbounded
  tree size/arity remain open. M19 closes
  the independent-law asymptotic `k-1` statement for every fixed finite
  ordered rooted topology with arities at least two, and M20 closes the exact
  fixed-eta independent-law constant for every finite `k=3` arity profile.

## Closed this pass

- **Every finite ordered full-binary topology, homogeneous gated-planar law**:
  the exact recursive formula
  `E_proj=|a(T)cos(d(T)theta)-cos(theta)^k|` is now proved and checked for
  all ordered shapes through four internal nodes, independently of finite
  dimension and coordinate-projector rank. The earlier chain and branching
  formulas are special cases. See `gated_rotation_full_binary.tex`.

- **Every finite ordered rooted tree with arity at least two, arity-compatible
  gated law**: the same `a(T),d(T)` recurrence now includes mixed arities;
  see `gated_rotation_general_arity.tex`. This remains a restricted shared
  active-rotation family.

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

- **M19 closes the finite-tree asymptotic frontier**: for every fixed ordered
  rooted topology with arities at least two and `k` internal vertices,
  `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k-1`. It does not give fixed-eta
  equality or a uniform growing-tree limit.

- **Independent-law chain fixed-eta constant** is closed exactly by M14:
  `C_3,ind,chain^P(eta)=W_3(eta)` for every `0<eta<=1`, with an explicit
  two-dimensional rank-one witness.

- **Independent-law branching fixed-eta constant** is closed exactly by M15:
  `C_3,ind,branch^P(eta)=W_3(eta)` for every `0<eta<=1`, using
  nuclear/operator-norm duality and a polar-factor root witness.

- **M20 closes all finite k=3 arity profiles**: after freezing unit leaf
  slots, every three-internal-node tree has only a chain or branching
  internal-child skeleton. M13--M15 provide the upper bound and unit `e0`
  gates embed the matching witnesses, so
  `C_{T,ind}^P(eta)=W_3(eta)` for every finite ordered profile and
  `0<eta<=1`.

- **M21 closes tagged same-law binary k=3**: a single repeated bilinear law
  with finite orthogonal projected leaf tags can be built as a direct sum of
  the M14/M15 blocks. Its chain and branching constants are exactly `W_3`.
  This does not cover rank-one/common-leaf same-law or gated restrictions.

- **M22 closes the high-eta strict same-law chain regime**: with rank-one
  `P=span(e0)`, common unit leaves, and one repeated rotation, fixing leakage
  at `sqrt(2/3)` attains `W_3(eta)` for `eta>=sqrt(2/3)`. The low-eta chain,
  rank-one/common-leaf branching, and broader gated/shared-law cases remain
  open.

- **M23 gives an exact reduction of the remaining strict chain class**: with
  one repeated law, common leaf `e0`, and rank-one `P`, set
  `A(x)=mu(x,e0)`. The projected error is exactly
  `|<e0,A^3 e0>-<e0,A e0>^3|`, and every finite-dimensional contraction `A`
  is realizable by a gated repeated law. This identifies the complete
  operator optimization but does not yet evaluate its low-eta supremum.

- **M11 conditional gap** is superseded for both binary topologies by M13--M15:
  the common `W_3` envelope is unconditional and exact. The result does not
  extend automatically to same-law/gated or arbitrary-tree classes.

- **Neither topology saturates the k=3 universal bound at any $\eta$**
  (best ratios $3/4$ and $1/4$, both $<1$) — unlike k=2's chain, which
  saturates exactly at $\eta=1$ (`research/math_closure/k2/`). Whether
  *some* law/topology saturates the k=3 bound at some $\eta$ remains
  open.
- The topology-wide gated formula is restricted to its declared
  arity-compatible gated-rotation laws and unit `e0` leaves. M19 separately
  closes only the independent-law asymptotic statement for arbitrary finite
  arity profiles; fixed-eta sharpness, same-law/gated classes, and
  non-coordinate projectors remain outside this closure.
- Fixed-eta independent laws, complex-field variants, and non-coordinate
  projectors: not attempted (same scope limits as M2).
- The arbitrary-node-law binary class is closed by the M16 corollary, M20
  extends the independent-law closure to all finite `k=3` arity profiles, and
  M21 closes the tagged same-law binary subclass. The remaining boundary is
  rank-one/common-leaf same-law and gated sharing, fixed-eta independent-law
  trees with `k>=4`, and broader classes beyond the finite-tree asymptotic
  declaration.
