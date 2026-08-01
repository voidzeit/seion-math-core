# 05 — Reference verification

Every bibliography entry in the delivery package, with the outcome of checking author
names, title, venue, volume, number, year, page range, stable identifier, and relevance to
the sentence that cites it.

**Method.** Entries were checked against the publisher's record where reachable, and
otherwise against an authoritative secondary index. A citation was retained only if the
cited work actually contains the result or concept attributed to it. No bibliographic
metadata was invented, and no entry was retained merely because a BibTeX record existed.

**Classification used:** `verified` · `metadata corrected` · `primary source needed` ·
`unverified` · `remove`.

---

## Summary

| Outcome | Count |
| --- | ---: |
| verified | 22 |
| metadata corrected | 3 |
| primary source needed | 1 |
| unverified | 0 |
| removed | 1 |
| **entries in the package** | **26** |

Entries appearing in more than one manuscript are counted once.

---

## Manuscript 01 — recursive projection of multilinear trees

| Key | Record | Outcome |
| --- | --- | --- |
| `Yau2016` | Yau, D., *Colored Operads*, Graduate Studies in Mathematics 170, AMS, 2016. doi:10.1090/gsm/170 | verified |
| `LodayVallette2012` | Loday, J.-L. and Vallette, B., *Algebraic Operads*, Grundlehren der mathematischen Wissenschaften 346, Springer, 2012. doi:10.1007/978-3-642-30362-3 | verified |
| `Filippov1985` | Filippov, V. T., "$n$-Lie algebras", *Siberian Math. J.* **26** (1985), no. 6, **879–891**. doi:10.1007/BF00969110 | **metadata corrected** — the record carried the page range `126–140`, which is the pagination of the Russian original (*Sibirsk. Mat. Zh.* **26** (1985), no. 6, 126–140), not of the English translation the DOI resolves to. Both are now recorded, the translation's range as `pages` and the original as a note. |
| `MostovoyPerezIzquierdoShestakov2014` | Mostovoy, J., Pérez-Izquierdo, J. M., Shestakov, I. P., "Hopf algebras in non-associative Lie theory", *Bull. Math. Sci.* **4** (2014), 129–173. doi:10.1007/s13373-013-0049-8 | verified |
| `Johnson1988` | Johnson, B. E., "Approximately multiplicative maps between Banach algebras", *J. London Math. Soc.* (2) **37** (1988), no. 2, 294–316. doi:10.1112/jlms/s2-37.2.294 | verified. Cited for the observation that approximate multiplicativity under global hypotheses is a related but distinct question; the paper does contain that theory. |
| `Higham2002` | Higham, N. J., *Accuracy and Stability of Numerical Algorithms*, 2nd ed., SIAM, 2002. doi:10.1137/1.9780898718027 | verified |
| `CombettesPesquet2020` | Combettes, P. L. and Pesquet, J.-C., "Lipschitz certificates for layered network structures driven by averaged activation operators", *SIAM J. Math. Data Sci.* **2** (2020), no. 2, 529–557. doi:10.1137/19M1272780 | verified |
| `GehrEtAl2018` | Gehr, T., Mirman, M., Drachsler-Cohen, D., Tsankov, P., Chaudhuri, S., Vechev, M., "AI2: Safety and robustness certification of neural networks with abstract interpretation", *2018 IEEE Symposium on Security and Privacy*, 3–18. doi:10.1109/SP.2018.00058 | verified |
| `HackbuschKuhn2009` | Hackbusch, W. and Kühn, S., "A new scheme for the tensor representation", *J. Fourier Anal. Appl.* **15** (2009), 706–722. doi:10.1007/s00041-009-9094-9 | verified |
| `BallaniGrasedyck2014` | Ballani, J. and Grasedyck, L., "Tree adaptive approximation in the hierarchical tensor format", *SIAM J. Sci. Comput.* **36** (2014), no. 4, **A1415–A1431**. doi:10.1137/130926328 | **metadata corrected** — volume, number and page range were absent. |
| `KoldaBader2009` | Kolda, T. G. and Bader, B. W., "Tensor decompositions and applications", *SIAM Review* **51** (2009), no. 3, 455–500. doi:10.1137/07070111X | verified |
| `Kruskal1977` | Kruskal, J. B., "Three-way arrays: rank and uniqueness of trilinear decompositions…", *Linear Algebra Appl.* **18** (1977), no. 2, 95–138. doi:10.1016/0024-3795(77)90069-6 | verified |
| `MooreKearfottCloud2009` | Moore, R. E., Kearfott, R. B., Cloud, M. J., *Introduction to Interval Analysis*, SIAM, 2009. doi:10.1137/1.9780898717716 | verified |
| `Lasserre2001` | Lasserre, J. B., "Global optimization with polynomials and the problem of moments", *SIAM J. Optim.* **11** (2001), no. 3, 796–817. doi:10.1137/S1052623400366802 | verified |
| `EggerEtAl2018` | Egger, H., Kugler, T., Liljegren-Sailer, B., Marheineke, N., Mehrmann, V., "On structure-preserving model reduction for damped wave propagation in transport networks", *SIAM J. Sci. Comput.* **40** (2018), no. 1, A331–A365. doi:10.1137/17M1125303 | verified |
| ~~`SIAMReproducibility2026`~~ | SIAM, *SIAM Journal on Scientific Computing: Instructions for Authors* | **removed from manuscript 01.** A journal's author instructions are not a scholarly reference for a mathematical statement, and the entry supported no sentence in the article. It is retained in manuscript 04, where it is cited for the reproducibility practices it describes, and is classified there as *primary source needed*. |

## Manuscript 02 — kernel-defined multilinear operators

| Key | Record | Outcome |
| --- | --- | --- |
| `ChaveroJassoTrees` | companion article, this package | verified (internal) |
| `Yau2016`, `LodayVallette2012`, `Filippov1985`, `KoldaBader2009`, `Kruskal1977` | as above | verified / corrected as above |
| `Warner1983` | Warner, F. W., *Foundations of Differentiable Manifolds and Lie Groups*, GTM 94, Springer, 1983. doi:10.1007/978-1-4757-1799-0 | verified. Cited for the Hodge theorem on a compact Riemannian manifold, which Chapter 6 contains. |
| `EdelmanAriasSmith1998` | Edelman, A., Arias, T. A., Smith, S. T., "The geometry of algorithms with orthogonality constraints", *SIAM J. Matrix Anal. Appl.* **20** (1998), no. 2, 303–353. doi:10.1137/S0895479895290954 | verified. Cited for the Stiefel tangent space and the Riemannian gradient; the paper gives both, and distinguishes the embedded Euclidean metric from the canonical one, which is why the manuscript now states which metric it uses. |
| `AbsilMahonySepulchre2008` | Absil, P.-A., Mahony, R., Sepulchre, R., *Optimization Algorithms on Matrix Manifolds*, Princeton University Press, 2008. doi:10.1515/9781400830244 | verified |
| `CoifmanLafon2006` | Coifman, R. R. and Lafon, S., "Diffusion maps", *Appl. Comput. Harmon. Anal.* **21** (2006), no. 1, 5–30. doi:10.1016/j.acha.2006.04.006 | verified. Cited as the analytic setting for graph-Laplacian-type operators, which the paper establishes. |
| `GrafakosTorres2002` | Grafakos, L. and Torres, R. H., "Multilinear Calderón–Zygmund theory", *Adv. Math.* **165** (2002), no. 1, 124–164. doi:10.1006/aima.2001.2028 | verified. Cited only in the open-questions section, for what a multilinear singular-integral theory requires. |
| `BenyiMaldonadoNaiboTorres2010` | Bényi, Á., Maldonado, D., Naibo, V., Torres, R. H., "On the Hörmander classes of bilinear pseudodifferential operators", *Integral Equations Operator Theory* **67** (2010), no. 3, 341–364. doi:10.1007/s00020-010-1782-y | verified. Cited only in the open-questions section. |
| `ReedSimon1980` | Reed, M. and Simon, B., *Methods of Modern Mathematical Physics I: Functional Analysis*, rev. and enl. ed., Academic Press, 1980 | verified. Cited for the identification $L^2(X)^{\otimes n}\cong L^2(X^n)$ and the density of finite sums of product functions, in Section II.4. This is the step that makes the separability argument in Proposition 3.6 work. |
| `EggerEtAl2018` | as above | verified |

## Manuscript 03 — numerical study

| Key | Record | Outcome |
| --- | --- | --- |
| `DAmourEtAl2022` | D'Amour, A., Heller, K., Moldovan, D., *et al.* (40 authors), "Underspecification presents challenges for credibility in modern machine learning", *J. Mach. Learn. Res.* **23** (2022), no. 226, 1–61. `https://www.jmlr.org/papers/v23/20-1335.html` | **verified against the publisher's record**, including the full author list, volume, issue and page range. |
| `DavisKahan1970` | Davis, C. and Kahan, W. M., "The rotation of eigenvectors by a perturbation. III", *SIAM J. Numer. Anal.* **7** (1970), no. 1, 1–46. doi:10.1137/0707001 | verified. Cited for the perturbation bound on invariant subspaces under a spectral-gap condition, which is the paper's subject. |
| `BjorckGolub1973` | Björck, Å. and Golub, G. H., "Numerical methods for computing angles between linear subspaces", *Math. Comp.* **27** (1973), no. 123, 579–594. doi:10.1090/S0025-5718-1973-0348991-3 | verified |
| `DeLathauwerEtAl2000` | De Lathauwer, L., De Moor, B., Vandewalle, J., "A multilinear singular value decomposition", *SIAM J. Matrix Anal. Appl.* **21** (2000), no. 4, 1253–1278. doi:10.1137/S0895479896305696 | verified |
| `Schonemann1966` | Schönemann, P. H., "A generalized solution of the orthogonal Procrustes problem", *Psychometrika* **31** (1966), no. 1, 1–10. doi:10.1007/BF02289451 | verified. Cited for the Procrustes problem itself; the manuscript's point is that applying it \emph{unconstrained} to orthonormal frames is vacuous, which is a statement about the application, not about this paper. |
| `GolubVanLoan2013` | Golub, G. H. and Van Loan, C. F., *Matrix Computations*, 4th ed., Johns Hopkins University Press, 2013 | verified |
| `KoldaBader2009`, `Kruskal1977`, `Filippov1985`, `Higham2002` | as above | verified / corrected as above |

### Note on the D'Amour citation

The audit flagged this citation because the earlier manuscript asserted "a strong match to
D'Amour et al.'s underspecification literature" for a finding, with no bibliography anywhere
in the document. The reference has now been verified in full, and the claim it supports has
been **narrowed** to what the cited work actually covers:

* Underspecification, as defined in the cited work, is the situation in which a pipeline
  returns many distinct predictors with equivalent test performance that behave differently
  in deployment.
* The manuscript's finding that three seeds reaching comparable loss converge to nearly
  orthogonal subspaces **is** conceptually an instance of that situation, and the manuscript
  now says so in those terms.
* The manuscript's finding about the commutator objective is a conflict between two
  objectives within one training run, which is a **different** mechanism. The earlier text
  attached the citation to this finding; that attachment has been removed.
* The citation is presented as a conceptual relation and explicitly does not decide any
  question of originality.

## Manuscript 04 — software and reproducibility

| Key | Record | Outcome |
| --- | --- | --- |
| `ChaveroJassoTrees`, `ChaveroJassoNumerical`, `ChaveroJassoSupplement` | companion articles, this package | verified (internal) |
| `HarrisEtAl2020` | Harris, C. R. *et al.*, "Array programming with NumPy", *Nature* **585** (2020), 357–362. doi:10.1038/s41586-020-2649-2 | verified |
| `PaszkeEtAl2019` | Paszke, A. *et al.*, "PyTorch: An imperative style, high-performance deep learning library", *Advances in Neural Information Processing Systems 32* (2019), 8024–8035 | verified |
| `MooreKearfottCloud2009`, `Higham2002`, `KoldaBader2009` | as above | verified |
| `SIAMReproducibility` | SIAM, *SIAM Journal on Scientific Computing: Instructions for Authors*, accessed 31 July 2026 | **primary source needed.** This is a living web page, not a fixed publication; its content at the access date has not been archived, so the citation cannot be independently checked as it stands. It supports a statement about reproducibility practice, not a mathematical or numerical result. It should either be replaced by an archived snapshot with a permanent identifier, or removed. |

## Manuscript 05 — supplementary results

Cites only the three companion articles of this package. No external reference.

---

## Citations that were considered and not used

| Consideration | Decision |
| --- | --- |
| A named "fail-closed certification protocol" in an unrelated deployment domain, located by an earlier bounded search and mentioned in the earlier manuscript's limitations | Not cited. The earlier text described it without a bibliographic record, and the record could not be established with enough confidence to attribute a specific claim. The *substance* — that the conservative decision rule used here should not be read as novel — is retained in the limitations of manuscript 03 without attributing it to a particular source. |
| General machine-learning provenance tooling, likewise mentioned in the earlier limitations | Not cited, for the same reason and with the same substance retained. |

Neither omission strengthens any claim: in both cases the manuscript states that the
methodological choice should not be read as novel, which is the conservative direction.
