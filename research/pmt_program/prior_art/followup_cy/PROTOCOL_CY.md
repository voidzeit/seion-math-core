# PRIOR-ART-R-CY — targeted follow-up protocol (tightness of heterogeneous composition constants, m ≥ 3)

```
VERSION:  cy-v1
FROZEN:   2026-09-14, before the first query of this follow-up (SHA-256 of this file, queries_cy.json,
          anchors_cy_spec.json and cy_round.py in FREEZE_CY.json)
PARENT:   PRIOR-ART-R-HET (SEARCH_PROTOCOL_HET.md, CLAIM_NOVELTY_MATRIX_HET.md §6 item 6)
GLOBAL:   NOVELTY_NOT_ESTABLISHED (regardless of outcome)
BRANCH:   research/prior-art-r (no commit / push in this follow-up)
```

Deviations after freezing are logged in §9 as dated `POST_HOC` entries (with new SHA-256 of any changed
frozen file, recorded in `FREEZE_CY.json`). Round-1 and HET files are not modified; the only file outside
`followup_cy/` that is touched is an append-only dated section of `../README.md`.

## 1. Target and question

Target constant (Lean-checked, novelty not established), $w(\theta)=\cos\theta\,e^{i\theta}=(1+e^{2i\theta})/2$:

$$g_{\rm Box}(\eta)=\max_{\theta_u\in[0,\arcsin\eta_u]}\Bigl|1-\prod_u w(\theta_u)\Bigr| ,$$

over non-root internal nodes $u$ of a projected multilinear tree; sharp (planar witness, independent angles);
depends only on the multiset $\{\eta_u\}$. Geometrically, $w([0,\arcsin\eta_u])$ is an **arc** of the circle
$|z-\tfrac12|=\tfrac12$, the boundary of the SRG disk $D(\tfrac12,\tfrac12)$ of firmly nonexpansive operators.

**Priority question.** Combettes–Yamada 2015 (CY15, Prop. 2.5 / Remark 2.7) give a composition constant for
$m$ averaged operators, symmetric in the per-factor parameters; Huang–Ryu–Yin 2020 (HRY20) prove tightness for
$m=2$. Does any work

- (i) prove tightness / sharpness of an $m\ge3$ heterogeneous composition constant, or
- (ii) compute Minkowski products of $m\ge3$ SRG disks or arcs of $|z-\tfrac12|=\tfrac12$ (or of
  $D(1-\alpha_i,\alpha_i)$) and maximize the distance to a point, or
- (iii) otherwise imply $g_{\rm Box}$ or its placement independence?

Answer vocabulary: `YES` (a source states it, with locator) · `NO_FOUND` (not found within this protocol's
coverage) · `UNRESOLVED` (a candidate exists but could not be read, or coverage gaps prevent a conclusion).
`NO_FOUND` is never reported as "does not exist".

## 2. Six-criterion rubric (Level 3)

For each Level-3 source, each criterion is answered `YES` / `NO` / `PARTIAL` with theorem/lemma/equation
numbers and at most one short quoted sentence per sheet.

| # | Criterion |
|---|---|
| C1 | The bounded quantity is expressible as a complex product, or as a Minkowski product of complex sets. |
| C2 | Per-factor parameters admit an angular / arc interpretation compatible with $\theta_u\le\arcsin\eta_u$ (a cap on the angle along the circle $\lvert z-\tfrac12\rvert=\tfrac12$, not a disk radius). |
| C3 | The constant is exact (sharp) for every number of factors $m$. |
| C4 | Equality is attained, with an explicit extremizer. |
| C5 | The constant is independent of the order / placement of the factors. |
| C6 | The result specializes directly to $g_{\rm Box}$ (substitution shown), or the precise obstruction is stated. |

Threat 0–5 as in `SEARCH_PROTOCOL.md` §2 (5 possibly equivalent; 4 very close theorem; 3 similar result,
materially different assumptions; 2 shared technique; 1 same broad field; 0 irrelevant). **Threat 5 only if
C1–C6 are all `YES` for an equivalent model.** Threat 4 requires C1, C3 and C6 `YES` or `PARTIAL` with a
sharp heterogeneous constant for $m\ge3$. A proof of tightness of the CY15 constant for $m\ge3$ alone is
threat ≤3 for H1/H2/H4 unless it also controls $\max|1-\prod|$ over angle-capped arcs (C2, C6).

## 3. Sources and procedures

### 3.1 Anchors and DOI verification (before any forward-citation query)

Anchors (`anchors_cy_spec.json`): CY15 (DOI 10.1016/j.jmaa.2014.11.044), HRY20 (10.1016/j.jmaa.2020.124211),
RHY22 "Scaled relative graphs" (10.1007/s10107-021-01639-w), Ogura–Yamada 2002 (OY02; DOI candidate
10.1081/NFA-120003674, to be verified), Pates 2021 "The scaled relative graph of a linear operator" (no DOI
known; resolved by OpenAlex title search, then DOI/arXiv if any). Each identifier is resolved through
OpenAlex **and** Crossref (Crossref not applicable to arXiv-only records); title, first author and year are
compared with the intended paper and the result is recorded in `anchors_cy.json`. A mismatch stops that
anchor until corrected (logged). If a paper has several OpenAlex work IDs (preprint + journal), forward
citations are collected for **each** verified ID and unioned.

### 3.2 Forward citations

OpenAlex `filter=cites:<Wid>`, `per-page=200`, cursor pagination until exhausted (all pages). Raw pages in
`raw/`. Every request logged in `SEARCH_LOG_CY.csv`. Counts reported per anchor (`meta.count` vs retrieved).

### 3.3 Co-citation sets

- $S_1$ = works citing both CY15 and HRY20;
- $S_2$ = works citing both HRY20 and RHY22.
Computed on OpenAlex work IDs (after unioning duplicate IDs of each anchor). Also reported: works citing
HRY20 and any of {CY15, OY02}, and works citing Pates 2021 and HRY20 (informational).

### 3.4 Keyword harvest

`queries_cy.json` (22 queries, families CY1–CY4) on OpenAlex (`search`, 25 per query), arXiv API (25 per
query; same query builder as `harvest.py`) and Semantic Scholar (10 per query). The `harvest.py` query
functions are imported unchanged. Error handling (preregistered, differs from round 1/HET only inside
`followup_cy/cy_round.py`): on HTTP 429/503/timeout retry with backoff 30/60/120 s; if still failing, log
`BLOCKED` for that request and continue with the next query (no global block); a blocked request is never
counted as zero results. One supplemental pass at the end re-tries every `BLOCKED`/`ERROR` request once.

### 3.5 Screening

- **Level 0.** Pool = forward citations ∪ keyword records, deduplicated (DOI, arXiv id, OpenAlex id,
  normalized title). A CY relevance count `cy_score` (number of matched groups among: averaged/firmly
  nonexpansive/conic/nonexpansive; composition/product; tight/sharp/optimal/exact/best constant; scaled
  relative graph/SRG; Minkowski; disk/disc/arc/circle/oval; projection/projector) orders reading only.
- **Level 1** (`screening_cy_L1.csv`: key, threat, flag_L2, reason). Title + abstract reading for: all of
  $S_1\cup S_2$; all forward citations of HRY20 and Pates 2021; every pool record with `cy_score ≥ 2`;
  the top 10 records (by source order) of every keyword request. Every other record: title only, recorded by
  a published keyword rule. Flag for Level 2 if the record plausibly discusses composition constants for ≥3
  operators, tightness of composition constants, or SRG/Minkowski products of several sets.
- **Level 2.** Open full text located (arXiv, publisher OA, author page). Access level recorded.
- **Level 3** (`L3_CY_<firstauthor><year>.md`): every Level-2 source that actually discusses composition
  constants for ≥3 operators, tightness, or SRG Minkowski products; C1–C6 and threat.

### 3.6 CY15 constant — numerical heuristic

`cy_numeric_check.py` writes down $\varphi(\alpha)=\bigl(1+(\sum_i\alpha_i/(1-\alpha_i))^{-1}\bigr)^{-1}$ and
compares, for several $\eta$ vectors, $g_{\rm Box}(\eta)$ with the distance-from-1 bound implied by
$\varphi$-averagedness ($\max_{z\in D(1-\varphi,\varphi)}|1-z|=2\varphi$) under two preregistered
correspondences: (A) containment: $\alpha_u$ = the smallest $\alpha$ with $w([0,\arcsin\eta_u])\subseteq
D(1-\alpha,\alpha)$; (B) single-factor matching: $\alpha_u=\eta_u/2$ (so $2\alpha_u=\max|1-w|=\eta_u$).
It also checks, in the complex-scalar (planar normal) model, whether $\varphi$ is the supremum of the minimal
averagedness over products of boundary points of $D(1-\alpha_i,\alpha_i)$ for $m=3,4$. This is a heuristic
check, not a proof, and is reported as such.

## 4. Outputs

`followup_cy/`: `PROTOCOL_CY.md`, `queries_cy.json`, `anchors_cy_spec.json`, `FREEZE_CY.json`, `cy_round.py`,
`anchors_cy.json`, `SEARCH_LOG_CY.csv`, `raw/`, `forward_citations_cy.csv`, `cocitation_cy.csv`,
`pool_cy.csv`, `screening_cy_L1.csv`, `L3_CY_*.md`, `cy_numeric_check.py` (+ output), `CY_FOLLOWUP_REPORT.md`.
`CLAIM_NOVELTY_MATRIX_HET.md` is not edited; proposed changes go in the report.

## 5. Stop criterion

Stop when: (1) all five anchors are verified (or the failure is logged) and all forward-citation pages are
retrieved; (2) $S_1$, $S_2$ are computed; (3) all 22 queries are attempted on the three sources with the
supplemental pass logged; (4) Level 1 of §3.5 is complete; (5) every Level-2 flag is read in open full text
or marked `ABSTRACT_ONLY`/`PAYWALLED` with a manual action; (6) the report answers the priority question
with one of the §1 labels. Google Scholar and MathSciNet are manual only (listed, not executed).

## 9. Deviations log

| Date | Entry |
|---|---|
| 2026-09-14 (pre-freeze) | This follow-up uses a new wrapper `followup_cy/cy_round.py` instead of `het_round.py`, because it needs all-page forward citations, per-request backoff without global blocking, and three sources (no zbMATH). `harvest.py` functions are imported unchanged; round-1/HET scripts and outputs are not modified. |
| 2026-09-14 18:02 | Freeze taken (`FREEZE_CY.json`); no smoke tests before the freeze. |
| 2026-09-14 `POST_HOC` (anchor verification) | All five anchors verified (`anchors_cy.json`). OY02 DOI 10.1081/NFA-120003674 is correct (OpenAlex W2093425777 + Crossref). A second OpenAlex OY02 record (W7208263737, no DOI, 0 citations) was also matched. Pates 2021 has **no DOI** other than the arXiv DataCite DOI 10.48550/arxiv.2106.05650, which Crossref does not index (HTTP 404, expected for DataCite); verified through OpenAlex title + author + year. CY15 has journal and arXiv records (both used). |
| 2026-09-14 `POST_HOC` (preprint records; `cy_supplement.py oa_preprints`) | The exact-title search did not return the arXiv-version records of HRY20 and RHY22, so they were resolved by DataCite DOI. HRY20 arXiv record W2994365220 matched (0 citing works). The RHY22 arXiv record W6948001508 failed the automatic exact-title match because its title reads "Scaled Relative Graph: ..." (singular). Manual adjudication: same paper (authors Ryu, Hannah, Yin; 2019). It has 0 citing works in OpenAlex, so nothing was added. The same ID appears in `../quarantine/anchor_id_errors/` from round 1, where it had been used as a seed for a *different* intended paper. |
| 2026-09-14 `POST_HOC` (harvest scheduling; `cy_harvest_v2.py`) | In the frozen interleaved order, arXiv and Semantic Scholar returned HTTP 429 on the first query, even after backoff 30/60/120 s. The projected run time was about 3 h. An arXiv-API timing probe (one request, 18:13) and open-PDF downloads from arxiv.org for Level-3 reading (≈18:15) may have contributed to the arXiv limit. The frozen run was stopped after 4 logged keyword requests (openalex CY1-0 OK, arxiv CY1-0 BLOCKED, S2 CY1-0 BLOCKED, openalex CY1-1 OK). A new scheduler `cy_harvest_v2.py` then ran the remaining requests with the same queries, query functions and per-request backoff, but ordered by source (OpenAlex → Semantic Scholar → arXiv) with a circuit breaker: after 2 consecutive BLOCKED, one 600 s cool-down; after 2 more, the remaining requests of that source are logged `DEFERRED` (not attempted, never counted as zero). |
| 2026-09-14 `POST_HOC` (harvest outcome) | OpenAlex 22/22 OK. arXiv API and Semantic Scholar search: 4 queries BLOCKED each (5 requests incl. the stopped run) and 18 DEFERRED each, so **0/22 successful**. The preregistered supplemental `retry` pass was **not run**: a probe at 19:13 still returned HTTP 429 on both, and the frozen retry has no circuit breaker (≈3 h of blocked backoff). It is listed as a manual re-run. Stop criterion (3) is therefore met for OpenAlex only. |
| 2026-09-14 `POST_HOC` (Semantic Scholar citations; `cy_supplement.py s2_cites`) | OpenAlex citation counts for the SRG anchors were low (RHY22 19; HRY20 12). Semantic Scholar **citation** lists (a different endpoint from search) were retrieved for all five anchors: CY15 116, HRY20 18, RHY22 64, OY02 80, PAT21 32. Co-citation sets recomputed by normalized title (`cocitation_cy_s2.csv`). The 67 citing works not in `pool_cy.csv` were screened at Level 1 (rows tagged `[S2-only record, POST_HOC]`). This route found Yang–Chen–Qiu 2026 and Yang–Zhang–Chen–Qiu 2025 (arXiv only), which are threat 3 and 2. |
| 2026-09-14 `POST_HOC` (L3 DOI check; `cy_verify_l3.py`) | All 10 DOIs cited in L3 sheets resolved at Crossref with title and first-author match (`l3_dois_cy.json`). Volume/page details not confirmed by Crossref were removed from the sheets. |
| 2026-09-14 `POST_HOC` (web searches) | As in HET, targeted web searches (not part of the frozen harvest) located open full texts and checked for tightness statements: "tight averagedness constant composition of three or more averaged operators Combettes Yamada tight"; arXiv ids of Lee–Yi–Ryu, Giselsson–Moursi, Guthrie–Mallada, Bauschke–Bendit–Moursi. They surfaced Song–Wang 2025 (arXiv:2507.19533) and Combettes–Pesquet 2020 (SIMODS), which are outside the frozen pool and are flagged as such in their L3 sheets. |
| 2026-09-14 `POST_HOC` (access) | Full texts: arXiv PDFs (text via `pdftotext`) and one publisher OA PDF (ELA). The Guthrie–Mallada author-page PDF is behind a Cloudflare bot check and was **not** bypassed (ABSTRACT_ONLY). Level-1 judgments are recorded by `screening_cy_L1_build.py` (explicit overrides + published title rule), following the HET convention. |
