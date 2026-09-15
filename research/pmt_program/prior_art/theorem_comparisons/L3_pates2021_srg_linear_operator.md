# L3 comparison: Pates (2021), "The Scaled Relative Graph of a Linear Operator" (plus adjacent SRG papers)

Prepared 2026-09-14. Level-2/3 check against Theorem R (chain and tree cases) and rows R1a, R1b, R2, R3, R5, R7.
Public sources only (arXiv abstract pages and arXiv PDF). Everything below is paraphrased.
This file follows up the open item in `L3_ryu2022_scaled_relative_graph.md` §6, which said to raise that threat to 3
if Pates 2021 states the η-constrained chain bound. **It does not.**

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| Pat21 | R. Pates, "The Scaled Relative Graph of a Linear Operator", arXiv:2106.05650 [math.OC], v1 10 Jun 2021, v2 4 Aug 2021. MSC 47A11, 47A12; 51M15. Lund University (Automatic Control). | VERIFIED (arXiv landing page and v2 PDF read in full, 16 pp.) |
| Pat21 venue | The arXiv page has no journal reference or DOI (other than the arXiv DOI 10.48550/arXiv.2106.05650). The search found no journal version. | UNVERIFIED as published. Cite as an arXiv preprint. |

## 2. Access level

FULL_TEXT (arXiv v2): §1 introduction, §2 preliminaries (SRG definition, Beltrami–Klein map, numerical range),
§3.1 Theorem 1 with proof and Examples 1–3, §3.2 Lemma 1 and Theorem 2 with proof, §4 conclusions, reference list.

## 3. Their setting

- H is a real or complex Hilbert space. T is a bounded linear operator, extended in remarks to closed densely defined
  operators. There is one operator at a time.
- For a linear T, SRG(T) is the set of points ‖Tx‖/‖x‖ · exp(±i·angle(Tx, x)), with the angle defined through
  Re⟨Tx, x⟩. This agrees with the RHY definition for linear operators.
- Goal: compute and characterise the SRG of a single linear operator (matrices, LTI differential operators, shifts).
  The motivation is system analysis and control.

## 4. Relevant results (paraphrased)

- **Theorem 1 (complex H).** SRG(T) = g(W(f(T))). Here f is the Beltrami–Klein-type map
  f(z) = (z̄ − i)(z − i)/(1 + |z|²), lifted to operators as (I+T*T)^{-1/2}(T* − iI)(T − iI)(I+T*T)^{-1/2}. The map g
  inverts f up to conjugation, and W is the numerical range. Consequences:
  (i) SRG(T) is convex in the hyperbolic (Poincaré half-plane) sense.
  (ii) For normal T, the closure of SRG(T) is the hyperbolic convex hull of the approximate point spectrum.
  (iii) The closure contains σ_ap(T).
  (iv) Hildebrandt analogue: the intersection over similarities of cl SRG(STS⁻¹) is the hyperbolic hull of σ_ap(T).
  (v)–(viii) Equivalences for when the spectrum, rather than σ_ap, is captured.
- **Proof device.** Distances from real points α to the SRG equal the minimum gain m(T − αI) and the norm ‖T − αI‖
  (eqs. 3.6–3.7). The SRG is the intersection over α ∈ ℝ of the annuli these distances define (eq. 3.5).
- **Examples 1–3.** Complex matrices (compact SRG, boundary computed via numerical-range algorithms, SRG(T) = SRG(T*)),
  LTI operators on L²(ℝ) via spectral factorisation, and the right shift on ℓ², where SRG(T) and SRG(T*) differ.
- **Lemma 1 / Theorem 2 (real H).** Via complexification, SRG(T) = SRG(T_ℂ), except in dimension 2, where SRG(T) is the
  boundary of SRG(T_ℂ).
- **Not present:** any composition or product rule, and any treatment of orthogonal projections, contractions
  composed with projections, or chains. The paper has no |1 − z|-type error bound, no products of several SRG disks,
  no cardioid or equal-angle envelope, no extremizers or sharpness statements for composites, and no defect
  constraint ‖(I − P)Ax‖ ≤ η‖x‖ or arcsin η angle cap. Composition is mentioned only in the introduction, as the
  general selling point of SRGs from [RHY].

Analyst remark (not in Pat21): for an orthogonal projection P, which is normal with spectrum in {0, 1}, Theorem 1(ii)
gives cl SRG(P) as the hyperbolic hull of {0, 1}. That hull is the closed disk |z − 1/2| ≤ 1/2, whose boundary points
are cos θ e^{±iθ}. This matches the RHY picture. Pat21 does not state this example.

## 5. Comparison table (Theorem R)

| Row | Status | Explanation |
|---|---|---|
| R1a (upper bound, projection-insertion error ≤ C·‖x‖) | NO | No composite operators and no projection-insertion error. The only link is that Theorem 1(ii) yields the SRG of a single projection, which is a building block of our chain argument. |
| R1b (sharpness) | NO | Sharpness appears only as exact SRG characterisation of single operators, not as sharpness of a composition bound. |
| R2 (explicit constant max_θ \|1 − ∏ cos θ_j e^{iθ_j}\| = max_θ \|1 − (cos θ e^{iθ})^{k−1}\|) | NO | No formula of this type. |
| R3 (tree / multilinear independence) | NO | Only linear operators. There are no multilinear maps and no interconnection topologies. |
| R5 (planar extremizer) | ADJACENT (weak) | Theorem 2 reduces real SRGs to 2D / complexified numerical ranges, and dimension 2 is singled out. This is a "planar reduction" of one operator's SRG, not an extremizer for a chain. |
| R7 (equal-angle extremization) | NO | No products of angles and no box constraint. |

## 6. Threat score

- **Pat21 vs Theorem R: 1 / 5** (background tool only). Pat21 is a structural paper on one linear operator's SRG:
  the numerical-range link, hyperbolic convexity and a Hildebrandt analogue. It supplies no ingredient of the chain or
  tree bound beyond the (implicit) SRG of a projection. It does not raise the RHY22 threat (2/5).
- **η-constrained chain bound: NOT FOUND** in Pat21, nor in any SRG paper screened (§7).

## 7. Other SRG papers screened (abstract level unless stated)

| Paper | What it does | Relevance | Threat |
|---|---|---|---|
| Chaffey, Forni, Sepulchre, "Scaled relative graphs for system analysis", IEEE CDC 2021, arXiv:2103.13971 (VERIFIED, abstract page) | Nyquist diagram of an LTI system is the convex hull of its SRG after a transform. Also covers describing functions, interconnections via SRG manipulation and incremental passivity. | Interconnection rules are inherited from RHY composition and parallel-sum theorems. No projections, no η, no many-factor extremal bound. | 0–1 |
| Chaffey, Forni, Sepulchre, "Graphical Nonlinear System Analysis", IEEE TAC 2023, DOI 10.1109/TAC.2023.3234016, arXiv:2107.11272 (VERIFIED, abstract page) | SRG-based feedback robustness as distances between SRGs. | The abstract does not mention series composition. From general knowledge (full text NOT read here), it uses RHY-style composition bounds under chord/arc conditions for feedback loops. Nothing on projection chains. | 1 |
| Huang, Ryu, Yin, "Tight coefficients of averaged operators via SRG", JMAA 490 (2020) 124211, arXiv:1912.01593 | Tight SRG of two composed averaged operators, with a cardioid-type envelope. | Already covered in `L3_ryu2022_scaled_relative_graph.md`. Two factors, no \|1 − ·\| with a box constraint. | 2 (same as RHY22) |
| Nauta, Pates, "Computable Characterisations of SRGs of Closed Operators", ECC 2026, DOI 10.1016/j.ejcon.2026.101574, arXiv:2511.08420 (VERIFIED, abstract page) | Exact computable SRGs of closed linear operators via max/min gain; state-space models (Bounded Real Lemma). | One operator at a time. No compositions mentioned. | 0 |
| van den Eijnden, Chen, Scheres, Chaffey, Lanzon, "On phase in scaled graphs", arXiv:2504.21448 (VERIFIED, abstract page) | Signed scaled graph using the Hilbert transform (phase lead/lag), with interconnection results. | Signed phase for feedback. No projection chains or product extremals indicated in the abstract. Not read in full. | 0–1 |

Searches run: Pates SRG venue; SRG composition of many averaged operators / cardioid; SRG orthogonal projections
product / alternating projections; SRG composition of m operators / arc property / Minkowski product; SRG projection
onto subspace / product / angle bound. None returned a paper with an m-factor (m > 2) equal-angle envelope, a
|1 − ∏ cos θ_j e^{iθ_j}| bound, or a per-step defect cap θ_j ≤ arcsin η.

Residual gap: full texts of the two Chaffey–Forni–Sepulchre papers and Ryu–Yin's book *Large-Scale Convex
Optimization* (2022, SRG chapter) were not read. A targeted read of their composition sections would close the
check. The expected finding is RHY Thm 7 restated, which is threat ≤ 2.

## 8. How to cite

Pat21 is not needed as a source for any step of Theorem R. Optional citation in related work:

> The scaled relative graph of Ryu, Hannah and Yin [RHY22] has been characterised for linear operators through the
> numerical range of an associated operator, which yields hyperbolic convexity and spectral properties [Pat21]; in
> particular the SRG of an orthogonal projection is the disk with diameter [0,1].

If the projection-disk fact is attributed, cite [RHY22, Fig. 4 / Fact 16 context] as the primary source. Pat21
Theorem 1(ii) is a secondary source (normal operator with spectrum {0,1}). That derivation is ours, since Pat21
does not state the projection example.
