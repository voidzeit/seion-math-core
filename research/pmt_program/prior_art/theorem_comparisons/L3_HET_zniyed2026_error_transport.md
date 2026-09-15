# L3-HET comparison: Zniyed & Boyer (2026), "Error transportation in SVD-based tensor-train approximations"

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison against H1 and H2, made **from the abstract only**. The threat score is
provisional.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| ZB26 | Y. Zniyed, R. Boyer, "Error transportation in SVD-based tensor-train approximations", HAL hal-05554951 (v2), 2026. OpenAlex W7139529380. No DOI. | Metadata from OpenAlex/HAL listing. The authors were not verified against the PDF. `NO_DOI`. |

## 2. Access level

ABSTRACT_ONLY. The HAL PDF (`https://hal.science/hal-05554951/document`) returned an automated bot-check page on 2026-09-14. It was
**not bypassed** (protocol). **Manual action:** the author must download the PDF in a browser.

## 3. Their setting (from the abstract)

- TT-SVD and TT-HSVD on general dimension trees for one tensor.
- Algorithmic matrices and *transport operators* carry local truncation errors to the ambient tensor.
- The results are exact global error decompositions, a priori bounds and quasi-optimality. Non-isometric transport on general trees gives
  data-dependent conditioning factors. In the chain case these factors vanish, which yields sharp Pythagorean identities.

## 4. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 | NO (CLOSE, provisional) | Local (heterogeneous) truncation errors are propagated through trees to a global bound. The setting is linear, with one tensor, SVD tails and conditioning factors. There are no multilinear maps with norm bounds and no defect ratio. |
| H2 | NO (contrast, provisional) | The bounds depend on the tree through the conditioning factors. Placement independence holds only in the chain case, as an exact Pythagorean identity for a different functional. |
| H4 | UNKNOWN | "Sharp" refers to the chain-case identity. Extremal examples on general trees cannot be judged without the full text. |
| H3 | NO | — |

## 5. Threat score

**3 / 5 (provisional, abstract only)**. It must be re-scored after the full text is read. The score is not raised to 4, because the abstract
states tree-dependent factors, which is the opposite of H2, and describes a linear setting.

## 6. How to cite (provisional)

> Error transport of local truncations through dimension trees in TT-SVD/TT-HSVD produces tree- and data-dependent factors
> (Zniyed–Boyer 2026); [to be completed after reading the full text].
