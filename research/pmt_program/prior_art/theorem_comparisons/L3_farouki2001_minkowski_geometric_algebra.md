# L3 comparison: Farouki, Moon, Ravani (2001), "Minkowski Geometric Algebra of Complex Sets"

Prepared 2026-09-14. This is a Level-3 comparison focused on R7 (the Diagonal Lemma) and its consequences R2 and R1b. Only public
sources were used, and everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| FMR01 | R. T. Farouki, H. P. Moon, B. Ravani, "Minkowski Geometric Algebra of Complex Sets", Geometriae Dedicata 85(1–3) (2001) 283–315. DOI 10.1023/A:1010318011860. | VERIFIED. The Springer landing page was seen (abstract; citation metadata vol. 85, issue 1, pp. 283–315, 2001/03) and matches Crossref. |

Related (not read): Farouki, Moon, Ravani, "Algorithms for Minkowski products and implicitly-defined complex sets",
Adv. Comput. Math. 13 (2000) 199–229, which is the source of the logarithmic-Gauss-map matching condition.

## 2. Access level

ABSTRACT_ONLY + SECONDARY.
- The Springer abstract was seen. OpenAlex and Semantic Scholar report no open-access copy. The Academia.edu and ResearchGate copies
  were not accessible (HTTP 403) and were not pursued further. No shadow libraries were used.
- Secondary descriptions of FMR01's content: (i) Farouki–Pottmann 2002 §2 and §3 (read in full); (ii) Huang–Ryu–Yin 2020
  §1.1 (read in full); (iii) R. T. Farouki's public lecture slides "Minkowski geometric algebra of complex sets — theory,
  algorithms, applications" (UC Davis faculty site, read in full). The slides are a survey, not the paper.

## 3. Their setting (from abstract and secondary sources)

- An algebra of planar point sets under Minkowski sums and products, presented as the complex extension of interval arithmetic.
  Listed applications: geometrical optics (anticaustics, wavefronts), shape operators, control-system stability.
- Catalogue of basic product boundaries: line × line (parabola), line × circle (conic), circle × circle (Cartesian oval,
  degenerating to a limaçon or a cardioid), Minkowski roots (Cassini-type ovals), Minkowski powers ⊗^n A versus ordinary powers A^n
  (inclusion A^n ⊆ ⊗^n A).

## 4. Relevant results (paraphrased, via secondary sources)

- The Minkowski product of two circles with center 1 is the region between the two loops of a Cartesian oval. The product of
  the corresponding *disks* is the region inside the outer loop (FP02 §2, citing FMR01, and crediting Polyak et al. 1994 with
  the disk statement).
- The degenerate cases are the limaçon (one radius = 1) and the **cardioid (both radii = 1)**. After scaling by 1/4, the cardioid bounds
  D² for our disk D = {|z − 1/2| ≤ 1/2}. The boundary is w(t)².
- According to HRY20 §1.1, FMR01 §6.7 performs the envelope computation that coincides with HRY20 Theorem 1 after a change of variables.
  It asserts the disk-enclosure step without proof. HRY20 therefore regard the FMR01 treatment as incomplete in rigor.
- As far as can be established without the full text: FMR01 does not treat N-fold products beyond general definitions (FP02 was
  written to do that), does not treat circular arcs as operands, and does not maximize |1 − z| over a product set.

## 5. Comparison table

| Row | Status | Explanation |
|---|---|---|
| R7, α = π/2 (full arc), general n | NO | Only the general definition of Minkowski powers appears. The explicit n-fold boundary is in FP02, not here. |
| R7, α < π/2 (truncated arc) | NO | No arcs, no box constraints. |
| R7, n = 2 | SPECIAL_CASE (α = π/2 only, heuristic) | The cardioid as boundary of the Minkowski square of a disk through 0 gives R7(n = 2, α = π/2) after maximizing \|1 − z\| on the boundary. The step is not in FMR01, and FMR01's own enclosure claim is unproved per HRY20. |
| Capped "moreover" inequality | NO | Nothing of this kind. |
| R2 explicit constant | NO | No operator or η context. |
| R1b sharpness | NO | Not addressed. |

Confidence caveat: the status entries rest on secondary descriptions. If the full text becomes available, check §6
(products of circles and disks) and any section on Minkowski powers for an n-fold equal-point statement. If one exists, it
would at most duplicate FP02 §5 and would not change the truncated-case verdict.

## 6. Threat score

**1 / 5** for R7. FMR01 is the foundational reference for Minkowski products of disks and the cardioid degeneration (n = 2,
full disk), with no box constraint, no |1 − ·| objective and no n-fold explicit result. **0 / 5** for R2 and R1b.

## 7. How to cite

Cite only as the general framework reference, bundled with FP02:

> Minkowski products of complex disks and their boundaries (Cartesian ovals; the cardioid for two disks through 0) are
> treated in [Farouki–Moon–Ravani 2001]; the n-fold case is in [Farouki–Pottmann 2002].

Do not cite FMR01 for any specific statement without first checking the full text. Section-level pointers (e.g. §6.7)
currently rest on HRY20's description.
