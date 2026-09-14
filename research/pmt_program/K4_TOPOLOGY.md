# k = 4: all four skeletons have the same constant (PMT-A)

Status: **ADVISORY_PROOF_DRAFT** (2026-09-13) for Theorems U, K4-BBR and K4-STAR;
the chain and mixed cases rest on `CHAIN_ALL_K.md` and
`k4_exploration/CHAIN_GRAM_REPORT.md` §11 (also advisory). Numerical controls
in §5 are `NUMERICAL_OBSERVATION`. Class: `PMT-A` (real).

**Answer to the experiment.** In PMT-A, `k = 4` is **not** a depth at which
topology matters:

```
C^P_T(η) = C^P_{4,chain}(η) = { √(9 − 15η² + 7η⁴),  0 < η ≤ √(3/7)
                               { 9/(7η),             √(3/7) ≤ η ≤ 1
```

for every finite ordered tree `T` with four internal vertices, all arities, all
dimensions and ranks. The first skeletons for which topology independence is
not proved are at `k = 5` (§4). Over `ℂ` the question is open and may have a
different answer (§6).

---

## 1. Skeletons

By Lemma A5.2 only the internal skeleton matters. Rooted unlabelled trees on four
vertices:

| id | skeleton | internal arities (root first) |
|---|---|---|
| CHAIN | `1 → 2 → 3 → r` | 1,1,1 |
| MIXED | `(1 → 2), 3 → r` | root 2 |
| BBR | `1, 2 → 3 → r` (branch below root) | root 1, parent 2 |
| STAR | `1, 2, 3 → r` | root 3 |

Orderings of children do not matter (permuting slots preserves norm and defect).

## 2. Universal lower bound (all k, all skeletons)

**Theorem U.** For every finite ordered tree `T` with `k` internal vertices and
every `η ∈ (0,1]`, `C^P_T(η; PMT-A) ≥ C^P_{k,chain}(η)`. In particular
`lim_{η↓0} C^P_T(η) = k − 1`.

*Witness.* All spaces `ℝ² ≅ ℂ`, leaves `z_ℓ = e_0 = 1`, `P_v = e_0e_0^*`
(real axis). Fix `θ ∈ [0, arcsin η]`. For a non-root internal `v`,

```
μ_v(x_1,…,x_m) = e^{iθ} · ∏_{internal slots i} x_i · ∏_{leaf slots j} ⟨x_j, e_0⟩ ,
```

product in `ℂ`. It is real-multilinear with norm 1 (`|∏x_i| = ∏|x_i|`, gates
have norm 1). On projected inputs every factor is real, so the output is
`e^{iθ}·(real)` and `ρ_v^proj = sin θ ≤ η` — **including arbitrary leaf
vectors**, because leaves enter only through the real functional `⟨·, e_0⟩`
(this is the correction of the historical M18/M19 witness noted in
`CHAIN_GRAM_REPORT.md` §2). By induction `F_v = e^{ik_vθ}`, `R_v = cos^{k_v}θ`.
At the root use `μ_r(x) = Re(λ ∏ x_i ∏⟨x_j,e_0⟩)·e_0`, `|λ| = 1`: norm 1, output
in `Ran P_r`, defect 0, and

```
E^P_T = |Re(λ(e^{i(k−1)θ} − cos^{k−1}θ))| = |1 − (cos θ e^{iθ})^{k−1}| = g_k(θ)
```

for the right `λ`. Maximize over `θ`. `□`

So topology can only *lower* the constant below the chain value; the question is
whether any skeleton does.

## 3. Upper bounds

Normalize `M = L_T = 1`. Two reductions are used repeatedly.

**R1 (unit children).** For a vertex with no internal child the admissible
values form `K = {f : ‖f‖ ≤ 1, ‖Qf‖ ≤ η}` (A5.2). The quantities bounded below
are norms of expressions linear in each such `f`, hence convex, maximized at
extreme points of `K`. After enlarging `Ran P` by one unused direction if
`P = 0` (laws extended by zero; admissibility preserved), every extreme point is
a unit vector. So `f = cos α R̂ + sin α D̂`, `R = P f = cos α R̂`,
`α ∈ [0, arcsin η]`, `R̂ ∈ Ran P`, `D̂ ∈ Ran Q` unit (if `α = π/2` then `η = 1`).

**R2 (complex coordinates on input planes).** Let `Π_a = span_ℝ{R̂_a, D̂_a}`,
identified with `ℂ` by `R̂_a ↦ 1`, `D̂_a ↦ i`. For any real bilinear
`b : Π_a × Π_b → X` into a real inner-product space there are unique real-linear
`U, V : ℂ → X` with `b(z,w) = U(zw) + V(z w̄)` (the four forms
`Re zw, Im zw, Re zw̄, Im zw̄` are a basis of real bilinear forms on `ℂ×ℂ`).
Since `(zw, zw̄)` ranges over the whole torus as `|z| = |w| = 1`,

```
‖b‖ ≤ 1   ⟺   L(p,q) := U(p) + V(q) satisfies ‖L(p,q)‖ ≤ max(|p|,|q|).
```

With `F := (e^{iS}, e^{iΔ})`, `E := (1,1)`, `S = α+β`, `Δ = α−β`, and
`ρ := cos α cos β`: `b(f_a,f_b) = LF` and `b(R_a,R_b) = ρ·LE`.

**Lemma G (Gram form of R2).** Put `f := LF`, `g := LE`, `G := Gram(f,g)`,
`K_S := [[1, cos S],[cos S, 1]]`, `M := K_S − G`. Then

```
(N−)   M_11 ≥ 0,  M_22 ≥ 0,  M_12 ≤ √(M_11 M_22).
```

*Proof.* For `ab ≤ 0`, `|ae^{iS}+b|² = a²+b²+2ab cos S ≥ |ae^{iΔ}+b|²` because
`|Δ| ≤ S ≤ π`. So `‖af+bg‖² ≤ a²+b²+2ab cos S` whenever `ab ≤ 0`, i.e.
`a²M_11 + b²M_22 − 2|ab|M_12 ≥ 0`. `□`

The chain-stage condition is `M ⪰ 0`, i.e. (N−) plus
`(CF)  M_12 ≥ −√(M_11M_22)`. The two differ only by allowing `f` and `g` to be
*more aligned* than a Hilbert contraction permits.

**Lemma S (one chain step from a state).** Let `F̂, Ê` be unit with
`∠(F̂,Ê) = S ∈ [0,π]`, `A` a contraction on `span{F̂,Ê}`, `P` an orthogonal
projector with `‖QAÊ‖ ≤ η`, `ρ ≥ 0`, and `Rot` any isometry moving every unit
vector by an angle `≤ γ`. Then, with `θ := arcsin‖QAÊ‖`,

```
‖AF̂ − ρ P AÊ‖²  ≤ 1 + (ρ cos θ)² − 2ρ cos θ · cos(min(S+θ, π)),
‖AF̂ − ρ cos γ · Rot AÊ‖² ≤ 1 + (ρ cos γ)² − 2ρ cos γ · cos(min(S+γ, π)).
```

*Proof.* Dilate `A` to an isometry `V` as in `CHAIN_ALL_K.md` §2.2 (the closure
bound on `Ê` survives, (D)); apply the angle triangle inequality exactly as in
§2.3 and take first coordinates, which can only shorten the vector. `□`

**Jensen step J.** If `α_1,α_2,α_3 ∈ [0, arcsin η]`,
`r = ∏cos α_j`, `Σ = Σα_j`, then
`1 + r² − 2r cos(min(Σ,π)) ≤ G_{4,chain}(η)²`. (`CHAIN_ALL_K.md` §2.4, `n = 3`.)

### 3.1 CHAIN — Theorem C with `k = 4`.

### 3.2 MIXED

(`CHAIN_GRAM_REPORT.md` §11, restated.) Dilate the two-vertex leg (isometries,
§2.2): its value `F'_a` is unit, `R'_a` has norm `r_a = cos θ_1 cos θ_2` and
`∠(F'_a,R'_a) = α ≤ θ_1+θ_2`. The singleton leg gives `F_b, R_b` with angle
`θ_3`. Extend the root law by the coordinate extraction and scalarize by a unit
`ω ∈ Ran P_r`: a real bilinear form of norm `≤ 1`. By operator/nuclear duality
`E^P ≤ ‖F'_aF_b^T − R'_aR_b^T‖_*` on the two real input planes, and for real
`2×2` matrices `‖K‖_*² = ‖K‖_F² + 2|det K| = 1 + r² − 2r cos(α+θ_3)`,
`r = r_a cos θ_3`. Since `α + θ_3 ≤ Σθ_j`, step J applies. Witness: Theorem U.

### 3.3 BBR — **Theorem K4-BBR** `C^P_BBR(η) = C^P_{4,chain}(η)`

Skeleton `a, b → v → r`. The root reads `e_v := F_v − R_v` losslessly
(`CHAIN_ALL_K.md` §2.1), so `G_BBR = sup ‖μ_v(f_a,f_b) − P_v μ_v(R_a,R_b)‖`.
Apply R1, R2 with `X = H_v`: `e_v = f − ρ P_v g`. Split `f = f_P + f_Q`,
`g = g_P + g_Q`; `G^P, G^Q` their Gram matrices; `G = G^P + G^Q`. Then

```
‖e_v‖² = J(G^P,G^Q) := G^P_11 − 2ρ G^P_12 + ρ² G^P_22 + G^Q_11,     closure: G^Q_22 ≤ η².
```

*Repair.* If (CF) fails, lower `G^P_12` (J increases at rate `2ρ`) and `G^Q_12`
(J unchanged) continuously, keeping `G^P, G^Q ⪰ 0`; `M_12` increases, (N−) is
preserved, diagonals and closure are untouched.

*Case A: (CF) is reached.* Then `G ⪯ K_S`, so there is a contraction `A` on a
Hilbert plane with `∠(F̂,Ê) = S` and `(AF̂, AÊ)` realizing `(G^P, G^Q)` in
`Ran P ⊕ Ran Q`, with `‖QAÊ‖ = √G^Q_22 ≤ η`. Lemma S (first form) and step J with
angles `(α, β, θ)` give `J ≤ G_{4,chain}(η)²`. (`S ∈ {0,π}` by continuity.)

*Case B: both off-diagonals reach `−√(G^•_11 G^•_22)` and (CF) still fails.*
Then with the unit vectors `u = (√G^P_11, √G^Q_11, √M_11)`,
`v = (√G^P_22, √G^Q_22, √M_22)`:
`u·v < κ := −cos S`, so `S > π/2`. At that point
`J ≤ 1 + 2ρ u_1v_1 + ρ² ≤ 1 + 2ρκ + ρ²`, and `ρ ≤ cos²(S/2) = (1−κ)/2`, so
`J ≤ max_κ [1 + κ(1−κ) + (1−κ)²/4] = 4/3`. But `S > π/2` forces
`η² > 1/2 > 3/7`, where `G_{4,chain}(η)² = 81/49 > 4/3`.

Since the repair never decreased `J`, `G_BBR(η) ≤ G_{4,chain}(η)`; Theorem U gives
equality. `□`

### 3.4 STAR — **Theorem K4-STAR** `C^P_STAR(η) = C^P_{4,chain}(η)`

Skeleton `a, b, c → r`. Scalarizing by unit `ω ∈ Ran P_r` gives a real trilinear
form `τ`, `‖τ‖ ≤ 1`, and `E^P ≤ sup_τ [τ(f_a,f_b,f_c) − τ(R_a,R_b,R_c)]`. Apply R1
and order `α ≤ β ≤ γ`. Let `b(z,w) ∈ Π_c ≅ ℂ` be the Riesz vector of
`τ(z,w,·)|Π_c`; `‖b‖ ≤ 1`. R2 with `X = ℂ` gives `f, g ∈ ℂ` with (N−), and with
`F_c = e^{iγ}`, `R_c = cos γ`:

```
τ(f_a,f_b,f_c) − τ(R_a,R_b,R_c) = Re(f̄ e^{iγ}) − r Re(ḡ) ≤ |f − r e^{iγ}g|,     r := ρ cos γ.
```

Write `G_12 = √(G_11G_22) cos ω`. Over the two orientations,
`|f − re^{iγ}g|² ≤ Φ(G) := G_11 + r²G_22 − 2r√(G_11G_22) cos(min(γ+ω, π))`,
which is **non-decreasing in `ω`**, i.e. non-increasing in `G_12`.

*Case A: (CF) holds.* Realize `(f,g) = (AF̂, AÊ)` with `∠(F̂,Ê) = S` and the
orientation attaining `Φ`; then `Φ(G) = |f − r e^{iγ'} g|²` with `γ' = γ` if
`γ + ω ≤ π` and `γ' = π − ω ≤ γ` otherwise. Lemma S (second form, `Rot` = rotation
by `γ'` on `ℂ` extended by the identity, an isometry moving unit vectors by at
most `γ`) and step J with `(α,β,γ)` give `Φ(G) ≤ G_{4,chain}(η)²`.

*Case B1: (CF) fails but `G*_12 := cos S + √(M_11M_22) ≥ −√(G_11G_22)`.* Lower
`G_12` to `G*_12`: the result is PSD, satisfies (CF), and `Φ` did not decrease.
Case A applies.

*Case B2: `cos S + √(M_11M_22) + √(G_11G_22) < 0`.* Put `G_11 = cos²p`,
`G_22 = cos²q`, `p,q ∈ [0,π/2]`. Then `cos(p−q) < κ := −cos S`, so `S > π/2`,
`β > π/4`, `γ > π/4`, and `r < (1−κ)/(2√2)`. Also `Φ ≤ (cos p + r cos q)²`.
Either `q ≥ p + arccos κ`, whence `cos q ≤ κ` and `cos p + r cos q ≤ 1 + κ(1−κ)/(2√2)
≤ 1 + 1/(8√2)`; or `p ≥ q + arccos κ`, whence `cos p + r cos q ≤ κ + (1−κ)/(2√2) ≤ 1`.
So `Φ ≤ (1 + 1/(8√2))² < 1.19 < 81/49 = G_{4,chain}(η)²` (as `η² > 1/2`).

Hence `G_STAR ≤ G_{4,chain}`; Theorem U gives equality. `□`

### 3.5 Arity and leaves

Extra leaf slots at any vertex are frozen (A5.2); a ternary non-root vertex with
one internal child is a linear stage, etc. So 3.1–3.4 cover every tree with four
internal vertices.

## 4. What is not covered, and where topology could first matter

The proofs above use, at a vertex with ≥ 2 internal children, either (i) that the
vertex is the root (nuclear duality), or (ii) that the vertex is followed by the
root only and its children are **singletons** (R1 gives `r = cos α`, used in the
residual cases). Rooted trees on five vertices not covered by Theorem C, MIXED
(its argument extends verbatim to a bilinear root fed by two chains of any
lengths) or Theorem U alone:

| skeleton (k=5) | obstruction |
|---|---|
| `(1→2), 3 → 4 → r` | bilinear vertex with a chain leg, followed by the root: residual case needs `r_a ≤ …` bound for a dilated leg (`r_a > cos α` is possible) |
| `1, 2 → 3 → 4 → r` | bilinear vertex followed by **two** stages: the Gram repair must be shown harmless for a later projection |
| `1, 2, 3 → 4 → r` | ternary internal vertex followed by the root |
| `(1→2), 3, 4 → r` | ternary root with a chain leg: residual case as in row 1 |
| `1, 2 → 3`, `4 → r` | bilinear root with a cherry below one leg |
| `1,2,3,4 → r` | quaternary root (4-fold projective norm) |

Numerically nothing above the chain value has been found at `k = 4`. First
`k = 5` probe (`experiments/k5_cherry_chain_search.py`, real field) for
`1,2 → 3 → 4 → r`: outer search over the cherry vertex (angles, a `ℝ²×ℝ² → ℝ⁴`
law, rank-2 projector), inner **exact upper-bound** Gram SDP for the remaining
stage started from the cherry's `(R_3, e_3)` Gram data (Lemma V applies to any
initial list). The Theorem U witness at the optimal angle reproduces
`G_{5,chain}` inside the SDP; local perturbation (step `0.05 → 10⁻⁴`) and three
random restarts per seed never exceed it by more than solver tolerance:

| η | `G_{5,chain}` | best SDP value found | excess |
|---|---|---|---|
| 0.3 | 1.0557896808 | 1.0557896834 | 2.7·10⁻⁹ |
| 0.5 | 1.3707320125 | 1.3707320182 | 5.7·10⁻⁹ |
| 0.6 | 1.3809009870 | 1.3809009878 | 8.6·10⁻¹⁰ |

This is `NUMERICAL_OBSERVATION` (a local-plus-random search, not a global
certificate), consistent with Conjecture R. An earlier version of the script
initialized the angles at `sigmoid(5)·arcsin η` and never reached the known
lower bound; it was discarded as a failed search, not as evidence. The monotonicity principle behind all repairs —
*extra alignment between the ambient and reduced values never helps the
adversary* — is the natural general conjecture (`RECURSION.md`, Conjecture R).

## 5. Numerical controls (`NUMERICAL_OBSERVATION`)

Cutting-plane LPs on the exact finite reductions (R1+R2 for BBR; real `2×2×2`
projective norm for STAR). For fixed angles (and output direction) each is a
linear program in 8 unknowns with semi-infinite constraints; the separation
oracle is a 2048-point (BBR) / 256² grid (STAR) with local refinement, and every
reported *lower* value is an admissible map rescaled by its verified norm.
Script `experiments/topo_lp.py`; outputs `experiments/outputs/topo_lp_*.json`.

| η | chain `G_4` | BBR best admissible | STAR best admissible |
|---|---|---|---|
| 0.1 | 0.2975012605 | 0.2975012583 | 0.2975012442 |
| 0.3 | 0.8328283136 | 0.8328283080 | 0.8328282942 |
| 0.5 | 1.1924240018 | 1.1924239995 | 1.1924239451 |
| 0.6 | 1.2738100329 | 1.2738100329 | 1.2738099322 |
| √(3/7) | 1.2857142771 | 1.2857142543 | 1.2857142326 |
| 0.8 | 1.2857142191 | 1.2853867291¹ | 1.2857141938 |
| 1.0 | 1.2857141920 | 1.2807763765¹ | 1.2857141431 |

¹ the BBR angle grid (`{0.25,…,1}·arcsin η`) does not contain `arcsin√(3/7)` for
`η ∈ {0.8, 1}`; the LP upper values at the best grid points (1.28538678,
1.28077640) are below the chain value, consistent. In every run the LP *upper* estimate at the
maximizing angles exceeds the chain value by `< 3·10⁻⁸` (grid discretization),
and the maximizer is the equal-angle configuration `α = β (= γ) = min(arcsin η,
arcsin√(3/7))`.

A first implementation placed the BBR closure bound on the wrong matrix entry
and reported `1.0949 > 3η`, violating the proved universal bound
`‖F_v − R_v‖ ≤ 3η`; the violation exposed the bug. The corrected code is the one
recorded here.

## 6. The complex class `PMT-A[C]`

* Upper bounds: every step above passes to complex spaces (real planes,
  `Re⟨·,·⟩`), so `C^P_T(η; PMT-A[C]) ≤ C^P_{4,chain}(η)` for all four skeletons.
* Lower bounds: CHAIN (complex-linear witness) and MIXED (matrices and gates) are
  attained over `ℂ`. For BBR and STAR the witness of Theorem U uses the
  multiplication of `ℝ² ≅ ℂ`; its complex-bilinear extension has norm `√2`.
* **Retention obstruction** at a non-root vertex: if a complex-bilinear `μ` of
  norm 1 had `μ(e_0,e_0) = u`, `μ(e_1,e_0) = μ(e_0,e_1) = v`, `u ⊥ v` unit, then
  expanding `‖μ(e_0 + εz e_1, e_0 + εz' e_1)‖² ≤ (1+ε²|z|²)(1+ε²|z'|²)` at order
  `ε²` forces `Re(z z̄') + Re(z z' ⟨u, μ(e_1,e_1)⟩) ≤ 0` for all `z,z' ∈ ℂ`, which
  forces `⟨u,μ(e_1,e_1)⟩ = −1` from real `z,z'` and then fails for `z = z' = i`.
  So over `ℂ` a bilinear vertex cannot simultaneously **retain** the reduced value
  (`‖u‖ = 1`) and **transport** both first-order errors coherently.
* This does **not** lower the BBR constant at first order: BBR does not need
  retention (the root reads `e_v`). The complex-bilinear form
  `μ(x,y) = xᵀ[[η, 1−η],[1−η, 0]]y` with `P_v = 0` has norm `≤ 1`, closure `η` and
  gives `E^P = 3η + O(η²)`. So `lim_{η↓0} C^P_BBR(η; PMT-A[C]) = 3`; whether the
  second-order coefficient is `5/2` over `ℂ` is **open**. Retention is needed when
  further stages follow the bilinear vertex, so the first skeleton where the field
  could change the *first-order* constant is `k = 5`, `1,2 → 3 → 4 → r`
  (`experiments/first_order_field.py`).
* Random-search comparison (`experiments/bbr_field.py`, same optimizer for both
  fields; `experiments/outputs/bbr_field_search.txt`), best `E^P/η` found:

  | η | chain `C_4` | real, d=2 | real, d=3 | complex, d=2 | complex, d=3 |
  |---|---|---|---|---|---|
  | 0.1 | 2.97501 | 2.96007 | 2.95006 | 2.94802 | 2.93346 |
  | 0.03 | 2.99775 | 2.99462 | — | 2.98203 | — |

  Neither field reaches the chain value (the search is weak: the real field is
  known to attain it). The complex deficit at `η = 0.03` (`0.0157 ≈ 17η²`) is
  larger than the real one (`0.0031`), which is compatible with a larger
  second-order coefficient over `ℂ` but does not establish it. An earlier complex
  run with a conjugation bug in its norm estimator returned ratios above the
  universal bound 3 and is void.
