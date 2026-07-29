# Structure-preserving reduction — foundations v2

This directory is a finite-dimensional research draft. It is intentionally
marked not for submission because the exact reduction and spectral-snapping
results are standard, the approximate tree recurrence is auxiliary, and
verified author metadata is still missing.

The local TeX installation does not provide `siamart.cls`; the draft therefore
uses `amsart` while preserving SIAM-compatible notation and bibliography
discipline. A submission pass would switch to the journal's current class.

## Rebuild

From the repository root:

```powershell
python scripts/run_research_v2.py
python scripts/build_research_v2_tables.py
python scripts/build_research_v2_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=papers/foundations_v2/build papers/foundations_v2/main.tex
latexmk -pdf -jobname=draft_not_for_submission -interaction=nonstopmode -halt-on-error -file-line-error -outdir=papers/foundations_v2/build papers/foundations_v2/main.tex
```

The source, proof ledger, theorem registry, counterexamples, figures, tables,
and registered artifacts are separate from the preserved legacy `paper/`
release path.
