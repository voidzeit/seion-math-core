# L3 comparison: hybrid argument (Bennett–Bernstein–Brassard–Vazirani 1997) and its angle version (Dohotaru–Høyer 2009)

Prepared 2026-09-14. Level-3 comparison against R6 (telescoping proof of the multilinear angle contraction),
R7 (diagonal lemma) and the main constant (R1a/R2). Public sources only; paraphrased. This is one cluster:
the original hybrid argument, the angle version, and a recent survey used to confirm the standard form.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| BBBV97 | C. H. Bennett, E. Bernstein, G. Brassard, U. Vazirani, "Strengths and weaknesses of quantum computing", SIAM J. Comput. 26(5) (1997) 1510–1523. DOI 10.1137/S0097539796300933. arXiv:quant-ph/9701001 | VERIFIED (Crossref metadata; arXiv PDF read) |
| DH09 | C. Dohotaru, P. Høyer, "Exact quantum lower bound for Grover's problem", Quantum Inf. Comput. 9(5&6) (2009) 533–540 | VERIFIED (open publisher PDF at rintonpress.com read; arXiv identifier not checked) |
| Ham25 | Y. Hamoudi, "A brief introduction to quantum query complexity", arXiv:2508.08852 (2025) | VERIFIED (arXiv PDF read, §2) |

## 2. Access level

- BBBV97: FULL_TEXT of §3.1 (Theorem 3.1, Definition 3.2, Theorem 3.3 with proof, Corollary 3.4).
- DH09: FULL_TEXT of §§2–3 (Lemmas 1–5 with proofs; the conclusion was not read in detail).
- Ham25: FULL_TEXT of §2.1 (Theorem 10 "hybrid method", Corollary 11, the "why hybrid" paragraph).

## 3. Their setting

- Quantum query algorithms: unit vectors evolved by unitaries U_t alternating with oracle unitaries O_x.
- BBBV97 Theorem 3.3: replacing the oracle answers on a set of (time, query) pairs changes the final state by
  at most ε in Euclidean norm. Proof: telescoping sum of per-step errors, unitary invariance of the norm, then
  Cauchy–Schwarz on the per-step error magnitudes.
- DH09 run the same three-step proof twice, with Euclidean distance and with the "quantum angle"
  ∡(ψ,ψ′) = arccos(|⟨ψ,ψ′⟩|/(‖ψ‖‖ψ′‖)), and noted to satisfy the triangle inequality (and to extend to mixed states via
  fidelity). Using angles gives Zalka's exact optimality of Grover search.

## 4. Relevant results (paraphrased)

- **BBBV97 Thm 3.3 / Ham25 Thm 10.** Distance between final states of two hybrid runs ≤ sum over steps of
  the per-step perturbation norms (telescoping + triangle inequality + unitary invariance).
- **DH09 Lemma 4 (increase in angle).** The average angle between the final states for the identity oracle
  and oracle y is ≤ 2TΘ, Θ = arcsin(1/√N). Proof: telescope over the hybrid states that switch oracle after
  i queries, use the triangle inequality for angles, and use unitary invariance to reduce each term to the
  angle between Ψ_i and O_yΨ_i.
- **DH09, inside Lemma 4.** With θ = arcsin ‖Π_y Ψ_i‖, the angle between Ψ_i and the reflected state
  O_yΨ_i = (I − 2Π_y)Ψ_i is arccos|cos 2θ| ≤ 2θ.
- **DH09 Lemma 2 (Cauchy–Schwarz, angle version).** The maximum of Σθ_i subject to θ_i ∈ [0, π/2] and
  Σ sin²θ_i ≤ 1 is N·arcsin(1/√N), attained at equal angles. Proof by pairwise averaging (smoothing), with Jensen
  mentioned as an alternative.
- **DH09 Lemma 5.** Converts final-state separation into success probability.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| Lemma A (φ is a metric on the ball) | KNOWN_IN_SPECIAL_CASE | DH09 use the triangle inequality of the projective angle arccos(\|⟨ψ,ψ′⟩\|/‖ψ‖‖ψ′‖) as known. This covers unit (or direction-only) vectors. The sub-normalized lift and the signed version are absent. |
| Lemma C (contraction monotonicity) | NOT_FOUND | Only unitary invariance of angle/norm is used. There are no contractions or sub-normalized states. |
| Theorem D (multilinear angle contraction) | ADJACENT (strong, for the proof scheme) | DH09 Lemma 4 is exactly an angle-version hybrid argument: telescope over hybrids that switch one ingredient at a time, apply the triangle inequality for the angle, and bound each consecutive pair by invariance. Theorem D is the same scheme with slots of a multilinear map instead of time steps, contraction monotonicity (Lemma C) instead of unitary invariance, and the lifted signed angle instead of the projective angle. Not stated for multilinear maps. |
| (N−) / tensor-angle inequality | ADJACENT | Both papers convert a final distance or angle bound into an operational bound (BBBV97 Thm 3.1: distance → total variation; DH09 Lemma 5). The specific vector inequality ‖f − tg‖ ≤ \|1 − t e^{iS}\| and its projective-tensor-norm reading are NOT_FOUND. |
| Projection step | ADJACENT | DH09 parametrize the defect by θ = arcsin ‖Π_yΨ‖ and compute the angle to the *reflected* state (2θ). Our step computes the angle to the *renormalized projected* state (exactly θ, for sub-normalized vectors via the lift). Same trigonometry; different map and normalization. |
| R7 diagonal lemma | ADJACENT | DH09 Lemma 2 proves an equal-angle extremality by a smoothing argument, but for a different functional (maximize Σθ_i under Σ sin²θ_i ≤ 1), not \|1 − ∏ cos θ_j e^{iθ_j}\| under a box constraint. |

## 6. Threat score

- **Main theorem (sharp constant C_k(η)): 2 / 5** (shared technique). No projected multilinear computations,
  no η-constrained constant.
- **Technique known: YES.** The telescoping hybrid argument, including a version measured in angles
  (DH09), is standard in quantum query complexity. Our Theorem D is a multilinear, sub-normalized,
  contraction-based instance of this scheme.

## 7. How to cite / credit in the proof section

Suggested sentence:

> The proof of Theorem D replaces one argument at a time and adds up the resulting angle increments with the
> triangle inequality. This is the hybrid argument of Bennett, Bernstein, Brassard and Vazirani [BBBV97,
> Thm. 3.3] carried out in an angle metric, as in Dohotaru and Høyer's exact lower bound for search [DH09,
> Lemma 4]. The new ingredients are the spherical lift, which makes the angle available for sub-normalized
> vectors, and the contraction lemma (Lemma C), which replaces unitary invariance.
