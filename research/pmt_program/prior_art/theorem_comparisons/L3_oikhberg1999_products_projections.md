# L3 comparison: Oikhberg (1999), "Products of orthogonal projections"

Prepared 2026-09-14. Level-3 comparison against Theorem R, rows R1a, R1b, R2, R3, R5 (planar
extremizer), R7 (diagonal lemma). Public sources only; paraphrased. (R-numbering follows the request
that produced this file; sibling files may number differently.)

## 1. Bibliographic record

- Author: Timur Oikhberg
- Title: Products of orthogonal projections
- Journal: Proceedings of the American Mathematical Society 127 (1999), no. 12, 3659–3669;
  electronically published 17 May 1999
- DOI: 10.1090/S0002-9939-99-05255-7; zbMATH Zbl 0983.47013
- Status: VERIFIED (AMS open-archive PDF read; Crossref and zbMATH records agree).

## 2. Access level

FULL_TEXT (AMS PDF, 11 pp.): Theorem 1, Lemmas 2–5, Corollaries 6–7, Proposition 8, Proposition 9 (quoting
Kuo–Wu), Theorem 10, Corollary 11, Lemma 12, Theorem 13, Proposition 14.

## 3. Their setting and assumptions

- Separable real/complex Hilbert space; which operators factor as finite products of orthogonal
  projections, and how many factors M(u) are needed.
- Parameters: operator norm ‖u‖ < 1, rank, dimension. No angle/defect constraint on consecutive factors
  as a hypothesis; no error comparison between products.

## 4. Their main results relevant here

- Theorem 1: an n×n operator of norm < 1 with nontrivial kernel is a product of projections, with
  M(u) ≲ C·(n/(n − rank u))·1/(1 − ‖u‖); optimal up to constants (lower bound via Lemma 5).
- Lemma 2(a) (after Kuo–Wu): a vector x can be moved to a shorter vector y in the same plane by projections
  onto lines at angles φ_0 < φ_1 < … < φ_k; the image is ∏ cos(φ_i − φ_{i−1}) times the final direction.
  The number of steps is controlled through the equal-step quantity cos(π/k)^k (bounded below by an
  exponential in −1/k); the intermediate angles are then adjusted ("suitable choice") to hit ‖y‖ exactly.
- Lemma 5: lower bound on the number of factors for u = −a P_E, via a telescoping decomposition
  P_E P_j⋯P_1 − P_E P_{j−1}⋯P_1 and Schatten-norm counting.
- Theorem 10 / Corollary 11: characterization of products of projections of the form I ⊕ S with ‖S‖ < 1
  in infinite dimensions; description of the norm closure of all products of projections.
- Proposition 14: disproves a Kuo–Wu conjecture.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | Factorization/counting theory; no bound on the discrepancy between projected and unprojected products. |
| R1b | NO | No η-dependent constant. |
| R2 | NO | Optimality statements concern the number of factors, not an error constant. |
| R3 | NO | No trees. |
| R5 | ADJACENT | Lemma 2(a) is exactly the planar "rotate by successive projections onto lines" construction: in complex notation the image of x is ∏ cos Δφ_j · e^{iΣΔφ_j}, i.e. the product ∏ cos θ_j e^{iθ_j} appearing in our planar extremizer. Used as a construction, not as an extremizer of an error functional. |
| R7 | ADJACENT | Uses the equal-step chain cos(π/k)^k as a counting device, but does not prove that equal angles are extremal for any functional, and has no box constraint or |1 − ∏| objective. |

## 6. Threat score

**1 / 5**.

Justification: shares the planar line-projection chain and a telescoping identity with our proofs, so it is a
good citation for the construction's classical character, but no statement of Theorem R is implied.

## 7. How to cite / position

The planar chain of projections onto lines at successive angles, whose action is ∏ cos θ_j e^{iθ_j}, is
classical in the factorization theory of contractions (Kuo–Wu; Oikhberg 1999, Lemma 2); Theorem R shows
that this chain, with equal angles at the defect limit arcsin η, is exactly extremal for the projected-evaluation
error.
