# Provenance

Where every part of this package came from, and what was and was not modified in producing
it.

## 1. Repository

| Item | Value |
| --- | --- |
| Repository | `voidzeit/seion-math-core` |
| Local path at assembly | `C:/Documents/metamaths/seion-math-core` |
| Default branch | `main`, at `a39de8047d3d33314adb485f762c2b74c7af73fb` |
| Assembly date | 2026-07-31 |

## 2. The deliverables come from two branches, which were not merged

| # | Document | Source directory | Branch | Commit |
| --- | --- | --- | --- | --- |
| 01 | recursive projection of multilinear trees | `papers/tree_stability_v4/` | `research/projected-tree-theory-v5` | `2e419ef4e1c028cfb85348feb515746e6c538ea8` |
| 02 | kernel-defined multilinear operators | `papers/kernel_integrated_laws_v5/` | `research/projected-tree-theory-v5` | `2e419ef4…` |
| 03 | numerical study | `papers/a_to_n_certification_v18/` | `research/spectral-a-to-n-v18` | `8e09941e56d6a514a44928ec1a6b5395fb8ceecb` |
| 04 | software and reproducibility | `papers/software_v4/` and `papers/software_reproducibility_v5/` | both | both |
| 05 | supplementary results | `papers/supplementary_visual_atlas_v18/` | `research/spectral-a-to-n-v18` | `8e09941e…` |

The two branches are **siblings**, not ancestor and descendant: their merge base is
`427ad529e7793b604cdb23bda089534420a6aee6`, and each is ahead of `main` by 8 and 16 commits
respectively with neither behind.

They are content-disjoint except for one file, `papers/tree_stability_v4/main.tex`, which
exists on both. The `research/projected-tree-theory-v5` version differs by `+93 / −2` lines
and strictly supersedes: the added material is two follow-up subsections and the
corresponding additions to the open-problem list. That version was used.

**No merge was performed, and none is required.** Sources were extracted by read-only copy
from the working tree at `2e419ef` and from a detached `git worktree` of `8e09941`.

### Windows path-length note

A detached worktree created under a deeply nested temporary directory checked out all 2 260
files and then failed with `fatal: Could not reset index file to revision 'HEAD'`, leaving
nothing behind. The same command against a short path succeeded. Paths such as
`spectral/certification_v18/artifacts/pilot_sweep/pilot_visual_diagnostics/02_block_h_associator_ratio_distribution.svg`
exceed the 260-character limit under a long prefix. Any working directory for this package
must use a short root path.

## 3. Material that was deliberately not used

At assembly time the working tree contained untracked copies of the case study II papers
and of the `spectral/` source directory. **None was used**, for the following reasons.

| Path | Reason |
| --- | --- |
| `papers/a_to_n_certification_v18/` (untracked) | Contained only build residue — `.aux`, `.log`, `.out` and a PDF — with **no `main.tex`**. The PDF's SHA-256 differs from the committed build at `8e09941`, so it was produced from a source not present anywhere in the working tree, at an unknown commit. |
| `papers/software_reproducibility_v5/` (untracked) | Same. |
| `papers/supplementary_visual_atlas_v18/` (untracked) | Same, and additionally with no `figures/` directory. |
| `spectral/` (untracked) | An incomplete copy: 536 files present, **109 files and 20 152 lines missing** relative to `8e09941`, including the entire test suite. Running the case study II tests against it produced "no tests ran"; running them in a clean worktree of `8e09941` produced 85 passed. |

Earlier drafts in the repository that are **not** part of this package:
`papers/tree_stability_v3/`, `papers/foundations/`, `papers/foundations_v2/`,
`papers/software/`, `papers/software_v2/`, `papers/software_v3/`, `papers/supplement_v4/`,
and the two empty stubs `papers/projector_reduction/` and `papers/truncated_cohomology/`.

## 4. Numerical evidence for document 01

The tables and figures of document 01 were produced by the experiment pipeline at source
commit **`b718f4e51785`** — "feat(research): add nodewise tree constants v3 system", an
ancestor of `main` — not at `2e419ef`, which carries the manuscript text. Document 01 states
this in its reproducibility appendix, and the manifest table reports the commit.

The two commits are not interchangeable, and the discrepancy is real. It is recorded rather
than concealed because the alternative — rerunning the pipeline at `2e419ef` — would change
reported numbers and is a research action, not an editorial one.

### The one derived quantity that was recomputed

The classification of enclosure outcomes was defective at `b718f4e`, and the defect reached
the manuscript. The classifier assigned the label reserved for an exactly determined
constant **only** when the proved upper bound was itself zero — the vacuous case — while
configurations whose bounds genuinely coincided at a positive value received a weaker
label, and configurations for which no positive lower bound had been obtained were
described as having a certified lower bound.

The classification is a pure function of the certified lower and upper bounds, both of which
are recorded in
`artifacts/index/optimality_gaps_v3.csv` (9 945 rows) and
`artifacts/research_v3/block_A_exact_atlas.csv` (4 185 rows). It was therefore

* corrected in the source
  (`src/seion_core/research_v3/interval_certification.py`, function `classify_optimality`),
* **re-derived** from the recorded bounds by
  `scripts/regenerate_optimality_classification.py`,
* written to `sources/recursive_projection_of_multilinear_trees/data/` **alongside** the
  original, never over it.

**No experiment was re-run, and no file under `artifacts/` was modified.**

The correspondence between the old and the new labels is a bijection on the agreement
classes, so the two derivations are directly comparable:

| Old label | Rows | New label | Rows |
| --- | ---: | --- | ---: |
| `EXACT_OPTIMAL_CONSTANT` | 30 | `EXACTLY_ZERO_BY_THEOREM` | 30 |
| `NEAR_OPTIMAL_WITH_CERTIFIED_GAP` | 309 | `EXACTLY_DETERMINED_POSITIVE` | 309 |
| `CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND` | 9 606 | `POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP` | 7 812 |
| | | `NO_POSITIVE_LOWER_BOUND_OBTAINED` | 1 794 |

The agreement test is unchanged — a relative tolerance of `10⁻¹⁰` against the upper bound,
exactly as before — so the only substantive changes are the corrected naming and the split
of the third class according to whether a positive lower bound exists.

## 5. Data shipped with the package

| File | Origin | Used by |
| --- | --- | --- |
| `sources/recursive_projection_of_multilinear_trees/data/optimality_gaps_reclassified.csv` | re-derived from `artifacts/index/optimality_gaps_v3.csv` | document 01, Table "outcome of comparing…" |
| `.../data/exact_atlas_reclassified.csv` | re-derived from `artifacts/research_v3/block_A_exact_atlas.csv` | document 01 |
| `.../data/optimality_classification_summary.json` | the same re-derivation | document 01 |
| `sources/supplementary_results/data/block_b_ablation_matrix.json` | verbatim copy from `8e09941` | figure 2 |
| `.../data/block_e_interscale_experiment.json` | verbatim copy from `8e09941` | figure 3 |
| `.../data/pilot_results.parquet` | verbatim copy from `8e09941` | figure 8 |
| `.../data/s1_results.parquet` | verbatim copy from `8e09941` | figures 4, 5, 7, 8, 9 |
| `.../data/final_gate_evaluation.json` | verbatim copy from `8e09941` | reference only |

Checksums for all of these are in `checksums.sha256` and, for the figure inputs, in
`sources/supplementary_results/figure_provenance.json`.

## 6. Source code changed in producing this package

All changes are in the repository working tree, uncommitted, and all are editorial or
corrective rather than scientific.

| File | Change |
| --- | --- |
| `src/seion_core/research_v3/interval_certification.py` | added `classify_optimality` with four mutually exclusive outcomes; `certified_gap` now delegates to it. The previous inline logic named the vacuous case "exact optimal" and the genuinely determined case "near optimal". |
| `scripts/tree_constants_v3_pipeline.py` | `_exact_status` delegates to `classify_optimality`; the block summary reports the three informative counts rather than one. |
| `scripts/build_tree_constants_v3_tables.py` | the optimality table reports the four disjoint counts; the misleading macros `\VThreeExactCells` and `\VThreeMaxRelativeGap` are replaced by counts per class, a total, and a percentage. |
| `scripts/tree_constants_v3_audit.py` | consumes the new classification; the acceptance check on "near-optimal" claims is restated as a check that exactly determined constants have coincident bounds. |
| `scripts/regenerate_optimality_classification.py` | **new.** Re-derives the classification and the dependent table and macros from recorded bounds. Idempotent. |
| `scripts/sanitize_generated_tables.py` | **new.** Rewrites implementation vocabulary in the generated LaTeX tables. Headings and labels only; no numeric value is touched; fails if a forbidden token survives. |

The 73-test suite passes before and after these changes.

## 7. Version-control actions taken

| Action | Performed? |
| --- | --- |
| Local file edits and new files | yes, as listed above and under `academic_submission_package/` and `academic_delivery_work/` |
| `git worktree add --detach` of `8e09941` at a short path, read-only | yes |
| Commit | **no** |
| Branch created | **no** |
| Merge, rebase, cherry-pick | **no** |
| Push, remote branch creation, force-push, branch deletion | **no** |
| Pull request opened or modified | **no** |
| Historical artifact under `artifacts/` modified | **no** |
| Network operations | two read-only: `gh pr list`, and reference verification against publisher records |

## 8. Environment

| | |
| --- | --- |
| Operating system | Windows 11 Pro, 10.0.26200 |
| Python | 3.12.10 (MSC v.1943, 64-bit) |
| TeX | MiKTeX, `latexmk` 4.88 |
| PDF tools | poppler `pdftotext`, `pdffonts` |
| Numerical libraries | versions recorded per figure in `sources/supplementary_results/figure_provenance.json` |

The hardware on which the original experiments ran is described in document 04; it is not
the same machine as the one used for this assembly, and no timing measurement was repeated
here.
