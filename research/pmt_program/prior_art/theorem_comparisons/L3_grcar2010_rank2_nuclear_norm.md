# L3 comparison: projective (nuclear) norm of a sum of two elementary tensors — Grcar (2010) and Friedland–Lim (2018)

Prepared 2026-09-14. Level-3 comparison for the tensor-angle inequality (N−) of R6, read as a bound on the
projective tensor norm ‖a·u₁⊗…⊗u_m + b·v₁⊗…⊗v_m‖_π. Public sources only; paraphrased. One cluster:
the closest exact formula found (matrix case, m = 2) and the standard reference on tensor nuclear norms (m ≥ 3).

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| Grc10 | J. F. Grcar, "Nuclear norms of rank 2 matrices for spectral condition numbers of full rank linear least squares solutions", arXiv:1003.2733 (2010) | VERIFIED (arXiv PDF read; journal publication not checked) |
| FL18 | S. Friedland, L.-H. Lim, "Nuclear norm of higher-order tensors", Math. Comp. 87 (2018) 1255–1281. DOI 10.1090/mcom/3239. arXiv:1410.6072 | VERIFIED (Crossref metadata; arXiv PDF read) |

Also screened, not relevant: Eisenmann–Uschmajew, arXiv:2111.12611 (spectral/Frobenius ratio of rank-two
tensors); Rudra–Jivulescu, arXiv:2508.07933 (numerical projective norms); Núñez-Alarcón–Pellegrino–Santos,
arXiv:2609.04469 (injective/projective distortion in ℓ_p). Web searches for a projective or nuclear norm of
"u⊗v + x⊗y" in terms of angles, for two-term superpositions of product states, and for tensor nuclear norms of
rank two found nothing further.

## 2. Access level

- Grc10: FULL_TEXT of §4 (eq. 4.15) and §6.4 (Lemma 6.3 with proof).
- FL18: FULL_TEXT scan. Lemma 4.1 (dual certificate for nuclear decompositions), Corollary 4.2 (orthogonally
  decomposable tensors), §6 (Lemmas 6.1–6.2: real versus complex nuclear norms), Theorems 8.1/8.10
  (NP-hardness).

## 3. Their setting

- Grc10: real matrices. The nuclear (trace) norm of u₁v₁ᵀ + u₂v₂ᵀ is used as a tool for least-squares
  condition numbers.
- FL18: nuclear and spectral norms of d-way tensors over R and C: duality, nuclear decompositions,
  dependence on the base field, computational hardness.

## 4. Relevant results (paraphrased)

- **Grc10 Lemma 6.3.** For real vectors, ‖u₁v₁ᵀ + u₂v₂ᵀ‖_* = √(A² + B² + 2AB cos(θ_u − θ_v)), where A, B
  are the norm products of the two rank-one terms and θ_u, θ_v ∈ [0,π] are the angles between u₁,u₂ and
  between v₁,v₂. Proof: 2×2 orthonormal representation, Frobenius norm plus determinant.
  - *Translation to our notation (analyst check).* Take a·u₁⊗u₂ + b·v₁⊗v₂ with unit vectors, angles ψ₁, ψ₂,
    and ab ≤ 0. Absorb the sign into one factor (angle ψ₁ ↦ π − ψ₁). This gives
    ‖·‖_π = √(a² + b² + 2ab cos(ψ₁ + ψ₂)) = |a e^{i(ψ₁+ψ₂)} + b|. So for m = 2 and ψ₁ + ψ₂ ≤ π our
    tensor-angle bound holds **with equality**. An informal random check against SVD in a scratch script agrees to
    machine precision. For m = 2, the projective norm of a Hilbert–Hilbert tensor is the trace norm.
- **FL18 Lemma 4.1.** A decomposition attains the nuclear norm iff a spectral-norm-one tensor certifies it.
  This is the standard duality that lets a single norm-one multilinear form certify a lower bound.
- **FL18 §6.** For d ≥ 3, nuclear and spectral norms depend on the field. The examples come from real and
  imaginary parts of complex products (tensors like Re(z⊗z̄⊗z̄)).
- **FL18 Thms 8.1, 8.10.** Nuclear norms are NP-hard for d ≥ 3 over R (d ≥ 4 over C), so closed forms exist
  only for special families.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| Lemma A | NOT_FOUND | No angle metric. |
| Lemma C | NOT_FOUND | — |
| Theorem D | NOT_FOUND | — |
| (N−) / tensor-angle inequality | KNOWN_IN_SPECIAL_CASE | m = 2: exact formula in Grc10 Lemma 6.3 (after the sign translation above), and elementary by SVD of a rank-2 matrix. m ≥ 3: NOT_FOUND. No formula or bound for ‖a⊗u_i + b⊗v_i‖_π in terms of Σψ_i was found. FL18 shows closed forms are rare in general, which gives the special family some interest. |
| Projection step | NOT_FOUND | — |
| R7 diagonal lemma | NOT_FOUND | — |

**Analyst observation (not a literature finding; to be checked before use).** In real Hilbert spaces the
tensor-angle bound is exact for every m, whenever ab ≤ 0 and S = Σψ_i ≤ π.
- Lower bound: in each plane span{u_i, v_i} pick orthonormal coordinates with u_i ↦ 1 and v_i ↦ e^{iψ_i}.
  The real multilinear form (x₁,…,x_m) ↦ Re(e^{−iα} ∏_i ⟨x_i⟩_C), with ⟨x⟩_C the complex coordinate of the
  orthogonal projection to the plane, has norm ≤ 1. With α chosen suitably it takes the value |a + b e^{iS}|.
  Projective-norm duality (norm-one multilinear forms) then gives ‖·‖_π ≥ |a + b e^{iS}|.
- Upper bound: this is our (N−) applied to scalar-valued contractive multilinear forms.

So (N−) yields the closed formula ‖a·⊗u_i + b·⊗v_i‖_π = |a e^{iS} + b| (real case, ab ≤ 0, S ≤ π), which
extends Grc10 Lemma 6.3 from m = 2 to all m. The complex-field version was not examined. If the paper states this
formula, credit Grc10 for m = 2 and label the general-m statement as ours pending a further targeted search
(MathSciNet: nuclear norm, rank-two tensors, 15A69/46B28).

## 6. Threat score

- **Main theorem (sharp constant C_k(η)): 1 / 5** (same broad field). Tensor-norm computations, no projected
  computations.
- **Technique known: NO** for the angle/lift technique. The m = 2 exact formula for the inequality is known
  (Grc10), but it is proved by SVD, not by angle contraction.

## 7. How to cite / credit in the proof section

Suggested sentence:

> For m = 2 the tensor angle inequality is an equality: it reduces to the classical expression of the trace
> norm of a rank-two matrix in terms of the angles between the factors (see e.g. [Grc10, Lemma 6.3]). For m ≥ 3
> we are not aware of a comparable statement; exact nuclear norms of higher-order tensors are in general hard to
> compute [FL18].
