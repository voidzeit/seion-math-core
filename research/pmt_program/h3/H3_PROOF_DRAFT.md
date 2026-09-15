# H3 — capped-equal-angle reduction: proof draft

```
STATUS:   SUPERSEDED BY LEAN (2026-09-15): PMT.capped_equal_angle / gBox_eq_capped / gBox_eq_capped_max
          in PMTFormal/Heterogeneous/CappedDiagonalFull.lean (build 8732 jobs, standard axioms).
          The Lean proof skips the separate π/Θ rescaling: Θ' = min(Σθ, π) and the tangent
          inequality with Σθ ≥ Σθ^c already cover Θ > π. Independent human review still pending.
PREVIOUS: PROOF DRAFT (on paper), 2026-09-15. Not machine-checked. Not independently reviewed.
EVIDENCE: numeric check h3_numeric_check.py (POST_HOC exploratory, seed 7, 400 random defect
          vectors, n = 2..7): max(multistart optimum − capped-curve maximum) = 1.3e-8 (grid error).
LEAN:     PMTFormal/Heterogeneous/CappedDiagonal.lean still records H3 as a Prop.
```

## Claim

Let `α_i = arcsin η_i ∈ [0, π/2]` and `w(θ) = cos θ · e^{iθ}`. Then

`gBox(η) = max_{τ ∈ [0, π/2]} |1 − ∏_i w(min(α_i, τ))|`.

## Notation

For `θ ∈ box = ∏[0, α_i]`, put `C(θ) = ∏ cos θ_i ∈ [0, 1]` and `Θ(θ) = Σ θ_i`. Then

`|1 − ∏ w(θ_i)|² = h_Θ(C) := 1 + C² − 2C cos Θ`.

The `≥` direction is immediate, because the capped curve lies in the box. For `≤`, fix `θ` in the
box.

## Step 1 — reduce to `Θ ≤ π`

If `Θ > π`, rescale `θ' = (π/Θ) θ`. Then `θ'` is in the box and `Θ(θ') = π`. Moreover
`C(θ') ≥ C(θ)`, because `cos` is decreasing on `[0, π/2]`. Hence

`h_Θ(C) ≤ (1 + C)² ≤ (1 + C')² = h_π(C')`.

This is the argument already machine-checked in `box_capped`.

## Step 2 — `C ≥ cos Θ` on the box when `Θ ≤ π`

- If `Θ ≤ π/2`, this is Lemma 6.1 (`cos_sum_le_prod_cos`): `cos(Σ θ_i) ≤ ∏ cos θ_i`.
- If `π/2 ≤ Θ ≤ π`, then `cos Θ ≤ 0 ≤ C`.

## Step 3 — for fixed `Θ`, larger `C` is better

Since `h_Θ'(c) = 2(c − cos Θ) ≥ 0` for `c ≥ cos Θ`, the function `h_Θ` is nondecreasing on
`[cos Θ, ∞)`. By Step 2, every achievable `C` with that `Θ` lies in this ray. So the value is
maximized by maximizing `C` subject to `Σ θ_i = Θ` and `0 ≤ θ_i ≤ α_i`.

## Step 4 — the capped vector maximizes `∏ cos θ_i` at fixed sum

Choose `τ` with `Σ min(α_i, τ) = Θ`, which exists by continuity since `Θ ≤ Σ α_i`, and put
`θ^c_i = min(α_i, τ)`.

**Case `τ = π/2` with some `α_i = π/2`.** Then `Θ = Σ α_i`, so the only feasible vector is
`θ = α = θ^c`.

**Case `cos θ_i = 0` for some `i`.** Then `C(θ) = 0 ≤ C(θ^c)` and there is nothing to prove.

**Otherwise.** Let `φ = log cos`, which is concave and decreasing on `[0, π/2)`, with
`φ' = −tan`. Concavity gives the tangent inequality
`φ(θ_i) ≤ φ(θ^c_i) + φ'(θ^c_i)(θ_i − θ^c_i)`.

- If `α_i > τ`: then `θ^c_i = τ` and the slope is `−tan τ`.
- If `α_i ≤ τ`: then `θ^c_i = α_i` and `θ_i − α_i ≤ 0`. Since `−tan α_i ≥ −tan τ`, we get
  `φ'(α_i)(θ_i − α_i) ≤ −tan τ · (θ_i − α_i)`.

Summing over `i`:

`Σ φ(θ_i) ≤ Σ φ(θ^c_i) − tan τ · Σ(θ_i − θ^c_i) = Σ φ(θ^c_i)`,

because both vectors have sum `Θ`. So `C(θ) ≤ C(θ^c)`.

## Conclusion

Steps 1–4 give `|1 − ∏ w(θ_i)| ≤ |1 − ∏ w(θ^c_i)|` for some `τ`. Taking the maximum over the box
yields the claim.

## Consequences (if confirmed)

- **Evaluation.** `gBox` becomes a one-dimensional maximization over `τ ∈ [0, max α_i]`. A rigorous
  upper bound needs only a 1-D enclosure (a Lipschitz or interval bound on each `τ`-cell).
- **Structure.** The extremal configuration is water-filling: every angle rises together until it
  hits its own cap.
- **Uniform case.** When all defects are equal, this recovers the Diagonal Lemma (`diagonal_capped`).

## To do

- Independent check of Steps 2–4, especially the edge cases `τ = π/2` and `cos θ_i = 0`.
- Lean formalization. The concave tangent inequality for `log cos` is the main new ingredient.
- Update `CLAIM_NOVELTY_MATRIX_HET.md`: H3 is `KNOWN_IN_SPECIAL_CASE` only for all `η = 1`
  (Farouki–Pottmann; Chaffey–Forni–Sepulchre 2023 Thm 5).
