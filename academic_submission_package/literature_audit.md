# Literature audit

The purpose of this file is to record, for each cited comparison, what the cited work
actually contains and how it differs from the material in this package — and to be explicit
that **no originality assessment has been performed**.

## The question that was and was not asked

The comparison below answers:

> Does the cited work contain the concept or result attributed to it, and what is the
> precise difference between it and the statement being compared?

It does **not** answer:

> Does there already exist a theorem which, under equivalent hypotheses, implies this
> result?

The second question is the one that decides originality, and answering it requires an
expert search of the primary literature in each of the areas listed in §3. That search has
not been carried out. Consequently every row below is marked **not assessed**, and no
manuscript in this package claims novelty for anything.

**Absence of a verbatim match in a bounded search is not evidence of originality.** This is
stated in each manuscript and repeated here because it is the single most likely
misreading.

---

## 1. Comparisons for document 01

| Field | Content |
| --- | --- |
| **Source** | Yau, D., *Colored Operads*, GSM 170, AMS, 2016. doi:10.1090/gsm/170 |
| Concept cited | Typed (coloured) composition of operations along ordered trees |
| Assumptions there | An operad in a symmetric monoidal category; no metric, no projectors |
| Present result | The same bookkeeping, specialised to finite trees of concrete multilinear maps between Hilbert spaces, with orthogonal projectors at every vertex |
| Overlap | The tree and type grammar |
| Difference | Orthogonal projection defects and quantitative bounds are additional structure, absent from the operadic setting |
| Originality conclusion | **not assessed** |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Johnson, B. E., "Approximately multiplicative maps between Banach algebras", *J. London Math. Soc.* (2) **37** (1988), 294–316 |
| Result cited | Stability of approximately multiplicative maps under global hypotheses |
| Assumptions there | Banach algebras; the perturbation is of the map, globally |
| Present result | A fixed finite tree with a prescribed subspace at each vertex; the defect is created locally at each vertex and propagated |
| Overlap | Both quantify how an approximately structure-preserving map behaves under composition |
| Difference | The hypotheses are of different type — global versus vertexwise — and the conclusion here is a tree-dependent constant, not a perturbation of the map |
| Originality conclusion | **not assessed**; adjacent but not directly applicable |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Higham, N. J., *Accuracy and Stability of Numerical Algorithms*, 2nd ed., SIAM, 2002 |
| Concept cited | Forward and backward error analysis; dependence on evaluation order |
| Assumptions there | Floating-point arithmetic; scalar and matrix computations |
| Present result | Exact multilinear residuals under orthogonal projection, on a typed tree |
| Overlap | The general shape of the estimates in §§6–8 of document 01 is recognisably that of forward error analysis |
| Difference | The error source is algebraic (failure of subspace invariance), not arithmetic |
| Originality conclusion | **not assessed.** Document 01 says explicitly that it does not claim a vertexwise recursion is itself new. |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Combettes, P. L. and Pesquet, J.-C., *SIAM J. Math. Data Sci.* **2** (2020), 529–557; Gehr, T. *et al.*, *IEEE S&P* 2018, 3–18 |
| Result cited | Layerwise Lipschitz estimates; sound abstract interpretation of layered computations |
| Assumptions there | Composition of averaged operators; neural network activations |
| Present result | Multilinear branching with separately tracked projected and orthogonal blocks and locally created sources |
| Overlap | Both replace a plain product of norms by a structure-aware recursion |
| Difference | Branching multilinearity and the orthogonal splitting have no counterpart in the cited settings |
| Originality conclusion | **not assessed**; these are the strongest prior-art reasons not to claim the recursion is new |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Hackbusch, W. and Kühn, S., *J. Fourier Anal. Appl.* **15** (2009), 706–722; Ballani, J. and Grasedyck, L., *SIAM J. Sci. Comput.* **36** (2014), A1415–A1431 |
| Result cited | Hierarchical tensor formats; tree-adaptive approximation |
| Assumptions there | A dimension tree organising the modes of one tensor; error from rank truncation |
| Present result | Recursive projection of the *outputs of multilinear maps* at every vertex; error from failure of subspace invariance |
| Overlap | Tree topology as the organising structure, and as an experimental factor |
| Difference | Different error mechanism. Document 01 §17 keeps representation error and closure error separate for exactly this reason |
| Originality conclusion | **not assessed** |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Egger, H. *et al.*, *SIAM J. Sci. Comput.* **40** (2018), A331–A365 |
| Result cited | Projection-based structure-preserving model reduction |
| Assumptions there | Damped wave propagation on transport networks; a specific physical structure to preserve |
| Present result | Abstract prescribed subspaces at every vertex of an algebraic composition |
| Overlap | The projection hypothesis, and the quantification of the structure lost |
| Difference | No dynamics, no physical structure; the trees here are static algebraic expressions |
| Originality conclusion | **not assessed**; the closest methodological precedent located |
| Human verification | pending |

| Field | Content |
| --- | --- |
| **Source** | Moore, R. E. *et al.*, *Introduction to Interval Analysis*, SIAM, 2009; Lasserre, J. B., *SIAM J. Optim.* **11** (2001), 796–817 |
| Result cited | Validated interval arithmetic; moment relaxations for polynomial optimisation |
| Present use | Directed interval recursion encloses the explicit lower constructions |
| Difference | Only the enclosure machinery is used; no semidefinite relaxation is reported as a bound, because the solver and relaxation status were not independently validated |
| Originality conclusion | **not assessed**; standard tools, used as such |
| Human verification | pending |

## 2. Comparisons for documents 02 and 03

| Source | Cited for | Difference from the present material | Originality |
| --- | --- | --- | --- |
| Grafakos & Torres, *Adv. Math.* **165** (2002), 124–164 | What a multilinear singular-integral theory requires | Cited **only** in the open-questions section of document 02. Nothing in that document is claimed to belong to such a theory | not assessed |
| Bényi, Maldonado, Naibo & Torres, *Integral Equations Operator Theory* **67** (2010), 341–364 | Bilinear Hörmander classes | Likewise, open questions only | not assessed |
| Warner, *Foundations of Differentiable Manifolds and Lie Groups*, GTM 94 | The Hodge theorem on a compact manifold | Document 02's Propositions on descent and harmonic subspaces are the **finite-complex** statements, which are standard; the manifold case is cited to mark that they are different settings | standard; cited, not claimed |
| Edelman, Arias & Smith, *SIAM J. Matrix Anal. Appl.* **20** (1998), 303–353; Absil, Mahony & Sepulchre, *Optimization Algorithms on Matrix Manifolds* | Stiefel tangent space and Riemannian gradient | Reproduced with the metric named. The formula used is that of the embedded Euclidean metric | standard; cited, not claimed |
| Coifman & Lafon, *Appl. Comput. Harmon. Anal.* **21** (2006), 5–30 | The analytic setting for graph-Laplacian-type operators | Document 02's construction is conditional and has no verified instance; the citation marks where such a construction would live | standard; cited, not claimed |
| Reed & Simon, *Methods of Modern Mathematical Physics I* | `L²(X)^{⊗n} ≅ L²(X^n)` and density of finite sums of products | This is the step that makes the separability argument work | standard; cited, not claimed |
| Davis & Kahan, *SIAM J. Numer. Anal.* **7** (1970), 1–46 | Perturbation of invariant subspaces under a spectral gap | Document 03 tests the necessity of the gap condition numerically; the theorem is cited, not reproved | standard; cited, not claimed |
| Björck & Golub, *Math. Comp.* **27** (1973), 579–594; Golub & Van Loan | Principal angles between subspaces | The comparison methodology of document 03 | standard; cited, not claimed |
| De Lathauwer, De Moor & Vandewalle, *SIAM J. Matrix Anal. Appl.* **21** (2000), 1253–1278 | Multilinear singular value decomposition | Used as a compression measure | standard; cited, not claimed |
| Schönemann, *Psychometrika* **31** (1966), 1–10 | The orthogonal Procrustes problem | Document 03's finding is about the *unconstrained* application of this to orthonormal frames being vacuous. That is a statement about the application, not about the cited paper, and the article says so | not assessed |
| Kolda & Bader, *SIAM Review* **51** (2009), 455–500; Kruskal, *Linear Algebra Appl.* **18** (1977), 95–138 | Low-rank tensor representation; identifiability | Used to state that a low-rank representation introduces no structure and that factor comparison must be modulo the representation freedom | standard; cited, not claimed |
| D'Amour *et al.*, *J. Mach. Learn. Res.* **23** (2022), no. 226, 1–61 | Underspecification | See below | not assessed |

### The D'Amour comparison, in detail

| Field | Content |
| --- | --- |
| Source | D'Amour, A., Heller, K., Moldovan, D. *et al.* (40 authors), "Underspecification presents challenges for credibility in modern machine learning", *J. Mach. Learn. Res.* **23** (2022), no. 226, 1–61 |
| Result cited | A pipeline is underspecified when it returns many distinct predictors with equivalently strong test performance which nonetheless behave differently in deployment |
| Assumptions there | Machine-learning pipelines; held-out test performance as the criterion of equivalence |
| Present result compared | Document 03, §"Local identifiability": three seeds reach comparable training loss and converge to subspaces that are pairwise nearly orthogonal |
| Overlap | Genuine and conceptual: many solutions equally good by the training criterion, differing in a property one cares about |
| Difference | The present setting is a fitted subspace under a hand-specified objective, not a predictive pipeline evaluated on held-out data; the property that differs is the subspace itself, not deployment behaviour |
| **Correction made** | The earlier text attached this comparison to a *different* finding — that a commutator objective fails when trained jointly with an associator objective. That is a conflict between two objectives within a single run, which is not underspecification. The attachment was moved to the finding that actually matches |
| Originality conclusion | **not assessed.** The manuscript states the relation as conceptual and explicitly does not let it decide any question of originality |
| Human verification | The bibliographic record was verified in full against the publisher. The *aptness* of the comparison is the author's judgement and has not been checked by anyone else |

---

## 3. Areas that an originality assessment would have to cover

Listed so that the scope of what has **not** been done is explicit.

* forward and backward error analysis;
* composition and perturbation of multilinear maps;
* perturbation analysis of computational trees and expression DAGs;
* structure-preserving model reduction;
* hierarchical and tree tensor formats;
* dynamical low-rank approximation and low-rank integrators;
* coloured and symmetric operads, and quantitative statements within them;
* approximate stability of homomorphisms and of algebraic identities;
* abstract interpretation and layerwise certified bounds;
* error analysis in tensor networks;
* validated numerics for extremal constants.

For each result in documents 01 and 02 the assessment would need to record: the closest
antecedent; its hypotheses; the present hypotheses; its conclusion; the present conclusion;
and the precise difference. Only after that comparison could any result be classified as
new, a new specialisation, a new proof of a known result, a new application, or already
known.

## 4. Prior work located for the study's own methodological choices

A bounded search located directly relevant prior work for three methodological choices in
document 03: a conservative decision protocol of the same design in an unrelated deployment
domain; established provenance tooling for reconstructing run lineage; and the
underspecification literature above. Document 03 records this in its limitations and claims
none of the three as novel.

Two of those three could not be pinned to a bibliographic record with enough confidence to
cite, so they are **not cited**; the substance — that the choice should not be read as novel
— is retained without attribution. This is recorded in
`verification/reference_verification/05_reference_verification.md`. Neither omission
strengthens any claim.

## 5. No novelty score

No numerical or ordinal score of originality is computed anywhere in this package, and none
should be inferred from the tables above.
