# L3 comparison: Zhang & Solomonik (2020), "On Stability of Tensor Networks and Canonical Forms"

Prepared 2026-09-14. Level-3 (theorem-by-theorem) comparison against Theorem R (R1a–R11).
Public sources only; paraphrased.

## 1. Bibliographic record

- Authors: Yifan Zhang, Edgar Solomonik (Dept. of Computer Science, UIUC)
- Title: On Stability of Tensor Networks and Canonical Forms
- Venue/year: arXiv preprint, math.NA, v1 submitted 5 Jan 2020. No journal version found
  (checked arXiv, Semantic Scholar, ADS, ResearchGate listings; all show only the preprint).
- Identifier: arXiv:2001.01191, DOI 10.48550/arXiv.2001.01191
- Status: VERIFIED (arXiv abstract page seen; v1 is the only version listed).

## 2. Access level

FULL_TEXT. Read the entire arXiv v1 PDF (24 pp.): Sections 1–8 (definitions, Lemma 3.4,
Theorem 3.5, Corollaries 3.6/3.8, Remarks 3.7/3.9, Theorem 4.2, Corollary 5.1, Theorem 5.2,
Section 5.2, Corollaries 6.1–6.3, 6.5–6.7, 6.9, Section 7 experiments, conclusion, references).
Citing works (11 listed by Semantic Scholar as of today) were scanned by title; none states a
sharp constant of Theorem-R type.

## 3. Their setting and assumptions

- Object: a tensor network (TN) on an arbitrary graph G (loops allowed, e.g. PEPS); the
  contraction map T_G(T^(1),...,T^(n)) is multilinear in the site tensors (Prop. 2.2). Finite
  dimensional, real (complex mentioned), Frobenius norms.
- Environment matrix M_{T(i)}: the Jacobian of vec(T) with respect to vec(T^(i)) (Def. 2.5, 2.7).
  Canonical form centered at a site = its environment matrix is an isometry (Def. 2.6).
- Perturbation model: additive sitewise perturbations Δ^(i) of the site tensors (Def. 2.9),
  with absolute control ‖Δ^(i)‖_F ≤ ε_i or relative control ‖Δ^(i)‖_F ≤ ε‖T^(i)‖_F (Def. 2.10).
- Error measured on the fully contracted tensor: E_a = ‖T̂ − T‖_F, E_r = E_a/‖T‖_F.
- All worst-case statements are FIRST ORDER: they hold up to an unquantified O(ε²) remainder.
- "Uniformly tight" (Def. 2.11) means sup over admissible perturbations equals the bound for every
  network — but again only to first order.
- No projections are applied to intermediate contraction results; truncation is modelled only as
  a site-tensor perturbation (Section 5.1). There is no notion of a projector attached to an
  internal node acting on the output of a multilinear map, and no restricted-range defect.

## 4. Their main results relevant here

- Lemma 3.4: absolute condition number of the TN equals max_i ‖M_{T(i)}‖_2; the relative one
  multiplies by Σ‖T^(i)‖_F/‖T‖_F.
- Theorem 3.5: up to O(ε²), the worst-case absolute error solves a quadratic maximization over the
  stacked perturbation; an explicit bound is Σ_i ε_i ‖M_{T(i)}‖_2 + O(ε²), uniformly tight when
  the TN contracts to a scalar; tightness also realized by product-state networks (Def. 2.12)
  with perturbations aligned with the sites. Remark 3.7: KKT/quadratic-system characterization.
- Corollary 3.8: one-site perturbation, error ≤ ε‖M_{T(1)}‖_2 (first order), uniformly tight,
  minimized by a canonical form centered at that site.
- Theorem 4.2: average-case squared relative error ≈ ε²‖M_T‖_F²/‖T‖_F² (first order).
- Corollary 5.1: attainable accuracy after sitewise truncation, minimized over gauges (first order).
- Theorem 5.2: truncating each site to relative accuracy ε after canonicalizing at that site gives
  relative error ≤ nε + O(ε²) — a linear-in-n telescoping accumulation (triangle inequality over
  sequential truncations).
- Corollaries 6.1–6.3 (MPS): single-site error ≤ ε‖T_[1,j−1]‖‖T^(j)‖‖T_[j+1,n]‖/‖T‖ (general) and
  ≤ ε (canonical); all-site bounds (22) and, for canonical MPS with bond dimension D,
  1 + (n−1)√D (23); tight up to second order via near-product-state constructions.
- Corollary 6.5 / 6.9: comparison factors (1+(n−1)√D)/n for MPS and an analogous PEPS factor,
  claimed sharp "in n and D" (first order).
- Corollaries 6.6–6.7: columnwise PEPS versions.

## 5. Comparison table

| Claim | Implied by source? | Explanation |
|---|---|---|
| R1a | ADJACENT | Their Theorem 3.5 bounds contraction error from site perturbations by Σ ε_i‖M_{T(i)}‖_2 + O(ε²). Inserting P_v after node v can be rewritten as the site perturbation −(I−P_v)μ_v, so a first-order bound of telescoping type (at most (k−1)ρM^{k−1}∏‖z‖ after bounding environments by M-products) is reachable in spirit. But (i) their perturbation size is the Frobenius norm of the whole site tensor, not an operator-norm defect restricted to inputs in Ran P_child; (ii) the O(ε²) remainder is not controlled; (iii) they work in finite-dimensional TN contractions, not bounded multilinear maps on real Hilbert spaces. No exact (all-orders) inequality of R1a form is stated. |
| R1b | NO | No closed-form constant in η; nothing resembling η^{-1} max_{θ≤arcsin η} |1−(cos θ e^{iθ})^{k−1}|. |
| R2 | NO | Their "tight"/"uniformly tight" claims concern first-order environment-norm formulas for a given network, not the best constant as a function of (k, η) over a class of maps. Nonlinear dependence on the defect ratio is outside their first-order framework. |
| R3 | NO | Their bounds depend explicitly on network-specific environment norms, bond dimension D, and topology (MPS vs PEPS factors differ). No tree-shape-independence statement. |
| R4 | ADJACENT | They exhibit extremizers (product-state networks, near-rank-one canonical cores) that attain first-order bounds. These are not low-dimensional (R²) realizations of an exact constant. |
| R5 | NO | No explicit equality construction for every tree shape at finite defect. |
| R10 | NO | No absolute bound with a universal constant < 2 (their factors grow with n, D). |
| R11 | ADJACENT | Theorem 5.2 (nε) and the first-order sum in Theorem 3.5 display the linear-in-node-count accumulation that R11 identifies as the η→0 limit k−1 of C_k. They do not identify k−1 as the limit of a sharp finite-η constant, and their counting (n sites, root included) differs from the k−1 non-root internal nodes in R. |

## 6. Threat score

**2 / 5** (relevant precedent, different theorem).

Justification: it is the closest published analysis of how local errors in a multilinear network are
amplified, with explicit tightness claims and extremal constructions, so reviewers may cite it. But
every quantitative statement is first order in ε, the error model is additive site-tensor
perturbation in Frobenius norm (not a projection defect restricted to projected inputs), the bounds
are network-dependent through environment norms, and no finite-η sharp constant, tree-shape
invariance, or R² extremizer appears. None of R1b–R10 is implied; R1a and R11 are only adjacent.

## 7. How to cite / position

Zhang and Solomonik quantify, to first order, how sitewise perturbations of a tensor network are
amplified through environment matrices and show that canonical forms reduce this amplification; our
Theorem R instead bounds the exact (all-orders) discrepancy caused by node-wise orthogonal projections
under a restricted-range defect hypothesis and identifies the best constant, which reduces to the
linear first-order count k−1 only in the limit η→0.
