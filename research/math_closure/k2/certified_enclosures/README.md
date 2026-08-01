# M2 certified enclosures

The certified lower/upper enclosures for the general class $A$ (any
law/topology/dimension/rank at $k=2$) are the 513 $k=2$ rows of
`artifacts/index/constants_atlas_v3.csv` (7,065-row atlas, re-verified in
`docs/research/track_t_v5_terminal_status_k2_k3.md`), extracted verbatim
into `../computational_registry.parquet` (513 rows, no recomputation —
same `certified_lower_bound`/`certified_upper_bound`/`relative_gap`
columns, same `mpmath` interval-arithmetic provenance recorded in
`lower_method`).

This directory does not add new certified enclosures for the general
class this pass — the new result (`../classification_theorem.tex`) is an
**exact closed form**, not a numerical enclosure, for the specific
homogeneous chain / gated-rotation sub-class, which supersedes the
atlas's 6 exact (`relative_gap=0`) rows with a proof of *why* they are
exact and *exactly how* the ratio behaves at every other $\eta$, not just
the discretely-sampled $\eta$ values the atlas happens to contain
($\eta \in \{0.001, 0.01, 0.1, 0.5, 1.0\}$).
