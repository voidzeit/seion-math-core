# L3 comparison: Deutsch & Hundal (1997), "The rate of convergence for the method of alternating projections, II"

Prepared 2026-09-14. Level-3 comparison against Theorem R, rows R1a, R1b, R2, R3, R5 (planar
extremizer), R7 (diagonal lemma). Public sources only; paraphrased. (R-numbering follows the request
that produced this file; sibling files may number differently.)

## 1. Bibliographic record

- Authors: Frank Deutsch, Hein Hundal
- Title: The Rate of Convergence for the Method of Alternating Projections, II
- Journal: Journal of Mathematical Analysis and Applications 205 (1997), no. 2, 381–405
- DOI: 10.1006/jmaa.1997.5202; zbMATH Zbl 0890.65053
- Status: metadata VERIFIED via Crossref and zbMATH Open (review text visible). ScienceDirect landing page
  returned HTTP 403 (not seen). Part I: F. Deutsch, ISNM 72 (1985).

## 2. Access level

ABSTRACT_ONLY / SECONDARY. Read: the zbMATH Open review; the abstract's three stated aims (via search
snippets of the publisher page); the description in Badea–Grivaux–Müller arXiv:1006.2047 (their reference
[13], Example 3.7). Full text NOT read (paywalled; an academia.edu copy returned 403). Theorem numbers
other than Example 3.7 are not known.

## 3. Their setting and assumptions

- r ≥ 2 closed subspaces of a Hilbert space; cyclic product of orthogonal projections; error
  ‖(P_{M_r}⋯P_{M_1})^n − P_M‖.
- Parameters: Friedrichs-type angles between subspaces (pairwise, and between a subspace and
  intersections of others).
- Linear, no trees, no multilinear maps.

## 4. Their main results relevant here (as reported)

- An easily computable upper error bound for the cyclic method in terms of angles (exact formula not seen).
- A counterexample to a conjecture of Kayalar and Weinert.
- Negative sharpness result: for r ≥ 3, NO error bound depending only on the angles between the subspaces
  can be sharp; BGM attribute to Example 3.7 that for N ≥ 3 the error is not a function of the pairwise
  Friedrichs angles.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | Different quantity (convergence of cyclic projections to P_M), no inserted projections into a product of contractions, no local defect. |
| R1b | NO | No constant resembling C_k(η). |
| R2 | ADJACENT | Relevant for positioning, not implied: DH show angle-only bounds cannot be configuration-wise exact for r ≥ 3. Theorem R's optimality is of a different type — best constant over the whole class of admissible trees/maps with given (k, η), attained by specific configurations — so there is no contradiction, but the paper should state explicitly which sense of "sharp" is meant. |
| R3 | NO | No tree structure. |
| R5 | NO | No planar extremizer statement known from the accessible material. |
| R7 | NO | No equal-angle extremal lemma reported. |

## 6. Threat score

**1 / 5** (background; useful for defining "sharp" carefully).

Justification: nothing in Theorem R is implied; the paper's main relevance is the warning that angle-only
bounds for ≥ 3 projections are not exact per configuration, which a referee could raise against a claim of
"sharpness" if it is not stated as a worst-case-over-class constant.

## 7. How to cite / position

Deutsch and Hundal showed that for three or more subspaces no angle-only error bound for cyclic projections
can be sharp for every configuration; Theorem R's constant C_k(η) is sharp in the worst-case sense (the
supremum over all admissible configurations with given k and η is attained), which is compatible with
their observation.
