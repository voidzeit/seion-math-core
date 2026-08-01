# Academic submission package

Five independent scholarly documents on multilinear maps under orthogonal projection,
together with their sources, data, build instructions and verification records.

**Author:** Eliuth Chavero Jasso, Independent Researcher, Apizaco, Tlaxcala, Mexico.
**Assembled:** 31 July 2026.

**Nothing in this package has been reviewed by anyone other than the author, and no
assessment of originality has been carried out for any statement in it.** Neither
condition is a formality: they bound what every claim below may be taken to mean. See
`scholarly_status.md`.

---

## The five documents

### 01 — Error Propagation under Recursive Orthogonal Projection of Finite Multilinear Composition Trees

| | |
| --- | --- |
| File | `papers/01_recursive_projection_of_multilinear_trees.pdf` (39 pages) |
| Subject | Multilinear algebra; error analysis; projection-based reduction. MSC 15A69, 65G50, 65F35, 41A65, 18M60 |
| Principal result | For a finite typed composition tree with `k ≥ 1` internal vertices, under uniform bounds `M` on the multilinear maps and `ρ` on their closure residuals: `E^amb ≤ kρM^{k−1}L` and `E^proj = E^red ≤ (k−1)ρM^{k−1}L`. The reduction from `k` to `k−1` is the exact removal of the root closure residual by the final projection. |
| Evidence | Complete proof under the stated finite-dimensional assumptions, for every theorem. Rigorous interval enclosures for the lower constructions. Exploratory numerical search for the signed combinations. |
| Limitations | The coefficient `k−1` is an upper bound and is **not** shown to be attained at fixed `ρ/M > 0`. Over 9 945 registered configurations the constant is determined in 309 and vanishes by the theorem in 30; in 1 794 (18.0 %) no positive lower bound was obtained at all. Complexity of the state-resolved recursion counts recursion steps only. All results are finite-dimensional. |
| Relation to the others | 02 cites this article for the finite theory and does not reprove it. 03 studies different objects and is explicitly not connected to it. 04 documents its software as case study I. |
| Source commit | text `2e419ef4e1c028cfb85348feb515746e6c538ea8`; numerical evidence `b718f4e51785` (see `provenance.md`) |
| Build | `cd sources/recursive_projection_of_multilinear_trees && latexmk -pdf -outdir=build main.tex` |
| Dependencies | `amsart`, `lmodern`, `amsmath`, `amssymb`, `amsthm`, `mathtools`, `array`, `booktabs`, `tabularx`, `siunitx`, `graphicx`, `xcolor`, `geometry`, `enumitem`, `placeins`, `hyperref` |
| Independent review | not performed |
| Literature comparison | not performed to a standard supporting any originality claim |

### 02 — Kernel-Defined Multilinear Operators and Conditional Analytic Extensions of a Finite Projection Theory

| | |
| --- | --- |
| File | `papers/02_kernel_defined_multilinear_operators.pdf` (10 pages) |
| Subject | Multilinear integral operators; associators; finite cochain complexes. MSC 47H60, 47G10, 46E30, 58J50, 17A30 |
| Principal result | A kernel in `L²(X^{a+1})` defines a bounded multilinear operator; its composites again have square-integrable kernels, with `‖κ_L‖_{L²(X⁶)} ≤ ‖κ‖²_{L²(X⁴)}`; and under separability of `L²(X,ν)` the associator vanishes on all products of `L²` functions if and only if the defect kernel vanishes almost everywhere. |
| Evidence | Complete proofs; two of them (the composite-kernel bound and the converse) close gaps in an earlier formulation. Conditional constructions where labelled as such. |
| Limitations | The Markov-operator construction has **no verified instance**: no condition on the kernel is given under which its hypothesis holds. Spectral truncation is a statement about the truncation only. Continuum limits, pseudodifferential class membership and microlocal regularity are open questions and are stated as questions. |
| Relation to the others | Companion to 01, which it cites for the finite theory. Independent of 03. |
| Source commit | `2e419ef4e1c028cfb85348feb515746e6c538ea8` |
| Build | `cd sources/kernel_defined_multilinear_operators && latexmk -pdf -outdir=build main.tex` |
| Independent review | not performed |
| Literature comparison | not performed. Several results (cochain descent, Hodge compatibility, the Stiefel gradient) are standard and are cited as such rather than presented as contributions. |

### 03 — A Numerical Study of Cyclic Multilinear Maps, Orthogonal Projectors, and Multiresolution Tensor Representations

| | |
| --- | --- |
| File | `papers/03_numerical_study_of_projected_multilinear_models.pdf` (10 pages) |
| Subject | Numerical linear algebra; subspace perturbation; tensor compression; experimental design. MSC 65F99, 65Y20, 15A69, 62-08 |
| Principal results | Four negative results in the tested regime: a parameterised commutator model does not outperform the zero predictor in any of fifteen trained checkpoints; no subspace transport across three resolutions (principal angles 1.407–1.472 rad against `π/2 ≈ 1.571`); no persistence of tensor factors; three seeds at comparable loss converge to nearly orthogonal subspaces. Two methodological corrections found by the study's own controls. A swept measurement over 208 configurations finding the GPU 3.17–3.51 times slower than the CPU throughout `n ∈ {12,24,48,96}`. |
| Evidence | Exact identities where labelled as such; otherwise exploratory numerical evidence. |
| Limitations | Negative results hold for the objectives actually tested, which were reduced for tractability. Ten of the fourteen experiments are single-configuration and CPU-only. Two sweep stages were specified and not executed. A single random tensor is a control, not a null distribution. |
| Relation to the others | **Explicitly not connected** to 01 or 02: different objects, no shared code, no shared evidence. The numeral 2 appears in both 01 and 03 as a bound on different quantities, by coincidence. 04 documents its software as case study II. 05 is its supplement. |
| Source commit | `8e09941e56d6a514a44928ec1a6b5395fb8ceecb` |
| Build | `cd sources/numerical_study && latexmk -pdf -outdir=build main.tex` |
| Independent review | not performed |
| Literature comparison | A bounded search found directly relevant prior work for three of the study's own methodological choices; the article says so and claims none of them as novel. |

### 04 — Software and Reproducibility for Numerical Experiments on Projected Multilinear Models

| | |
| --- | --- |
| File | `papers/04_software_and_reproducibility.pdf` (7 pages) |
| Subject | Reproducible computational mathematics. MSC 68N30, 65Y05, 65G50, 15A69 |
| Content | The software behind 01 and 03, as **two explicitly separate case studies**: object representation, reference-versus-optimised implementations, precision and hardware controls, the configuration/execution/restart identity scheme, provenance, reconstruction of tables and figures, testing, and instructions for independent reproduction. |
| Evidence | 73 automated tests for case study I and 85 for case study II, both passing; agreement between reference and optimised implementations; agreement between two devices in double precision. |
| Limitations | **No clean-environment reproduction has been performed**, by the author or anyone else. This is the largest outstanding gap and the article says so first. |
| Relation to the others | Makes **no independent mathematical claim**. Every mathematical statement it mentions is cited to 01 or 03. |
| Source commits | both, since it covers both case studies |
| Build | `cd sources/software_and_reproducibility && latexmk -pdf -outdir=build main.tex` |
| Independent review | not performed |

### 05 — Supplementary Numerical Results for Projected Multilinear Models

| | |
| --- | --- |
| File | `papers/05_supplementary_numerical_results.pdf` (11 pages) |
| Content | Nine figures supporting 03, each regenerated from committed data, supplied as vector PDF, archival SVG and 300-dpi PNG, with a checksum manifest; the data source and parameters of each; the visual conventions; and an explicit list of what is not included. |
| Evidence | Figures only. Every plotted value is read from an input file; none is entered by hand. |
| Limitations | No confidence interval is drawn anywhere, because no sampling model is specified for any of these experiments. Ranges shown are observed minimum-to-maximum. |
| Relation to the others | Supplement to 03. |
| Source commit | `8e09941e56d6a514a44928ec1a6b5395fb8ceecb` |
| Build | `cd sources/supplementary_results && python generate_figures.py && latexmk -pdf -outdir=build main.tex` |
| Independent review | not performed |

---

## Layout

```
academic_submission_package/
├── README.md                       this file
├── PATH_TO_ESTABLISHED.md          the four filters, and where the work stands on each
├── MATHEMATICAL_CORRECTIONS_CLOSED.md  every known defect found and repaired
├── scholarly_status.md             what each document does and does not establish
├── statement_evidence_table.md     one row per major statement, with its support
├── notation_and_conventions.md     unified notation; the collisions it resolves
├── mathematical_audit.md           result-by-result audit of every proof
├── literature_audit.md             comparison with the cited literature
├── reproducibility_report.md       what was verified, how, and what was not
├── provenance.md                   commits, data lineage, and the branch split
├── checksums.sha256                SHA-256 of every delivered file
├── build_manifest.json             machine-readable build and verification record
├── rebuild_all.sh                  rebuilds everything from these sources
├── papers/                         the five PDFs
├── sources/                        LaTeX sources, data, figure generator
├── external_review/                originality table to complete; reviewer request
├── clean_room/                     container recipe and reproduction script
└── verification/                   build logs, test results, extracted text,
                                    figure provenance, reference verification,
                                    source commits
```

## Where this stands

Four filters separate a promising internal result from an established one:

```
correctness  →  bounded originality  →  independent verification  →  publication
  closed            not started              not started              not started
```

Correctness is closed: 15 known mathematical defects were found and repaired, recorded in
`MATHEMATICAL_CORRECTIONS_CLOSED.md`. The most serious was an undeclared hypothesis in the
representation-error proposition; its correction is both simpler and strictly tighter than
what it replaces.

The remaining three filters need people other than the author. The instruments are prepared
and empty: a twelve-row theorem-by-theorem originality table, a structured request for two
mathematical reviewers, and a container recipe that reproduces the minimal supporting set.
`PATH_TO_ESTABLISHED.md` sets out what each requires.

Note that the optimality of `k−1` is **not** on that path. `C_T^proj(η) ≤ k−1` is proved;
`C_T^proj(η) = k−1` is open, and a theorem does not cease to be correct for failing to be
optimal.

## Rebuilding

```bash
bash rebuild_all.sh
```

The script re-derives the optimality classification from the recorded certified bounds,
rewrites the vocabulary of the generated tables, regenerates every figure with checksums,
builds all five manuscripts from clean directories, checks each build against the
acceptance criteria below, runs the test suite, and writes `checksums.sha256`.

It runs **no experiment**. Every number in the manuscripts comes from a committed data file
or from a deterministic re-derivation of one.

## Acceptance criteria, and the measured result

| Criterion | 01 | 02 | 03 | 04 | 05 |
| --- | --- | --- | --- | --- | --- |
| LaTeX errors | 0 | 0 | 0 | 0 | 0 |
| Undefined references | 0 | 0 | 0 | 0 | 0 |
| Undefined citations | 0 | 0 | 0 | 0 | 0 |
| Overfull boxes | 0 | 0 | 0 | 0 | 0 |
| Missing figures | 0 | 0 | 0 | 0 | 0 |
| Placeholder text | 0 | 0 | 0 | 0 | 0 |
| Corrupted ligatures in extracted text | 0 | 0 | 0 | 0 | 0 |
| Type 3 bitmap fonts embedded | 0 | 0 | 0 | 0 | 0 |
| Pages | 39 | 10 | 10 | 7 | 11 |

The last two rows deserve a note. In the previous build, the text fonts were embedded as
Type 3 bitmaps, whose ligature glyphs carry no usable Unicode mapping, so extracting text
from the PDFs turned *finite* into *nite*, *difference* into *dierence* and *certificate*
into *certicate* — 125 occurrences across the five documents. Loading an outline font
(`lmodern`) fixes it; the check above is what confirms the fix, and `rebuild_all.sh` fails
if it ever regresses.

## What this package does not assert

It is not asserted that any document here is accepted, original, independently verified, or
ready for a particular journal. None of those facts has been established.


