# 00 — Source audit

**Audit date:** 2026-07-31
**Auditor:** automated editorial/mathematical audit pass, under the delivery instruction of 2026-07-31.
**Scope:** establish the verified source state of the five intended manuscripts *before* any rewriting.
**Status:** audit complete. **Rewriting has not started.** Two conditions in §26 of the governing
instruction are met and are reported in `REPORT_TO_AUTHOR` at the end of this file.

Nothing in the governing instruction was treated as a statement of repository fact. Every claim below
was obtained by direct inspection of the repository.

---

## 1. Repository identity

| Item | Value |
| --- | --- |
| Working directory | `C:/Documents/metamaths/seion-math-core` |
| Remote `origin` | `https://github.com/voidzeit/seion-math-core.git` (fetch and push) |
| Checked-out branch at audit start | `research/projected-tree-theory-v5` |
| Default/base branch | `main` (`origin/main` = `a39de80`) |
| Working tree clean? | **No** — five untracked paths (§4) |

### Local branches

`infra/agent-graph-loop-v1`, `master`, `program/seion-canonical-repository-v4`,
`release/seion-integrated-v5`, `research/nodewise-tree-constants-v3`,
`research/projected-tree-theory-v5` (checked out), `research/spectral-a-to-n-v18`,
`research/structure-preserving-reduction-v2`.

Remote-tracking branches exist for `main`, `infra/agent-graph-loop-v1`,
`program/seion-canonical-repository-v4`, `research/projected-tree-theory-v5`,
`research/spectral-a-to-n-v18`. `master`, `release/seion-integrated-v5`,
`research/nodewise-tree-constants-v3`, `research/structure-preserving-reduction-v2` are local-only or
alias existing remote commits.

### Pull requests (`gh pr list --repo voidzeit/seion-math-core --state all`)

| # | Title | Head → base | State | Merged |
| --- | --- | --- | --- | --- |
| 4 | Track T: terminal status synthesis for k=2/k=3 (SEION V5 Phase 6/7) | `research/projected-tree-theory-v5` → `main` | OPEN | no |
| 3 | Agent-graph-loop: executable development-lifecycle executor | `infra/agent-graph-loop-v1` → `main` | OPEN | no |
| 2 | Spectral A-N v18: fail-closed certification suite | `research/spectral-a-to-n-v18` → `main` | OPEN | no |
| 1 | Implement SEION canonical repository v4 | `program/seion-canonical-repository-v4` → `main` | OPEN | no |

**No pull request has been merged.** `main` is at `a39de80` and is 0 commits ahead of every research
branch; each research branch is strictly ahead of `main`.

---

## 2. Branch topology relevant to the five manuscripts

```
a39de80  origin/main
   |
   ... (release/seion-integrated-v5 line)
   |
427ad52  release/seion-integrated-v5   <-- common ancestor of the two research branches
   |\
   | \
   |  8e09941  research/spectral-a-to-n-v18   (16 commits ahead of main)
   |
   2e419ef  research/projected-tree-theory-v5 (8 commits ahead of main)
```

Verified:

* `git merge-base research/projected-tree-theory-v5 research/spectral-a-to-n-v18` = `427ad52`.
* `git rev-list --left-right --count origin/main...research/projected-tree-theory-v5` = `0 8`.
* `git rev-list --left-right --count origin/main...research/spectral-a-to-n-v18` = `0 16`.

The two research branches are **siblings, not ancestor/descendant**. Neither contains the other's work.

---

## 3. Manuscript inventory: exact source commit per document

The five intended deliverables are split across **two branches**. This is the principal structural
finding of the audit.

| # | Intended deliverable | Source directory | Source branch | Source commit | `main.tex` blob |
| --- | --- | --- | --- | --- | --- |
| 01 | Main mathematical article | `papers/tree_stability_v4/` | `research/projected-tree-theory-v5` | `2e419ef4e1c028cfb85348feb515746e6c538ea8` | `f35f07d5…` |
| 02 | General/operator-theoretic article | `papers/kernel_integrated_laws_v5/` | `research/projected-tree-theory-v5` | `2e419ef4…` | `a64b7cfa…` |
| 03 | Numerical study | `papers/a_to_n_certification_v18/` | `research/spectral-a-to-n-v18` | `8e09941e56d6a514a44928ec1a6b5395fb8ceecb` | `95f19249…` |
| 04 | Software/reproducibility article | `papers/software_reproducibility_v5/` | `research/spectral-a-to-n-v18` | `8e09941e…` | `aded2f12…` |
| 05 | Supplementary figures | `papers/supplementary_visual_atlas_v18/` | `research/spectral-a-to-n-v18` | `8e09941e…` | `fd070ca4…` |

Commit metadata:

| Commit | Date (ISO) | Author | Subject |
| --- | --- | --- | --- |
| `2e419ef` | 2026-07-30 23:45:07 −0400 | Eliuth Chavero Jasso | Expand tree_stability_v4 with this session's signed-forest and k=2/k=3 findings |
| `8e09941` | 2026-07-30 23:41:23 −0400 | Eliuth Chavero Jasso | Expand supplementary visual atlas with 2 new figures from the 416-cell sweep |

### 3.1 Supporting source files per manuscript

**01 — `papers/tree_stability_v4/`** (`research/projected-tree-theory-v5`)
`main.tex` (36 517 B), `proofs/full_proofs.tex`, `generated_results.tex` (16 generated macros),
`references.bib` (15 entries), `figures/captions.tex`, 18 figures (`.pdf` + `.svg` each) plus 8
`atlas_fig04_*` topology tiles, 17 generated `tables/*.tex`, `README.md`.
Figure/table generators: `scripts/build_tree_constants_v3_tables.py` (21 391 B),
`scripts/build_tree_constants_v3_figures.ps1`, `scripts/tree_constants_v3_pipeline.py` (68 535 B).

**02 — `papers/kernel_integrated_laws_v5/`** (`research/projected-tree-theory-v5`)
`main.tex` (29 640 B) **only**. No `references.bib`. No figures. No tables. No generated results.
No `\bibliography` command anywhere in the file.

**03 — `papers/a_to_n_certification_v18/`** (`research/spectral-a-to-n-v18`)
`main.tex` (≈374 lines) **only**, plus a committed `main.pdf`. No `references.bib`, no
`\bibliography`, no figures of its own. Underlying evidence lives in
`spectral/certification_v18/` (14 `blocks/block_*.py` modules, 14 `BLOCK_*_FINDINGS.md`,
`artifacts/*.json`, `artifacts/pilot_sweep/pilot_results.parquet`,
`artifacts/phase4_s1_broad_screening/s1_results.parquet`, `gates.py`, `GATE_TAXONOMY.md`).

**04 — `papers/software_reproducibility_v5/`** (`research/spectral-a-to-n-v18`)
`main.tex` (213 lines) **only**, plus a committed `main.pdf`. No bibliography, no figures.

**05 — `papers/supplementary_visual_atlas_v18/`** (`research/spectral-a-to-n-v18`)
`main.tex` (159 lines), `generate_figures.py` (212 lines), 9 figures as `.png` **and** `.svg`
pairs, committed `main.pdf`. **No vector `.pdf` figure files** — the manuscript includes PNG only
(`\graphicspath{{figures/}}` + `\includegraphics{01_an_dashboard}` resolves to `.png`).

---

## 4. Untracked paths in the working tree, and their status

`git status --short` reports five untracked paths. Each was checked against the branch that owns the
corresponding tracked content.

| Untracked path | Verdict |
| --- | --- |
| `docs/research/NEXT_SESSION_DELIVERY_PACKAGE_PROMPT.md` | Working note. Not a manuscript source. Excluded. |
| `docs/research/truth_audit_2026_07_29/` | 11 files. Prior-session audit notes. Useful as *input* to the statement–evidence table; **not** a manuscript source. |
| `papers/a_to_n_certification_v18/` | **Stale build residue only** — `main.aux`, `main.log`, `main.out`, `a_to_n_certification_v18.pdf`. **No `main.tex`.** |
| `papers/software_reproducibility_v5/` | **Stale build residue only** — `.aux`, `.log`, `.out`, `software_reproducibility_v5.pdf`. **No `main.tex`.** |
| `papers/supplementary_visual_atlas_v18/` | **Stale build residue only** — `.aux`, `.log`, `.out`, `supplementary_visual_atlas_v18.pdf`. **No `main.tex`, no `figures/`.** |
| `spectral/` | **Incomplete copy** — 536 files present; `git diff research/spectral-a-to-n-v18 -- spectral/` reports **109 files / 20 152 lines missing**, including the entire `spectral/certification_v18/tests/` directory and all of `spectral/legacy/v17/`. |

### 4.1 The untracked PDFs are not reproducible from anything in this working tree

`papers/a_to_n_certification_v18/a_to_n_certification_v18.pdf`
SHA-256 `A2693279 8C2FE3B4 6A862F3C E17BC393 5ECE2974 C6907120 9D027C20 FCD5C260`

`research/spectral-a-to-n-v18:papers/a_to_n_certification_v18/main.pdf`
SHA-256 `8B112BA8 39CD04B7 9BFEEA42 92BE5FCC 600CBFF0 7E4AF416 341F846F 7D543D86`

They **differ**. The working-tree PDF was produced by a build whose source is not present in this
working tree, from a `main.tex` that is not in this working tree, at an unknown commit.

**Consequence for the delivery package: the three untracked PDFs and the untracked `spectral/`
directory must not be used as sources.** They carry no verifiable provenance. The authoritative
sources are the tracked files at `8e09941`, extracted non-destructively (§9).

Confirming test: `python -m pytest spectral/certification_v18/tests` in the main working tree →
**"no tests ran" (exit 5)** — the tests are among the 109 missing files. The same command in a clean
detached worktree of `8e09941` → **85 passed in 51.09 s**, exactly matching the count asserted in
manuscript 04.

---

## 5. Relation between manuscript versions

### 5.1 `papers/tree_stability_v4/main.tex` exists on both branches, and they differ

| Branch | Blob | Size |
| --- | --- | --- |
| `research/projected-tree-theory-v5` @ `2e419ef` | `f35f07d5…` | 36 517 B |
| `research/spectral-a-to-n-v18` @ `8e09941` | `d8fd525a…` | ≈33 kB |

`git diff --numstat` between them: **+93 / −2 lines**, all inside `main.tex`. The added material is
exactly the two follow-up subsections `\label{sec:signed-followup}` and `\label{sec:k23-followup}`
plus the corresponding additions to the open-problem list.

**Verdict: the `research/projected-tree-theory-v5` version strictly supersedes the
`research/spectral-a-to-n-v18` version.** No content is lost by preferring `2e419ef`.

### 5.2 The two branches are otherwise content-disjoint

`git diff --name-status research/spectral-a-to-n-v18 research/projected-tree-theory-v5` shows, apart
from the single `M papers/tree_stability_v4/main.tex` above, only pure `A` (added on
projected-tree) and pure `D` (present only on spectral) entries. There is **no file that both
branches modified in conflicting ways**.

Added only on `research/projected-tree-theory-v5`:
`papers/kernel_integrated_laws_v5/main.tex`, `docs/research/novelty_matrix_v5.md`,
`docs/research/signed_forest_terminal_status_v5.md`, `docs/research/track_t_v5_terminal_status_k2_k3.md`,
`scripts/signed_forest_adversarial_search_v5.py`,
`artifacts/research_v3/signed_forest_adversarial_search_v5.json`.

Present only on `research/spectral-a-to-n-v18`:
all of `spectral/`, the three v18 paper directories, `.github/workflows/spectral-v18.yml`,
`.ai/SPECTRAL_TRACK_ROADMAP.md`, `docs/research/spectral_a_to_n_v18/*`.

`claims/scope_registry_v4.yaml` is modified on both, but the two edits touch different scope entries.

### 5.3 Superseded manuscript directories (must not be delivered)

The repository retains earlier drafts that are **not** part of the five deliverables:

| Directory | Relation |
| --- | --- |
| `papers/tree_stability_v3/` | Direct predecessor of `tree_stability_v4`. Superseded. |
| `papers/foundations/`, `papers/foundations_v2/` | Earlier formulation attempts. `foundations_v2/RESEARCH_BLOCKED.md` records why it was abandoned; its build directory contains `draft_not_for_submission.pdf`. Superseded. |
| `papers/software/`, `software_v2/`, `software_v3/`, `software_v4/` | Four earlier software-companion drafts, distinct from `software_reproducibility_v5`. Superseded. |
| `papers/supplement_v4/` | Earlier supplement (3 015 B `main.tex`), distinct from `supplementary_visual_atlas_v18`. Superseded. |
| `papers/projector_reduction/`, `papers/truncated_cohomology/` | `README.md` stubs only (139 B and 142 B). Empty placeholders. |

**Ambiguity requiring the author's decision:** `papers/software_v4/` (14 305 B, with
`references.bib`) and `papers/software_reproducibility_v5/` (213 lines, no bibliography) are *two
different software papers about two different tracks*, not two versions of one paper. `software_v4`
documents the `CANONICAL_FINITE_CORE` pipeline behind manuscript 01; `software_reproducibility_v5`
documents the `spectral/certification_v18` suite behind manuscript 03. The delivery instruction asks
for **one** software article. See `REPORT_TO_AUTHOR` item R-5.

---

## 6. Current compilation state

Toolchain present and verified: MiKTeX (`pdflatex`, `xelatex`, `lualatex`, `latexmk`, `bibtex`,
`biber`, `pdftotext`, `pdffonts`), Python 3.12.10. Absent: `uv`, `gs`, `qpdf`.

| # | PDF present? | Path | Built | Bytes |
| --- | --- | --- | --- | --- |
| 01 | yes | `papers/tree_stability_v4/build/main.pdf` | 2026-07-30 23:43 | 816 754 |
| 02 | yes | `papers/kernel_integrated_laws_v5/build/main.pdf` | 2026-07-30 20:06 | 398 492 |
| 03 | committed | `research/spectral-a-to-n-v18:papers/a_to_n_certification_v18/main.pdf` | — | 282 233 |
| 04 | committed | `research/spectral-a-to-n-v18:papers/software_reproducibility_v5/main.pdf` | — | 228 391 |
| 05 | committed | `research/spectral-a-to-n-v18:papers/supplementary_visual_atlas_v18/main.pdf` | — | 1 018 271 |

`build/` is git-ignored (`.gitignore:10`), so the PDFs for 01 and 02 exist only as local build
artifacts and are not under version control.

**Manuscript 02 was compiled at 20:06 but its `main.tex` was last modified at 23:42 on the same
day. The committed build of manuscript 02 is stale relative to its own source.**

### 6.1 PDF text extraction is corrupted in all five PDFs — cause identified and fix verified

The governing instruction reports corrupted extraction of "finite", "difference", "certificate".
This is confirmed, quantified, diagnosed, and a verified fix is available.

Measured with `pdftotext`, counting whole-word occurrences of the mutilated stems
`nite | erence(s) | cate(s) | rst | nding(s) | cient(s) | ected`:

| # | Corrupted stems | Intact `finite`/`difference`/`certificate`/`coefficient` |
| --- | --- | --- |
| 01 `tree_v4` | **79** | 4 |
| 02 `kernel_v5` | **28** | 0 |
| 03 `an_v18` | **14** | 0 |
| 04 `soft_v5` | **3** | 0 |
| 05 `atlas_v18` | **1** | 0 |

Codepoint dump of the first corrupted occurrence in manuscript 01 (`…ction on a ␜nite typed…`):

```
U+0063(c) U+0074(t) U+0069(i) U+006F(o) U+006E(n) U+0020( ) U+006F(o) U+006E(n) U+0020( )
U+0061(a) U+0020( ) U+001C(?) U+006E(n) U+0069(i) U+0074(t) U+0065(e)
```

The `fi` ligature extracts as **U+001C**, i.e. the raw T1 (Cork) encoding slot 0x1C. The other
ligature slots are 0x1B `ff`, 0x1D `fl`, 0x1E `ffi`, 0x1F `ffl`.

**Root cause.** `pdffonts` on manuscript 01 shows the text fonts are embedded as **Type 3 bitmap
fonts** (`F42`…`F98`, `type = Type 3`, `encoding = Custom`, `uni = no`). All five preambles already
contain `\input{glyphtounicode}` and `\pdfgentounicode=1`, but that mechanism writes a `ToUnicode`
CMap from *glyph names* and cannot apply to Type 3 bitmap fonts, which carry no usable glyph names.
The preambles request `\usepackage[T1]{fontenc}` without loading a T1 outline font, so MiKTeX falls
back to bitmapped EC fonts.

**Verified fix.** Two minimal documents were compiled with the identical sentence
`finite difference certificate coefficient first field defined finding affine`:

| Case | Preamble | `pdftotext` output |
| --- | --- | --- |
| A | current preamble (`glyphtounicode` + `\pdfgentounicode=1` + `[T1]{fontenc}`) | `nite dierence certicate coecient rst eld dened nding ane` — **corrupted** |
| B | same **plus `\usepackage{lmodern}`** loaded before `glyphtounicode` | `finite difference certificate coefficient first field defined finding affine` — **correct** |

The fix is one line per manuscript: `\usepackage{lmodern}` (Latin Modern Type 1 outlines) after
`\usepackage[T1]{fontenc}` and before `\input{glyphtounicode}`. This is recorded here rather than
applied, because §30 of the governing instruction defers all editing until after the audit report.

Incidental finding from the same `pdffonts` run: manuscript 01 also embeds
`STIXGeneral-Regular/Bold/Italic` as CID TrueType. These arrive from the matplotlib-produced figure
PDFs and are correctly Unicode-mapped; they are not part of the defect.

---

## 7. Current test state

| Command | Working directory | Result |
| --- | --- | --- |
| `python -m pytest -q` | `C:/Documents/metamaths/seion-math-core` (branch `research/projected-tree-theory-v5`, `2e419ef`, dirty) | **73 passed** in 9.54 s |
| `python -m pytest spectral/certification_v18/tests -q` | same working tree | **no tests ran (exit 5)** — test files absent from the untracked copy |
| `python -m pytest spectral/certification_v18/tests -q` | clean detached worktree of `8e09941` | **85 passed** in 51.09 s |

Environment: Python 3.12.10 (MSC v.1943, 64-bit), Windows-11-10.0.26200-SP0.

Passing tests establish implementation consistency only. They do not establish any mathematical
statement in any manuscript.

---

## 8. Discrepancies between source code, manuscript, and generated results

| ID | Discrepancy | Evidence |
| --- | --- | --- |
| D-1 | Deliverables split across two unmerged sibling branches. | §2, §3 |
| D-2 | Working-tree PDFs for manuscripts 03/04/05 have no source in this working tree and differ by SHA-256 from the committed builds. | §4.1 |
| D-3 | Working-tree `spectral/` is missing 109 files (20 152 lines) relative to `8e09941`, including the entire test suite. | §4 |
| D-4 | Manuscript 02's committed build (20:06) predates its own source (23:42). | §6 |
| D-5 | All five PDFs have broken ligature-to-Unicode mapping; the PDFs are not reliably searchable or copyable. | §6.1 |
| D-6 | Manuscripts 02, 03, 04, 05 have **no bibliography whatsoever** — no `references.bib`, no `\bibliography`, no `\cite`. Manuscript 03 nevertheless names "D'Amour et al." in prose (§Limitations) as supporting a substantive comparison. Manuscript 02 invokes Davis–Kahan-type reasoning, Hodge theory, Stiefel-manifold geometry, spectral dimension, Ψ⁰, D-modules and the Riemann–Hilbert correspondence with zero citations. | direct read of the four `main.tex` files |
| D-7 | Manuscript 02 restates manuscript 01's principal theorem (`thm:kk1` ≡ `thm:homogeneous`) **and reproves it**, with no statement of the relationship between the two papers. | `kernel_integrated_laws_v5/main.tex` §"The structural k→k−1 theorem" vs `tree_stability_v4` §"Homogeneous universal bounds" |
| D-8 | Manuscript 01's abstract and body render generated macros (`\VThreeReleaseStatus` → `FAIL_CLOSED_NOVELTY`, `\VThreeMaxAbsoluteGap` → `32`, `\VThreeMaxRelativeGap` → `1`) directly into scholarly prose. `\VThreeMaxRelativeGap = 1` is printed as a bare number with no unit or scale; from context it is a **relative gap of 1**, i.e. **100 %**, which the follow-up section states in words ("a full 100 %"). The abstract's phrasing invites reading it as a small number. | `generated_results.tex:7-8,15`; `main.tex:63`; `main.tex:536-537` |
| D-9 | Manuscript 01 cites `\VThreeSourceCommit` = `b718f4e51785` as the reproducibility manifest's source commit. That commit is `b718f4e` ("feat(research): add nodewise tree constants v3 system"), an **ancestor of `main`**, not the commit that produced the current manuscript (`2e419ef`). The manuscript's own caption acknowledges this ("the displayed source commit is the development checkpoint"). All generated tables and figures in manuscript 01 therefore trace to `b718f4e`, not to `2e419ef`. | `generated_results.tex:12`; `main.tex:846` |
| D-10 | Manuscript 05 ships figures as **PNG + SVG only**; no vector PDF. §18.1 of the delivery instruction requires vector PDF as the primary manuscript format. | `git ls-tree` of `8e09941 -- papers/supplementary_visual_atlas_v18/figures/` |
| D-11 | Manuscript 03's §Limitations describes a novelty search finding "a strong match to D'Amour et al.'s underspecification literature"; that search lives in `docs/research/novelty_matrix_v5.md`, which exists **only on the other branch** (`research/projected-tree-theory-v5`). Manuscript 03 cites a file its own branch does not contain. | §5.2; `a_to_n_certification_v18/main.tex` §Limitations |
| D-12 | Two distinct software papers exist for two distinct tracks (`software_v4` and `software_reproducibility_v5`); the delivery specifies one. | §5.3 |
| D-13 | `relative_gap := (upper − lower)/upper`, so the abstract's "maximum relative gap 1" means **`certified_lower_bound = 0`**. In **1794 of 9945** registered rows the certified lower bound is exactly zero — vacuous for a nonnegative quantity. | `src/seion_core/research_v3/interval_certification.py:130-141`; recomputed from `artifacts/index/optimality_gaps_v3.csv` |
| D-14 | Of the 60 cells reported as "certified globally", **30 are projected-error cells with lower = upper = 0** — the single-vertex case, where the manuscript's own theorem gives `E^{proj} = 0` identically. | recomputed from `artifacts/research_v3/block_A_exact_atlas.csv` |
| D-15 | `_exact_status` returns `EXACT_OPTIMAL_CONSTANT` only when `upper == lower == 0`. Consequence: the **45 genuinely exactly determined rows (`lower = upper = 1`) are labelled `NEAR_OPTIMAL_WITH_CERTIFIED_GAP`**, and the 30 trivial zero rows are labelled `EXACT_OPTIMAL_CONSTANT`. The label is inverted. | `scripts/tree_constants_v3_pipeline.py:438-444`; recomputed |
| D-16 | The 416 sweep "cells" behind manuscripts 03 and 05 are **208 distinct `scientific_instance_id`s, each executed twice** (once `cpu`, once `cuda`). Manuscript 03 nevertheless writes "96 **independent configurations**". | recomputed from `pilot_results.parquet` (96 rows / 48 ids) and `s1_results.parquet` (320 rows / 160 ids) |
| D-17 | Three reported numbers do not match their artifacts: block B "frozen projector, train law = 0.000000 / exactly 0" is `2.46×10⁻⁷`; block E "all transported angles sit at 1.41–1.53 rad" — the reported angles span 1.331–1.553; pilot/S1 wall times 945.5 s / 6316.5 s vs 942.8 s / 6300.8 s summed from the per-cell records. | recomputed from `block_b_ablation_matrix.json`, `block_e_interscale_experiment.json`, the two parquet files |

---

## 9. Non-destructive assembly method (no merge required)

§26.8 of the governing instruction requires stopping if the package "would require merging
branches". **It does not.** §5.2 establishes that the two branches are content-disjoint apart from
one file where one version strictly supersedes the other. The package can therefore be assembled by
read-only extraction:

* Manuscripts 01, 02 and their supporting `scripts/`, `artifacts/`, `docs/`, `claims/`:
  extract from `2e419ef`.
* Manuscripts 03, 04, 05 and `spectral/`: extract from `8e09941`.
* `papers/tree_stability_v4/main.tex`: take the `2e419ef` version (supersedes).

Method used and verified during this audit: `git worktree add --detach <short-path> <commit>`.

**Windows path-length caveat, encountered and worked around.** A worktree created under the
session scratchpad
(`C:\Users\ELIUTH~1\AppData\Local\Temp\claude\C--Documents-metamaths-seion-math-core\<uuid>\scratchpad\wt_spectral`)
checked out all 2 260 files and then failed with `fatal: Could not reset index file to revision
'HEAD'`, leaving nothing behind. The same command against `%TEMP%\swt` succeeded. Deep repository
paths such as
`spectral/certification_v18/artifacts/pilot_sweep/pilot_visual_diagnostics/02_block_h_associator_ratio_distribution.svg`
exceed the 260-character limit when prefixed by the scratchpad path. **Any assembly directory for
this package must use a short root path.**

No merge, rebase, push, branch creation, or history rewrite has been performed. The only
git-state-modifying operation of this audit was
`git worktree add --detach "%TEMP%\swt" research/spectral-a-to-n-v18`, which is read-only with
respect to both branches and is removed with `git worktree remove`.

---

## 10. `REPORT_TO_AUTHOR` — conditions of §26 that are met

Per §26 of the governing instruction, the following require reporting before large-scale rewriting.
Each is stated with the issue, location, mathematical or editorial consequence, safest correction,
and whether author authorization is needed.

### R-1 — §26.11: manuscript 02 duplicates manuscript 01's main theorem (authorization required)

**Issue.** `papers/kernel_integrated_laws_v5/main.tex` §"The structural k→k−1 theorem"
(Theorem `thm:kk1`) states
`E_T^amb ≤ kρM^{k−1}L_T`, `E_T^N ≤ kρM^{k−1}L_T`, `E_T^P = E_T^red ≤ (k−1)ρM^{k−1}L_T`
and gives a full inductive proof. This is verbatim the same statement as
`papers/tree_stability_v4` Theorem `thm:homogeneous` / `thm:homogeneous-full`. Manuscript 02 also
restates the exact root geometry (`thm:orthogonality` ≡ `prop:root`), the exact subset expansion
(`thm:subset` in both), the telescoping-order rule, the path-sum certificate, the signed-forest
triangle bound, and the representation-error estimate. Neither paper mentions the other.

**Consequence.** As they stand, manuscript 02's genuinely independent content is confined to:
CP representation and gauge freedom; associator conventions; the associator/left-operator curvature
identity; kernel-defined multilinear operators on `L²`; the associator kernel and its energy; the
variational functional and Stiefel geometry; finite cochain complexes and truncated Hodge
compatibility; the induced Markov operator and spectral dimension; and multiscale transport defects.
Everything else is a restatement of manuscript 01.

**Safest correction.** Restructure manuscript 02 as a companion on **kernel-defined multilinear
operators and conditional analytic extensions**, which cites manuscript 01 for the finite tree
theorem rather than reproving it, and retains only the finite material needed to state its own
hypotheses. This matches §21.2 of the governing instruction ("a shorter companion focused on
kernel-defined operators").

**Authorization required:** yes. Choosing between "shorter companion", "self-contained survey", and
"section of a collected volume" is the author's decision, and it changes the abstract, title, and
roughly half the section list of manuscript 02.

### R-2 — §26.6: a material statement rests on an unverifiable citation

**Issue.** Manuscript 03 §Limitations asserts a substantive comparison — that block B's
capacity-versus-deployment finding has "a strong match to D'Amour et al.'s underspecification
literature" — and uses that comparison to withdraw a novelty claim. The manuscript contains **no
bibliography and no `\cite`**. The supporting file `docs/research/novelty_matrix_v5.md` is not on
manuscript 03's own branch (D-11).

**Consequence.** A statement that materially weakens the paper's own novelty position cannot be
checked by a reader or a referee.

**Safest correction.** Add a verified bibliographic record for the intended work and cite it at the
point of use, or restate the sentence without attributing it to a specific literature.

**Authorization required:** no for adding the citation once verified; yes if the author wants the
sentence removed instead.

### R-3 — §26.5 / §26.4: manuscript 05's figures are not vector, and its data path is cross-branch

**Issue.** All nine figures ship as PNG + SVG with no PDF (D-10). Figures 8 and 9 are generated from
`spectral/certification_v18/artifacts/.../s1_results.parquet` on `8e09941`; the manuscript that
interprets the same sweep (03) is on the same branch, but manuscript 01's competing account of the
associator constant is on the other branch.

**Consequence.** §18.1 and §28 ("figures and tables are legible", vector PDF primary) cannot be met
without regenerating. Regeneration is possible: `generate_figures.py` is present and the parquet
inputs are present.

**Safest correction.** Re-run `generate_figures.py` from a `8e09941` worktree with a PDF backend
added, and record checksums in `06_figure_provenance.md`.

**Authorization required:** no — this is regeneration from committed data, not new computation.

### R-4 — §26.4: a headline number in manuscript 01's abstract is traceable but misleading as printed

**Issue.** D-8. The abstract prints "the maximum unresolved absolute and relative gaps are 32 and 1".
The value `1` is a *relative* gap of 1 — 100 % — which the paper's own §"Terminal status for k=2 and
k=3" states as "a full 100 %". Printed bare next to "32", it reads as a small number.

**Consequence.** The abstract understates the paper's central open problem. This is the opposite of
the governing rule that no statement be stronger than its evidence.

**Safest correction.** Print the relative gap as a percentage and state the normalisation explicitly
("relative to the proved upper bound" or "relative to the certified lower bound" — the two readings
give different factors, and `generated_results.tex` does not record which is meant). The
normalisation must be read off the generator
(`scripts/build_tree_constants_v3_tables.py`) and the underlying
`artifacts/index/constants_atlas_v3.csv` before the sentence is written. Until then the only wording
justified by what is on record is "the largest unresolved relative optimality gap is 100 %".

**Authorization required:** no — this is a correction toward accuracy. The wording should be
confirmed with the author.

### R-5 — §26.7 / scope: which software paper is deliverable 04

**Issue.** D-12. `papers/software_v4/` documents the finite-core pipeline behind manuscript 01;
`papers/software_reproducibility_v5/` documents the `spectral/certification_v18` suite behind
manuscript 03. They cover disjoint software.

**Consequence.** Delivering `software_reproducibility_v5` alone leaves manuscripts 01 and 02 with no
reproducibility article, even though manuscript 01 explicitly defers to "the software companion" for
"API and command-level details" (`tree_stability_v4/main.tex` §Reproducibility appendix).

**Safest correction.** Write deliverable 04 as a **single** reproducibility article covering both
computational tracks, with clearly separated sections, drawing on `software_v4` and
`software_reproducibility_v5` as sources.

**Authorization required:** yes. The alternative — delivering two software papers, making six
documents rather than five — changes the package structure the instruction specifies.

### R-6 — §26.9: no remote operation has been or will be performed without authorization

No push, PR modification, merge, rebase, force-push, branch deletion, or remote branch creation has
occurred. `gh pr list` (read-only) was the only network operation. Per §27, none will occur without
explicit authorization.

---

## 11. What this audit did **not** do

* No manuscript text was edited.
* No proof was corrected in place (findings are recorded in `03_proof_audit.md`).
* No figure was regenerated.
* No file was deleted, including the stale untracked build residue of §4.
* No commit was created.
* No claim of originality was assessed; that requires the expert literature review of §14.
