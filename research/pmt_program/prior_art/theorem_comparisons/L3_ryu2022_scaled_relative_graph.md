# L3 comparison: Ryu–Hannah–Yin (2022), "Scaled relative graphs: nonexpansive operators via 2D Euclidean geometry" (with Huang–Ryu–Yin 2020)

Prepared 2026-09-14. Level-3 comparison against R6 (spherical-lift angle, multilinear angle contraction,
telescoping proof), R7 (diagonal lemma) and the main constant (R1a/R2). Public sources only; paraphrased.
Flagged earlier as a "specific antecedent of the angle mechanism".

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| RHY22 | E. K. Ryu, R. Hannah, W. Yin, "Scaled relative graphs: nonexpansive operators via 2D Euclidean geometry", Mathematical Programming 194 (2022) 569–619 (online 2021). DOI 10.1007/s10107-021-01639-w. arXiv:1902.09788 | VERIFIED (Crossref metadata; arXiv PDF read, journal-version numbering) |
| HRY20 | X. Huang, E. K. Ryu, W. Yin, "Tight coefficients of averaged operators via scaled relative graph", J. Math. Anal. Appl. 490 (2020) 124211. DOI 10.1016/j.jmaa.2020.124211. arXiv:1912.01593 | VERIFIED (Crossref metadata; arXiv PDF read, introduction and §3) |

## 2. Access level

FULL_TEXT (arXiv v-latest of RHY22): §3.1 (SRG definition; Theorem 1 on eigenvalues), Theorem 4 (scaling and
translation), §4.5 (arc properties, Theorem 7 and proof, Facts 15–16 with the appendix proof of Fact 16),
Appendix C (Fact 17, spherical triangle inequality, with proof).
HRY20: abstract, §1.1 (prior work on circular arithmetic), statement of Theorem 1.

## 3. Their setting

- Real Hilbert space H; (possibly nonlinear, set-valued) operators and operator classes (nonexpansive,
  averaged N_θ, firmly nonexpansive N_{1/2}, monotone, cocoercive, ...).
- The SRG of an operator is the set of complex numbers z = (‖u − v‖/‖x − y‖)·exp(±i∠(u − v, x − y)) over
  input pairs x ≠ y with outputs u, v. The magnitude is a Lipschitz-type ratio and the argument is the angle
  between the output difference and the input difference.
- Goal: tight convergence and contraction factors via 2D geometry.

## 4. Relevant results (paraphrased)

- **Theorem 4.** G(αA) = αG(A) and G(I + A) = 1 + G(A), so the SRG of I − T is 1 − G(T). Bounds on the
  "error operator" become bounds of the form max |1 − z| over z in the SRG.
- **Theorem 7 (composition).** For SRG-full classes, G(AB) ⊇ G(A)G(B) (Minkowski product of complex sets),
  with equality under an arc property. The proof of the inclusion G(AB) ⊆ G(A)G(B) is pointwise: for fixed
  inputs, the magnitudes multiply, and by the spherical triangle inequality the angle of the composite lies in
  [|φ_A − φ_B|, φ_A + φ_B]. The arc property then places the point in the product set.
- **Fact 17 (Appendix C).** For nonzero a, b, c ∈ H, |∠(a,b) − ∠(b,c)| ≤ ∠(a,c) ≤ ∠(a,b) + ∠(b,c). They note it
  is known and prove it by decomposing a and c along b.
- **Fact 16.** G(N_{1/2}N_{1/2}) = {r e^{iφ} : 0 ≤ r ≤ cos²(φ/2)}, a cardioid. The SRG of N_{1/2} is the
  disk with diameter [0,1], whose boundary points are cos θ e^{iθ}. The cardioid boundary cos²(φ/2)e^{iφ} is
  the square of the boundary point with angle φ/2: the product of two such points with total angle φ has
  maximal modulus at equal angles. They describe the precise set as new, derived by an envelope/inversion
  argument.
- **HRY20 Theorem 1.** Characterizes G(N_{θ₁}N_{θ₂}) (two averaged operators with different coefficients) as the
  region bounded by an explicit envelope. The authors link the geometry to circular arithmetic (Gargantini–Henrici,
  Hauenschild) and to envelope computations of Farouki et al. Only two-factor compositions are treated.
- Figure 4 of RHY22: the SRG of the orthogonal projection onto a line is the circle through 0 and 1, i.e. the
  points cos θ e^{±iθ}.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| Lemma A (φ is a metric on the ball) | KNOWN_IN_SPECIAL_CASE | Fact 17 is the triangle inequality for angles between nonzero vectors, i.e. Lemma A restricted to the unit sphere. The hemisphere lift that turns ball vectors into unit vectors is absent. With the lift, Lemma A is Fact 17 applied in G ⊕ R. |
| Lemma C (contraction monotonicity) | NOT_FOUND | The SRG splits magnitude ratio and angle. There is no statement that a contraction decreases a combined angle, and ∠ alone is not monotone under contractions. |
| Theorem D (multilinear angle contraction) | ADJACENT | Theorem 7's pointwise argument ("angles add by the spherical triangle inequality, magnitudes multiply, then read off a complex product") is the same mechanism for compositions of operators. There is no multilinear slot-by-slot replacement, no sub-normalized lift and no contraction lemma. |
| (N−) / tensor-angle inequality | ADJACENT (strong) | Theorem 4 plus Theorem 7 bound ‖x − Tx‖ by max\|1 − z\|·‖x‖ with z in a product set. This is structurally the form \|1 − t e^{iS}\| of (N−). The SRG carries the magnitude separately (z = r e^{iα}) instead of through the lift, and says nothing about multilinear maps or projective tensor norms. |
| Projection step | KNOWN_IN_SPECIAL_CASE | For a unit vector g, Pg/√(1−q²) = Pg/‖Pg‖ and φ = ∠(Pg, g) = arcsin q. This is the elementary fact behind the SRG of an orthogonal projection (points cos θ e^{iθ}). The sub-normalized renormalized version in the lift is not there. |
| R7 diagonal lemma | ADJACENT | Fact 16 (cardioid r ≤ cos²(φ/2)) and HRY20 Thm 1 give the equal-angle envelope of the product of two projection-type SRG points. Our R7 extremizes \|1 − ∏_j cos θ_j e^{iθ_j}\| under a box constraint θ_j ≤ arcsin η for k − 1 factors. RHY22 has neither the \|1 − ·\| objective, nor the box constraint, nor m > 2 factors. The m-factor envelope r ≤ cos^m(Φ/m) follows from log-concavity of cos, but it is not stated. |

**Mechanism-level observation (analyst, not a literature finding).** Take a *linear chain* x ↦ P_{k−1}⋯P_1 x
of orthogonal projections, where each step moves its current vector by relative amount ≤ η (angle
θ_j ≤ arcsin η). Theorem 7's pointwise argument plus Theorem 4 gives
‖x − P_{k−1}⋯P_1 x‖ ≤ max_{θ_j ≤ arcsin η} |1 − ∏_j cos θ_j e^{iθ_j}| · ‖x‖. With R7, this is the
linear-chain specialization of the upper bound R1a/R2. RHY22 does not state it, because the per-step relative-defect
constraint is a condition on the trajectory and does not define an SRG-full operator class. It is,
however, derivable in a few lines from their tools. The multilinear/tree case, where angles from different
slots add, needs Theorem D and the lift, which have no SRG counterpart. Sharpness (R1b) is not addressed.

## 6. Threat score

- **Main theorem (sharp constant C_k(η)): 2 / 5** (shared technique), at the upper end. The complex-plane
  mechanism (angles add, magnitudes multiply, bound by |1 − z|) and the equal-angle cardioid are genuinely
  close. No stated result concerns projected multilinear trees, η-constrained defects or sharp constants.
  Upgrade to 3 if a later SRG paper (e.g. follow-ups on SRGs of linear operators, Pates 2021, cited in RHY22
  as linking SRG and numerical range; not read here) states the η-constrained chain bound.
- **Technique known: YES (partially).** The spherical triangle inequality and the composition-in-the-complex-plane
  mechanism are known. The spherical lift, Lemma C, multilinear Theorem D and the box-constrained diagonal lemma
  are not in RHY22 or HRY20.

## 7. How to cite / credit in the proof section

Suggested sentence:

> Representing the action of a step by the complex number r e^{iθ} (relative length and turning angle) and
> composing steps by multiplying these numbers, with angles controlled by the spherical triangle inequality, is
> the mechanism of the scaled relative graph of Ryu, Hannah and Yin [RHY22, Thm. 7 and Fact 17]. The
> equal-angle envelope cos²(φ/2) of a product of two projection-type factors appears there as [RHY22, Fact 16]
> (see also [HRY20, Thm. 1]). Our contribution is the extension of this mechanism to sub-normalized vectors
> (via the spherical lift) and to contractive multilinear maps, and the resulting sharp constant for projected
> trees.

Place this in the related-work paragraph and at the start of the proof of Theorem D and of the diagonal lemma.
