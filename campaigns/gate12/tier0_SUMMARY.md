# Tier 0 screening — summary (NOT confirmatory)

Executed on branch `campaign/gate12-closeout`, real FB15K-237/WN18RR data, real RTX PRO 5000
Blackwell GPU (A0) / CPU (A3, per the logged deviation in `preregistration.md` §11). All 8 runs
completed; raw artifacts in `campaigns/gate12/tier0/{A0,A3}/<dataset>_seed<N>/` (gitignored,
local only — this file plus `tier0_results.json` are the committed compact evidence).

## Base-expert selection (before A0/A3)

1-epoch pass, FB15K-237, dim=64, eval_max_queries=200, seed=1: **TuckER** wins on valid MRR
(0.2534) over ComplEx (0.2210), DistMult (0.2195), CP (0.2092). `best_base = tucker` for A0/A3.
Full numbers: `tier0_base_selection_result.json`.

## A0 (TuckER only, full dataset) vs A3 (TuckER+path+seion, 5,000-triple subsample)

| Config | Dataset | Seed | Test MRR | Valid MRR | Test Hits@1 | Test Hits@10 | Head MRR | Tail MRR | Wall (s) |
|---|---|---|---|---|---|---|---|---|---|
| A0 | FB15K-237 | 1 | 0.2795 | 0.2912 | 0.1917 | 0.4450 | 0.1929 | 0.3662 | 78.2 |
| A0 | FB15K-237 | 2 | 0.2774 | 0.2895 | 0.1867 | 0.4550 | 0.1876 | 0.3673 | 84.9 |
| A0 | WN18RR    | 1 | 0.4414 | 0.4140 | 0.4233 | 0.4767 | 0.4209 | 0.4620 | 22.3 |
| A0 | WN18RR    | 2 | 0.4235 | 0.4073 | 0.3933 | 0.4700 | 0.4219 | 0.4252 | 24.3 |
| A3 | FB15K-237 | 1 | 0.0095 | 0.0119 | 0.0050 | 0.0250 | 0.0015 | 0.0175 | 217.2 |
| A3 | FB15K-237 | 2 | 0.0229 | 0.0090 | 0.0200 | 0.0300 | 0.0025 | 0.0434 | 214.6 |
| A3 | WN18RR    | 1 | 0.0018 | 0.0034 | 0.0000 | 0.0050 | 0.0021 | 0.0016 | 53.4 |
| A3 | WN18RR    | 2 | 0.0030 | 0.0138 | 0.0000 | 0.0150 | 0.0043 | 0.0016 | 53.4 |

Full machine-readable version: `tier0_results.json`.

## Honest interpretation

**A0 (TuckER alone) clearly learns real structure** on both full datasets, at levels broadly
consistent with published TuckER numbers for a 5-epoch, dim-64, screening-scale run (no
hyperparameter search performed — this is not a tuned reproduction).

**A3's near-random MRR (0.002–0.023) is NOT evidence that the path/seionic branches hurt
performance.** It is confounded, by design (a logged, pre-result deviation), with:
1. A3 trained on a ~5,000-triple subsample (1.8% of FB15K-237, 5.8% of WN18RR) — far too little
   data for the shared TuckER base alone to learn useful embeddings, independent of any
   experimental branch.
2. A3 ran 3 epochs vs. A0's 5.
3. Per `negative_controls_results.json` and `09_negative_results.tex` §"gate did not open", the
   path/seionic branches' near-zero-init gates showed negligible measured influence even after 40
   epochs in a separate synthetic-graph run — so even if A3 had trained on full data, there is an
   open question about whether these branches would have had any measurable effect within a
   3–5 epoch budget at all.

**No causal conclusion about the path reasoner, seionic branch, or any other architectural
component follows from this comparison.** A clean version of this experiment would run A0 and A3
on the *same* full-scale training data for the *same* number of epochs — not attempted this
campaign because the path reasoner does not scale to full-dataset batches within this session's
compute budget (§09 "path reasoner does not scale").

## What this Tier 0 pass DOES establish

- The full architecture (TuckER + path reasoner + seionic branch, all five manifest files, the
  reciprocal evaluator, checkpointing) executes correctly end-to-end on real FB15K-237 and WN18RR
  data, produces finite metrics, and is measurably different in wall-clock cost from the base
  expert alone (as expected — the path reasoner's per-sample BFS is the dominant cost).
- A0-alone reproduces the qualitative expectation that TuckER learns real, non-trivial structure
  on both datasets at screening scale.
- The specific numeric gap between A0 and A3 in this pass is not informative about architecture;
  it is informative about the compute-budget deviation's cost, which is exactly why that deviation
  is logged and this interpretation is spelled out rather than left implicit.
