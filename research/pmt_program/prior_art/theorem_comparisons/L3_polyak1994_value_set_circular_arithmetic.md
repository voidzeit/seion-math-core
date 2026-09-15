# L3 comparison: Polyak, Scherbakov, Shmulyian (1994), "Construction of value set for robustness analysis via circular arithmetic"

Prepared 2026-09-14. This is a Level-3 comparison focused on R7 (the Diagonal Lemma) and its consequences R2 and R1b. Only public
sources were used, and everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| PSS94 | B. T. Polyak, P. S. Scherbakov, S. B. Shmulyian, "Construction of value set for robustness analysis via circular arithmetic", International Journal of Robust and Nonlinear Control 4(3) (1994) 371–385. DOI 10.1002/rnc.4590040305. | VERIFIED via Crossref (title, authors, vol. 4, issue 3, pp. 371–385, 1994, abstract). The Wiley landing page was *not* seen (bot check / HTTP 403). |

Identification: this is the paper Huang–Ryu–Yin 2020 cite as [19] (arXiv v2) or [17] (arXiv v3). HRY20 say its Theorem 1 matches
theirs after a change of variables. Farouki–Pottmann 2002 cite the same paper as [27], for the observation that the
product of two disks is the region inside the outer loop of a Cartesian oval, and in the context of robust stability of
disk polynomials.

## 2. Access level

ABSTRACT_ONLY + SECONDARY. The Crossref abstract was read. The paper is not in Boris Polyak's public "works in English" list, and no open copy
was found. The ResearchGate copy was not accessed. No shadow libraries were used. Content is known only through HRY20 §1.1 and FP02 §1–2.

## 3. Their setting

- Robust stability of polynomials with uncertain complex coefficients given by disks ("disk polynomials").
  Value sets are built with circular arithmetic, and the zero-exclusion principle is applied.
- According to the abstract: necessary and sufficient robust-stability conditions for disk polynomials and simple
  combinations of them, sufficient conditions in harder cases, and examples with multilinear (real or complex) parameter
  perturbations.

## 4. Relevant results (paraphrased, via secondary sources)

- **Theorem 1 (per HRY20).** A description of the Minkowski product of two complex disks as the region inside the outer loop of
  a Cartesian oval. HRY20 state that it is equivalent to HRY20 Thm 1 after a change of variables, but that it omits the two steps that
  make the proof rigorous: enclosure of the disk product and absence of holes.
- **Per FP02.** PSS94 made the observation that the disk product fills the inside of the outer loop.
- Nothing indicates n-fold products with explicit boundaries, arcs or box constraints on arguments, or maximization of |1 − z|.
  The multilinear examples in the abstract are about value sets of polynomials in perturbation parameters, not products
  of points on one circle through 0 and 1. This could not be checked without full text.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| R7, α = π/2 (full arc), general n | NO | Two-disk products only (as far as secondary sources show). |
| R7, α < π/2 (truncated arc) | NO | No arcs, no angle box. |
| R7, n = 2 | SPECIAL_CASE (α = π/2 only, non-rigorous) | Theorem 1 with two disks through 0 and 1 (radius 1/2 about 1/2) gives the cardioid region, and R7(n = 2, α = π/2) follows by maximizing on the boundary. HRY20 flag the proof as incomplete. |
| Capped "moreover" inequality | NO | — |
| R2 explicit constant | NO | Robust-stability margins are a different functional, with no η-constraint. |
| R1b sharpness | NO | "Necessary and sufficient" refers to stability conditions, not to sharpness of a contraction constant. |

## 6. Threat score

**1 / 5** for R7, the earliest known appearance of the two-disk product region, with no n-fold or truncated content.
**0 / 5** for R2 and R1b. Confidence is limited by abstract-only access. Upgrade only if the full text shows an n-fold,
arc-constrained extremal statement, which is unlikely given how both HRY20 and FP02 describe it.

## 7. How to cite

Cite only for historical priority on the two-disk product region, via HRY20's attribution:

> The Minkowski product of two disks was described in the robust-stability literature by Polyak, Scherbakov and Shmulyian
> (1994) (see [HRY20, §1.1] for a comparison and a rigorous proof).

Do not quote theorem content from PSS94 directly until the full text has been checked.
