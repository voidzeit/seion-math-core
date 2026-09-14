# Theorem-to-theorem novelty matrix

Status for every row is intentionally `NOT_ESTABLISHED` until independent
prior-art review is completed.

| Frozen statement | Exact object to compare | Status |
|---|---|---|
| projected-root `(k-1)` bound | finite typed multilinear tree with recursive orthogonal projection | NOT_ESTABLISHED |
| exact subset expansion | local multilinear error expansion with normal residual | NOT_ESTABLISHED |
| scalar DAG source weights | finite DAG nonnegative recurrence and reverse sensitivity | NOT_ESTABLISHED |
| first-order source recombination | same-source vector operator aggregation before norm | NOT_ESTABLISHED |
| exact finite source polynomial | multi-index provenance with repeated sources on a multilinear DAG | NOT_ESTABLISHED |
| signed source cancellation | finite signed source-polynomial expression | NOT_ESTABLISHED |
| restricted gated-rotation projected Jacobiator zero | exact zero for the declared structured law, not a generic Jacobi identity | NOT_ESTABLISHED |
| truncation remainder | finite omitted multi-index norm envelope | NOT_ESTABLISHED |
| separated approximate-law budget | closure/representation/interaction decomposition | NOT_ESTABLISHED |
| exact V5-A k=3 scalar lower curve | fixed defect-budget optimization inside a declared witness family | NOT_ESTABLISHED |
| k=3 asymptotic sharpness as eta tends to zero | squeeze of the V5-A lower curve with the universal coefficient two | NOT_ESTABLISHED |
| repeated-law k=2 fixed-eta band | shared-law projected chain with eta <= C <= 1 | NOT_ESTABLISHED |
| declared gated-planar rotation k=2 exact value | homogeneous repeated gated rotation with `E_proj=eta^2` and saturation iff eta=1 | NOT_ESTABLISHED |
| M8 k=2 equality characterization | equality conditions for a recursively projected multilinear chain | NOT_ESTABLISHED |
| M9 k=3 unconditional upper envelope | independent-law chain/branching projected-root constant | NOT_ESTABLISHED |
| M10 k=3 envelope non-attainment | equality obstruction for the M9 envelope | NOT_ESTABLISHED |
| exact all-k left-comb gated-rotation formula | restricted same-law family with `E_proj=|T_k(c)-c^k|` | NOT_ESTABLISHED |
| exact all-topology homogeneous gated-rotation recurrence | every finite ordered full-binary topology under one declared gated law | NOT_ESTABLISHED |
| exact finite variable-arity gated-rotation recurrence | every ordered rooted tree with arities at least two under arity-compatible shared rotations | NOT_ESTABLISHED |
| M11 conditional quantitative k=3 gap | first-propagator saturation class and explicit angle–magnitude bound | NOT_ESTABLISHED |
| fixed-tree support compression | evaluation-preserving projector-invariant finite support and k=3 global strict gap | NOT_ESTABLISHED |
| finite source-resolved error calculus | exact finite DAG source polynomials, first-order source recombination, truncation, and signed coefficient bounds | NOT_ESTABLISHED |
| endpoint eta=1 strict k=3 gap | M10 non-attainment plus finite support compactness gives `C_3(1)<sqrt(2)` | NOT_ESTABLISHED |
| unconditional chain `W_3` envelope | contraction Gram-matrix cross-term bound and explicit gap below M9 | NOT_ESTABLISHED |
| exact independent-law chain constant | M13 envelope attained by a dimension-two rank-one witness | NOT_ESTABLISHED |
| exact independent-law branching constant | nuclear/operator-norm duality plus polar-factor witness attains `W_3` | NOT_ESTABLISHED |
| arbitrary-node-law binary k=3 corollary | independent-law convention with freely selectable laws at each node; chain and branching constants `W_3` | NOT_ESTABLISHED |
| M18 finite-binary asymptotic sharpness | every fixed ordered full-binary topology has `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` | NOT_ESTABLISHED |
| M19 finite-arity asymptotic sharpness | every fixed ordered rooted topology with arities at least two has `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` | NOT_ESTABLISHED |
| M20 k=3 all-arity fixed-eta exact constant | every finite ordered k=3 arity profile has `C_{T,ind}^P(eta)=W_3(eta)` by effective chain/branching reduction and gate embedding | NOT_ESTABLISHED |
| M21 tagged same-law k=3 exact constant | one repeated bilinear law with finite orthogonal projected leaf tags simulates M14/M15 by direct-sum blocks | NOT_ESTABLISHED |
| M22 rank-one same-law high-eta exact regime | common-leaf repeated rotation attains `W_3(eta)` for the chain when `eta>=sqrt(2/3)` | NOT_ESTABLISHED |
| M23 rank-one same-law chain operator reduction | strict rank-one/common-leaf repeated law reduces exactly to a contraction problem for `|<e0,A^3e0>-<e0,Ae0>^3|` under `||Q A e0||<=eta` | NOT_ESTABLISHED |

The audit must compare hypotheses, object class, constants, tree/DAG scope,
source attribution, signed cancellation, truncation, and validation status.
It must not ask whether “SEION” is novel as a name.

## Targeted primary-source search addendum — 2026-08-08

This addendum records a bounded search against primary or publisher sources.
It does not establish novelty and does not replace independent expert review.

| Source | Direct overlap | Difference from V5 | Candidate status |
|---|---|---|---|
| Hackbusch, *Truncation of tensors in the hierarchical format*, SeMA Journal 78 (2021), DOI `10.1007/s40324-018-00184-5` | finite-dimensional hierarchical/tree tensor formats, vertex-indexed orthogonal projections, explicit truncation error control | studies tensor representation/truncation; V5 studies recursively applied multilinear laws, local normal closure defects, projected-root cancellation, and extremal constants | `KNOWN_ADJACENT_RESULT`; human review pending |
| Chen, Surana, Bloch, Rajapakse, *Data-Driven Model Reduction for Multilinear Control Systems via Tensor Trains*, arXiv:1912.03569 | multilinear systems, tensor-train reduction, projection/compression in applications | no V5 projected-tree error decomposition or k=2/k=3 extremal theorem | `KNOWN_ADJACENT_RESULT`; human review pending |
| Weiss, Rubio González, Liblit, *Database-Backed Program Analysis for Scalable Error Propagation*, ICSE 2015 | graph-based error propagation and source/dataflow analysis | software-analysis dataflow, not finite multilinear Hilbert-space propagation or signed source polynomials | `METHODOLOGICALLY_ADJACENT`; human review pending |

The search found substantial adjacent prior art for tree-indexed projection,
tensor truncation, multilinear model reduction, and graph error propagation.
It did not verify an exact match for the M8/M9/M10 theorem statements or the
source-polynomial projected-DAG calculus. That absence is not evidence of
novelty; all V5 novelty fields therefore remain `NOVELTY_NOT_ESTABLISHED`.

## 2026-08-09 systematic comparator expansion

The rows above were rechecked against a broader category pass covering
hierarchical tensor approximation, tensor-manifold step truncation, TTN
rank-adaptive integration, bilinear MOR, semiring provenance, and adaptive-rank
HT solvers. The disposition remains `NOT_ESTABLISHED` for every row. The
following source-to-row mapping records why the closest literature is adjacent
rather than an exact theorem match:

| Source | Rows most directly compared | What overlaps | What remains unmatched |
|---|---|---|---|
| Nouy, arXiv:1705.00880 | universal bound, M18--M20 | tree-indexed subspaces, interpolation/projection, tree-format error | recursive typed multilinear laws, homogeneous closure defect, root cancellation, fixed-eta extremizers |
| Rodgers--Dektor--Venturi, doi:10.1007/s10915-022-01868-x | universal bound, M18--M20 | nonlinear tensor evolution followed by local truncation and convergence/error criteria | finite-tree law recursion and exact `k-1`/`W_3` constants |
| Ceruti--Lubich--Sulz, arXiv:2201.10291 | M18--M20, M21 | leaves-to-root TTN recursion, Galerkin update, rank truncation | V5 residual algebra, same-law direct-sum exactness, equality witnesses |
| Redmann--Pontes Duff, arXiv:2102.07534 | universal bound, M16, M20 | projection-based reduction for bilinear systems and error bounds | topology-indexed multilinear tree constants and local normal residual |
| Grädel--Tannen, arXiv:2412.07986 | DAG source polynomial, signed cancellation | polynomial source provenance and semiring composition | vector/operator coefficients, norm enclosures, closure defects, signed Hilbert-space cancellation theorem |
| Sands--Guthrey--Roberts, arXiv:2606.21750 | M18--M20 | adaptive-rank HT projection for nonlinear systems | exact finite-arity effective-law reduction and fixed-eta sharpness |

This matrix is an audit aid, not a novelty certificate. An expert may still
discover an exact match in a cited paper's references or in literature outside
the bounded search corpus.

Primary URLs:

- https://link.springer.com/article/10.1007/s40324-018-00184-5
- https://arxiv.org/abs/1912.03569
- https://pages.cs.wisc.edu/~liblit/icse-2015/
