# SEION Math Core: reproducibility companion v2

This companion contains the research-v2 implementation, artifact contracts,
run identity, parity checks, and build procedure. It is separate from the
mathematical foundations draft and from the preserved legacy 0.1 paper.

## Rebuild

From the repository root, run:

    python scripts/run_research_v2.py
    python scripts/build_research_v2_tables.py
    python scripts/build_research_v2_figures.py
    latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=papers/software_v2/build papers/software_v2/main.tex

The foundations draft uses the same first three commands and is built with
the corresponding papers/foundations_v2/build output directory. No command
rewrites artifacts/runs or the legacy index.

## Evidence

The runner generated 180 complete rows and five seeds per principal family.
The v2 manifest records stronger scientific identity fields than the legacy
deduplicator: source commit, implementation version, resolved configuration
hash, mathematical-object hash, input-artifact hash, seed, precision,
backend, and device.

The strict research gate remains fail-closed because no theorem-level novelty
has been established and author contact metadata is missing. This is a
deliberate scientific status, not a build failure.
