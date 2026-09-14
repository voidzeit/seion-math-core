# Geometry of projected rebracketings

**Scope.** The extremal geometry of *pairs* of computation trees over the same
leaves, evaluated ambiently and under recursive projection. Paper A / the
canonical PMT formalization studies the error **inside one tree**,
`C_T^P(eta)`. This line studies the distortion **between two trees**, and it is
a different extremal problem: the bridge of
`research/math_closure/associator/ASSOCIATOR_REBRACKETING_CANONICAL.md` §2
relates them but does not reduce one to the other.

Nothing here uses the six-term GJI, a cohomological differential, an anchor, or
the word *curvature*. The object is the **rebracketing defect** and its
projected counterpart; a geometric reading is offered in §7 and is labelled as
an interpretation, not a theorem.

Status labels follow the repository convention: **EXACT/PROVED** for statements
proved here, **EXPERIMENTAL** for measured quantities, **OPEN** otherwise. All
proofs here are repository-internal and carry
`approval_status: PENDING_HUMAN_REVIEW`.

---

## 1. RG-0: canonical objects and typing

Throughout, the setting is exactly Definitions 1.1–6.1 of
`papers/projected_multilinear_trees/CANONICAL_FORMALIZATION.md`: finite ordered
rooted trees, multilinear laws `mu_v` with `||mu_v||_op <= M`, orthogonal
projectors `P_v`, closure defect `rho_v^proj <= rho` measured on inputs already
in the range of the children's *extended* projectors (leaves are **not**
reduced, Definition 1.4), `eta := rho/M in (0,1]`, `L_T` the leaf-norm product.
By Lemma 7.1 we normalize `M = 1`, `rho = eta`, unit leaves, `L_T = 1`.

**Definition 1.1 (rebracketing pair).** A *rebracketing pair* is an ordered pair
`(T, T')` of typed trees over the **same ordered leaf data**, with the same root
space and the **same root projector** `P`. Internal laws, internal projectors,
arities and shapes may differ. `k(T)`, `k(T')` are their internal-vertex counts.

**Definition 1.2 (the four evaluations).** With `F` the ambient and `R` the
recursively projected evaluation at the root (Definitions 2.2, 2.3):

```
A_{T,T'}  := F_T - F_{T'}            rebracketing defect        (uncompressed)
Ahat_{T,T'} := R_T - R_{T'}          observed defect            (compressed)
e_T^P     := P F_T - R_T             projected error of T,  E_T^P = ||e_T^P||
D_{T,T'}  := Ahat_{T,T'} - P A_{T,T'}   rebracketing distortion
```

`A` is not called a tensor, a curvature, or an associator: for a ternary law the
five-input elementary defects `T_1 - T_2` etc. of the associator file are the
special case `k(T) = k(T') = 2` of Definition 1.2, and the anchored four-input
objects are a further specialization.

**Proposition 1.3 (bridge identity, EXACT).** `D_{T,T'} = -e_T^P + e_{T'}^P`,
hence `||D_{T,T'}|| <= E_T^P + E_{T'}^P`.
*Proof.* `R_T = P F_T - e_T^P` by definition of `e_T^P`; subtract the same for
`T'`. ∎ (This is the §2 theorem of the associator file, restated.)

**Definition 1.4 (the three extremal constants).** Fix `k`. Over all admissible
rebracketing pairs with `k(T) = k(T') = k` in a class `C`:

```
J_k^C(eta) := sup ||D_{T,T'}||      / (rho M^{k-1} L)                distortion
S_k^C(eta) := sup { ||Ahat_{T,T'}|| / (rho M^{k-1} L) :  P A = 0 }   fabrication
H_k^C(eta) := sup { ||P A_{T,T'}|| / (rho M^{k-1} L) :  Ahat = 0 }   concealment
```

`J` is what Proposition 1.3 bounds. `S` asks how much rebracketing signal the
representation alone can **manufacture**; `H` asks how much genuine signal it
can **hide**. `S` and `H` are the operationally meaningful ones: an experiment
observes `Ahat`, never `A`.

**Definition 1.5 (class hierarchy).** `C^free` (independent laws, independent
projectors) ⊇ `C^same-mu` (one law at every vertex of both trees) ⊇
`C^same-mu,shared-P` (additionally one projector at every vertex). Also
`C^kernel`, `C^cyclic` — not used below.

**Definition 1.6 (equality geometry).** For nonzero errors and nonzero `PA, D`:

```
chi_{T,T'} := Re<e_T^P, e_{T'}^P> / (||e_T^P|| ||e_{T'}^P||)
cos(theta) := Re<P A, D> / (||P A|| ||D||)
```

`chi = -1` is maximal distortion, `chi = 0` the Pythagorean regime, `chi = +1`
the regime where the errors cancel out of the tree-to-tree difference.
`theta ≈ 0` amplification, `theta ≈ pi/2` rotation, `theta ≈ pi` concealment.

---

## 2. The `k = 2` reduction — **EXACT**

Everything at `k = 2` follows from one normal form. Let `T` have `k(T) = 2`:
one inner vertex `i` and the root `r`; every other child of `r`, and every
child of `i`, is a leaf.

**Lemma 2.1 (normal form).** With `M = 1`, unit leaves, write
`F_i = mu_i(leaves)`, `R_i = P_i F_i`, `D_i = (I - P_i)F_i`, and let
`Lambda(x) := mu_r(..., x, ...)` be the root law with the inner vertex's slot
free and every other slot filled with its leaf datum. Then `Lambda` is linear
with `||Lambda||_op <= 1`, and

```
d := ||D_i|| <= eta,   r := ||R_i||,   d^2 + r^2 = ||F_i||^2 <= 1,
n := D_i/d,  q := R_i/r   are orthonormal   (n in ker P_i, q in Ran P_i),
u := P Lambda(n),   v := P Lambda(q),
```

give

```
e_T^P = d u,     R_T = r v,     P F_T = d u + r v,
```

and the pair `(u, v)` satisfies `|<psi,u>|^2 + |<psi,v>|^2 <= 1` for every unit
`psi`.

*Proof.* `F_T = Lambda(F_i) = Lambda(R_i) + Lambda(D_i)` by linearity of
`Lambda`; `R_T = P mu_r(R_i, leaves) = P Lambda(R_i) = r v`; so
`e_T^P = P F_T - R_T = P Lambda(D_i) = d u`. `||Lambda||_op <= M * (product of
the root's leaf norms) = 1` and `||F_i|| <= M * (product of the inner leaf
norms) = 1` are Definition 1.2 and Lemma 8.1 of the canonical formalization;
`d <= eta` is the closure budget at `i` (the inner vertex's children are leaves,
whose extended projector is the identity, so `rho_i^proj` is the unrestricted
norm). `d^2 + r^2 = ||F_i||^2` is orthogonality of `P_i`. Finally `n ⊥ q` are
unit, so `(alpha,beta) -> P Lambda(alpha n + beta q)` has operator norm at most
`||P Lambda||_op <= 1`, which applied to the functional `<psi, .>` gives the
stated inequality. ∎

**Lemma 2.2 (root laws may be taken `P`-valued).** Replacing `mu_r` by
`P mu_r` at the root of either tree leaves `Ahat`, `P A`, `D`, `e_T^P` and
`e_{T'}^P` unchanged, does not increase `||mu_r||_op`, and makes the root's
closure defect `rho_r^proj` vanish. Hence the root closure budget is never
binding for any of the three constants of Definition 1.4, and the search of
`rg4_s2_search.py` may parametrize root laws as `P`-valued without shrinking
the supremum.

*Proof.* Every quantity listed is of the form `P(...)` by Lemma 2.1 and
Definition 1.2 (`Ahat = R_T - R_{T'}` with both `R` in `Ran(P)`, `PA` and
`e^P` carry an explicit `P`), and `P mu_r` differs from `mu_r` only in
`(I-P)`-components; `||P mu_r||_op <= ||mu_r||_op` since `||P|| <= 1`; and
`(I-P)P = 0` gives `rho_r^proj = 0`. ∎

Note the lemma does **not** say `A` is unchanged — it is not, only `P A` is.
The witnesses of §5 achieve the stronger `A = 0` without invoking it.

**Warning 2.3 (a WLOG reduction can stop being WLOG under shared parameters).**
Lemma 2.2 replaces the root law *independently of the inner law*. In `C^free`
that is free of charge, since the root law is a separate parameter. In
`C^same-mu` it is **not admissible as a reduction**: applying it produces a
configuration whose root and inner vertices carry different tensors, which is
outside the class. Any search or proof restricted to a shared-parameter class
must therefore re-derive its normalizations rather than inherit them from the
free class. This is not pedantry — a first version of `rg_fused_search.py`
shared the raw tensor but normalized the root by `‖P mu‖` and the inner vertex
by the closure-shrunk factor, so its "same-law" arm was silently an unnamed
correlated-law class and its numbers said nothing about `C^same-mu`. The same
caution applies to every reduction used below: leaf normalization and the
homogeneity rescaling of Lemma 7.1 are safe under sharing (they act on all
vertices at once); the root-projection reduction is not.

No assumption is made on arity, dimension, rank, or on whether the two trees
share laws or projectors. Writing the primed symbols for `T'`, a `k = 2`
rebracketing pair is completely described by `(d, r, u, v; d', r', u', v')` with

```
e_T = d u,  e_{T'} = d' u',   Ahat = r v - r' v',
P A = (d u + r v) - (d' u' + r' v'),   D_{T,T'} = -d u + d' u'.
```

---

## 3. RG-1 / RG-2: `J_2 = 2`, and the class hierarchy collapses — **PROVED (M40)**

**Theorem 3.1.** For every `eta in (0,1]`,

```
J_2^free(eta) = J_2^same-mu(eta) = J_2^same-mu,shared-P(eta) = 2,
```

and the supremum is **attained**, in ambient dimension 3 with a single ternary
law, a single rank-2 projector at both vertices of both trees, and unit leaves.

*Proof of `<= 2`.* `C_2^P(eta) = 1` (Corollary 11.3 of the canonical
formalization), so `E_T^P, E_{T'}^P <= rho M L`; Proposition 1.3 gives
`||D|| <= 2 rho M L`. Equivalently `||D|| = ||-du + d'u'|| <= d + d' <= 2eta`
from Lemma 2.1. ∎

*Attainment.* Let `V = R^3` with orthonormal basis `e_0, e_1, e_2`, and let
`P = ` orthogonal projector onto `span(e_0, e_2)` — used at **both** inner
vertices and at **both** roots. Define one trilinear law by

```
mu(x, y, z) = eta * x_0 y_0 z_0 * e_1  +  (x_1 y_0 - x_0 y_1) * z_2 * e_0.
```

Leaves: `x_1 = x_2 = x_3 = x_4 = e_0`, `x_5 = e_2` (all unit, all in `Ran P`).
Trees: `T_L = mu(mu(x1,x2,x3), x4, x5)` and `T_M = mu(x1, mu(x2,x3,x4), x5)`.

*Admissibility.* Since `e_0 ⊥ e_1`,

```
||mu(x,y,z)||^2 = eta^2 x_0^2 y_0^2 z_0^2 + (x_1y_0 - x_0y_1)^2 z_2^2
                <= max( eta^2 x_0^2y_0^2 , (x_1y_0-x_0y_1)^2 ) * (z_0^2 + z_2^2)
                <= max(eta^2, 1) = 1,
```

using `|x_1y_0 - x_0y_1| <= 1` for unit `x,y` (it is a 2×2 determinant of unit
rows). The value `1` is attained at `(e_1, e_0, e_2)`, so `||mu||_op = M = 1`
exactly. The closure defect is `(I-P)mu(x,y,z) = eta x_0y_0z_0 e_1`, of norm
`<= eta` for **all** unit inputs, hence a fortiori on projected inputs; it
equals `eta` at `(e_0,e_0,e_0)`. So `rho^proj = eta = eta M` at every vertex and
the realization is `(1, eta)`-admissible.

*Evaluation.* `mu(e_0,e_0,e_0) = eta e_1`, so both inner vertices produce
`F_i = eta e_1`, `R_i = P F_i = 0`, `D_i = eta e_1` (the closure bound EQ2 of
Theorem 11.2 is saturated). At the roots,

```
F_L = mu(eta e_1, e_0, e_2) = +eta e_0,     R_L = P mu(0, e_0, e_2) = 0,
F_M = mu(e_0, eta e_1, e_2) = -eta e_0,     R_M = 0,
```

(the first summand of `mu` vanishes because `z_0 = 0`, and the sign flips
because the determinant `x_1y_0 - x_0y_1` is antisymmetric under exchanging the
first two slots). Hence `e_L^P = eta e_0`, `e_{T'}^P = -eta e_0`, both of norm
`eta = rho M L`, i.e. **both trees saturate `C_2^P = 1`**, and

```
A = 2 eta e_0,   P A = 2 eta e_0,   Ahat = 0,   D = -2 eta e_0,
||D|| / (rho M L) = 2. ∎
```

**Corollary 3.2 (no rigidity from sharing at `k = 2`).** Sharing the law and
sharing the projector do not lower the distortion constant: the three classes of
Definition 1.5 have the same value `2`. The mechanism is the one already
recorded for `k = 2` saturation in §28 of the canonical formalization — a single
multilinear map can have distinct norm-attaining input tuples for its
structurally different monomials — here reinforced by the fact that the two
trees feed the shared law's *slot-antisymmetric* monomial in opposite orders.

**Remark 3.3 (dimension 2 suffices without the leaf convention).** If leaves are
not required to lie in `Ran P` (they are not, Definition 1.4), the same
computation runs in `V = R^2` with `P = ` projector onto `span(e_0)`,
`mu(x,y,z) = eta x_0y_0z_0 e_1 + (x_1y_0 - x_0y_1) z_1 e_0`, leaves
`x_1..x_4 = e_0`, `x_5 = e_1`. Ambient dimension 2 is minimal: `k = 2`
saturation needs `D_i != 0` and `R`-space room for the root output, i.e. both
`ker P != 0` and `Ran P != 0`.

**Corollary 3.4 (sharpness of the naive certificate).** The constant `2` in
`||Ahat - P A|| <= 2 rho M L` cannot be replaced by any smaller constant. It is
the wrong constant for the **certificate** `||Ahat|| > c * rho M L => P A != 0`;
see §5.

---

## 4. RG-5: concealment is total, `H_2 = 2` — **PROVED (M41)**

**Theorem 4.1.** `H_2^free(eta) = H_2^same-mu,shared-P(eta) = 2` for every
`eta in (0,1]`, attained by the witness of Theorem 3.1.

*Proof.* If `Ahat = 0` then `P A = -D`, so `||P A|| <= 2 rho M L` by Theorem
3.1's upper bound. The witness of Theorem 3.1 has `Ahat = R_L - R_M = 0` and
`||P A|| = 2 eta = 2 rho M L`. ∎

**Interpretation.** A rebracketing defect of the *largest size the class
permits* can be rendered **exactly invisible** by the projection: the compressed
computation reports `R_L = R_M` — literal observed associativity — while the
ambient law satisfies `F_L = -F_M != 0`. In the notation of Definition 1.6 this
extremizer has `chi = -1` and `theta = pi`. Concealment is not a small-`eta`
perturbative effect: it is total at every `eta`, with one law and one projector.

---

## 5. RG-4: fabrication is *not* total — `S_2(eta) < 2` sharply — **PROVED (M42)**

Write

```
Sigma_2(eta) := sin( min(2 arcsin eta, pi/2) )/eta
             =  2 sqrt(1 - eta^2)      for 0 < eta <= 1/sqrt(2),
             =  1/eta                  for 1/sqrt(2) <= eta <= 1.
```

`Sigma_2` is continuous, equals `sqrt(2)` at the crossover `eta_c = 1/sqrt(2)`,
tends to `2` as `eta -> 0`, equals `1` at `eta = 1`, and satisfies
`Sigma_2(eta) < 2` for every `eta > 0`.

**Theorem 5.1 (quantitative, unconditional).** For every admissible `k = 2`
rebracketing pair,

```
||Ahat_{T,T'}||  <=  ||P A_{T,T'}||  +  Sigma_2(eta) * rho M L.
```

*Proof.* Use Lemma 2.1 for both trees and put `d = sin(alpha)`,
`d' = sin(alpha')` with `alpha, alpha' in [0, arcsin eta]`; then
`r <= cos(alpha)`, `r' <= cos(alpha')`. Assume `Ahat != 0` and take
`psi := Ahat/||Ahat||`. Write `a := <psi,u>`, `b := <psi,v>`,
`a' := <psi,u'>`, `b' := <psi,v'>`, `t := <psi, Ahat> = ||Ahat||`,
`p := <psi, P A>`. By Lemma 2.1, `a^2 + b^2 <= 1` and `a'^2 + b'^2 <= 1`. The
normal form gives two expressions for `t`:

```
(i)   t = r b - r' b'                 (from Ahat = r v - r' v')
(ii)  t = p + (d' a' - d a)           (from P A = du + rv - d'u' - r'v')
```

For any `lambda in [0,1]`, `t = lambda*(ii) + (1-lambda)*(i)`, i.e.

```
t = lambda p + <(a,b), (-lambda d, (1-lambda) r)> + <(a',b'), (lambda d', -(1-lambda) r')>
  <= lambda |p| + h(lambda, alpha) + h(lambda, alpha'),
     where h(lambda, x) := sqrt( lambda^2 sin^2 x + (1-lambda)^2 cos^2 x ),
```

by Cauchy–Schwarz on each pair. Choose

```
lambda := c/(c+s),   c := cos(alpha)cos(alpha'),   s := sin(alpha)sin(alpha'),
```

which lies in `[0,1]`. Then `c + s = cos(alpha - alpha')` and

```
h(lambda, alpha)^2 = [c^2 sin^2(alpha) + s^2 cos^2(alpha)]/(c+s)^2
                   = sin^2(alpha)cos^2(alpha)[cos^2(alpha') + sin^2(alpha')]/(c+s)^2,
```

so `h(lambda,alpha) = sin(alpha)cos(alpha)/(c+s)` and likewise for `alpha'`,
whence

```
h(lambda,alpha) + h(lambda,alpha') = [sin(2alpha) + sin(2alpha')] / (2 cos(alpha - alpha'))
                                   = sin(alpha + alpha').
```

(If `c + s = 0`, then `{alpha, alpha'} = {0, pi/2}` and `lambda = 1` gives the
same bound `sin(alpha + alpha') = 1` directly.) Therefore
`t <= |p| + sin(alpha + alpha')`. Finally `alpha, alpha' <= arcsin(eta)` and
`sin` is increasing on `[0, pi/2]`, so
`sin(alpha + alpha') <= sin(min(2 arcsin eta, pi/2)) = eta * Sigma_2(eta)`, and
`|p| <= ||P A||`. Restoring the normalization gives the statement. ∎

**Corollary 5.2 (sharp fabrication constant).**
`S_2^free(eta) = Sigma_2(eta)`, attained, with `A = 0` exactly (not merely
`P A = 0`).

*Proof of attainment.* Put `d := min(eta, 1/sqrt(2))`, `r := sqrt(1 - d^2)`.
Let `V = R^2`, `P = ` projector onto `span(e_0)`, all five leaves `= e_0`, and

```
mu_i (x,y,z) = x_0 y_0 z_0 (r e_0 + d e_1)              (both inner vertices)
mu_r^L(x,y,z) = (r x_1 - d x_0) y_0 z_0 e_0             (root of T_L)
mu_r^M(x,y,z) = x_0 (- r y_1 + d y_0) z_0 e_0           (root of T_M)
```

Each law has operator norm `sqrt(r^2 + d^2) = 1 = M`. The closure defects are
`(I-P)mu_i(x,y,z) = d x_0y_0z_0 e_1`, of norm `<= d <= eta`, and `0` at both
roots. So the realization is `(1, eta)`-admissible. Evaluating,

```
F_i = r e_0 + d e_1,   R_i = r e_0,   D_i = d e_1,
F_L = mu_r^L(F_i, e_0, e_0) = (r*d - d*r) e_0 = 0,   R_L = -d r e_0,
F_M = mu_r^M(e_0, F_i, e_0) = (-r*d + d*r) e_0 = 0,  R_M = +d r e_0,
```

so `A = F_L - F_M = 0` and `Ahat = R_L - R_M = -2 d r e_0`, giving
`||Ahat||/(rho M L) = 2 d r / eta = Sigma_2(eta)` by the choice of `d`. ∎

**Corollary 5.3 (the sharp certificate).** For any observed compressed
rebracketing signal,

```
||P A_{T,T'}||  >=  ||Ahat_{T,T'}||  -  Sigma_2(eta) * rho M L,
```

so `||Ahat|| > Sigma_2(eta) rho M L` **certifies** `P A != 0`. Since
`Sigma_2(eta) < 2` for all `eta in (0,1]`, this is a strictly stronger
certificate than the one obtained from Proposition 1.3 and `J_2 = 2`, at every
leakage level; e.g. at `eta = 0.2` the threshold drops from `2` to `1.9596`, at
`eta = 1/sqrt(2)` to `1.4142`, and at `eta = 1` to `1`.

**Remark 5.4 (why the two directions differ).** Concealment needs only two
maximal, anti-aligned errors — no constraint couples them. Fabrication needs the
*ambient* values to agree while the *projected* ones disagree, so the difference
must be carried by the clean parts `R_i = r q`, and `r` competes with `d` for
the norm of `F_i` through `d^2 + r^2 <= 1`. The optimum balances them at
`d = r = 1/sqrt(2)` when the closure budget allows it (`eta >= 1/sqrt(2)`), and
otherwise is clamped at `d = eta`. This is the same Pythagorean coupling that
makes `W_3(eta) < 2` at `k = 3` (§12, §33 of the canonical formalization),
appearing here at `k = 2`, where the *single-tree* constant `C_2^P = 1` shows no
such effect.

**Corollary 5.5 (equality geometry, RG-3 at `k = 2`).** At every extremizer of
`J_2`, `H_2` and `S_2` the two projected errors are exactly anti-aligned,
`chi = -1`. For `J_2` and `H_2` this is forced by
`||-e_T + e_{T'}|| = ||e_T|| + ||e_{T'}||` with both norms maximal; for `S_2` it
follows from the equality analysis in the proof of Theorem 5.1 (equality in both
Cauchy–Schwarz steps forces `(a,b) ∝ (-d,r)` and `(a',b') ∝ (d',-r')`, hence
`u' ∝ -u`). The witnesses realize `chi = -1` explicitly.

---

## 6. Summary of `k = 2` constants

| constant | meaning | value | attained | class |
|---|---|---|---|---|
| `C_2^P(eta)` | error inside one tree | `1` | yes | prior work (M8) |
| `J_2(eta)` | distortion between trees | `2` | yes | **collapses** over free / same-`mu` / same-`mu`+shared-`P` |
| `H_2(eta)` | concealment of genuine defect | `2` | yes | same witness as `J_2` |
| `S_2(eta)` | fabrication of spurious defect | `min(2 sqrt(1-eta^2), 1/eta) < 2` | yes | free (same-law: **OPEN**) |

The conceptual statement, in the same register as §33 of the canonical
formalization:

> **A projection can conceal an arbitrarily large rebracketing defect entirely,
> but it cannot fabricate one of the same size: concealment is sharp at
> `2 rho M L`, fabrication is sharp at `Sigma_2(eta) rho M L < 2 rho M L`.**

---

## 7. Interpretation (not a theorem)

`Ahat = P A + D` decomposes an observed rebracketing signal into a genuine part
and a representation-induced part, and `theta` of Definition 1.6 measures their
relative orientation: amplification near `0`, rotation near `pi/2`, concealment
near `pi`. Calling `A` a curvature remains a *constitutive choice*, not a
theorem, exactly as recorded in §4 of the associator file; nothing above depends
on that reading.

---

## 8. What is open in this line

- **RG-2 for `S_2`.** `S_2^same-mu` and `S_2^same-mu,shared-P`: the `S_2`
  witness of Corollary 5.2 uses three different laws. Whether a single tagged
  law reaches `Sigma_2(eta)` is **OPEN**; `rg4_s2_search.py` is the falsification
  harness. (`J_2` and `H_2` are already settled in the strictest class.)
- **RG-6.** `J_3(eta)` versus `2 W_3(eta)`, and the corresponding `S_3`, `H_3`.
  The `k = 2` result predicts the interesting asymmetry survives: `H_3 = 2W_3`
  should follow from the same two-anti-aligned-witnesses argument once two
  `k = 3` extremizers with opposite root errors are exhibited, while `S_3` needs
  a genuinely new coupling argument.
- **RG-7.** Geometry of the whole bracketing family `{F_T}` versus `{R_T}`, and
  `Delta_geom := max_ij | ||R_i - R_j|| - ||F_i - F_j|| |`.
- **RG-8.** Anchor dependence of the anchored associator `Assoc_e`.
- **RG-9.** Kernel/continuum extension.

Deliberately **not** attempted: `delta^2 = 0`, GJI, Hodge, `E8`, fractal
manifolds, or any claim that a differential curvature has been discovered.

---

## 9. Verification

- `rg_witnesses.py` — builds the three witnesses as explicit dense tensors and
  checks, independently of the proofs: operator norms, closure defects (both
  `rho^proj` and `rho^amb`), every evaluation, the bridge identity, `chi`,
  `theta`, and the achieved ratios against `2`, `2`, `Sigma_2(eta)`.
- `rg4_s2_search.py` — adversarial batched search over the free and same-law
  classes trying to violate Theorem 5.1 in the constraint-free form
  `(||Ahat|| - ||P A||)/(rho M L) <= Sigma_2(eta)`. Superseded for production
  runs by `rg_fused_search.py`; kept because it is the readable one-cell-at-a-
  time reference implementation the fused version is checked against.
- `rg_fused_search.py` — the same search with every cell at a given ambient
  dimension folded into one batch axis (see below).
- `rg_cpu_falsify.py` — uniform random sampling of admissible pairs across all
  CPU cores, as an unbiased complement to gradient ascent.
- `rg_readout.py` — the positive-control readout (below).
- `rg_harness_selftest.py` — feeds Theorem 3.1's exact witness through the
  search harness's own feasibility pipeline, to separate optimizer failure
  from a parametrization bug.

### Positive control: what a numerical shortfall is allowed to mean

`J_2 = 2` is **proved attainable in the same-law/shared-projector class** by an
exact witness. That makes the `J` arm a positive control on the search itself.
Define, within a class,

```
gamma_J := J_found / 2 ,      gamma_S := S_found / Sigma_2(eta) .
```

A shortfall in `gamma_S` is evidence about the *geometry* only if `gamma_J` is
close to `1` in the same class. If `gamma_J < 1`, the search has not been shown
to reach that class's frontier and `gamma_S` measures the optimizer, not the
mathematics. Measured on the 144-cell sweep (2026-08-16):

| class | `gamma_J` | `gamma_H` | `gamma_S` | reading |
|---|---|---|---|---|
| free | **0.99972** | **0.99965** | **0.99842** | calibrated; `S` saturates `Sigma_2` |
| same-`mu`, shared `P` | **0.88136** | 0.88408 | — | **not calibrated; `gamma_S` uninterpretable** |

Re-graded sweep, 2026-08-16: 144 cells, 147,456 restarts, 1189 s, converged
grading (`restarts = 64`, `iters = 40`, top-24 finalists per cell). **Zero
cells above any ceiling** and zero inadmissible at a tolerance matched to the
arithmetic. Worst excess: free `J` −5.6e−4, `H` −7.0e−4, `S` −1.6e−3.

Two things changed against the earlier, under-graded sweep, and both in the
expected direction:

- the **free** class barely moved (`gamma_S` 0.99805 → 0.99842) and now stands
  on a converged grading, so the claim it supports — that a search which was
  never told the answer independently approaches `Sigma_2` — is sound;
- the **same-law** class got *worse* (`gamma_J` 0.93448 → **0.88136**), which
  is exactly what removing an inflating estimator must do.

At `D = 3`, `rank 2` — the cell where the witness attains `2` for every `eta` —
the search returns `1.5189`–`1.6921`, i.e. `0.76`–`0.85` of the known extremum.
So `S_2^same-mu` stays **OPEN**: the harness has not been shown to reach that
class's frontier, and its `S` values (0.81–0.90 of `Sigma_2`) measure the
optimizer, not the geometry.

| `eta` | free `S`/`Sigma_2` | same-`mu` `S`/`Sigma_2` |
|---|---|---|
| 0.05 | 0.99135 | 0.88146 |
| 0.30 | 0.95868 | 0.80648 |
| 0.7071 | 0.99709 | 0.88808 |
| 1.00 | **0.99842** | 0.90354 |

### Feasibility belongs to the backward pass, not only the forward

The search evaluates an **admissible** law, obtained by dividing a raw tensor by
a scale factor built from its own operator norm and closure defect. The first
implementation computed that factor under `no_grad` and treated it as a
constant, so autograd differentiated

```
Ftilde_{mu0}(mu) = J( mu / s(mu0) )     instead of     F(mu) = J( mu / s(mu) )
```

These are different optimization problems, and they disagree in exactly the
direction a homogeneous problem cannot ignore. Before normalization the
same-law objective is homogeneous of degree 2, so Euler gives
`<grad J(mu), mu> = 2 J(mu) > 0`: the frozen-denominator surrogate reports a
strongly ascending **radial** direction. But `s` is homogeneous of degree 1
too, so the normalized objective is scale invariant, `F(c mu) = F(mu)`, and
therefore

```
DF(mu)[mu] = 0     exactly.
```

Measured on this repository (`rg_gradient_checks.py`):

| quantity | frozen | differentiable |
|---|---|---|
| radial derivative `\|DF(mu)[mu]\|` (must be 0) | **0.5443** | **7.6e-17** |
| finite-difference vs autograd, relative error | **10.7** | **9.1e-6** |
| forward scale invariance `\|F(c mu) - F(mu)\|` | 1.4e-16 | 1.4e-16 |
| Euler identity `\|<grad N, mu> - N\|` | — | 2.7e-15 |

The forward was never wrong; only the backward was. The consequence was that
the optimizer actively walked away from configurations valued at `1.9997` out
of `2`, down to a `~1.68` attractor, which is what produced the apparent
same-law plateau at `gamma_J ~ 0.84`. With the gradient corrected, the same
starting points hold at `1.9968` and points perturbed to `1.77` now **climb**
to `1.99`.

Two secondary lessons, both structural rather than numerical:

- **The damage scaled with `eta`.** It was worst at `eta = 1` (drift `-0.50`
  versus `-0.31` at `eta = 0.3`), because at `eta = 1` the closure budget is
  vacuous and the operator norm is the only active constraint, so the entire
  spurious radial direction lands on it with no second branch of the `max` to
  share it.
- **A cached factor and a differentiable factor are mutually exclusive.** The
  `refresh` cache that made the sweep affordable silently presupposed the frozen
  mode: a constant can be cached, a graph cannot. The correct loop pays the
  feasibility cost every step.

A restart-batched kernel is where this hid: `m39_gpu_kernels` searches the
maximizing directions under `no_grad` but contracts the final value against the
**live** tensor, which is the envelope theorem,
`d/dt ||mu_t||_op = d/dt <mu_t, v*>` at fixed maximizer. The first version of
`rg_kernels.op_norms` contracted against the detached copy instead, returning a
norm with no gradient at all. Search vectors may be detached; the tensor they
are contracted against may not.

**The residual, decomposed.** After the fix a small drift remained when
starting `1e-3` from the witness at `eta = 1`. Sweeping the two candidate causes
separately settles it:

| axis | setting | drift |
|---|---|---|
| inner-solver fidelity | `(3,20)` / `(16,40)` / `(32,40)` | −0.0153 / −0.0130 / −0.0062 |
| | `(64,40)` / `(128,60)` | −0.0047 / **−0.0047** (plateau) |
| learning rate at `(64,40)` | `0.05` / `0.01` / `0.002` | −0.0070 / **+0.0005** / **+0.0009** |

So the residual is `inner-solve` plus `finite optimizer step`, and nothing else:
at `lr = 0.01` with converged in-loop fidelity the witness **holds**
(`1.998865 -> 1.999384`). The non-smooth corner where `||mu||_op = 1` and
`closure = eta` tie costs nothing measurable above those two.

The sharpest confirmation that the diagnosis is right is the reversal of the
learning-rate sweep. Under the FROZEN backward, lowering `lr` did not help and
was not even monotone -- `lr = 1e-3` gave `1.328`, worse than `lr = 0.05`'s
`1.686` -- because the flow was ascending the wrong function and `lr` only set
how far it got. Under the corrected backward the same sweep is monotone and
lowering `lr` recovers the extremizer, which is how gradient ascent near a
maximum is supposed to behave.

**Consequence for the record.** Every same-law number produced before this fix
— `gamma_J = 0.88136`, the A/B/C/D initialization matrix, the learning-rate
sweep — is `INVALID AS LANDSCAPE EVIDENCE`. Those configurations were graded
honestly and really are admissible, so they remain valid lower bounds; what is
void is reading them as information about basin width, extremizer rigidity, or
the difficulty of the constant. `S_2^same-mu` therefore has **no valid
numerical evidence of any kind** and stands exactly as open as before the
sweeps. Theorems M40-M42 are untouched: they rest on analytic proofs, exact
witnesses, measured-norm audits, the scalar verification and the tests, none of
which involve the gradient search.

### Estimator-independent check of Theorem 5.1

Because the tensor-level searches all depend on the operator-norm estimator,
`rg_scalar_verification.py` checks the theorem where the mathematical content
actually sits — the **scalar** optimization the proof reduces to — with no
tensors and no estimator anywhere in the loop. It maximizes
`t = r b - r' b'` over the raw feasible set

```
d a + r b = d' a' + r' b',   a^2+b^2 <= 1,  a'^2+b'^2 <= 1,
0 <= d, d' <= eta,   r <= sqrt(1-d^2),  r' <= sqrt(1-d'^2)
```

by sampling, deliberately **without** using the proof's interpolation weight
`lambda = cos(alpha)cos(alpha')/cos(alpha-alpha')`, so agreement is a check and
not a restatement. Over 11 values of `eta`:

| `eta` | sampled max | `sin(min(2 arcsin eta, pi/2))` | ratio | `d*` | `d'*` |
|---|---|---|---|---|---|
| 0.20 | 0.38607 | 0.39192 | 0.985 | 0.200 | 0.200 |
| 0.45 | 0.79675 | 0.80373 | 0.991 | 0.450 | 0.450 |
| 0.7071 | 0.99517 | 1.00000 | 0.995 | 0.689 | 0.707 |
| 1.00 | 0.99806 | 1.00000 | 0.998 | 0.650 | 0.775 |

The largest amount by which sampling exceeded the proved optimum is
`+0.000e+00` — it approaches from within at every `eta` and never crosses.
The extremizer's **active constraint** also switches where the proof says it
must: below `eta_c = 1/sqrt(2)` the optimum sits at `d = d' = eta`, the closure
budget binding; above it the pair moves to the interior with
`d^2 + d'^2 ≈ 1`, the norm budget binding. The `eta_c` transition is thus
recovered from raw sampling rather than assumed.

What is *not* affected: Theorems 3.1, 4.1 and 5.1 and their witnesses. Those
are analytic, and `rg_witnesses.py` checks the witnesses against their
**analytic** operator norms and closure defects rather than against an
estimator — for the witnesses the estimator returns `1.000000000000` exactly,
and the identity `E_T^P = rho M L` holds to `1e-12` at every `eta` tested. The
convergence defect is a property of the adversarial search over *random* laws,
not of the extremal constructions.

In the same-law class the search returns only `1.5261`–`1.6848` at `D = 3`,
`rank(P) = 2` — the very cell where the witness attains `2` for every `eta`. So
the observed same-law `S` deficit (0.81–0.87 of `Sigma_2`) is **recorded as an
optimizer result, not as evidence that `S_2^same-mu < Sigma_2`**, which remains
OPEN exactly as before the sweep.

`rg_harness_selftest.py` then separates the two possible causes by pushing the
exact witness through the harness: it returns `J = 2.000000000` at
`eta in {0.05, 0.3, 1/sqrt(2), 1.0}` with a gap of `9e-16`, measured operator
norm `1.000000`, measured closure `= eta`, and `chi = -1`. The extremizer is
therefore **inside** the search space and is not distorted by the feasibility
projection: the same-law shortfall is optimizer failure, and the thing to fix
is the search, not the class.

### Why all three ceilings are testable without constraint handling

`J`, `H` and `S` are each defined by a *constrained* supremum, but each has an
unconstrained surrogate, so the searches need no penalty, projection or
multiplier:

```
J:  ||D||               / (rho M L)  <= 2
H:  (||PA|| - ||Ahat||) / (rho M L)  <= 2
S:  (||Ahat|| - ||PA||) / (rho M L)  <= Sigma_2(eta)
```

The first two follow from `||D|| <= 2 rho M L` with `Ahat = P A + D`; the third
is Theorem 5.1 itself, which is why the theorem was stated in the quantitative
form rather than only as a statement about the constrained supremum.

### Hardware and run economics

Measured on this machine: **RTX PRO 5000 Blackwell Laptop** (24 GB, 82 SMs,
CC 12.0, CUDA 12.8, torch 2.12) and an **Intel Core Ultra 9 285HX** (24 cores,
127 GB RAM). All arithmetic stays `float64`: at these tensor sizes the run is
launch-bound rather than FLOP-bound, so lower precision would buy almost
nothing while introducing a precision question into a run whose purpose is to
test a certified bound.

The naive harness runs one optimization per `(objective, class, dim, rank,
eta)` cell. A cell is a few hundred kilobytes, so every kernel retires before
the next is queued: **42% GPU utilization, 2.0 of 24 GB resident, ~34 s per
cell.** Folding objective, class, rank and `eta` into per-element vectors makes
a whole sweep at one ambient dimension a single optimization loop, which reaches
**100% utilization at 24 GB.** Group size is measured, not guessed: two probe
sizes give the *marginal* bytes per element, because a single probe charges the
fixed workspace overhead to its own few elements and underfills the card
several-fold.

The CPU side is used for the two jobs that are embarrassingly parallel and
reproducibility-critical: the witness audit (`--workers`, **123 audits over 41
`eta` values in 15 s** on 24 cores, versus ~3 min for 24 audits serially) and
the random falsifier. Running the GPU sweep and the CPU falsifier together
holds the machine at ~73% GPU and ~92% CPU simultaneously.

Under the theorems these are implementation controls, not evidence for the
statements.

Outcome as of 2026-08-16: **24/24 witness audits pass**, 19 checks each, over
`eta in {0.05, 0.1, 0.2, 0.4, 1/sqrt(2), 0.8, 0.9, 1.0}` — including the
operator norms and closure defects *measured* (alternating maximization with
400 restarts, corroborated by a brute sweep as a stall detector) and matched to
their analytic values at `1e-9`, and the three ratios matched to `2`, `2`,
`Sigma_2(eta)` at `1e-12`. **50/50 tests pass** in
`tests/math_closure/test_m40_m42_rebracketing_geometry.py`, including
randomized admissible pairs checked against all three ceilings.

**Convention note (defect found while writing this file).** In
`research/math_closure/associator/m39a_j2_fused.py` the root law's closure is
made feasible with `restrict=P_L` on *all three* slots. Definition 4.1 restricts
slot `i` to `Ran(P_hat_{c_i})`, and the root's other two children are **leaves**,
whose extended projector is the identity. Restricting them shrinks the supremum
and can therefore admit laws whose true `rho_r^proj` exceeds `eta`. It does not
affect any bound proved here — the `k = 2` bounds use the *inner* vertex's
closure budget only, and the root's local defect cancels by `P(I-P) = 0` — but
that script's admissibility claim should be read with the caveat. The scripts in
this directory use the canonical restriction.
