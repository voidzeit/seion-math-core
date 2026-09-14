# The free chain at every depth: exact constant, second-order coefficient

Status: **ADVISORY_PROOF_DRAFT** (2026-09-13), pending independent human review.
Class: `PMT-A` (`ADMISSIBLE_CLASS_PMT_A.md`); every upper bound also holds for
`PMT-A[C]`, and the witness is complex-linear, so the theorem holds verbatim
over `ℂ`.

This generalizes the `k=4` argument of `k4_exploration/CHAIN_GRAM_REPORT.md`
§§3–6 (itself `ADVISORY_PROOF_DRAFT`, audited in
`CHAIN_PROOF_AUDIT_20260910.md`) to every `k`, and replaces the fitted
conjecture `a_k = (k−2)(2k−3)/4`, which is **false from `k=5` on**.

---

## 1. Statement

Let `n := k − 1 ≥ 1` and

```
w(θ) := cos θ · e^{iθ} = (1 + e^{2iθ})/2,        g_k(θ) := |1 − w(θ)^n|.
```

**Theorem C (free chain).** For the chain skeleton with `k` internal vertices
and every `η ∈ (0,1]`,

```
G_{k,chain}(η) = max_{0 ≤ θ ≤ arcsin η} g_k(θ),        C^P_{k,chain}(η) = G_{k,chain}(η)/η.
```

Equivalently, with `s = sin²θ`, `g_k(θ)² = E_k(s)` is a polynomial with
`E_k(0)=0`, `E_k'(0) = n²`. If `E_k` has a unique critical point
`s_c(k) ∈ (0, sin²(π/n))` — **verified exactly for `3 ≤ k ≤ 12`, open in
general** — then

```
C^P_{k,chain}(η) = √E_k(η²)/η          for η² ≤ s_c(k),
C^P_{k,chain}(η) = √E_k(s_c(k))/η       for η² ≥ s_c(k).
```

| k | `E_k(s)` | `s_c` | `G^max_k` | `a_k` |
|---|---|---|---|---|
| 2 | `s` | 1 | 1 | 0 |
| 3 | `s(4−3s)` | 2/3 | `2/√3` | 3/4 |
| 4 | `s(9−15s+7s²)` | 3/7 | 9/7 | 5/2 |
| 5 | `s(4−3s)(4−8s+5s²)` | `3/5−√21/15` | 1.380900987 | 11/2 |
| 6 | `s(25−100s+160s²−115s³+31s⁴)` | `(15−√70)/31` | 1.452990673 | 10 |
| 7 | `s(4−3s)(1−3s+3s²)(9−15s+7s²)` | root of `63x³−109x²+53x−6` | 1.509590371 | 65/4 |

(k = 2…12 in `experiments/outputs/chain_constants_table.json`.)

**Corollary C.1 (second order).**

```
C^P_{k,chain}(η) = (k−1) − a_k η² + b_k η⁴ + O(η⁶),     a_k = (k−1)(k−2)(k+6)/24.
```

`a_3 = 3/4`, `a_4 = 5/2`, `a_5 = 11/2`, `a_6 = 10`, `a_7 = 65/4`;
`b_3 = −9/64`, `b_4 = 1/8`, `b_5 = 55/32`, `b_6 = 6`.
The formula `(k−2)(2k−3)/4` agrees only at `k = 3, 4` (a quadratic and a cubic
through two points) and gives `a_5 = 21/4 ≠ 11/2`.

**Corollary C.2 (depth limits).** With `n = k−1`, `G^max_k := max_η G_{k,chain}(η)`
and `η_c(k) := sin θ*_k`, where `θ*_k` is the smallest maximizer of `g_k`:

1. `1 + cos^n(π/n) ≤ G^max_k < 2`; hence **`G^max_k → 2`**.
2. `θ*_k ∈ (0, π/n]`; hence **`η_c(k) ≤ sin(π/(k−1)) → 0`**.
3. `C^P_{k,chain}(1) = G^max_k < 2` for every `k`.

*Proof.* By §2.4 the maximum of `g_k` over `[0, π/2]` is attained on `[0, π/n]`,
giving 2. At `θ = π/n`, `w^n = −cos^n(π/n)`, so `g_k(π/n) = 1 + cos^n(π/n)`; and
`g_k(θ) ≤ 1 + cos^nθ < 2` for `θ > 0`, with `g_k(0) = 0`. Finally
`cos^n(π/n) = exp(n log cos(π/n)) = exp(−π²/(2n) + O(n^{−3})) → 1`. `□`

**Not proved:** that `G^max_k` is increasing in `k`, or that `η_c(k)` is
decreasing. Numerically (`k ≤ 1600`) both hold, with
`G^max_k = 2 − π²/(2k) + o(1/k)` (`k(2 − G^max_k) = 4.924` at `k = 1600`, vs
`π²/2 = 4.935`) and `k·η_c(k) → π` (`3.1396` at `k = 1600`).

---

## 2. Proof

Normalize `M = L_T = 1`, `ρ = η` (Lemma A5.1).

### 2.1 Operator reduction

Label the chain `1 → 2 → ⋯ → k = r`. By Lemma A5.2 vertex 1 carries a vector
`f` with `‖f‖ ≤ 1`, `‖Q_1 f‖ ≤ η`; write it as `A_1 : ℝ → H_1`, `A_1(1) = f`,
with `P_0 := I` on `H_0 := ℝ`, `x := 1`. Vertex `j ≥ 2` becomes a linear
contraction `A_j : H_{j−1} → H_j` with `‖Q_j A_j P_{j−1}‖ ≤ η` (closure over
the *whole* `Ran P_{j−1}`). Then

```
F_j = A_j F_{j−1},    R_j = P_j A_j R_{j−1},    F_0 = R_0 = x,
E^P = ‖P_k A_k (F_{k−1} − R_{k−1})‖ ≤ ‖F_{k−1} − R_{k−1}‖ =: ‖e_n‖,
```

because `P_k A_k R_{k−1} = R_k`. Conversely every vector `e_n` is read without
loss by the rank-one contraction `A_k = e_0 ⟨e_n/‖e_n‖, ·⟩`, `P_k = e_0e_0^*`,
whose closure defect is 0. So `G_{k,chain} = sup ‖e_n‖` over `n` active stages.

### 2.2 Budget-preserving isometric dilation

Put `H'_0 = H_0`, `H'_j = H_j ⊕ H'_{j−1}`, `π_j : H'_j → H_j` the first
coordinate, `π_0 = I`, and recursively

```
B_j := A_j π_{j−1},    V_j z := (B_j z, (I − B_j^*B_j)^{1/2} z),    P'_j := P_j ⊕ I.
```

`B_j` is a contraction, so `V_j^*V_j = I`: **`V_j` is an isometry**. One checks
`π_j V_j = A_j π_{j−1}` and `π_j P'_j = P_j π_j`, so the dilated evaluations
`F'_j = V_jF'_{j−1}`, `R'_j = P'_jV_jR'_{j−1}` satisfy `π_jF'_j = F_j`,
`π_jR'_j = R_j`, hence `‖e_n‖ ≤ ‖F'_n − R'_n‖`. Moreover `Q'_j = Q_j ⊕ 0` and

```
Q'_j V_j P'_{j−1} = (Q_j A_j P_{j−1} π_{j−1}, 0),     ‖Q'_j V_j P'_{j−1}‖ ≤ η,       (D)
```

an identity on all of `Ran P'_{j−1}`: the dilation keeps the global closure
budget. (Over `ℂ` the same holds.)

### 2.3 One-step angle lemma

**Lemma C.3.** Let `V` be an isometry, `P` an orthogonal projector with
`‖Q V u‖ ≤ η‖u‖` for a given vector `u ≠ 0`, `y := Vu`, `R := Py`. Then
`‖R‖ = ‖u‖ cos θ` and `∠(y, R) = θ` for a real angle `θ ∈ [0, arcsin η]`,
where `∠(a,b) := arccos(Re⟨a,b⟩/(‖a‖‖b‖))`.

*Proof.* `‖y‖ = ‖u‖`, `‖Qy‖ ≤ η‖u‖`, `‖Py‖² + ‖Qy‖² = ‖y‖²` and
`Re⟨y, Py⟩ = ‖Py‖²`. Put `sin θ := ‖Qy‖/‖y‖`. `□`

Apply it at stage `j` with `u = R'_{j−1} ∈ Ran P'_{j−1}` (legitimate by (D)).
With `r_j := ‖R'_j‖`, `ψ_j := ∠(F'_j, R'_j)` and `F'_j` unit (isometries):

```
r_j = r_{j−1} cos θ_j,     ψ_j ≤ ψ_{j−1} + θ_j,     θ_j ∈ [0, arcsin η],
```

the second by the triangle inequality for the angular metric on the unit sphere
of the real Hilbert space `(H'_j, Re⟨·,·⟩)`, since `∠(F'_j, V_jR'_{j−1}) =
ψ_{j−1}` (isometry) and `∠(V_jR'_{j−1}, R'_j) = θ_j`. Starting from
`r_0 = 1`, `ψ_0 = 0`:

```
r := r_n = ∏ cos θ_j,     ψ := ψ_n ≤ min(S, π),     S := Σ θ_j.
```

(If some `R'_j = 0` then `e_n = F'_n`, `‖e_n‖ = 1`, covered below.)

### 2.4 Scalar optimization

`‖F'_n − R'_n‖² = 1 + r² − 2r cos ψ ≤ 1 + r² − 2r cos(min(S,π))`.

*Case `S ≤ π`.* By concavity of `log cos` on `[0, π/2)`,
`r ≤ b := cos^n(S/n)`. Also `r ≥ cos S` (iterating
`cos(A+B) = cos A cos B − sin A sin B ≤ cos A cos B` for `A ∈ [0,π]`,
`B ∈ [0,π/2]`). Since `(b² − r²) − 2cos S (b − r) = (b − r)(b + r − 2 cos S) ≥ 0`,

```
‖e_n‖² ≤ 1 + b² − 2b cos S = |1 − cos^n(S/n) e^{iS}|² = g_k(S/n)²,
```

and `S/n ≤ arcsin η`, `S/n ≤ π/n`.

*Case `S > π`.* `‖e_n‖ ≤ 1 + r ≤ 1 + cos^n(S/n) ≤ 1 + cos^n(π/n) = g_k(π/n)`,
and `π/n < S/n ≤ arcsin η`.

Hence `G_{k,chain}(η) ≤ max_{0≤θ≤min(arcsin η, π/n)} g_k(θ)`.

### 2.5 Witness

`P = diag(1,0)` on `ℝ²` at every vertex, `θ ∈ [0, arcsin η]`, `c = cos θ`,
`t = sin θ`, `A_1(1) = (c,t)`, `A_2 = ⋯ = A_n = [[c,−t],[t,c]]`, reader
`A_k` as in 2.1. All norms are 1; `‖Q_1 A_1‖ = t`,
`‖Q A_j P‖ = t` on the whole `Ran P`; root defect 0. Then
`F_n = e^{inθ}`, `R_n = c^n` (identifying `ℝ² ≅ ℂ`), so
`‖e_n‖ = |e^{inθ} − c^n| = g_k(θ)`. The multilinear lift
`μ_j(z, ℓ) = ⟨ℓ, e_0⟩ A_j z` is PMT-A-admissible, and complex-linear over `ℂ`.
Taking the best `θ ≤ arcsin η` gives the lower bound; the upper bound of 2.4
is at most this (the witness is admissible for every `θ ≤ arcsin η`, so the
maximum over `[0, arcsin η]` cannot exceed the maximum over `[0, min(arcsin η,
π/n)]`). `□`

### 2.6 Closed forms and Corollary C.1

`cos(nθ)` and `cos^{2n}θ` are polynomials in `s = sin²θ` after pairing, so
`E_k(s) := 1 + (1−s)^n − 2(1−s)^{n/2} cos(nθ)` is a polynomial
(`experiments/chain_constants_table.py` checks this symbolically for
`k ≤ 12`). Expansion: `log w = iθ + log cos θ = iθ − θ²/2 − θ⁴/12 + O(θ⁶)`, so
`X := n log w = inθ − nθ²/2 + O(θ⁴)` and

```
|1 − e^X|² = n²θ² + (n²/4 − n³/2 − n⁴/12) θ⁴ + O(θ⁶),
g_k = nθ (1 + (1/8 − n/4 − n²/24) θ² + O(θ⁴)),
θ = arcsin η = η + η³/6 + O(η⁵),
C = g_k/η = n − n(n² + 6n − 7)/24 · η² + O(η⁴) = n − n(n−1)(n+7)/24 · η² + O(η⁴).
```

With `n = k−1`: `a_k = (k−1)(k−2)(k+6)/24`. The script asserts this identity
against the exact series for `k = 2,…,12` and finds exactly one interior
critical point of `E_k` on `(0, sin²(π/n))` for every `3 ≤ k ≤ 12`, which gives
the two-regime form of Theorem C in that range (for general `k` the
`max` form of Theorem C is what is proved).

---

## 3. Independent computational controls (not premises)

1. **Exact Gram SDP** (`k4_exploration/chain_gram_sdp.py`, an exact variational
   model of the chain class, §7 of the k=4 report): Clarabel optimum vs Theorem C
   at `η ∈ {0.02,…,1}`, `k = 3,…,6`: agreement to `≤ 1.6·10⁻⁶` (solver
   tolerance) at every point. At `k = 5`, `η = 0.05`:
   `(4 − C_SDP)/η² = 5.495679`, prediction `11/2 − (55/32)η² = 5.495703`,
   refuted value `21/4`. Log: `experiments/outputs/sdp_scan.txt`.
2. **Exact rational certificates** at `(k,η) ∈ {(3,3/5),(3,4/5),(4,3/5),
   (4,5/13),(4,8/17),(5,5/13),(5,8/17)}`: the SDP optimum is certified equal to
   `E_k(η²)` in exact arithmetic (`EXACT_CERTIFICATES.md`).

## 4. Consequences for the program

* `a_T` is **not** `(k−2)(2k−3)/4`. The data `3/4, 5/2` came from `k = 3, 4`,
  which cannot distinguish the two formulas.
* The extremal recursion for chains is one-dimensional in `ℂ`: the state
  `z_j := r_j e^{iψ_j}` evolves as `z_j = z_{j−1} · cos θ_j e^{iθ_j}` and the
  extremum is the equal-angle orbit (`RECURSION.md`).
* The first coefficient beyond `k−1` is cubic in depth: `a_k ~ k³/24`.
