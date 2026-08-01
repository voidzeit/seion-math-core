# Prompt for next agent session — final delivery package

(Paste everything below into a fresh session)

---

You are working in the repository at `C:\Documents\metamaths\seion-math-core`
(GitHub: `voidzeit/seion-math-core`). Your task is to produce a polished,
submission-grade **final delivery package**: a single folder containing
the cleaned-up, deeply-edited final PDFs of every SEION V5 paper, merged
and cross-consistent, at the highest achievable standard of mathematical
writing — the level of exposition, rigor, and precision expected in a
top-tier pure-mathematics venue (Annals of Mathematics / Inventiones /
JAMS tier: exact definitions, complete proofs or explicitly labeled open
statements, no hand-waving, no inflated claims, immaculate notation,
professional-grade figures). This is a **polish and packaging pass**, not
a research pass — you are not being asked to resolve open problems, prove
new theorems, or claim novelty that hasn't been independently reviewed.
Elevating presentation quality must never mean elevating epistemic
claims. Read this entire prompt before touching anything.

## 0. Ground truth before you start — do not trust this summary blindly

This prompt describes the state as of 2026-07-30 evening. Before editing
anything, verify it yourself: `git log`, `git branch -a`, `gh pr list
--repo voidzeit/seion-math-core`, and re-read the actual `.tex` files.
Treat every claim below as a hypothesis to confirm, not a fact to act on
unverified — the same standard this project applies to its own scientific
claims applies to this prompt.

## 1. Repository structure you need to know

Four branches, four open PRs, **none merged into `main`, none merged into
each other**. This matters: the five papers below are split across two
unmerged branches. To build one delivery package you must pull content
from both without merging the branches themselves (unless the user
explicitly authorizes a merge — see Section 6).

- `program/seion-canonical-repository-v4` — PR #1. CANONICAL_FINITE_CORE
  track (older, `FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW`). Has its own
  older paper drafts (`papers/foundations_v2/`, `papers/software_v4/`,
  `papers/supplement_v4/`, `papers/tree_stability_v3/`) — check these but
  they are superseded by v4/v5 versions on the branches below unless you
  find evidence otherwise.
- `research/spectral-a-to-n-v18` — PR #2. SPECTRAL_LEGACY_TRACK (the A-N
  cyclic-law/projector/tensor audit). Contains:
  - `papers/a_to_n_certification_v18/main.tex` (5 pages as of last edit)
  - `papers/software_reproducibility_v5/main.tex` (3 pages)
  - `papers/supplementary_visual_atlas_v18/main.tex` (8 pages, 9 figures)
- `infra/agent-graph-loop-v1` — PR #3. Governance/lifecycle tooling, no
  papers.
- `research/projected-tree-theory-v5` — PR #4. Track T (projected n-ary
  tree mathematics) + a new broader formalization. Contains:
  - `papers/tree_stability_v4/main.tex` (32 pages — the deepest, most
    mathematically complete document in the repo; has a real appendix
    with full proofs at `proofs/full_proofs.tex` and generated tables at
    `tables/*.tex`, plus 18 figures)
  - `papers/kernel_integrated_laws_v5/main.tex` (10 pages — broader
    formalization spanning finite core + kernel/cohomology/Hodge
    extensions, explicitly three-tiered: proved / conditioned / open)

Track separation is enforced project-wide: `SPECTRAL_LEGACY_TRACK` and
Track T (`CANONICAL_FINITE_CORE`-adjacent) are evidentially separate. A
claim from one track may not be used to certify the other without an
explicitly proved connecting theorem. Preserve this separation in the
final package — do not silently blend results across tracks to make the
overall narrative sound more unified than it is.

To gather everything without merging branches, use e.g.:
```bash
mkdir -p /tmp/delivery-src
git -C /path/to/repo archive research/spectral-a-to-n-v18 papers/a_to_n_certification_v18 papers/software_reproducibility_v5 papers/supplementary_visual_atlas_v18 | tar -x -C /tmp/delivery-src
git -C /path/to/repo archive research/projected-tree-theory-v5 papers/tree_stability_v4 papers/kernel_integrated_laws_v5 | tar -x -C /tmp/delivery-src
```
(adjust for the actual shell/OS — this is Windows with Git Bash available
per the existing CLAUDE.md-equivalent environment notes; use forward
slashes and the Bash tool, not PowerShell, for git operations matching
the rest of this project's convention).

## 2. What every paper currently claims — read each `main.tex` in full

Do not skim. Each paper has an epistemic-status system already baked in
(typed claim states, explicit "what this does NOT prove" sections, open-
problem lists). Your polish pass must preserve every one of these
qualifications exactly — a "Fields-Medal-level" paper is not one that
sounds more confident than its evidence; it is one whose confidence is
*calibrated exactly* to its evidence, stated with total precision. If you
find a sentence that overclaims relative to what the referenced
proof/experiment actually establishes, fix the sentence to be accurate,
do not delete the qualification.

Key facts to preserve accurately (verify against the actual files, this
is a summary):
- The central proved theorem across both tracks is the ambient-vs-
  projected coefficient improvement: $E_T^{\rm amb} \le k\rho M^{k-1}L_T$
  vs $E_T^P \le (k-1)\rho M^{k-1}L_T}$ for a $k$-internal-node typed
  composition tree, proved by exact error-orthogonality + induction.
  **Sharpness at fixed $\eta>0$ is NOT proved** — stated as
  `OPEN_K2_WITH_CERTIFIED_GAP` / `OPEN_K3_WITH_CERTIFIED_TOPOLOGY_GAPS`.
  Do not let any rewritten sentence imply sharpness is established.
- The A-N certification track found real negative results (Block B
  commutator explanation `REFUTED_IN_DEPLOYED_REGIME`; Blocks E/J/M
  `NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME`) — these are genuine
  contributions, not failures to hide. Present them with full confidence
  as *negative results*, not apologetically.
- One associator-forest identity (`named_gji_variants`) is flagged
  `NOT_CERTIFIABLE_AS_DEFINED` — looks like a vacuous formal identity,
  not yet symbolically confirmed. State this exactly as the uncertain,
  flagged-but-unconfirmed finding it is.
- A novelty audit exists (`docs/research/novelty_matrix_v5.md`, also
  `claims/prior_art_registry_v3.yaml`) with every verdict
  `PENDING_HUMAN_REVIEW`. No paper may state or imply a novelty claim has
  been approved — human approval has not happened. If any paper's prose
  currently reads as claiming novelty outright, soften it to accurately
  reflect "candidate novelty, pending human review," citing the specific
  prior art found.

## 3. The polish rubric — apply uniformly across all five papers

### 3.1 Mathematical language and notation
- Absolute notational consistency across ALL papers being merged/
  packaged together: if $E_T^P$ means the same thing in two papers, it
  must be *defined identically*, in the same order, with the same
  hypotheses stated the same way. Build a shared notation table if
  helpful and verify every paper against it.
- Every theorem/proposition/lemma must have: a complete, unambiguous
  statement; every hypothesis explicit (no implicit assumptions); a
  proof that is either complete or explicitly labeled as a proof sketch
  with the gap named. Check `proofs/full_proofs.tex` for `tree_stability_v4`
  and inline proofs elsewhere — verify each one is actually complete as
  written, not merely plausible-looking.
- Use precise, standard mathematical English: "we show," "it follows
  that," "by Theorem X," never colloquial hedges ("basically," "sort of,"
  "kind of works"). Passive/active voice should match top-journal
  convention (active is generally preferred in modern math writing:
  "We prove..." not "It is proven...").
- Check every cross-reference resolves (`\ref`, `\label`, `\cite`) after
  final compilation — zero `??` marks, zero undefined-reference warnings
  in the LaTeX log, checked programmatically not by eye alone.

### 3.2 Prose and structure
- Native-level, publication-grade English throughout. Fix any awkward
  phrasing, redundancy, or grammatical error. Vary sentence structure;
  avoid repetitive paragraph openers.
- Each paper needs: a precise, self-contained abstract (states the main
  result and its exact scope in the first two sentences); an introduction
  that motivates the problem and states the contribution list explicitly;
  clearly delineated sections with logical progression; a conclusion that
  does not merely restate the abstract but synthesizes what was learned
  and what remains open, matching the honest epistemic-status system
  already in place.
- Consistent section/subsection numbering, consistent theorem/definition/
  remark environments (check `\newtheorem` blocks match across papers if
  you are producing a merged document — see Section 5).
- Bibliography: every `\cite` must resolve to a real, verifiable entry in
  `.bib` — check `papers/*/references.bib` for entries that might be
  placeholder/unverified and flag them rather than silently keeping them.
  Do not invent citations. If a citation looks fabricated or unverifiable,
  remove the claim it supports or mark it as needing verification rather
  than leaving it uncited-but-asserted.

### 3.3 Figures — "hyper-professional, graphically detailed," generated from real data only
- Every figure must be regenerated (not just re-styled) from its
  underlying real data using a script, not hand-drawn or fabricated.
  Existing generator scripts:
  `spectral/certification_v18/dataset/generate_atlas_figures.py`,
  `scripts/signed_forest_adversarial_search_v5.py`, and whatever
  generates `papers/tree_stability_v4/figures/*.pdf` (check
  `papers/tree_stability_v4/README.md` / any `Makefile` /
  `scripts/tree_constants_v3_pipeline.py` for the actual figure pipeline
  — do not assume, verify).
- Upgrade figure quality: consistent colorblind-safe palette across ALL
  figures in the package (Okabe-Ito is already used in
  `supplementary_visual_atlas_v18` — extend that palette project-wide),
  consistent font sizes matching the paper's body text size, vector
  formats (PDF/SVG) as the primary output with high-DPI PNG (300+) as a
  fallback, properly labeled axes with units, legends that don't overlap
  data, captions that state what the figure shows AND what conclusion it
  supports (not just a description).
  - Prefer regenerating any A-N block figures directly through
  `matplotlib`/`tikz` scripts checked into the repo (not one-off
  interactive edits) so the whole figure set is reproducible from a
  single command. If you build new consolidated figures (e.g. one
  combined dashboard spanning both tracks), write the generator as a
  script under `scripts/` or the relevant `dataset/` directory and commit
  it alongside its output, exactly matching this project's existing
  provenance convention (PNG+SVG+source-JSON+sha256-manifest per figure
  — see `spectral/certification_v18/dataset/hashes/*.manifest.json` for
  the pattern).
- Do not fabricate a single number in any figure. Every data point must
  trace to a real artifact already in the repo (`artifacts/`,
  `spectral/certification_v18/artifacts/`, `spectral/certification_v18/
  dataset/`) or one you regenerate by re-running the existing, already-
  verified code. If you want a figure that doesn't exist yet and the data
  for it doesn't exist either, either compute it for real (bounded,
  reasonable compute — check with the user before anything that would
  take hours) or state explicitly in the package README that it's not
  included and why.

### 3.4 Compilation and verification (non-negotiable, matches this project's established standard)
For every PDF in the final package:
1. Compile with `pdflatex` **twice** (cross-references/TOC need two
   passes minimum; run `bibtex`/`biber` + two more passes if the
   bibliography changed).
2. Grep the `.log` for `Overfull \hbox`, `Underfull \hbox`, `undefined`,
   and `! ` (LaTeX errors) — fix every one you introduce; pre-existing
   ones not touched by your edits may be left with a one-line note, but
   check first whether fixing them is trivial (most overfull-hbox issues
   in this repo so far have been one-line fixes: convert `tabular` to
   `tabularx`, split a too-long display equation, or add a short
   `\markboth` override for a long title).
3. Render at least 2-3 pages of each PDF to PNG (e.g. via `pymupdf`/
   `fitz`) and actually look at them before calling the PDF final — this
   project's established practice, do not skip it. Confirm figures
   render, tables aren't truncated, headers/footers are sane.
4. Run the repository's test suite (`python -m pytest -q`, and
   `pytest spectral/certification_v18/tests/` on the spectral branch) if
   you touch any `.py` figure-generation script — must stay green.

## 4. The delivery package itself

Create a new top-level directory, e.g. `delivery_package_v5/`, with a
clear internal structure:
```
delivery_package_v5/
  README.md                          -- what's inside, provenance, how to rebuild
  papers/
    01_a_to_n_certification.pdf
    02_software_reproducibility.pdf
    03_supplementary_visual_atlas.pdf
    04_track_t_tree_stability.pdf
    05_kernel_integrated_laws.pdf
  sources/                           -- the polished .tex + figures + bib for each, so it's fully reproducible
    a_to_n_certification/...
    software_reproducibility/...
    supplementary_visual_atlas/...
    tree_stability_v4/...
    kernel_integrated_laws_v5/...
  checksums.sha256                   -- sha256 of every PDF, so tampering is detectable
```
Number/name the files clearly (the user asked for "los archivos
nombrados" — use descriptive, stable filenames, not `main.pdf` x5 in one
flat folder). The `README.md` must state, per paper: title, page count,
one-paragraph summary, and its terminal epistemic status (proved /
open-with-certified-gap / refuted / etc, matching this project's own
vocabulary) — do not let the README oversell what's inside.

Where should this directory live? Given the branch-separation issue in
Section 1, the cleanest option is a new dedicated branch (ask the user
first — creating a new branch is low-risk but should still be confirmed,
and pushing it is an explicit-permission action per this project's
standing safety rules, same as every push this session required
individual confirmation). Do not silently merge `research/
spectral-a-to-n-v18` and `research/projected-tree-theory-v5` to produce
this — that would violate the deliberate track separation unless the
user explicitly authorizes a real merge decision.

## 5. Optional: a single merged "main paper" (only if the user explicitly wants this)

The user's request could be read as wanting one consolidated master
document as well as the five individual papers. If so, build a sixth PDF
(`00_seion_v5_complete.pdf`) that sequences the five papers with a short
connecting preface explaining the two-track structure and how the pieces
relate (kernel_integrated_laws_v5 as the broad formalization, tree_stability_v4
as the deep Track T treatment, the three A-N papers as the certification/
software/atlas triad) — do not silently interleave their content or
create false continuity between tracks that don't connect. If unifying
notation across all five for this merged document requires nontrivial
rewriting of theorem statements, do that rewriting carefully and note in
the merged document's preface exactly which paper each section is drawn
from, so provenance stays traceable.

## 6. Standing safety/process rules (same for you as for every session on this repo)

- Never push to any remote branch, open/modify a PR, or create a new
  branch on origin without asking the user first in chat, even under a
  broad "proceed" instruction — permission is per-action.
- Never merge branches without explicit user authorization — track
  separation is a deliberate project policy, not an oversight.
- Never fabricate a citation, a data point, a proof step, or a "novelty"
  claim. If you cannot verify something, say so explicitly rather than
  smoothing over the gap.
- If you find a claim in an existing paper that appears to overclaim
  relative to its evidence, fix the claim's wording rather than either
  (a) silently leaving it or (b) deleting the result — the goal is
  calibrated precision, not censorship.
- Commit messages should explain *why*, not just *what*, matching this
  repo's existing commit style — look at recent commits with `git log`
  for the tone/format expected.
- Run `python -m pytest -q` before any commit that touches source code.
