# Prior-art audit: nodewise error certificates for typed multilinear trees

Search date: 2026-07-29.  The audit used publisher pages, DOI records, original
papers, recognized monographs, and author/preprint versions where a publisher
page did not expose the theorem text.  Search topics included colored operads,
approximate homomorphisms, multilinear perturbation, computational-graph bound
propagation, hierarchical/tree tensors, backward error, interval arithmetic,
SOS optimization, and structure-preserving reduction.

## Findings

- Colored operads already provide the standard semantics of typed operations
  and rooted-tree composition.  The v3 typed model is an implementation and
  specialization, not a new operad.
- Multilinear telescoping and norm-product perturbation estimates are standard
  analysis tools.  The homogeneous ambient (k) estimate is therefore treated
  as a standard multilinear bound.
- Approximate-homomorphism/Hyers--Ulam work asks when an approximately
  multiplicative map is close to an exact homomorphism.  That is adjacent but
  not the same optimization problem as recursive orthogonal projection with a
  nodewise normal closure map.
- Backward-error and abstract-interpretation literature develops compositional
  propagation of local summaries.  It establishes strong prior art against a
  broad claim that dynamic-programming certificates themselves are new.
- Hierarchical Tucker and tree tensor-network literature makes topology and
  tree-dependent approximation error central, but its errors arise from
  low-rank truncation/representation rather than a normal closure defect at
  each algebraic node.
- We did not locate, in this search, the exact projected-root theorem removing
  the root residual and yielding coefficient (k-1), nor the signed/typed
  mixed-mask formulation here.  Absence from a bounded search is not proof of
  novelty.  The registry therefore retains `NOVELTY_NOT_ESTABLISHED` pending an
  independent expert search.

## Core primary and official sources

1. D. Yau, *Colored Operads*, AMS GSM 170, provides typed/colored operad and
   partial-composition foundations: <https://doi.org/10.1090/gsm/170>.
2. J.-L. Loday and B. Vallette, *Algebraic Operads*, gives standard tree and
   algebra-over-operad semantics: <https://doi.org/10.1007/978-3-642-30362-3>.
3. B. E. Johnson, “Approximately multiplicative maps between Banach algebras,”
   studies stability of approximate homomorphisms:
   <https://doi.org/10.1112/jlms/s2-37.2.294>.
4. N. J. Higham, *Accuracy and Stability of Numerical Algorithms*, supplies
   forward/backward error and order-of-evaluation context:
   <https://doi.org/10.1137/1.9780898718027>.
5. P. L. Combettes and J.-C. Pesquet derive architecture-sensitive layered
   Lipschitz certificates rather than only products of layer bounds:
   <https://doi.org/10.1137/19M1272780>.
6. T. Gehr et al., “AI2,” uses sound compositional overapproximation and
   abstract transformers: <https://doi.org/10.1109/SP.2018.00058>.
7. W. Hackbusch and S. Kühn introduce a hierarchical tensor representation
   organized by a dimension tree: <https://doi.org/10.1007/s00041-009-9094-9>.
8. J. Ballani and L. Grasedyck study adaptive tree choice in hierarchical
   tensor approximation: <https://doi.org/10.1137/130926328>.
9. T. G. Kolda and B. W. Bader survey CP/Tucker tensor decompositions:
   <https://doi.org/10.1137/07070111X>.
10. R. E. Moore, R. B. Kearfott, and M. J. Cloud, *Introduction to Interval
    Analysis*, supplies validated interval methodology:
    <https://doi.org/10.1137/1.9780898717716>.
11. J. B. Lasserre’s moment/SOS hierarchy supplies certified polynomial upper
    bounds under its assumptions: <https://doi.org/10.1137/S1052623400366802>.
12. H. Egger et al. provide projection-based structure-preserving model
    reduction under compatibility hypotheses: <https://doi.org/10.1137/17M1125303>.

The machine-readable overlap matrix is generated from
`claims/prior_art_registry_v3.yaml`; no novelty label is inferred from the
software or from terminology.
