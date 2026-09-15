# L3 comparison: Huang, Ryu, Yin (2020), "Tight coefficients of averaged operators via scaled relative graph"

Prepared 2026-09-14. This is a Level-3 comparison focused on R7 (the Diagonal Lemma) and its consequences R2 and R1b. It
complements `L3_ryu2022_scaled_relative_graph.md`, which covers the SRG mechanism (R6 / Theorem D). Only public sources were
used, and everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| HRY20 | X. Huang, E. K. Ryu, W. Yin, "Tight coefficients of averaged operators via scaled relative graph", J. Math. Anal. Appl. 490(1) (2020), article 124211. DOI 10.1016/j.jmaa.2020.124211. arXiv:1912.01593 (v1 3 Dec 2019, v2 7 Jan 2020, v3 27 Apr 2020). | VERIFIED. The arXiv abstract page was seen, and Crossref metadata confirms title, vol. 490, issue 1, article 124211, Oct 2020. The ScienceDirect landing page was not opened. |

Note on reference numbering: in arXiv v2 the relevant references are [19] Polyak et al., [20] Farouki–Moon–Ravani,
[21] Farouki–Pottmann. In v3 they are [17], [18], [19]. The journal numbering was not checked.

## 2. Access level

FULL_TEXT (arXiv v2 and v3 PDFs). Read: abstract, §1.1 (contribution and prior work), §2 (preliminaries: SRG, Disk(θ),
Facts 1–2, envelope definition), §3 (Theorem 1, Corollary 1, proofs in §3.1–3.2). §4 (Davis–Yin splitting) was skimmed and is not
relevant.

## 3. Their setting

- Real Hilbert space. θ-averaged operators N_θ = (1 − θ)I + θN with N nonexpansive.
- SRG facts: G(N_θ) = Disk(θ) := {z : |z − (1 − θ)| ≤ θ}, a disk through 1. θ = 1/2 gives firmly nonexpansive
  operators, whose SRG is exactly our disk |z − 1/2| ≤ 1/2 (boundary points cos t · e^{it} = w(t)).
- The composition class N_{θ1}N_{θ2} has SRG equal to the Minkowski product Disk(θ1)Disk(θ2) (RHY22, Thm 4.5 plus the arc property).
- Objective: the smallest averagedness coefficient θ with N_{θ1}N_{θ2} ⊆ N_θ, i.e. the smallest *disk through 1* containing
  the product region. This is not max |1 − z|.

## 4. Relevant results (paraphrased)

- **Theorem 1 (§3).** For θ1, θ2 ∈ (0,1), G(N_{θ1}N_{θ2}) is the region inside the outer loop of an explicit polar
  quartic, a Cartesian oval. With θ1 = θ2 = 1/2 the equation reduces to r = (1 + cos φ)/2 = cos²(φ/2), the
  cardioid, i.e. the curve w(t)² with φ = 2t.
- **Proof, §3.1, three steps.** Step 1: the envelope of the rotated and scaled circles is the Cartesian oval and encloses the product of the two
  *circles*. Step 2: a compactness and open-interior argument shows the boundary of the product of the *disks* lies in the product of the circles,
  so the outer loop encloses the product of the disks. Step 3: a winding-number and simple-connectedness argument shows the product of the disks
  fills the whole enclosed region.
- **§1.1 priority statement.** Theorem 1 of Polyak–Scherbakov–Shmulyian (1994) is the same result after a change of
  variables, but that proof omits Steps 2–3. Farouki et al. (FMR01, FP02) do the same envelope calculation, and FMR01 §6.7
  only asserts the enclosure. HRY20 thus claim Step 1 is known and Steps 2–3 are new. This makes HRY20 the **rigorous
  reference for the two-factor full-disk product**.
- **Corollary 1.** N_{θ1}N_{θ2} ⊆ N_θ with θ = (θ1 + θ2 − 2θ1θ2)/(1 − θ1θ2), and this is tight via curvature matching at z = 1.
  For θ1 = θ2 = 1/2 this gives θ = 2/3, hence only max |1 − z| ≤ 4/3. The true maximum of |1 − z| over the cardioid is
  2/√3 ≈ 1.1547, attained at cos² t = 1/3 (analyst computation). So their tightness notion is different from ours.
- Only two factors. There are no arcs or box constraints on angles, and no maximization of |1 − z|.

## 5. What R7 gets from HRY20 (analyst derivation)

- n = 2, α = π/2: by Theorem 1 (θ1 = θ2 = 1/2), A_{π/2}² ⊆ Disk(1/2)² = {r e^{iφ} : r ≤ cos²(φ/2)}. Maximizing
  |1 − z| over this compact region is attained on the boundary cardioid, which gives max_t |1 − w(t)²| and so R7 for
  (n = 2, α = π/2). The derivation is rigorous and two lines long, but it is not stated in HRY20.
- n = 2, α < π/2: not implied. The same obstruction as in the FP02 file applies. Region-level information plus the arg bound yields
  max(1, d_2(α)), which is sharp only for α ≥ arccos √(2/3) ≈ 0.6155 (η ≥ 1/√3).
- n ≥ 3: not treated. Iterating Theorem 1 is not available, because the product of the cardioid with a disk is not covered.

## 6. Comparison table

| Row | Status | Explanation |
|---|---|---|
| R7, α = π/2 (full arc), general n | NO | Only two factors. The n-fold envelope cos^n(Φ/n) is not stated (it follows from log-concavity of cos). |
| R7, α < π/2 (truncated arc) | NO | No box constraint on the factor angles. Disk-level results are non-sharp for small α (see §5). |
| R7, n = 2 | SPECIAL_CASE (α = π/2 only) | Theorem 1 with θ1 = θ2 = 1/2 rigorously identifies the cardioid region, and R7(n = 2, α = π/2) follows by maximizing on the boundary. The truncated n = 2 case is not covered. |
| Capped "moreover" inequality | NO | No pointwise inequality in (R, Θ) and no cap at Θ = π. |
| R2 explicit constant C_k(η) | NO (ADJACENT) | The analogous "sharp coefficient" is the averagedness θ of Corollary 1, a different functional (smallest disk through 1, not max \|1 − z\|, no η). |
| R1b sharpness | ADJACENT | The notion of tightness (a constant that cannot be improved without further assumptions) and the mechanism (SRG equality via the arc property, curvature matching) are analogous. Nothing about η-constrained chains or trees. |

## 7. Threat score

- **R7: 1 / 5.** A rigorous special case (n = 2, full disk) is obtainable in two lines, but only for the case we do not need.
- **R2 / R1b: 1 / 5** (analogous tightness philosophy, different functional).
- Combined with RHY22 (Fact 16, Theorem 7) the SRG literature scores 2/5 at the mechanism level; see the RHY22 file.

## 8. How to cite

> For two factors and α = π/2, the set {w(θ1)w(θ2)} fills the cardioid r ≤ cos²(φ/2); a rigorous proof of the
> corresponding Minkowski-product identity Disk(1/2)·Disk(1/2) is given by Huang, Ryu and Yin [HRY20, Thm. 1 with
> θ1 = θ2 = 1/2] (see also [RHY22, Fact 16]), who also credit the envelope computation to Polyak–Scherbakov–Shmulyian (1994)
> and Farouki et al.

Use this as the rigorous citation for the n = 2 full-disk picture. Pair it with FP02 §5 for the n-fold full-disk picture.
