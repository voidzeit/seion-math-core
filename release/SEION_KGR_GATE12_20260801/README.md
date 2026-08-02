# SEION-KGR v26 MAX — Gate 12 Closeout Package

Campaign ID: `gate12-closeout-2026-08-01`
Canonical commit: `6af3c35271ae2ffab41ecba2aad098d1988fdc0c`
Branch: `campaign/gate12-closeout`

## What this is

12 PDFs documenting the `gate12-closeout` campaign: engineering closure (CI, a real learned
path selector, a controlled E8 residual branch with matched controls, a state-to-score-to-ranking
certification chain, a reproducibility audit that caught and fixed real bugs), a bounded and
explicitly non-confirmatory screening pass on real FB15K-237/WN18RR data, two real negative-control
integration runs, and an honest accounting of what was not done. **Start with
`pdf/00_package_index.pdf`, then `pdf/01_executive_summary.pdf`. Read `pdf/09_negative_results.pdf`
before treating any number elsewhere in this package as more than screening-tier evidence.**

## Contents

```
sources/     LaTeX sources for all 12 PDFs (+ shared preamble.tex)
pdf/         Compiled PDFs (00-11), zero LaTeX "Overfull hbox" warnings
manifests/   artifact_manifest.json, PDF_MANIFEST.json (SHA-256 + page count per PDF)
```

`figures/` and `tables/` are empty — every table in this package is typeset directly from the
campaign's real numeric results (`campaigns/gate12/tier0_results.json`,
`negative_controls_results.json`) rather than generated as separate image files; no plots were
produced this campaign (a real, stated gap — see `09_negative_results.pdf`).

## Reproduction

```bash
git clone https://github.com/voidzeit/seion-math-core
git checkout campaign/gate12-closeout
python -m pip install -e '.[test,research]'
python -m pytest tests/kgr -q                      # 130 tests
python seion_kgr_reference_fp64.py --self_test
python seion_kgr_v26_train.py --self_test
```

Tier 0 screening commands and the full hyperparameter grid: `pdf/11_supplement.pdf` §6, or
`campaigns/gate12/tier0_config.json` directly.

To recompile this PDF package from source:

```bash
cd release/SEION_KGR_GATE12_20260801/sources
for f in *.tex; do [ "$f" = preamble.tex ] && continue; pdflatex -interaction=nonstopmode "$f"; pdflatex -interaction=nonstopmode "$f"; done
```

## What is NOT in this package

Dataset files, individual run checkpoints, and the 59MB `E8_Exact_v18_2/f_E8.npy` kernel are not
included (large/third-party/binary, kept local-only, same convention as the rest of this
repository's `.gitignore`). Their SHA-256 hashes and provenance are recorded in
`manifests/artifact_manifest.json` and the campaign's own `campaigns/gate12/*.json` files.

## Honesty statement

This package documents engineering closure plus a **screening-tier** (2-seed, 2-of-13-ablation-
point, confounded-by-training-data-scale) benchmark pass. It is explicitly **not** a Gate 12
confirmatory statistical campaign. No SOTA claim is made. See `pdf/09_negative_results.pdf` for the
complete, unhidden list of what did not work, what remains open, and what must not be claimed from
this package's evidence.
