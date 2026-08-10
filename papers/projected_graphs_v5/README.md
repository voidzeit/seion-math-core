# Projected multilinear graphs v5 paper package

This directory contains the v5 paper sources. The papers are deliberately
split into a mathematical core, a source-resolved DAG extension, and a
software/reproducibility companion. They reuse registered v4 figures and
bibliography but make the v5 theorem statuses explicit.

Build the final PDFs with `scripts/build_projected_graphs_v5_papers.ps1`.
Then run `scripts/verify_projected_graphs_v5_papers.ps1` to validate page counts,
SHA-256 hashes, Poppler rendering, and the visual-review audit. The final
deliverables and compact manifests are written to `output/pdf/`.

The package is a reproducible research artifact, not a novelty or publication
approval. The explicitly declared same-map k=2 class and the contractive
gated-planar repeated-law subclass are closed at the universal value; variable
gate/arbitrary-leaf/non-planar gated variants and fixed-eta same-law/gated
sharpness remain explicitly open. Every fixed finite ordered rooted topology
with arities at least two is now asymptotically sharp with coefficient `k-1`
as `eta` tends to zero, while M20 closes the independent-law fixed-eta k=3
constant at `W_3(eta)` for every finite arity profile and M21 closes the
tagged same-law binary k=3 class at the same value. M22 additionally closes
the strict rank-one/common-leaf same-law chain in the high-eta regime
`sqrt(2/3) <= eta <= 1`; M23 gives an exact unary-operator reduction for the
remaining strict chain class, while its low-eta value, branching, and broader
gated/shared-law variants remain open. Gate 13.5,
Gate 14, KGR, and historical artifacts are outside this package.
