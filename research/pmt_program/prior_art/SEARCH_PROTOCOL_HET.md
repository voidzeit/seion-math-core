# PRIOR-ART-R-HET — search protocol (heterogeneous Theorem R)

```
VERSION:  het-v1
FROZEN:   2026-09-14, before the first query of this round (SHA-256 of this file, queries_het.json
          and het_round.py in FREEZE_HET.json)
SCOPE:    heterogeneous (nodewise-defect) extension of Theorem R for projected multilinear trees
          (see ../HETEROGENEOUS_THEOREM_R.md); round 1 = SEARCH_PROTOCOL.md (unchanged)
GLOBAL:   NOVELTY_NOT_ESTABLISHED (globally and for every claim of this round, regardless of outcome)
```

Deviations after freezing are allowed only as dated entries in §9 and are labelled `POST_HOC`
(with the new SHA-256 of any changed frozen file).

## 1. Model and claims under comparison

Projected multilinear tree (PMT): $F_v=\mu_v(F_{\rm children})$, $R_v=P_v\mu_v(R_{\rm children})$,
$P_v$ orthogonal projectors, $\lVert\mu_v\rVert\le M_v$, nodewise local projection defect
$\lVert(I-P_v)\mu_v(x)\rVert\le\rho_v\prod\lVert x_i\rVert$ on admissible inputs,
$\eta_v=\rho_v/M_v$, $\Lambda_T=(\prod_v M_v)(\prod_\ell\lVert z_\ell\rVert)$,
$E=\lVert P_rF_r-R_r\rVert$, $w(\theta)=\cos\theta\,e^{i\theta}$.

| ID | Claim | Note |
|---|---|---|
| H1 | Heterogeneous upper bound $E\le\Lambda_T\,G_{\rm box}(\eta)$, $G_{\rm box}(\eta)=\max_{\theta_u\in[0,\arcsin\eta_u]}\lvert1-\prod_u w(\theta_u)\rvert$ over non-root internal nodes $u$ | Lean-checked; novelty not established |
| H4 | Sharpness: $\sup E/\Lambda_T=G_{\rm box}(\eta)$, attained by a planar complex witness with independent per-node angles | Lean-checked |
| H2 | Placement independence: the sharp constant depends only on the multiset of non-root defects (not topology, arity, placement) | corollary of H1+H4; search targets weaker statements |
| H3 | **OPEN** capped-equal-angle reduction $G_{\rm box}(\eta)=\max_\tau\lvert1-\prod_u w(\min(\arcsin\eta_u,\tau))\rvert$ | separate; not proved |
| H-dev | Proof device: lifted spherical angle $\varphi(f,g)$ subadditive along multilinear contractions; uniform angle scaling by $\pi/\Theta$ when $\Theta=\sum\theta>\pi$ (no diagonal reduction) | auxiliary; round-1 R6 already `KNOWN_IN_SPECIAL_CASE` |

## 2. Status vocabulary and threat scale

Identical to `SEARCH_PROTOCOL.md` §2 (threat 0–5; per-claim labels `KNOWN` ·
`KNOWN_IN_SPECIAL_CASE` · `CLOSE_PRIOR_ART` · `NO_EQUIVALENT_FOUND` · `NOVELTY_NOT_ESTABLISHED`).
Additional preregistered calibration for this round:

- A bound with node-dependent tolerances that is additive / first-order / non-sharp is at most
  `CLOSE_PRIOR_ART` for H1 (threat ≤3) and must be cited.
- Threat 4–5 only if a source states an equivalent **sharp** heterogeneous constant, or placement
  independence of a sharp constant, for this model or a model that trivially contains it.
- Scalar results on $\max\lvert1-\prod z_i\rvert$ over heterogeneous arcs/disks count for H1/H4 only
  through the scalar step; they are threat ≤3 unless they also give the operator-level statement.

## 3. Search families and queries

Exact queries: `queries_het.json` (families O1–O6, 30 queries, 5 per family, English).

| Family | Topic | Claims |
|---|---|---|
| O1 | heterogeneous / nodewise local error bounds in HT, TT/MPS, TTN | H1, H2, H4 |
| O2 | nonuniform truncation tolerances; tolerance / error-budget allocation | H1, H2, H3 |
| O3 | nodewise error budgets in quantum simulation / TN contraction; fidelity products | H1, H2, H4 |
| O4 | heterogeneous projection defects; products of near-projections, averaged-operator compositions, sectorial products | H1, H4, H2 |
| O5 | box-constrained products of complex numbers; Minkowski products of arcs/disks; water-filling | H1, H4, H3 |
| O6 | local tolerance allocation under multiplicative fidelity; angle budgets; hybrid argument with nonuniform steps | H1, H2, H3 |

## 4. Sources

Same as round 1 (`SEARCH_PROTOCOL.md` §4), same code paths (`harvest.py` imported unchanged through
`het_round.py`, which only redirects file paths): OpenAlex (primary), zbMATH Open (HTTP 404 = no
results, logged `OK`), arXiv API and Semantic Scholar (HTTP 429/503/timeout: one retry, then block
for the rest of the run; logged). **Preregistered addition:** one supplemental retry pass
(`het_round.py retry`) for every arXiv / Semantic Scholar request that was `SKIPPED` or `ERROR`,
with backoff 30/60/120 s; still-blocked requests are logged `SKIPPED`. Crossref for DOI validation
only. MathSciNet and Google Scholar are manual (§8).

Records: `SEARCH_LOG_HET.csv` (one row per request), raw responses in `raw/het/` (not edited).

## 5. Screening (rules identical to round 1)

0. **Level 0.** Dedup and rubric of `harvest.py`/`merge_pool.py` unchanged (tiers T1/T2/T3; ordering
   only, never exclusion). `pool_het.csv` adds `seen_in_round1` (key or normalized title in round-1
   `pool.csv`) and an informational `het_score` (heterogeneity keywords; ordering inside a tier only).
1. **Level 1** (`screening/het_level1.csv`: key, threat, claims, reason, level2). T1/T2 and every
   row with `het_score ≥ 2` by title+abstract; T3 by title. Round-1-seen rows are re-screened against
   H-claims (their round-1 threat concerned R-claims).
2. **Level 2** (`screening/het_level2.csv`: key, threat_L2, access, theorem_location,
   claims_affected, verdict, level3). Every L1 threat ≥3, plus the round-1 carry-over list: sources
   with round-1 threat ≥2 that contain node-dependent parameters (Ceruti–Lubich–Sulz 2023;
   Bachmayr–Nouy–Schneider 2021; Zhang–Solomonik 2020; Grasedyck 2010; Farouki–Pottmann 2002;
   Huang–Ryu–Yin 2020; Ryu–Hannah–Yin 2022; BBBV 1997) re-read for heterogeneous statements.
   Full text where open access; otherwise `ABSTRACT_ONLY`.
3. **Level 3** (`theorem_comparisons/L3_HET_*.md`, same template as round 1): every source with
   threat ≥3 after Level 2, and the closest 5–8 overall. Verdicts adjudicated in
   `l3_verdicts_het.json` (same schema as `l3_verdicts.json`).

## 6. Anchors and snowballing

After Level 1, 4–8 anchors (`anchors_het.json`) are chosen from the closest sources across O1–O6
(at least one of O1/O2, O3/O6, O4, O5). **Each anchor DOI is resolved (OpenAlex + Crossref) and the
returned title/authors/year are checked against the intended paper before snowballing**; failures
are logged and corrected before the run. One hop: backward (referenced works) + forward (top 50
citing works by citation count) via `snowball.py` (through `het_round.py snowball`). New candidates go
through §5.

## 7. Outputs

`pool_het.csv` · `screening/het_level1.csv`, `screening/het_level2.csv` · `theorem_comparisons/L3_HET_*.md`
· `l3_verdicts_het.json` · `PRIOR_ART_MATRIX_HET.csv` · `CLAIM_NOVELTY_MATRIX_HET.md` ·
`bibliography/references_het.bib` (new file; round-1 bib untouched; `NO_DOI` flagged) · README
append-only section. Round-1 files are not modified; superseded or contaminated outputs go to
`quarantine/`.

## 8. Stop criterion for this mini-round

This is a targeted round, not a saturation round. It ends when: (1) all 30 queries were attempted on
OpenAlex and zbMATH and arXiv/S2 retry passes are logged; (2) one snowball hop from 4–8 verified
anchors is done; (3) every T1/T2 and `het_score ≥ 2` row is screened at Level 1 by abstract and every
other row by title; (4) every threat ≥3 source is read at Level 3; (5) every claim H1/H2/H4/H3 has a
documented status. Manual MathSciNet / Google Scholar steps are listed, not executed. The global label
stays `NOVELTY_NOT_ESTABLISHED`.

## 9. Deviations log

| Date | Entry |
|---|---|
| 2026-09-14 (pre-freeze) | Level-3 threshold for this round is threat ≥3 plus the closest 5–8 (round 1: threat ≥4), as instructed for the mini-round. |
| 2026-09-14 17:05 | Freeze taken (`FREEZE_HET.json`). No smoke tests were run before the freeze. |
| 2026-09-14 `POST_HOC` (coverage) | The arXiv API returned HTTP 429 on the first harvest request and 503 in the retry pass. Semantic Scholar returned 429 in both passes. Only 1 of 30 Semantic Scholar queries succeeded (10 records), and **no arXiv API records** were obtained. Preprints are covered only through OpenAlex. zbMATH Open returned HTTP 404 ("no results") for **all 30** multi-word queries, so zbMATH coverage of this round is nil. Manual follow-up is listed in `CLAIM_NOVELTY_MATRIX_HET.md` §6. |
| 2026-09-14 `POST_HOC` (Level 1 recording) | Level-1 judgments are recorded by `screening/het_level1_build.py`. Explicit overrides (threat ≥2 and checked borderline titles) are matched by normalized title. Every other row gets 0/1 from a published keyword rule that encodes the screener's title reading ("broad field" → 1, else 0). Three overrides were corrected after abstract checks (Ballani–Grasedyck 2014 → 1; Banjac–Goulart 2018 → 1; Haberstich et al. reason text). Two substring matches that hit wrong titles were fixed by exact-title matching before the file was finalized. |
| 2026-09-14 `POST_HOC` (L2/L3 access) | Full texts were located through arXiv PDFs and author pages (Palomar's page for PF05). Two web searches were used to locate full texts and to check the tightness status of the Combettes–Yamada constant. They surfaced two Zeno-dragging papers (Lewalle et al. 2024; Zhang et al. 2025), which are recorded in `l3_verdicts_het.json` at threat 1 and flagged as outside the frozen harvest. Vannieuwenhoven et al. 2012 (round-1 pool) and round-1 Level-3 readings (Grasedyck, Huang–Ryu–Yin, Ryu–Hannah–Yin, Farouki–Pottmann, Oikhberg, Dohotaru–Høyer) were reused, not re-harvested. The HAL PDF of Zniyed–Boyer is behind a bot check; it was not bypassed. |
| 2026-09-14 `POST_HOC` (anchors) | Seven anchors were verified via OpenAlex and Crossref (title, authors, year all match) before the snowball; see `anchors_het.json`. No identifier errors were found. |
