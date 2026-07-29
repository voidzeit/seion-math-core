# Mathematical research paper

This directory contains the theorem-focused manuscript requested by the
research/software split:

`Structure-Preserving Reduction of Finite-Dimensional N-Ary Laws: Exact
Functoriality, Associator Stability, and Projection Error Bounds`.

The paper states the exact invariant-reduction theorem, the explicit
tree-level approximate-closure bound, the $2M\varepsilon$ associator
specialization, spectral-snapping stability, and the no-gap counterexample.
It keeps numerical claims conservative and points to the machine-readable
blockers in `.ai/KNOWN_BLOCKERS.md`.

Build from this directory with `latexmk -pdf -interaction=nonstopmode
-halt-on-error -file-line-error -outdir=build main.tex`, or use
`scripts/build_companions.ps1` from the repository root.
