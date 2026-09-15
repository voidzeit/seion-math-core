# L3 comparison: Tomamichel–Colbeck–Renner (2010) and Tomamichel (2012, 2016), generalized fidelity and purified distance

Prepared 2026-09-14. Level-3 comparison against R6 (spherical-lift angle, multilinear angle contraction,
telescoping proof), R7 (diagonal lemma) and, through R6, the main constant of Theorem R (R1a/R2).
Public sources only; paraphrased. This file covers one cluster: the TCR paper, Tomamichel's thesis,
Tomamichel's SpringerBrief, and one later paper that names the angle explicitly (Sone et al. 2021). It
also records the searches for family 4 of the request (contractive metrics on the Hilbert ball), which
found nothing beyond this cluster.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| TCR10 | M. Tomamichel, R. Colbeck, R. Renner, "Duality between smooth min- and max-entropies", IEEE Trans. Inf. Theory 56(9) (2010) 4674–4681. DOI 10.1109/TIT.2010.2054130. arXiv:0907.5238 | VERIFIED (Crossref metadata; arXiv PDF read) |
| Tom12 | M. Tomamichel, "A Framework for Non-Asymptotic Quantum Information Theory", PhD thesis, ETH Zurich, 2012. arXiv:1203.2142 | VERIFIED (arXiv PDF read) |
| Tom16 | M. Tomamichel, "Quantum Information Processing with Finite Resources — Mathematical Foundations", SpringerBriefs in Mathematical Physics 5, Springer 2016. DOI 10.1007/978-3-319-21891-5. arXiv:1504.00233 | VERIFIED (Crossref metadata; arXiv PDF read) |
| SCBC21 | A. Sone, M. Cerezo, J. L. Beckey, P. J. Coles, "Generalized measure of quantum Fisher information", Phys. Rev. A 104 (2021) 062602. DOI 10.1103/PhysRevA.104.062602. arXiv:2010.02904 | VERIFIED (Crossref metadata; arXiv PDF read) |

## 2. Access level

FULL_TEXT for all four, restricted to the relevant sections:
- TCR10: §II (Definition 2, Lemmas 3, 5–8, Corollary 9).
- Tom12: Ch. 3 (Table 3.1, Definition 3.2, Lemma 3.1, Definition 3.3, Propositions 3.2–3.3, Theorem 3.4,
  Theorem 3.5, Corollary 3.6, Lemmas 3.7–3.8).
- Tom16: §3.3.1–3.4 (Definition 3.12, eqs. (3.38)–(3.45), Proposition 3.13, Corollary 3.14,
  Definition 3.15, Proposition 3.16, eq. (3.53)).
- SCBC21: Definitions 2 and 5, Lemma 4 and its proof (Appendix E).

## 3. Their setting

- Sub-normalized density operators ρ (positive, tr ρ ≤ 1) on a finite-dimensional complex Hilbert space.
- Fidelity F(ρ,τ) = ‖√ρ √τ‖₁ (TCR10, Tom12: not squared; Tom16 uses the squared convention F*).
- Generalized fidelity F̄(ρ,τ) = F(ρ,τ) + √((1 − tr ρ)(1 − tr τ)); purified distance P = √(1 − F̄²).
- Maps: completely positive, trace-non-increasing (includes compressions ρ ↦ TρT* with ‖T‖ ≤ 1 and
  projections ρ ↦ ΠρΠ).

**Pure-vector specialization.** For ρ = |f⟩⟨f|, τ = |g⟩⟨g| (tr ρ = ‖f‖²), F̄ becomes
|⟨f,g⟩| + √(1 − ‖f‖²) √(1 − ‖g‖²). Tom16 eq. (3.39) writes exactly this formula for vectors (in the
purification form of Uhlmann's theorem).

**Relation to our φ.** Our cos φ(f,g) = ⟨f,g⟩ + √(1 − ‖f‖²) √(1 − ‖g‖²) uses the real, signed inner product.
Hence cos φ(f,g) ≤ F̄(f,g), with equality iff ⟨f,g⟩ ≥ 0, and arccos F̄(f,g) = min{φ(f,g), φ(f,−g)}
(checked by hand; an informal random check in a scratch script agrees). So arccos F̄ is the projective
(phase-quotient) version of our angle; φ keeps the sign, which the telescoping and (N−) steps need.

**The lift.** TCR10 Lemma 3 / Tom12 Lemma 3.1 show that F̄(ρ,τ) equals the ordinary fidelity of the
extensions ρ̂ = ρ ⊕ (1 − tr ρ) and τ̂ = τ ⊕ (1 − tr τ) on H ⊕ C, and that F̄ is the supremum of the fidelity
over all normalized states on a larger space that compress to ρ and τ. For pure states, |f⟩⟨f| ⊕ (1 − ‖f‖²)
has the same fidelity with the corresponding extension of g as the pure lift (f, √(1 − ‖f‖²)) when
⟨f,g⟩ ≥ 0. Our hemisphere lift is therefore the vector form of their extension, up to the sign issue above.

## 4. Relevant results (paraphrased)

- TCR10 Lemma 3 / Tom12 Lemma 3.1: closed formula for F̄ via the one-dimensional extension (the lift).
- TCR10 Lemma 5: P is a metric. The proof goes through purifications of the extensions and the trace-distance
  triangle inequality.
- Tom12 Proposition 3.2 (metric property of P): the proof uses the **triangle inequality of the angular
  distance A = arccos F on the extensions** ρ̂, σ̂, τ̂, i.e. A(ρ̂,τ̂) ≤ A(ρ̂,σ̂) + A(σ̂,τ̂), together with
  A(ρ̂,τ̂) = arccos F̄(ρ,τ) = arcsin P(ρ,τ). It also gives the sharper form P(ρ,τ) ≤ sin(A₁ + A₂) (eqs. 3.7–3.9).
  Tom16 Proposition 3.16 repeats this, with the explicit remark (3.53) that P ≤ sin φ and P ≤ sin ϑ imply
  P ≤ sin(φ + ϑ) when φ + ϑ ≤ π/2.
- SCBC21 Appendix E: names the "generalized angular distance" arccos F̄ on sub-normalized states
  (angles in [0, π/2]) and cites TCR10/Tom16 for its triangle inequality.
- TCR10 Lemma 7 / Tom12 Theorem 3.4 / Tom16 Proposition 3.13: F̄ does not decrease (P does not increase)
  under trace-non-increasing CP maps. Proof: split the map into an isometry, a projection and a partial trace.
  For the projection, TCR10/Tom12 use the sup-over-extensions definition; Tom16 uses an explicit trace-preserving
  map on the extended space that sends ρ̂ to ΠρΠ ⊕ (1 − tr Πρ) (eq. 3.43). This is the lift-plus-dilation idea.
- Tom12 Lemma 3.8: P(ρ, ΠρΠ) ≤ √(2 tr(Π^⊥ρ) − tr(Π^⊥ρ)²), for the *unrenormalized* compression.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| Lemma A (φ is a metric on the ball) | KNOWN | arccos F̄ satisfies the triangle inequality on sub-normalized states. It is used inside the proof of Tom12 Prop. 3.2 and Tom16 Prop. 3.16 through the one-dimensional extension, and SCBC21 App. E states it with credit to TCR10/Tom16. Our version keeps the sign (real inner product), so it is the great-circle distance between lifted unit vectors in G ⊕ R. This is a trivial translation: same lift, spherical triangle inequality. It is not literally the same function, because arccos F̄ = min{φ(f,g), φ(f,−g)}. |
| Lemma C (contraction monotonicity) | KNOWN_IN_SPECIAL_CASE | For f = Tx, g = Ty with ‖T‖ ≤ 1, the map ρ ↦ TρT* is CP and trace-non-increasing, so TCR10 Lemma 7 / Tom12 Thm 3.4 give monotonicity of arccos F̄, i.e. the absolute-value version. The signed version does not follow formally, because the absolute value discards the sign of ⟨Tx,Ty⟩ versus ⟨x,y⟩. It does follow from the same dilation idea: embed x ↦ (Tx, (I − T*T)^{1/2}x, √(1 − ‖x‖²)) and apply Cauchy–Schwarz. Our Gram-domination hypothesis ‖sf + tg‖ ≤ ‖sx + ty‖ for all s,t is equivalent to the existence of a contraction on span{x,y} with x ↦ f, y ↦ g, so nothing more general is claimed. |
| Theorem D (multilinear angle contraction) | ADJACENT | Not stated. For μ = tensor product, the absolute-value analogue arccos F̄(ρ₁⊗ρ₂, σ₁⊗σ₂) ≤ arccos F̄(ρ₁,σ₁) + arccos F̄(ρ₂,σ₂) follows from their metric property plus monotonicity: tensoring with a fixed sub-normalized state is a trace-non-increasing CP map, and one telescopes. General contractive multilinear maps and the signed version: NOT_FOUND. |
| (N−) / tensor-angle inequality | ADJACENT | Closest: the angle-addition form P ≤ sin(A₁ + A₂) (Tom12 (3.7)–(3.9), Tom16 (3.53)) and the purified-distance ↔ trace-distance bounds. The vector bound ‖f − tg‖ ≤ \|1 − t e^{iS}\| for sub-normalized vectors (one AM–GM step beyond the law of cosines) is NOT_FOUND. The unit-vector case is the law of cosines. |
| Projection step φ(g, Pg/√(1−q²)) = arcsin q | KNOWN_IN_SPECIAL_CASE | In lifted form this is the elementary identity that a unit vector and its renormalized projection meet at angle arccos‖Π ψ‖, applied with the projector P ⊕ 1 on G ⊕ R. Tom16 (3.43) uses exactly this extended projector (identity on the extra coordinate) to prove monotonicity. Tom12 Lemma 3.8 gives only an inequality for the unrenormalized compression, and it is weaker. The exact renormalized identity is not stated. |
| R7 diagonal lemma | NOT_FOUND | No product-of-angles or equal-angle extremization. |

## 6. Threat score

- **Main theorem (sharp constant C_k(η), R1a/R2): 2 / 5** (shared technique). Nothing about projected
  multilinear computations, error constants or sharpness.
- **Technique known: YES (partially).** The lift, the angle metric (Lemma A) and contraction monotonicity
  (Lemma C, absolute-value form) are known quantum-information facts. The signed real version, the multilinear
  telescoping (Theorem D) and (N−) are not stated there.

## 7. How to cite / credit in the proof section

Suggested sentence:

> The quantity cos φ(f,g) = ⟨f,g⟩ + √(1−‖f‖²)√(1−‖g‖²) is the real, sign-retaining vector analogue of the
> generalized fidelity of Tomamichel, Colbeck and Renner [TCR10, Lemma 3; Tom16, eq. (3.39)], and the lift
> f ↦ (f, √(1−‖f‖²)) is the vector form of their extension ρ ↦ ρ ⊕ (1 − tr ρ). Lemma A and Lemma C are the
> corresponding analogues of the triangle inequality for the angular distance on sub-normalized states
> [Tom12, proof of Prop. 3.2; Tom16, Prop. 3.16] and of its monotonicity under trace-non-increasing completely
> positive maps [TCR10, Lemma 7; Tom12, Thm. 3.4]. We include short proofs because the signed version needed
> here does not follow formally from the absolute-value version.

Do not claim novelty for the lift, Lemma A or Lemma C. If novelty is claimed at all, restrict it to
Theorem D in the generality of contractive multilinear maps and to its use for the sharp constant.

## Appendix: family-4 searches (contractive metrics on the Hilbert ball)

Web searches for a metric on the closed unit ball that does not increase under linear contractions, for the
angle between (x, √(1−‖x‖²)) lifts, and for Bures angles of sub-normalized vectors returned only this cluster
(generalized fidelity / purified distance / generalized angular distance) and generic Hilbert-metric or
hyperbolic material. The hyperbolic and Carathéodory-type metrics are Möbius-invariant, which φ is not, so
they are not relevant here. No source outside quantum information was found that defines φ. Status for
family 4: nothing beyond this cluster; logged here instead of in a separate file.
