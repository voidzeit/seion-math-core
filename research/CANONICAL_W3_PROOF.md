# The constant `W_3` — canonical proof

Date: 2026-08-25. Convention A (`eps_r = 1`, the root projects).
Class: `free` — laws independently selectable per vertex, orthogonal
projectors, unit leaves, any finite dimension, any projector rank.

This file replaces the discovery genealogy M9 → M10 → M13 → M14 → M15 with a
single linear argument. A referee should be able to locate the inequality that
produces `4 - 3 eta^2`, and see why it is sharp, without reading anything else.

```
Reduction Lemma  ->  Geometric Constraint  ->  Scalar Optimization
                 ->  W_3  ->  Equality Conditions  ->  Extremizer
```

Everything not on that line — `U_3`, non-attainment, compactness, support
compression, asymptotics — is genealogy and belongs in appendices. Their only
role in the main argument is that `U_3` is **not** needed: `W_3` is proved
directly and is strictly smaller.

---

## Setup

Ordered binary `k = 3` chain: leaves `a,b -> mu_1 ->` with leaf `c ->
mu_2 ->` with leaf `d -> mu_3` (root). All laws bilinear with
`||mu_v||_op <= M`; orthogonal projectors `P_1, P_2, P_3`; each vertex's own
closure-residual cap `rho = eta M`; unit leaves, so `L_T = 1`.

Write `D_1 = (I-P_1) mu_1(a,b)` and `R_1 = P_1 mu_1(a,b)`, and normalize

```
q = ||D_1|| / M ,      p = ||R_1|| / M .
```

---

## Step 1 — Reduction Lemma (the Gram bound)

> **Lemma.** Let `N` be linear with `||N||_op <= M`, let `u, v` be orthonormal,
> and let `Q` be an orthogonal projector. Put `y = Nv` and `s = ||Qy||`. Then
> ```
> | <Nu, Qy> |  <=  M s sqrt(1 - s^2/M^2) .
> ```

*Proof.* Put `Ntilde = N/M` and `K = Ntilde^* Q Ntilde`, so `0 <= K <= I`.
Restricted to `span{u,v}`, write `K_vv = s^2/M^2` and `K_uu = a`. Positivity of
`K` and of `I - K` gives the two constraints

```
|K_uv|^2 <= a (s/M)^2 ,        |K_uv|^2 <= (1-a)(1 - s^2/M^2) .
```

Maximizing the minimum of the right-hand sides over `0 <= a <= 1` occurs at
`a = 1 - s^2/M^2` and yields the claim. `[]`

**Why this lemma and not operator-norm saturation.** It uses *no* exact
saturation hypothesis. That is precisely what makes the resulting envelope
unconditional, and it is the difference between this argument and the earlier
`U_3` route, which had to bound `||R_1||` and the cross term separately and
therefore lost a factor.

---

## Step 2 — Geometric Constraint

Two constraints, both from orthogonality, and they are the entire geometric
input:

```
(G1)   0 <= q <= eta            closure budget at vertex 1
(G2)   p <= sqrt(1 - q^2)       norm budget: P_1 orthogonal => D_1 _|_ R_1, so
                                ||D_1||^2 + ||R_1||^2 = ||mu_1(a,b)||^2 <= M^2
```

At the second vertex freeze the sibling leaf and set `N(x) = mu_2(x, c)`. With
`u = D_1/||D_1||`, `v = R_1/||R_1||`, `Q = I - P_2`, and

```
x = Nu/M ,     y = Nv/M ,     s = ||Qy|| <= eta ,
```

the exact chain expansion contributes `q x` and `p Q y`. The root map is a
contraction once its sibling leaf is frozen, so the Lemma controls the cross
term and

```
E_T^P / (M^3 L_T)   <=   sqrt( q^2 + p^2 s^2 + 2 q p s sqrt(1 - s^2) )      (*)
```

using `||x|| <= 1` in the first term.

---

## Step 3 — Scalar Optimization

The right side of (*) increases with `p`, so (G2) is tight: `p = sqrt(1-q^2)`.
Substitute `q = sin alpha`, `s = sin beta`. The square becomes

```
f(alpha, beta) = sin^2 a + cos^2 a sin^2 b + 2 sin a cos a sin b cos b
```

and with `u = tan alpha`, `v = tan beta`,

```
              (u+v)^2 + u^2 v^2
f(u,v)  =  -------------------------
             (1 + u^2)(1 + v^2)
```

> **This is the inequality that produces `4 - 3 eta^2`.**
>
> ```
> 4 (1+u^2)(1+v^2)  -  3 [ (u+v)^2 + u^2 v^2 ]
>     =  u^2 v^2 + u^2 + v^2 - 6 u v + 4
>     =  (uv - 2)^2  +  (u - v)^2                                        (SOS)
>     >=  0
> ```

so `f <= 4/3` unconditionally, and the bound is a **sum of two squares** — it
is exact, not an estimate, and it makes the equality analysis immediate.

*(Verification of the identity: `(uv-2)^2 = u^2v^2 - 4uv + 4`, and subtracting
it from `u^2v^2 + u^2 + v^2 - 6uv + 4` leaves `u^2 + v^2 - 2uv = (u-v)^2`.)*

**Two regimes.** The feasible square is `u, v <= tan(arcsin eta)`.

- If `eta <= sqrt(2/3)` then `tan(arcsin eta) <= sqrt2`, so the unconstrained
  equality point lies outside the square. Both partial derivatives of `f` are
  nonnegative there, so the maximum sits at the corner `q = s = eta`, giving
  `f <= eta^2 (4 - 3 eta^2)`.
- If `eta >= sqrt(2/3)` the square contains the equality point and `f <= 4/3`.

---

## Step 4 — the constant

Dividing (*) by `rho M^2 L_T = eta M^3 L_T`:

```
                              sqrt(4 - 3 eta^2)      0 < eta <= sqrt(2/3)
C_{3,free}^{P,chain}(eta)  <=
                              2 / (sqrt3 eta)        sqrt(2/3) <= eta <= 1
```

Continuous at the crossover, where both branches equal `sqrt2`. Zero `q` or `p`
cases follow by continuity. `[]`

---

## Step 5 — Equality Conditions

Because Step 3 is a sum of squares, equality in `f = 4/3` holds **iff both
squares vanish**:

```
(uv - 2)^2 = 0    and    (u - v)^2 = 0        <=>        u = v = sqrt2
```

Translating back through `u = tan alpha`, `q = sin alpha`:

```
u = v = sqrt2      <=>      q = s = sqrt(2/3)
```

> **This is why the extremizer changes at `eta_c = sqrt(2/3)`.** It is not a
> feature of the formula and not an artifact of the parametrization: `sqrt(2/3)`
> is the unique interior maximizer of `f`, and `eta_c` is exactly the leakage at
> which that maximizer becomes **feasible**. Below `eta_c` the closure budget
> binds and the optimum is pushed to the corner `q = s = eta`; at and above
> `eta_c` the interior optimum is available and the closure budget stops being
> active.

**Full equality data at an extremizer.** Chasing equality back up the chain:

| step | condition for equality |
|---|---|
| (G2) | `||mu_1(a,b)|| = M`, i.e. vertex 1 saturates its operator norm |
| `||x|| <= 1` | `||N u|| = M`: vertex 2 saturates its norm on the *normal* direction `u` |
| Reduction Lemma | `K_uu = 1 - s^2/M^2` — the Gram matrix of `(Nu, Qy)` is the extremal one |
| Step 3 | `q = s = min{eta, sqrt(2/3)}` |
| root | the root map loses nothing under `P_3` |

The Gram matrix of the two propagated contributions is therefore pinned: the
angle between them satisfies `cos theta = sqrt(1 - s^2)` with `s = min{eta,
sqrt(2/3)}`, so the two error contributions meet at `arcsin(s)` — and at
`eta >= eta_c` that angle is frozen at `arcsin sqrt(2/3) ~ 54.7356 deg`
regardless of `eta`.

This upgrades `W_3` from an exact-constant statement to an **extremizer
geometry** statement, which is what the equality analysis of `k = 2` (M8) does
at the previous level.

---

## Step 6 — Extremizer (attainment)

Take `M = 1`, `L_T = 1`, `rho = eta`, `P = e_0 e_0^*`, and

```
t := min{ eta, sqrt(2/3) },        p := sqrt(1 - t^2),        c := sqrt(1 - t^2)
```

*(note `t` is exactly the `q = s` of Step 5, so the witness is reading its
value off the equality conditions, not guessing)*

```
mu_1(x,y) = <x,e_0> <y,e_0> ( t e_1 + p e_0 )

N_t e_0 = t e_1 - c e_0 ,   N_t e_1 = c e_1 + t e_0 ,   mu_2(x,y) = <y,e_0> N_t x

x := N_t e_1 = c e_1 + t e_0 ,   z := e_1 ,   v := t x + p t z
A h := <v,h> e_0 / ||v|| ,        mu_3(x,y) = <y,e_0> A x
```

Each law has operator norm `1`; the vertex-1 and vertex-2 closure residuals
have norm `t <= eta`; the root residual is `0`.

Evaluating with unit leaves `e_0`: `D_1 = t e_1`, `R_1 = p e_0`, and

```
F_2 - R_2  =  t N_t e_1 + p (I-P) N_t e_0  =  t x + p t z  =  v
```

so, using `p = c`,

```
E_T^P = ||v|| = sqrt( t^2 + p^2 t^2 + 2 p t^2 c ) = t sqrt(1 + 3c^2)
      = t sqrt(4 - 3 t^2)
```

- `t = eta <= sqrt(2/3)`:  `E/eta = sqrt(4 - 3 eta^2)`.
- `t = sqrt(2/3)`:          `E = sqrt(2/3) sqrt2 = 2/sqrt3`, so `E/eta = 2/(sqrt3 eta)`.

Matching Step 4 in both regimes. Therefore

```
C_{3,free}^{P,chain}(eta)  =  W_3(eta) ,      attained.        []
```

> **Scope note that must travel with the theorem.** Above `eta_c` the witness
> operates at leakage `t = sqrt(2/3) < eta` and **deliberately underuses** its
> closure budget. Earlier prose claiming "all closure residuals exactly at cap"
> was false above `eta_c` and contradicted its own verification table (V5 freeze
> defect C1).

---

## What the appendices carry

| result | role | why it is not in the main line |
|---|---|---|
| M9 `U_3` | historical envelope | strictly weaker than `W_3`; superseded, not used |
| M10 | `U_3` not attained | about `U_3`, which the main line never invokes |
| M10b/c/d | compactness, support compression, endpoint | needed only to convert non-attainment of `U_3` into a strict gap |
| M15 | branching | same `W_3` by nuclear/operator duality plus a 2-D witness |
| M16, M20, M21 | class corollaries | extend `free`-chain to branching, all arities, tagged same-law |
| M18, M19 | `lim_{eta->0} C = k-1` | different regime (asymptotic, all `k`) |

**Field caveat, unresolved.** M14's witness and law class are stated over `R`.
M16 declares its class over `R` **or** `C` and proves it by identifying the
chain component with the M14 class — a step that does not close on the complex
part. See `FROZEN_SCOPE_V6_2026-08-25.md` §6.1. The Reduction Lemma, the SOS
identity and Step 5 are field-agnostic; only the witness needs a line
confirming it embeds in `C^2`.
