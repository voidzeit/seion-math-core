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
approval. Global repeated-law and k=3 sharpness remain explicitly open, and
Gate 13.5, Gate 14, KGR, and historical artifacts are outside this package.
