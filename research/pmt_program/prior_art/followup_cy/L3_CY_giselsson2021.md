# L3-CY: Giselsson, Moursi (2021), "On compositions of special cases of Lipschitz continuous operators"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Rubric: `PROTOCOL_CY.md` §2. Paraphrased.

## 1. Record

| Field | Value | Status |
|---|---|---|
| Venue | Fixed Point Theory Algorithms Sci. Eng. (2021); DOI 10.1186/s13663-021-00709-0; arXiv:1912.13165 | HET anchor (verified OpenAlex + Crossref in `anchors_het.json`); forward set of CY15 and OY02 |
| Access | FULL_TEXT arXiv v1 (PDF text): §1, §3 (Thm 3.3, 3.4), §4 (Thm 4.2, Cor. 4.3, Ex. 4.4, Prop. 4.5, **Thm 4.7**, Ex. 4.8, Thm 4.9), Remark 6.4, §8 figures | |

## 2. Setting and results (paraphrased)

Compositions $R=R_m\cdots R_1$ of operators with $(\alpha_i,\beta_i)$ identity–nonexpansive decompositions
(averaged, conically nonexpansive, cocoercive, scaled).

- **Thm 3.4 / Thm 4.2 (m = 2).** The composition of two scaled conically nonexpansive maps is scaled conically
  nonexpansive under a product condition on the parameters.
- **Thm 4.7 (m factors).** Induction gives a conic constant for $m$ scaled conic factors, with at most one factor
  $r$ allowed a conic parameter above 1. The constant is the Combettes–Yamada form $\sum_{i}\alpha_i/(1-\alpha_i)$
  over $i\ne r$, combined with $\alpha_r$. It is symmetric in the non-exceptional factors.
- **Ex. 4.8 (m = 3).** Commuting planar rotation-scalings show that the assumption $\alpha_r\kappa<1$ cannot be dropped.
  This is a necessity example for the hypothesis, not a tightness proof of the constant.
- **Thm 4.9.** Composition of $m$ cocoercive operators (from Thm 4.7 with all $\alpha_i=1/2$).
- Remark 6.4 and the §8 figures: tightness of **two-factor** Lipschitz/contraction constants (forward–backward).

## 3. Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | **PARTIAL** | Planar examples use commuting $2\times2$ rotation-scalings (complex scalars), but constants are derived algebraically. |
| C2 | **NO** | Parameters are averagedness / conic / scale constants (disk radii), not angle caps. |
| C3 | **NO** | Thm 4.7 is an upper bound for $m$ factors; tightness shown only in $m=2$ examples. |
| C4 | **NO (m ≥ 3)** | Ex. 4.8 is a counterexample to dropping a hypothesis, not an extremizer of the constant. |
| C5 | **PARTIAL** | Symmetric in non-exceptional factors; exceptional factor $r$ is distinguished. |
| C6 | **NO** | Disk-radius parameters. Even with all $\alpha_i=1/2$ the bound is cap-blind (see `cy_numeric_check_output.txt`, correspondence A). |

## 4. Threat

**2 / 5** (m-factor heterogeneous composition constants, CY-type, non-sharp for $m\ge3$; no angle caps).
