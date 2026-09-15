# Claim novelty matrix — Theorem R (PRIOR-ART-R v1, first pass)

```
DATE:    2026-09-14
GLOBAL:  NOVELTY_NOT_ESTABLISHED   (stop criterion §8 not met; manual MathSciNet/Scholar steps pending)
INPUTS:  PRIOR_ART_MATRIX.csv (1763 screened sources) · theorem_comparisons/ (Level 3) ·
         screening/ (Level 1–2) · l3_verdicts.json (adjudication) · SEARCH_LOG.csv
RESULT:  no source with threat 4–5; 3 sources at threat 3 (none implies a Theorem R claim);
         Farouki–Pottmann 2002 is threat 3 only for the sub-case α = π/2 of R7 (overall 2)
```

Claim IDs are those of `SEARCH_PROTOCOL.md` §1. Some Level-3 files written by the
tensor-network reader label the planar extremizer "R4/R5" jointly. This matrix uses the protocol
numbering throughout.

## 1. Per-claim status

| ID | Claim | Status | Closest prior art (evidence) | Relation / what to write in the paper |
|---|---|---|---|---|
| R1a | Upper bound for projected error of tree-structured multilinear computations | `NO_EQUIVALENT_FOUND` | Ceruti–Lubich–Sulz 2023 Thm A.1 (linear, tree-shape-independent, **non-sharp** (d−1) bound; L3) · Zhang–Solomonik 2020 (first order, network-dependent; L3) · Bachmayr–Nouy–Schneider arXiv:2112.01474 Lemma 4.9 (nonlinear compositions, L∞, depth-growing constants; L2) · Bargetz–Reich–Zalas 2017 Thm 11 (linear accumulation; L2) · Zniyed–Boyer 2026 (tree/data-dependent; **abstract only**) | Cite all five; state that existing estimates are first-order, non-sharp or format-specific |
| R1b | Sharpness (best possible constant over the admissible class) | `NO_EQUIVALENT_FOUND` | Sharp rates for alternating/cyclic projections (Kayalar–Weinert 1988; Deutsch–Hundal 1997; Reich–Zalas 2017; Bauschke et al. 2014; Feshchenko 2019) — different quantity (convergence to an intersection, global angle constraint) | Define "sharp" as worst case over the $(k,\eta)$ class; Deutsch–Hundal show angle-only bounds cannot be exact configuration-wise for ≥3 subspaces |
| R2 | Explicit constant $C_k(\eta)=\eta^{-1}\max_{\theta\le\arcsin\eta}\lvert1-(\cos\theta e^{i\theta})^{k-1}\rvert$ | `NO_EQUIVALENT_FOUND` | No source states $\lvert1-(\cos\theta e^{i\theta})^n\rvert$ as a worst-case error (targeted Zeno, SRG, Minkowski-product and projection searches) | — |
| R3 | Sharp constant independent of tree structure at fixed $k,\eta$ | `NO_EQUIVALENT_FOUND` (sharp form) · `CLOSE_PRIOR_ART` (non-sharp tree-independent bound) | Ceruti–Lubich–Sulz Thm A.1 (tree-independent but not sharp) · contrast: Grasedyck 2010 $\sqrt{2d-3}$ and Zniyed–Boyer 2026 (tree-dependent) | Say explicitly that tree-independent non-sharp bounds exist; the new point is that the **sharp** constant is tree-independent |
| R4 | Extremizer for every tree structure | `NO_EQUIVALENT_FOUND` | — | — |
| R5 | Two-dimensional (planar) extremizer | `CLOSE_PRIOR_ART` | Oikhberg 1999 Lemma 2(a) (same planar chain of line projections, no extremality) · Jeong et al. 2023 (reduction to $\mathbb C^2$ for numerical ranges) · Bauschke et al. 2014 (DR operator $=\cos\theta\cdot$rotation) | Credit the planar construction; the extremality for the projected-error problem is the contribution |
| R6 | Spherical-lift angle; multilinear angle contraction (telescoping) | `KNOWN_IN_SPECIAL_CASE` | Tomamichel–Colbeck–Renner 2010 / Tomamichel 2016 (lift $\rho\oplus(1-\operatorname{tr}\rho)$, triangle inequality, monotonicity in absolute-value form) · BBBV 1997, Dohotaru–Høyer 2009 Lemma 4 (angle hybrid argument) · Ryu–Hannah–Yin 2022 Thm 7 (angles add, lengths multiply) · Grcar 2010 (tensor-angle identity for $m=2$) | Use the attribution sentence of §3; present Lemmas A/C as analogues with proofs (signed version) |
| R7 | Equal-angle (diagonal) extremization of $\lvert1-\prod\cos\theta_je^{i\theta_j}\rvert$ with caps | `KNOWN_IN_SPECIAL_CASE` for $\alpha=\pi/2$ · `NO_EQUIVALENT_FOUND` for $\alpha<\pi/2$ and for the capped inequality | $\alpha=\pi/2$, any $n$: Farouki–Pottmann 2002 §5 (boundary of the $n$-fold Minkowski power of $\lvert z-\tfrac12\rvert\le\tfrac12$ lies on $w(t)^n$; heuristic argument; also immediate by Jensen) · $n=2$, $\alpha=\pi/2$: Huang–Ryu–Yin 2020 Thm 1 (rigorous cardioid), Polyak–Scherbakov–Shmulyian 1994, Farouki–Moon–Ravani 2001 · Jeong et al. 2023 Lemma 5 (equal factors, different objective) · Ryu–Hannah–Yin Fact 16 | Do **not** claim novelty for $\alpha=\pi/2$; the box-constrained case $\alpha<\pi/2$ (needed for $C_k(\eta)$, and not recoverable from disk-product boundaries: they give only $\max(1,d_n(\alpha))$, sharp only when $d_n(\alpha)\ge1$), the capped inequality and $C_k(\eta)$ were not found (L3: `L3_farouki2002_*`, `L3_huang2020_*`, `L3_farouki2001_*`, `L3_polyak1994_*`) |
| R10 | Absolute bound $G_k<2$ | `NO_EQUIVALENT_FOUND` (elementary) | $\lvert1-z\rvert\le2$ for $\lvert z\rvert\le1$ is trivial; strictness and the limit are the content | Present as a remark, not a contribution |
| R11 | $C_k(\eta)\to k-1$ as $\eta\downarrow0$ | `CLOSE_PRIOR_ART` | Zhang–Solomonik first-order stability coefficients; Ceruti–Lubich–Sulz (d−1) | Present as consistency with first-order theory |
| R12 | Upper bound under trajectory closure | `NO_EQUIVALENT_FOUND` (minor) | Bargetz–Reich–Zalas (inexact operators), Liang–Fadili–Peyré (summable errors) — adjacent | Remark |
| R8 | Lean 4 / Mathlib formalization (**artifact**) | `NO_EQUIVALENT_FOUND` at Level 1 only | Lean formalizations of fixed-point algorithms in Hilbert spaces and convergence rates exist (Level 1 titles) | Artifact statement only, never a mathematical novelty claim |
| R9 | Relation to TT/HT/TTN truncation (**positioning**) | n/a | Grasedyck 2010; Oseledets 2011; Hackbusch 2019, 2021; Lubich et al. 2013; Verstraete–Cirac 2006; Kolda–Bader 2009 | "Not a quasi-optimality estimate" paragraph (style contract §9) |

## 2. Sources at threat 3 (all read at Level 2 or 3; none implies a claim)

| Source | Level | Why 3 | Open action |
|---|---|---|---|
| Feshchenko, arXiv:1908.00531 | L3 | Best constants for products of projections; equally spaced planar lines in the lower bound | **Disputed** (L3 reader: 1, L2 reader: 3) — author adjudication |
| Zniyed–Boyer 2026, HAL hal-05554951 | L2, abstract only | Error transport through dimension trees | **Manual**: download PDF (HAL bot check blocks automated access) |
| Bachmayr–Nouy–Schneider, arXiv:2112.01474 | L2, full text | Tree-shaped accumulation lemma of R1a shape | Verify title/venue; L3 optional |

## 3. Attribution sentences (for the proof section)

> The quantity $\cos\varphi(f,g)=\langle f,g\rangle+\sqrt{1-\lVert f\rVert^2}\sqrt{1-\lVert g\rVert^2}$ is the real,
> sign-retaining vector analogue of the generalized fidelity of Tomamichel, Colbeck and Renner, and the lift
> $f\mapsto(f,\sqrt{1-\lVert f\rVert^2})$ is the vector form of their extension $\rho\mapsto\rho\oplus(1-\operatorname{tr}\rho)$.
> Lemmas A and C are the corresponding analogues of the triangle inequality for the angular distance on
> sub-normalized states and of its monotonicity under trace-non-increasing maps; we include proofs because the
> signed version does not follow formally. The telescoping proof of Theorem D is an angle version of the hybrid
> argument, and the mechanism "angles add, lengths multiply" is that of scaled relative graphs.

> For $\alpha=\pi/2$ the equal-angle extremality reflects the fact that the $n$-fold Minkowski power of the disk
> $\lvert z-\tfrac12\rvert\le\tfrac12$ is bounded by the curve $t\mapsto w(t)^n$, i.e. by $n$-th powers of single boundary
> points (Farouki–Pottmann 2002, §5); for $n=2$ this is the cardioid, described by Polyak–Scherbakov–Shmulyian (1994)
> and Farouki–Moon–Ravani (2001) and proved rigorously by Huang–Ryu–Yin (2020, Thm. 1; see also Ryu–Hannah–Yin 2022,
> Fact 16). The box-constrained case $\alpha<\pi/2$, which is not accessible from disk-product boundaries, the capped
> inequality, and the resulting constant $C_k(\eta)$ are what the present argument adds.

Cautions: cite Farouki–Pottmann for the geometric picture, not for rigor; do not quote specific content of
Farouki–Moon–Ravani 2001 or Polyak et al. 1994 until their full texts are read. The phrase "what the present
argument adds" replaces any novelty wording until the stop criterion (§4) is met. Precise locators per source are
in the Level-3 files.

## 4. Stop criterion (protocol §8) — status

| # | Criterion | Status |
|---|---|---|
| 1 | Every family has anchors | **Partial**: seeded anchors for A, B, D, E, H, I, J, K, M; none designated yet for C, F, G, L, N |
| 2 | Backward + forward chasing of all anchors | **Partial**: 14 seed anchors via OpenAlex (one round); Scholar forward chasing manual pending |
| 3 | MSC searched | **Not met**: zbMATH MSC coverage sparse (9 relevant records; recurring prefixes 47, 65, 46); MathSciNet manual pending |
| 4 | Every threat 4–5 source read at Level 3 | **Met vacuously** (none found); threat-3 sources: Feshchenko L3 (disputed), Zniyed–Boyer abstract only (manual PDF), Bachmayr–Nouy–Schneider L2 |
| 5 | Two consecutive snowball rounds without new family / threat ≥4 | **Not met** (one round) |
| 6 | Every claim has a documented status | **Met** (§1) |
| 7 | Recent literature re-checked at submission | Later |

**MSC codes to use in MathSciNet** (from relevant zbMATH records; small sample, verify against anchors):
47A12 (numerical range), 47A30 (norms), 47H09 (nonexpansive maps), 46C05 (Hilbert space geometry),
65K10, 65F (numerical linear algebra), 15A60 (norms of matrices), and — expected from tensor
anchors, not yet observed — 15A69 (multilinear algebra, tensor products).

## 5. Search coverage and limitations

- **Automated:** OpenAlex 47/47 queries; zbMATH 47/47 (many zero-result multi-word queries — zbMATH
  coverage is weak for this phrasing); arXiv API and Semantic Scholar rate-limited from the first query
  (skipped and logged; OpenAlex indexes arXiv).
- **Citation graph:** 14 seed anchors, backward + forward (OpenAlex), two anchor identifiers corrected
  (quarantined outputs).
- **Screening:** 1745 pooled candidates at Level 1 (63 by abstract, 1682 by title), consistency
  audit of low-threat rows with strong keywords; 58 at Level 2; 18 Level-3 comparisons.
- **Access limits:** Kayalar–Weinert and Deutsch–Hundal originals not read (paywall; statements via
  open secondary sources); Zniyed–Boyer and Krämer thesis blocked by bot checks.
- **Title-only screening** of 1682 candidates can miss papers with uninformative titles; this is why the
  manual MathSciNet/Scholar passes and a second snowball round are required before any novelty sentence.

## 6. Manual actions for the author

1. Run `MANUAL_QUERIES.md` (MathSciNet, Google Scholar) and log in `SEARCH_LOG.csv`.
2. Download Zniyed–Boyer 2026 (HAL hal-05554951) and check whether any bound is sharp or tree-independent.
3. Adjudicate Feshchenko 2019 (threat 1 vs 3).
4. If institutional access allows: read Kayalar–Weinert 1988 and Deutsch–Hundal 1997 in the original.
5. Fix the wrong DOI of Deutsch–Hundal in `papers/paper_a/references.bib` (`10.1006/jmaa.1997.5216` → `10.1006/jmaa.1997.5202`).
6. Designate anchors for families C, F, G, L, N and run `snowball.py round2`.

## 7. Wording allowed now (style contract §12)

Internal drafts only: *"We are not aware of an equivalent sharp result; a systematic prior-art review is ongoing."*
No novelty sentence in any external text until §4 criteria 1–5 are met.
