# L3 comparison: Farouki & Pottmann (2002), "Exact Minkowski Products of N Complex Disks"

Prepared 2026-09-14. This is a Level-3 comparison against R7 (the scalar extremal problem, or "Diagonal Lemma") and
its consequences R2 (explicit constant) and R1b (sharpness). Only public sources were used, and everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| FP02 | R. T. Farouki, H. Pottmann, "Exact Minkowski Products of N Complex Disks", Reliable Computing 8(1) (2002) 43–66. DOI 10.1023/A:1014737602641. Received 2 Dec 2000, accepted 6 Mar 2001. | VERIFIED. Springer landing-page metadata was seen (title, vol. 8, issue 1, pp. 43–66, 2002/02, DOI) and matches Crossref. The author PDF was read in full. |

Author PDF (TU Wien, public): https://dmg.tuwien.ac.at/geom/ig/papers/pot114.pdf (also mirrored at geometrie.tuwien.ac.at).

## 2. Access level

FULL_TEXT (author PDF, typeset journal version with page numbers 43–66). All sections were read: §1 Preamble, §2 Cartesian
ovals, §3 two disks (Lemma 3.1, Prop. 3.1), §4 N disks (Lemma 4.1, Prop. 4.1, Prop. 4.2), §5 N-th Minkowski power
of a disk, §6 Closure.

## 3. Their setting

- Minkowski geometric algebra. For complex sets A, B the Minkowski product is A⊗B = {ab : a∈A, b∈B}. The objects are
  *closed disks* D_k with center 1 and radius R_k (general disks reduce to this by scaling).
- Goal: an exact parameterization of the boundary ∂(D_1⊗⋯⊗D_N), as opposed to the bounding disks of
  Gargantini–Henrici circular arithmetic.
- Method: a boundary point of a Minkowski product must come from factor points with matched *logarithmic Gauss maps*
  (a necessary condition taken from Farouki–Moon–Ravani 2000). A coordinated polar parameterization then turns this
  into a one-parameter family.
- Nothing about arcs, box constraints on factor angles, or the functional |1 − z|.

## 4. Relevant results (paraphrased)

- **§2.3 (envelopes).** For N = 2 the product boundary is the envelope of the rotated and scaled copies of one circle, which is a
  Cartesian oval. For N ≥ 3 the iterated envelope contains the boundary as "a subset of" it. The authors call this route impractical.
- **Lemma 3.1 / Lemma 4.1.** Candidate boundary N-tuples z_k = 1 + R_k e^{iφ_k} satisfy the common-ratio condition
  sin φ_k / (R_k + cos φ_k) = tan ψ for all k. This is stated as a *necessary* condition only: the products "may lie" on the
  boundary.
- **Prop. 4.1.** ∂(D_1⊗⋯⊗D_N) is (a subset of) the outer loop of the explicit curve z(ψ) = ∏_k [a_k + ρ_k(ψ) e^{iψ}],
  with a_k = 1 − R_k². The "subset of" qualifier covers possible self-intersections that must be trimmed. The curve has
  2^{N−1} loops in general.
- **Prop. 4.2.** Corresponding points are the intersections of the operand circles with one member of the coaxal family
  of circles through 0 and 1. The circle |z − 1/2| = 1/2 belongs to that family (ψ = π/2). This is a geometric curiosity
  and has no bearing on R7.
- **§5 (N-th Minkowski power of one disk).** For identical operands the authors argue that choosing *the same point on every
  copy* meets the matching condition. They conclude that the locus z_N(φ) = (1 + R e^{iφ})^N contains the boundary of
  ⊗^N D as a subset: it is the outermost of several candidate loops, while mixed products z(φ')^{N−r} z(φ)^r "may also
  contribute" inner loops. The locus is a *higher trochoid* (N-bar linkage). For **R = 1, a circle through 0**, it is a
  *cycloidal trochoid* for every N, and for N = 2 it is the cardioid (an epicycloid). A footnote notes that for N = 2 the mixed
  product is the constant 1 − R², which is 0 when R = 1.
- Rigor. §5 is heuristic ("we may expect", "a subset of"). No proof is given that the outermost loop *is* the
  boundary, that the region is simply connected, or that the necessary condition is valid at the singular point 0
  (where the log-Gauss map of a circle through 0 degenerates). Huang–Ryu–Yin (2020, §1.1) make the same criticism of
  the N = 2 case: Farouki et al. do not prove the enclosure and simple-connectedness steps.
- No statement about max |1 − z|, no maximization of any functional over the product set, no truncated operands.

## 5. Translation to our notation (analyst derivation, not in FP02)

Our disk is D = {|z − 1/2| ≤ 1/2} = (1/2)·D(1,1), and (1 + e^{iφ})/2 = cos(φ/2) e^{iφ/2} = w(φ/2). With R = 1, FP02 §5
therefore says: ∂(⊗^n D) ⊆ {w(t)^n : |t| ≤ π/2} (heuristically). The arc product A_α^n = {∏ w(θ_j) : θ_j ∈ [0, α]} is
contained in ⊗^n D.

1. **Full arc (α = π/2).** The maximum of |1 − z| over a compact set is attained on its boundary. So, granting §5,
   max over A_{π/2}^n of |1 − z| ≤ max_{|t|≤π/2} |1 − w(t)^n| = max_{t∈[0,π/2]} |1 − w(t)^n| (by conjugate symmetry),
   with equality at equal angles. This is R7(a).
   The same conclusion also follows in two lines *without* FP02. Writing ∏ w(θ_j) = R e^{iΘ}, Jensen for log cos gives
   R ≤ cos^n(Θ/n). The map r ↦ |1 − r e^{iΘ}| is convex, so it is maximized at r = 0 (value 1) or at r = cos^n(Θ/n)
   (value |1 − w(Θ/n)^n|). Also w(π/2) = 0 gives max_t |1 − w(t)^n| ≥ 1. The content of FP02 used here is exactly this
   equal-angle modulus envelope.
2. **Truncated arc (α < π/2).** FP02 concerns full disks and cannot see the box constraint. Adding the trivial bound
   Θ ≤ nα to the envelope yields only max over A_α^n of |1 − z| ≤ max(1, d_n(α)), where d_n(α) = max_{t≤α} |1 − w(t)^n|.
   This is sharp iff d_n(α) ≥ 1, i.e. iff α ≥ α*(n). Numerically (scratch computation):

   | n | α*(n) | η* = sin α* | n·α* |
   |---|---|---|---|
   | 2 | 0.6155 | 0.5774 (= 1/√3) | 1.231 |
   | 3 | 0.3876 | 0.3780 | 1.163 |
   | 4 | 0.2829 | 0.2792 | 1.132 |
   | 5 | 0.2228 | 0.2209 | 1.114 |
   | 8 | 0.1360 | 0.1356 | 1.088 |
   | 16 | 0.0667 | 0.0667 | 1.067 |

   For α < α*(n), the small-η regime relevant to C_k(η) with η below roughly 1.07–1.23/(k−1), the disk-level information
   gives the non-sharp value 1. Example: n = 3, α = 0.3 gives 1 versus the true value 0.8223. The missing ingredient is a
   *lower* bound on R = ∏ cos θ_j in terms of Θ under θ_j ≤ α, together with the case split at Θ = π. Neither appears in FP02.

## 6. Comparison table

| Row | Status | Explanation |
|---|---|---|
| R7, α = π/2 (full arc) | SPECIAL_CASE (implied, heuristic) | §5 with R = 1, rescaled, puts ∂(⊗^n D) inside the curve w(t)^n. The maximum-on-boundary step then gives R7(a) at once, and FP02 describes the boundary explicitly as N-th powers of a single boundary point. The argument in FP02 is not rigorous (necessary condition plus the qualifier "a subset of"). The same case is also elementary via Jensen, so R7(a) should be treated as essentially known or folklore. |
| R7, α < π/2 (truncated arc) | NO (ADJACENT only for α ≥ α*(n)) | FP02 treats only full disks. Envelope plus the arg bound proves R7 only in the large-α regime d_n(α) ≥ 1, and even that uses a step (Θ ≤ nα) outside FP02. The PMT regime (small η) is not covered. |
| R7, n = 2 | SPECIAL_CASE (full disk only) | For N = 2 and R = 1 the boundary is the cardioid cos²(φ/2)e^{iφ}, i.e. w(t)². FP02 attributes the two-disk product to FMR01 and the observation that the disk product is enclosed by the outer loop to Polyak et al. 1994. The truncated n = 2 case is not treated. |
| Capped "moreover" inequality \|1 − R e^{i min(Θ,π)}\| ≤ max_t \|1 − w(t)^n\| | NO | FP02 has no pointwise inequality, no functional and no cap at Θ = π. |
| R2 explicit constant C_k(η) = η⁻¹ max_{θ≤arcsin η} \|1 − w(θ)^{k−1}\| | NO | FP02 has no operator or projection context and no η. The curve w(t)^{k−1} does appear (as (1+e^{iφ})^N up to scaling), but not the truncated max or the normalization. |
| R1b sharpness | NO (ADJACENT) | The claim that the equal-angle curve is attained, i.e. the boundary is made of N-th powers of actual points, is the scalar analogue of attainment. Operator-level sharpness is absent. |

## 7. Threat score

- **R7 as stated (truncated box, capped inequality): 2 / 5.** FP02 contains, explicitly and for all N, the fact that the
  N-th Minkowski power of a disk through 0 is bounded by the N-th powers of single boundary points (equal-angle extremality).
  That is the geometric heart of the full-arc case. It does not reach the truncated box constraint, the |1 − ·| objective
  or the cap, and its argument is heuristic.
- **Sub-claim R7(a), α = π/2: 3 / 5.** Implied in a few lines, modulo FP02's missing rigor. It is also provable from Jensen
  directly, so we should not claim novelty for it.
- **R2 / R1b: 0–1 / 5.**

## 8. How to cite

Cite FP02 as the source for the equal-angle boundary description of Minkowski powers of a disk, and do **not** rely on it for
rigor. Suggested wording:

> For α = π/2 the diagonal extremality is a manifestation of the fact that the n-fold Minkowski power of the disk
> |z − 1/2| ≤ 1/2 is bounded by the curve t ↦ w(t)^n, i.e. by n-th powers of single boundary points — a cycloidal trochoid,
> the cardioid for n = 2 [Farouki–Pottmann 2002, §5]. Our proof is self-contained and treats the box-constrained case
> α < π/2, which is not accessible from disk-product boundaries.

Place this in the remark after the Diagonal Lemma and in related work. Do not cite FP02 for R2 or R1b.
