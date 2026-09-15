# PRIOR-ART-R — search protocol

```
VERSION:  v1
FROZEN:   2026-09-14, before the first query (SHA-256 of this file and queries.json in FREEZE.json)
SCOPE:    Theorem R — sharp worst-case projected-error constant for tree-structured multilinear
          computations with intermediate orthogonal projections (see ../paper/STYLE_CONTRACT.md)
GLOBAL:   NOVELTY_NOT_ESTABLISHED until §8 stop criterion is met AND manual MathSciNet/Scholar
          steps (§4) are logged
```

Deviations after freezing are allowed only as dated entries in §10 and are labelled `POST_HOC`.

## 1. Claims under comparison

| ID | Claim | Note |
|---|---|---|
| R1a | Upper bound $\lVert P_rF_r-R_r\rVert\le C_k(\eta)\rho M^{k-1}\prod\lVert z_\ell\rVert$ for tree-structured multilinear computations with intermediate orthogonal projections | |
| R1b | Sharpness: $C_k(\eta)$ is best possible | separate from R1a |
| R2 | Explicit formula $C_k(\eta)=\eta^{-1}\max_{\theta\le\arcsin\eta}\lvert 1-(\cos\theta e^{i\theta})^{k-1}\rvert$ | |
| R3 | Independence of the sharp constant from tree structure at fixed $k$ | logically a corollary of R2; search targets weaker independence statements |
| R4 | Extremizer for every tree structure | |
| R5 | Two-dimensional (planar) extremizer | |
| R6 | Spherical-lift angle; multilinear angle contraction; telescoping proof | auxiliary; likely partly known (generalized fidelity) |
| R7 | Diagonal (equal-angle) extremization of $\lvert1-\prod\cos\theta_je^{i\theta_j}\rvert$ | |
| R10 | Absolute bound $E\le G_k(\eta)M^kL$ with $G_k<2$ | |
| R11 | Asymptotics $C_k(\eta)\to k-1$ as $\eta\downarrow0$ | also stated in the project's own v5 material |
| R12 | Upper bound under trajectory closure (weaker than subspace closure) | |
| R8 | Lean 4 / Mathlib formalization | **artifact claim**, tracked separately; not a mathematical novelty claim |
| R9 | Relation to TT/HT/TTN truncation and projection error | positioning, not a novelty claim |

## 2. Status vocabulary

Per claim: `KNOWN` · `KNOWN_IN_SPECIAL_CASE` · `CLOSE_PRIOR_ART` · `NO_EQUIVALENT_FOUND` ·
`NOVELTY_NOT_ESTABLISHED`.

Per source (harmonized with `research/projected_trees_v5/novelty/`):

| This protocol | Repository label (v5) |
|---|---|
| threat 5 — possibly equivalent / subsumes | (none; blocks novelty) |
| threat 4 — very close theorem | `KNOWN_ADJACENT_RESULT` (close) |
| threat 3 — similar result, materially different assumptions | `KNOWN_ADJACENT_RESULT` |
| threat 2 — shared technique | `METHODOLOGICALLY_ADJACENT` |
| threat 1 — same broad field | background |
| threat 0 — irrelevant | excluded |

## 3. Search families and queries

Exact queries: `queries.json` (families A–N, 47 queries). Families A–H follow the author's plan;
I–N were added before freezing because they contain structurally close mechanisms
(products of projections with $\cos^n$ factors, repeated projective measurements, hybrid arguments,
numerical ranges, MPS truncation, layerwise compression).

## 4. Sources

| Source | Mode | Use |
|---|---|---|
| OpenAlex | automated | primary discovery; citation graph (backward via `referenced_works`, forward via `cites:`) |
| arXiv API | automated | preprints |
| zbMATH Open API | automated | mathematics coverage; MSC codes of anchors |
| Semantic Scholar API | automated, best effort | skipped and logged on HTTP 429 |
| Crossref | automated | DOI/metadata validation only |
| **MathSciNet** | **manual (subscription)** | same queries + MSC searches; logged by the author in `SEARCH_LOG.csv` |
| **Google Scholar** | **manual** | same queries; forward citation chasing of anchors; logged by the author |

Every automated request is logged (date, source, query, result count, status). Raw records are kept
in `raw/` (not edited).

## 5. Screening

1. **Level 0 (automated pre-rank).** Deduplicate by DOI/arXiv/normalized title; score title+abstract
   with a fixed keyword rubric (`harvest.py`). The rubric only orders the list; it never excludes.
2. **Level 1 (metadata/abstract).** For every candidate in the top slice of each family plus every
   candidate matching a Level-0 red-flag term: "can this contain an equivalent or more general
   theorem?" → threat 0–5 with a one-line reason.
3. **Level 2 (introduction + main theorem).** Threat ≥3 → read definitions, main theorems, related
   work (open full text where available; otherwise marked `ABSTRACT_ONLY`).
4. **Level 3 (theorem-by-theorem).** Threat ≥4 → written comparison in `theorem_comparisons/`
   (their assumptions/conclusion vs ours).

## 6. Anchors and snowballing

- 3–5 anchors per family (technique origin, classical result, survey, closest bound, strongest
  modern result, rich bibliography).
- Backward: all references of each anchor (OpenAlex). Forward: citing works of each anchor
  (OpenAlex; Scholar manually). Lateral: same authors, same MSC (zbMATH; MathSciNet manually).
- Each round's new candidates go through §5.

## 7. Records

`SEARCH_LOG.csv` (one row per request) · `PRIOR_ART_MATRIX.csv` (one row per screened source) ·
`CLAIM_NOVELTY_MATRIX.md` (R1a–R12) · `theorem_comparisons/` · `bibliography/references.bib`
(DOI-validated via Crossref) · `MANUAL_QUERIES.md` (MathSciNet/Scholar checklist).

## 8. Stop criterion (saturation)

All must hold: (1) every family has anchors; (2) backward + forward chasing of all anchors;
(3) relevant MSC searched (zbMATH automated, MathSciNet manual); (4) every threat 4–5 source read at
Level 3; (5) two consecutive snowball rounds produce no new family and no new threat ≥4 source;
(6) every claim has a documented status; (7) recent literature re-checked at submission date.

## 9. Disclosure

No public posting of the formula or theorem (forums, MathOverflow) before the preprint. Expert
consultation privately (see `research/projected_trees_v5/review/EXTERNAL_REVIEWER_SHORTLIST_2026-08-09.md`).

## 10. Deviations log

| Date | Entry |
|---|---|
| 2026-09-14 (pre-freeze) | Tooling smoke tests with one query each for OpenAlex, zbMATH and arXiv. These are not used for screening. The arXiv API returned HTTP 429 during the tests; the harvester retries once after 30 s and otherwise skips arXiv, logging each skip. Preprints are then covered through OpenAlex, which indexes arXiv. |
| 2026-09-14 13:17 `POST_HOC` | Attempt 1 was stopped after 5 logged requests because of two tooling bugs (queries unchanged). (a) zbMATH returns HTTP 404 "No results found" for empty result sets; this was logged as `ERROR` and is now logged as `OK` with 0 results. (b) arXiv returned HTTP 503; the harvester now treats 503 and timeouts like 429 (one retry, then skip for the rest of the run). Attempt 1 (log + raw) is quarantined in `quarantine/attempt1/` and not used for screening. `harvest.py` hash after the fix: see `FREEZE.json` → `post_hoc_fixes`. |
| 2026-09-14 `POST_HOC` | Anchor identifier verification (titles resolved via OpenAlex/Crossref) found two errors in the seed anchors. (a) `10.1006/jmaa.1997.5216`, copied from `papers/paper_a/references.bib`, resolves to a different paper; the correct DOI for Deutsch–Hundal (1997) is `10.1006/jmaa.1997.5202`. **The repository bibliography carries a wrong DOI.** (b) The arXiv DOI of Ryu–Hannah–Yin is an empty OpenAlex record; the published DOI `10.1007/s10107-021-01639-w` is used instead. Snowball outputs of the two wrong identifiers are quarantined in `quarantine/anchor_id_errors/` and redone as `round1_fix`. `snowball.py` gained an optional anchor-subset argument; the query logic is unchanged. |
