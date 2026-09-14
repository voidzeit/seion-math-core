# Gate 12 campaign preregistration

- **Campaign ID:** `gate12-closeout-2026-08-01`
- **Branch:** `campaign/gate12-closeout`
- **Canonical starting commit:** `6af3c35271ae2ffab41ecba2aad098d1988fdc0c`
- **Frozen:** before any confirmatory result is generated or interpreted. This
  file is committed before Phase C begins. Any deviation from this
  protocol is logged in the "Deviations log" section at the bottom with a
  timestamp and reason, never silently.

## 0. Honest compute-budget declaration (read this first)

This campaign runs inside a single interactive agent session with a wall-
clock budget of hours, not days. The full protocol below (§7-§8) — 3-seed
screening across 13 causal ablations × up to 5 baselines × 5 kernel
controls × 2-5 datasets, followed by 5-seed confirmatory runs — is a
multi-day-to-multi-week compute program on this hardware (single RTX PRO
5000 Blackwell, 24GB, one heavy run at a time per the hardware-safety
rule). It is **not** executed to completion in this campaign.

Per the mission's own priority order (mandate §X), this campaign executes,
in order, as much of the following as the session's compute budget
allows, and documents the rest as `OPEN` with the exact commands needed
to run it later:

1. CI and full test closure — **executed**.
2. Exact evaluator and artifact integrity — **executed** (audit + fixes).
3. Learned selector implementation/tests — **executed**.
4. Primary FB15K-237 screening — **executed at reduced scale** (see §9,
   "Tier 0"), not the full preregistered 3-seed/13-ablation grid.
5. FB15K-237 confirmatory finalists + matched baselines (5 seeds) — **not
   executed**; `OPEN`.
6. WN18RR replication — **executed at reduced scale** (Tier 0 only).
7. Projection/rank-controller Pareto study — **not executed**; `OPEN`.
8. Certification coverage study — **instrumentation executed and unit
   tested**; a coverage study on a real dataset is **not executed**;
   `OPEN`.
9. E8 matched-control block — **implemented and unit-tested**; the full
   statistical comparison against controls on a benchmark dataset is
   **not executed**; `OPEN`.
10. Exploratory transfer datasets (CoDEx-M, YAGO3-10, ogbl-biokg) — **not
    executed**; `OPEN`.
11. Full PDF package — **executed**, with every section that depends on
    an un-executed experiment stating so explicitly rather than
    inventing numbers.

No result in this campaign is labeled `CONFIRMATORY`. Everything executed
is labeled `EXPLORATORY` or `SCREENING` (Tier 0, §9) unless it is a
deterministic engineering check (tests, CI, negative controls), which
carry their own PASS/FAIL status independent of the statistical protocol.

## 1. Primary and secondary hypotheses

**H1 (primary, architecture).** Adding the path reasoner and/or seionic
ternary branch to a strong reciprocal base expert (A0 -> A3 in the causal
ladder, §8) improves filtered validation MRR on FB15K-237 relative to the
matched base-expert-only model, at equal or better VRAM/latency budget.

**H2 (secondary, projection).** Orthogonal projection (A3 -> A4) with an
adaptive rank controller (A4 -> A6) recovers most of the unprojected
model's MRR at a materially reduced rank budget.

**H3 (secondary, selector).** The learned selector (A3 -> A7, A6 -> A8)
matches or exceeds fixed budgeted-BFS path coverage and downstream MRR at
equal edge-visit budget.

**H4 (secondary, E8 causal attribution).** `E8_exact`'s specific
algebraic structure produces a measured MRR gain that `random_scale_matched`
does not, under matched parameter count, kernel norm, optimizer, schedule,
and seeds.

**Falsification criteria are declared for each hypothesis in §8/§C3 of
the mandate this preregistration implements; a hypothesis not supported
by the confirmatory protocol is reported as a negative result, not
omitted.**

## 2. Datasets and hashes

| Dataset | Split | SHA-256 |
|---|---|---|
| FB15K-237 | train | `6e4c2782169af21e9743f3b1d200886f5d595bf6bc504ec1351720949c5cdfae` |
| FB15K-237 | valid | `cf6309010852f6a8d47a45df830a426415d1ee6f7a3970a8376ff1fb81db4a5c` |
| FB15K-237 | test  | `5711cf41623ceb4eacc50eb6108a3ca6565c7492e3caaf82a3e355cc660d1574` |
| WN18RR    | train | `038612e783c215ee5f3ca9fbfca27b8d0739be1028fe4ee7c174aecf0b83d5df` |
| WN18RR    | valid | `453ce7202afa58094a04d2b1560ee2b02660f1c260b32ce6651c8ccedd1028ab` |
| WN18RR    | test  | `0383bceaaa1096cf3c03ec021ed0048068e2355dbfc0239b292cefdac821cec5` |

Computed via `sha256sum data/<name>/{train,valid,test}.txt` on the campaign
branch. CoDEx-M, DB100K+, and YAGO3-10 are present under `data/` but are
exploratory-transfer datasets (§0 item 10) and are out of scope for this
campaign's executed portion.

## 3. Baseline families (contract §XI.1)

`DistMult`, `ComplEx` (reciprocal), `CP` (reciprocal, asymmetric
head/tail tables), `TuckER` — all four already implemented in
`seion_kgr/scorers.py` and exercised in the canonical commit's smoke
runs. A `path_reasoner_standard_message` baseline (path reasoning with a
plain linear/bilinear message instead of the CP ternary law) is declared
in the causal ladder as `A1`; it reuses `PathReasoner` with
`CPTernaryLaw` swapped for a bilinear message function — **not yet
implemented** as of this preregistration; if not implemented before
Phase C executes, `A1` is skipped and logged as a deviation, not
silently merged into `A3`.

No internal implementation is named after NBFNet or C-MPNN. The path
reasoner in `seion_kgr/reasoner.py` is a budgeted-BFS query-conditioned
message passer with a fixed-random neighbor selector; any comparison
point using that architecture family is named `nbf_style_baseline` per
the mandate's naming rule, and only if actually implemented to a
faithful standard — otherwise it is omitted, not approximated under a
borrowed name.

## 4. Architecture / causal ablation matrix (mandate §C3, verbatim)

`A0`-`A12` and `K0`-`K4` as specified in the mandate. Recorded here
without modification so later evidence can be checked against an
unedited frozen list:

```text
A0  best_base
A1  best_base + path_reasoner
A2  best_base + seionic_scalar
A3  best_base + path_reasoner + seionic_message
A4  A3 + orthogonal_projection
A5  A4 + adaptive_rank_local_greedy
A6  A4 + adaptive_rank_hybrid_controller
A7  A3 + learned_selector
A8  A6 + learned_selector
A9  A8 + closure_curriculum
A10 A9 + associator_curriculum
A11 A10 + FI_curriculum
A12 A8 + relation_metaencoder

K0 zero_kernel
K1 random_scale_matched
K2 permuted_indices
K3 sign_shuffled
K4 E8_exact
```

`best_base` = whichever of DistMult/ComplEx/CP/TuckER has the best
screening-tier validation MRR on the given dataset (selected before any
ladder rung above `A0` is run, per the mandate's finalist-selection
rule).

## 5. Screening and confirmatory seed rules

- **Screening (full protocol, not executed this campaign):** 3 seeds
  (`{1,2,3}`), reduced epoch budget, validation-only selection, no test
  inspection.
- **Confirmatory (full protocol, not executed this campaign):** 5
  independent seeds (`{1,2,3,4,5}`) for each finalist and its matched
  baseline on FB15K-237; 5 seeds on WN18RR for the reduced finalist set
  if budget permits.
- **Tier 0 (executed this campaign, §9):** 2 seeds (`{1,2}`), sharply
  reduced epoch/entity-block budget, a 2-point reduced ladder
  (`A0`, `A3`) on both datasets. Labeled `SCREENING (reduced)` in every
  artifact — never `CONFIRMATORY`.

## 6. Metrics

Exactly the metric list in mandate §C6 (prediction, efficiency,
compression/projection, certification, geometry), computed by
`seion_kgr/evaluate.py` (prediction), `seion_kgr/reproducibility.py`
manifests (efficiency), `seion_kgr/rank_controller.py` +
`seion_kgr/projection.py` (compression), `seion_kgr/certification.py`
(certification, once implemented in Phase B4), and
`seion_kgr/geometry.py` diagnostics (geometry). Geometry metrics are
reported separately per relation/layer, never merged into a master
score, per mandate §C6's explicit prohibition.

## 7. Early stopping and selection rule

Early stopping: no improvement in validation combined MRR for
`early_stop_patience` consecutive eval points (not yet a CLI flag in
`seion_kgr/train.py` as of the canonical commit — added in Phase B5 if
time permits; if not added, early stopping is disabled and epoch budget
is the sole stopping rule, logged as a deviation).

Confirmatory finalist selection (mandate §C4), applied only if/when the
full screening tier is actually run:
1. valid MRR improvement or Pareto efficiency over the matched baseline;
2. no severe head/tail collapse (ratio of head MRR to tail MRR within
   [0.3, 3.0], chosen conservatively given `SEION_V25_DESIGN.md`'s
   documented severe collapse case of ~0.28);
3. numerical stability (no NaN/Inf across any screening seed);
4. acceptable runtime/VRAM (fits the single-heavy-run 24GB budget);
5. complete artifacts (full manifest set, §E1 of the mandate);
6. no failed leakage or reproducibility gate (Phase D negative controls
   must fail as expected; Phase B5 evaluator/reference-parity checks
   must pass).

## 8. Statistical tests (full protocol, applied only to confirmatory-tier data if/when collected)

Paired bootstrap CI (10,000 resamples) on per-query metric differences
between a finalist and its matched baseline, sharing the same seed and
data hashes. Effect size via Cohen's d on the bootstrap distribution.
Holm-Bonferroni correction across the preregistered family of pairwise
comparisons for a given dataset. Confirmatory p-values are reported only
for the preregistered comparisons; anything computed post hoc is labeled
`EXPLORATORY, NOT CONFIRMATORY` regardless of the p-value obtained.

## 9. Tier 0 — what is actually executed in this campaign

Given §0's compute declaration, Tier 0 is the honest, bounded substitute
for §5-§8 that this campaign actually runs and reports:

- Datasets: FB15K-237, WN18RR (both already hash-verified in §2).
- Ladder points: `A0` (best of the 4 base experts by a short screening
  pass) and `A3` (`A0` + path reasoner + seionic ternary branch, no
  projection/rank controller/curricula/selector/metaencoder — those are
  unit-tested in Phase B but not benchmarked at dataset scale here).
- Seeds: `{1, 2}` — two, not three, and explicitly insufficient for any
  variance claim; per-seed values are reported individually, never
  reduced to "mean ± std" as if that were a confirmatory statistic.
- Epoch budget, batch size, `entity_block_eval`, and `eval_subset` are
  fixed in advance in `campaigns/gate12/tier0_config.json` before Tier 0
  execution begins, and are not changed after seeing any result.
- Output: `campaigns/gate12/tier0/*` run directories with full manifests,
  and `campaigns/gate12/tier0/SUMMARY.md` reporting exactly what ran,
  what the metrics were, and explicitly restating that this is not a
  Gate 12 confirmatory result.

## 10. Failure criteria

The campaign fails to support H1-H4 (reported as negative results, not
omitted) if: Tier 0 (or later, full-protocol confirmatory data) shows no
MRR improvement from `A0` to `A3` beyond noise visible even at n=2 seeds
(e.g., ladder direction inconsistent between the two seeds); if any
Phase D negative control fails to degrade as expected (investigated
before any other conclusion is accepted, per mandate §D1); or if
`E8_exact` does not outperform `random_scale_matched` in whatever
E8-vs-control evidence is actually collected (Phase B3 unit-level, or a
future full campaign).

## 11. Deviations log

| Timestamp (UTC) | Deviation | Reason |
|---|---|---|
| campaign start | Full 3-seed screening / 5-seed confirmatory protocol (§5, full) not executed; replaced by Tier 0 (§9) | Single-session compute budget; declared in §0 before any Phase C execution, per mandate §X's explicit fallback instruction |
| Phase C execution, before any A3 result was seen | A3 (path+seion enabled) Tier 0 runs use a SUBSAMPLED training set (first 5,000 triples of each dataset's train split, `--eval_max_queries` capped), not the full dataset §9 originally specified. A0 (base-expert-only) runs remain full-scale. | A live timing probe (A3, full WN18RR, batch_size=256, 1 epoch) ran 8+ minutes without completing before being stopped — the path reasoner's per-sample Python-loop BFS does not scale to full-dataset batches within a single session's compute budget at the settings tested. This is a real, measured performance finding (recorded in 09_negative_results.tex and the architecture doc), not a hidden scope cut. Decided and logged BEFORE any A3 subsampled-run result was generated. |
