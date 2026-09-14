# Leakage finding: evaluation filters were shaping the training gradient

Date: 2026-08-10. Branch `campaign/gate13-closeout`.
Status: **ESTABLISHED BY CODE PATH AND BY CONTROLLED MEASUREMENT.**

## Summary

Two SRATM trainers reused evaluation-time known-positive filter tables to mask
hard negatives during training. Masking a candidate sets its score to `-inf`, so
it can never be selected as a negative, so the training objective never pushes
it down. Applied to a *held-out* split's gold entities, that is leakage: the
model is told, for each query, which entity not to suppress.

* The sealed trainer leaked **VALID** membership.
* The historical trainer `train_spectral_mixture.py` leaked **VALID and TEST**
  membership.

This is not a data-loading bug and no forbidden file access occurs. The sealed
runtime sentinel correctly reported zero forbidden TEST accesses throughout,
because the sealed trainer genuinely never opened TEST. The leak is in what the
*filter tables are used for*, which no file-access audit can detect.

## Mechanism

```
build_filters(train, valid, test)      # data.py:92-104  -> tails_of_hr / heads_of_rt
        |
        v
mine_full_entity_hard_negatives(..., kg, ...)   # masks kg.tails_of_hr to -inf
        |
        v
negatives = model.score_tail_candidates(h, r, hard_ids)   # gold never appears
```

Sealed path: `load_train_valid_only` calls `build_filters(train_orig, valid, [])`
(`sratm_certified_compression.py:193`), and `train_sratm_sealed.py` passed that
`kg` straight to the miner.

Historical path: `train_spectral_mixture.py:82` *requires* `--test`; line 83
calls `load_knowledge_graph(train, valid, test)`, whose
`build_filters(train_orig, valid, test)` (`data.py:115`) places TEST triples in
the tables; line 162 passes that same `kg` to the miner.

By construction every held-out triple `(h,r,t)` inserts `t` into `tails[(h,r)]`,
so **100%** of held-out golds are exempted for their own query. Establishing this
for TEST requires no TEST read — it follows from the code.

## Magnitude, measured

FB15K-237 structural counts (TRAIN+VALID only, no TEST read):

| quantity | value |
|---|---|
| VALID triples | 17,535 |
| whose gold is absent from TRAIN for its own `(h,r)` | 17,535 (100.0%) |
| VALID query keys that also occur in TRAIN | 7,930 (65.7%) |
| VALID-only tails attached to actively-trained query keys | 13,341 |

Controlled A/B — identical architecture, seed 42, batch 512, candidate block
14541, hard_k 128, cosine schedule, identical 2,048-row VALID evaluation subset,
matched wall clock:

| run | mining filter | step | elapsed | VALID MRR |
|---|---|---|---:|---:|
| `SEALED_SOTA_V1_..._2H` | TRAIN+VALID (leaking) | 1702 | 603 s | **0.51818** |
| `SEALED_SOTA_V2_..._NOLEAK` | TRAIN-only (fixed) | 1678 | 603 s | **0.20571** |

**The leak was worth +0.312 MRR — it inflated the metric by ~2.5x**, i.e. about
60% of the reported number was artefact. The only changed variable is the filter
used for mining.

## Independent confirmation: the VALID-TEST gap collapsed

After the fix, the V2 checkpoint (`checkpoint_best.pt`, step 1678, SHA256
`6dda0c1b…20138`, selected on VALID only) was measured under the preregistered
single-shot TEST protocol:

| split | queries | MRR | H@1 | H@3 | H@10 |
|---|---:|---:|---:|---:|---:|
| VALID (full, TRAIN+VALID filters) | 35,070 | 0.19610 | 0.12652 | 0.21526 | 0.33972 |
| TEST (standard filtered) | 40,932 | 0.19764 | 0.12802 | 0.21536 | 0.34022 |

**Gap = +0.0015.** A clean protocol produces a held-out split that behaves like
the selection split; a leaking one does not. The leaking V1 configuration
reported VALID `0.51818` against a TEST reality of roughly `0.20` — that ~0.32
discrepancy *was* the leak, and it is now gone. The VALID-TEST gap is therefore
the practical detector for this defect class, and it is recommended as a
standing control.

## TTN track re-run under `train_only` — 2026-08-11

Eleven scientific TTN runs (headline D32, D128, and the nine-seed spread) were
reproduced with identical hyperparameters and only the negative filter changed,
so each pairs directly against its existing leaking counterpart.
Script: `scripts/rerun_ttn_track_noleak.ps1`.

**Certificates survive the fix, exactly as predicted.** Hold fraction `1.000`,
violation rate `0.000`, zero false certificates — in all eleven no-leak runs and
in all eleven leaking baselines. This confirms the scoping stated above: a
certificate is a bound on the tensor it was computed from, and does not depend
on how that tensor was trained.

**Predictive metrics barely moved** (headline D32, full filtered TEST, 40,932
queries):

| metric | leaking | no-leak | delta |
|---|---:|---:|---:|
| MRR | 0.06458 | 0.06602 | +0.00144 |
| Hits@1 | 0.01825 | 0.03061 | +0.01236 |
| Hits@3 | 0.07476 | 0.06601 | −0.00875 |
| Hits@10 | 0.13679 | 0.12384 | −0.01295 |
| mean rank | 676.48 | 765.31 | +88.83 |

Training loss rose from mean `0.11562` (sd `0.01296`) to `0.15431` (sd `0.05015`)
across the nine seeds — the task is genuinely harder once held-out golds can be
sampled — but that difficulty does not translate into a metric collapse.

**Why the leak cost SRATM 0.31 MRR and TTN almost nothing.** The size of this
defect scales with how aggressively the trainer mines negatives. SRATM ranks all
14,541 entities and takes the 128 hardest, so shielding the gold hands it the
single most valuable candidate on every step. TTN draws 32 uniform random
negatives at D32, where the gold is unlikely to be drawn at all and the model is
too weak (TEST MRR ≈ 0.065) to exploit the exemption. **The leak is dangerous in
proportion to the strength of the negative miner**, which is the opposite of
where intuition puts it: the more sophisticated the training loop, the worse the
contamination.

Practical consequence: the TTN allocator and certified-compression conclusions
stand. The SRATM/discovery predictive numbers do not.

(The original `TTN_FB15K237_TTN_V2_D128_E10_2026-08-09` directory holds a
checkpoint and configs but no `ttn_results.json`, so the D128 pair has no
baseline to compare against; the no-leak D128 run is recorded on its own.)

## Consequence for the historical `MRR = 0.6116475`

The repository recorded that number as `HISTORICAL_UNRECONCILED` with TEST usage
`UNKNOWN / NOT_ESTABLISHED`, and correctly refused to use it. That status can now
be sharpened: the historical trainer provably consumed TEST and provably used it
to mask training negatives. Combined with the measured inflation above, this is a
sufficient mechanical explanation for a value far above published FB15K-237 SOTA
(~0.33–0.37 MRR). The number should be treated as **leakage-explained**, not
merely unreconciled, and remains unusable as a baseline or target.

This also means the earlier campaign's honest instinct was right for a reason it
had not yet identified.

## Fix

`train_sratm_sealed.py` gains `--mining-filter {train_valid, train_only}`.
Default stays `train_valid` so previously executed runs remain reproducible and
are not silently reinterpreted; `train_only` is the non-leaking setting and is
what the V2 campaign uses. `_train_only_filter_view` rebuilds the tables from
original-relation TRAIN rows alone and shares every other field. Evaluation is
untouched and still uses TRAIN+VALID filters, which is the correct standard
protocol — filtering at evaluation time is not the defect.

Pinned by `tests/kgr/test_mining_filter_no_valid_leak.py` (4 tests), including
that the shipped tables *do* exempt the VALID gold, that the view stops doing so
while still masking genuine TRAIN positives, that no field is mutated in place,
and that reciprocal rows are excluded when rebuilding.

## Scope: this is the whole KGE training surface, not one trainer

Every trainer below loads via `load_knowledge_graph(train, valid, test)` — so its
`tails_of_hr`/`heads_of_rt` contain VALID **and TEST** — and then uses those same
tables to build or mask training negatives. `sample_negatives`
(`data.py:160-182`) excludes `kg.tails_of_hr` from the sampled pool, so it
carries the defect exactly like the full-entity miner does.

| path | negative route | status |
|---|---|---|
| `train_spectral_mixture.py:162` | `mine_full_entity_hard_negatives` | leaks VALID+TEST |
| `train_sratm_sealed.py` | `mine_full_entity_hard_negatives` | leaked VALID; **fixed** |
| `train.py:560` (tail) | `sample_negatives` | leaks VALID+TEST |
| `train.py:561` (head) | `sample_negatives` with reciprocal ids | tables are keyed on original relations only, so the lookup misses and these negatives are effectively unfiltered — the in-code comment already says "unfiltered" |
| `run_ttn_fb15k237.py:115` | `sample_negatives` | leaks VALID+TEST — this is the TTN track behind `runs/TTN_FB15K237_*` |
| `ttn_training_canary.py:122` | `sample_negatives` | leaks VALID+TEST |
| `train_sota_discovery.py:96` | `sample_negatives` builds the pool, then `mine_hard_negatives` without `forbidden=` | pool already excludes held-out golds, so leaks VALID+TEST |

A seventh instance lives outside the package: **`seion_train_v25.py`** carries its
own private copy of `build_filters(train_orig, valid, test)` (line 381) and uses
those tables as `tail_forbidden`/`head_forbidden` in its own `sample_negatives`
(line 474), so it leaks whenever `--neg_mode filtered` is active or the Bernoulli
path selects the filtered branch. `seion_kgr_v26_train.py` is only a thin wrapper
over `seion_kgr/train.py` and inherits that module's fix.

### Status after this pass — all seven fixed

| trainer | flag | default |
|---|---|---|
| `train_sratm_sealed.py` | `--mining-filter train_only` | `train_valid` |
| `train_spectral_mixture.py` | `--negative-filter train_only` | `train_valid_test` |
| `train.py` (and the v26 wrapper) | `--negative-filter train_only` | `train_valid_test` |
| `run_ttn_fb15k237.py` | `--negative-filter train_only` | `train_valid_test` |
| `ttn_training_canary.py` | `--negative-filter train_only` | `train_valid_test` |
| `train_sota_discovery.py` | `--negative-filter train_only` | `train_valid_test` |
| `seion_train_v25.py` | `--negative_filter train_only` | `train_valid_test` |

Defaults deliberately preserve the historical behaviour so previously executed
runs stay reproducible and are not silently reinterpreted. Switching the default
is a separate decision that should be taken explicitly. The shared implementation
is `data.train_only_filter_view`; both filter modes were smoke-tested end to end
for `ttn_training_canary.py` and `seion_train_v25.py`.

### Registered runs implicated

Resolved from each run's recorded command, not from directory names:

* **29 run directories from `run_ttn_fb15k237`** — the entire `runs/TTN_FB15K237_*`
  track, including the certified/allocation and normed-E10 runs;
* `runs/SPECTRAL_MIXTURE_*` and `runs/SRATM_*_DISCOVERY_*` from
  `train_spectral_mixture.py`, which includes the run holding the historical
  `audit_step4600.json` with `MRR=0.6116475`;
* `runs/V25_FB237_*` (6 directories) from `seion_train_v25.py`;
* `runs/KGR_V26_*` from `seion_kgr/train.py` via the wrapper;
* `runs/SRATM_FB15K237_SEALED_FROM_ZERO_*` (VALID-only leak) and
  `runs/SEALED_SOTA_V1_*`.

**Precise scope of the damage.** What is invalidated is every *predictive-quality*
number (MRR/Hits/mean rank) from those runs, and any claim that a conclusion
transfers to a correctly-trained model. What is **not** automatically invalidated
is the mathematics applied *to* those checkpoints: a compression certificate, a
rank/spectrum diagnostic, or a score-error bound is a statement about the tensor
it was computed on, and remains true of that tensor regardless of how it was
trained. The TTN allocator and certified-compression work therefore needs
re-basing on a clean checkpoint before its *empirical* conclusions are quoted,
but its certificates were not shown to be wrong.

Note the defect is *not* "filtering negatives is wrong". Filtering against TRAIN
is standard and correct, because a TRAIN positive is a genuine false negative.
The defect is that `load_knowledge_graph` folds VALID and TEST into the same
tables, and training then consumes them.

A file-access sentinel cannot catch this class of bug — no forbidden file is
opened at training time in the sealed case, and in the historical case TEST is
opened legitimately for evaluation. A useful complementary control is a negative
control asserting that held-out golds appear among mined negatives at the rate
chance predicts.
