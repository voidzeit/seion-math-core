# Gate 13.5 — Causal Screening of Base, Path and SEION Contributions

Preregistration. Frozen before any Stage 3/4 result is generated. Mirrors the
format of `campaigns/gate12/preregistration.md` and `campaigns/gate13/preregistration.md`.
Branch: `campaign/gate13-closeout`. Preceding state: Gate 13.4 PASS
(`gate13-nontrivial-certification-pass`, commit `0ebc3fb`), Gate 13.5 Stage 0
infrastructure fix (commit `5094d44`, unpushed at the time this is written).

## 1. Objective

Determine whether the path branch and the SEION scalar branch produce
measurable predictive value over the TuckER base expert, under a controlled,
paired, reproducible design — screening, not the final confirmatory
campaign. Six causal questions (master brief §2, Q1–Q6): does path help
base; does SEION help base; does combining outperform either alone; do the
router gates activate meaningfully; are gains concentrated in particular
relation/path-availability regimes; are gains worth the added cost.

Acceptance label `PASS_GATE13_5_CAUSAL_SCREENING` requires the complete
preregistered design executed correctly — a negative result is a valid,
acceptable outcome under that label.

## 2. Frozen ablation matrix

| Config | `--enable_path` | `--enable_seion` | `--structural_kernel_variant` |
|---|---|---|---|
| A0 (base) | off | off | none |
| A1 (base+path) | on | off | none |
| A2 (base+seion) | off | on | none |
| A3 (base+path+seion) | on | on | none |

`--base_expert tucker` for all four. Adaptive rank allocation, associator/FI
losses (`--fi_weight 0 --assoc_weight 0`, the CLI default) are out of scope
for this gate, per master brief §3 — not included in any A0–A3 config.

## 3. Base model verification (Stage 0, completed)

Confirmed by direct code inspection (`seion_kgr/data.py`, `seion_kgr/evaluate.py`,
`seion_kgr/train.py`) before writing this document:

- Reciprocal training is unconditional in this codebase (`data.py`:
  "v26 does not offer a non-reciprocal mode") — identical for all four
  configs by construction, not a chosen setting.
- Evaluation is the existing blocked filtered evaluator
  (`evaluate.py::evaluate`), head-ranking via the reciprocal trick — same
  evaluator identity for all four configs (same function, same call site).
- `--enable_path` / `--enable_seion` are independent boolean flags in
  `model.py`/`train.py` (`self.enable_path`, `self.enable_seion` gate the
  forward and `score_tail_candidates` paths separately) — A0–A3 is a clean
  2×2, not four hand-maintained code paths.

## 4. Datasets

Screening dataset: **FB15K-237**, full official splits (train 272,115 /
valid 17,535 / test 20,466 lines). Diagnostic-only: WN18RR (train 86,835 /
valid 3,034 / test 3,134). SHA-256 hashes frozen in `dataset_manifest.json`
(this directory). No subsampling in any A0–A3 primary run — a 5,000/20,000
triple subsample is the exact deviation Gate 12 and Gate 13.3b/13.4 used and
is explicitly excluded here (master brief §5); any smoke-only subsample run
is labeled `ENGINEERING_SMOKE_ONLY` and never appears in the causal
contrasts.

## 5. Path configuration

`--path_backend batched --path_selector_mode budgeted_bfs` (Gate 13.2's
CSR/vectorized reasoner — closes the exact scaling gap, documented in
`campaigns/gate12/preregistration.md` §11, that forced Gate 12's A3
subsample deviation; a full WN18RR epoch completes in 11.8s under this
backend per Gate 13.2's acceptance test, vs. 8+ minutes unfinished under
`legacy`). `learned_topk` is not used (Gate 13.2b/13.3b/13.4 precedent: not
supported by the batched backend / not certifiable). Frozen for both A1 and
A3: `--path_rank 16 --path_layers 2 --path_max_neighbors 16` (Gate 12's A3
values, carried forward for continuity with prior screening).

## 6. Router configuration — predictive vs. certification profile

Gate 13.4's `gate_g_max=0.0002` is a certification-only value (chosen there
specifically to make the frozen LayerNorm+tanh envelope bound achievable at
positive coverage) and is excluded from this campaign's primary predictive
claims, per master brief §7.

**Predictive profile selection (Stage 3, validation-only):** preregistered
set `gate_g_max ∈ {0.25, 0.5, 1.0}`. Selection procedure: during the Stage 3
one-seed pilot, run A3 (both branches active — the config where router
under- or over-saturation is most visible) at all three values for a
reduced epoch budget, pick the value with the highest **validation** MRR,
freeze it, and use the identical frozen value for A1/A2/A3 in Stage 4 (A1
and A3 are never tuned independently — the same frozen `gate_g_max` value
applies to both). Recorded in `configuration_freeze.json` once selected;
not re-opened afterward.

Per-epoch, per-branch gate diagnostics already exist in `train.py`
(`compute_gate_diagnostics`, `gate_diagnostics.jsonl`) since the Gate 13
precisions commit (`20f86d9`) — reused as-is, not reimplemented.

## 7. Training protocol — shared hyperparameters

Frozen for every A0–A3 run at a given seed (identical across the matrix;
only `--enable_path`/`--enable_seion`/`--gate_g_max`-selection differ):

| Field | Value | Rationale |
|---|---|---|
| `dim` | 64 | matches Gate 12's shared config for continuity |
| `batch_size` | 256 | master brief §15 hardware safety: known-safe 2048×256 region |
| `entity_block_eval` | 2048 | same safety region; Gate 12 used 4096, explicitly the size the master brief now warns against |
| `neg_k` | 64 | Gate 12 value |
| `adversarial_temperature` | 1.0 | Gate 12 value |
| `n3_weight` | 1e-3 | Gate 12 value |
| `lr` | 1e-3 | Gate 12 value |
| `weight_decay` | 0.0 | CLI default |
| `grad_clip` | 1.0 | CLI default |
| `router_lr_multiplier` | 5.0 | CLI default, Gate 13.1 value |
| `epochs` | 15 | frozen here (not a Gate 12 carryover): enough for the router's known slow-open behavior (Gate 12 negative control: near-zero gate after 40 epochs on a tiny synthetic graph) to have a real chance of showing SOME displacement at full-dataset scale within a bounded screening budget |
| `eval_every` | 3 | evaluate at epochs 3/6/9/12/15 — validation-only, for best-epoch selection |
| `eval_max_queries` | 0 (uncapped) | master brief §10/§7: never report capped evaluation as the primary result |
| `eval_subset` | 1.0 | full valid/test, no random subsetting |
| `device` | cuda | RTX PRO 5000 Blackwell Laptop GPU, 24GB, confirmed available this session |
| `--path_proj_rank` | 0 | no compression in the predictive campaign — orthogonal to Gate 13.4 |
| `--structural_kernel_variant` | none | disabled for all A0–A3, per §2 |
| `--fi_weight`, `--assoc_weight` | 0.0 (CLI default) | out of scope, §2 |

Seeds: **1, 2, 3** (master brief §8 screening seeds). Matched
initialization: A0 is trained first for each seed; A1/A2/A3 for that same
seed use `--init_from_checkpoint <A0's best.pt> --seed <same seed>` (new
mechanism, commit `5094d44`) so the shared tucker/embedding weights start
from IDENTICAL values across the matrix, and the new `--seed`-driven
`data_gen` (same commit) gives all four configs the identical train-triple
batch order. Both mechanisms are covered by
`tests/kgr/test_gate13_5_paired_seeding.py`, run and passing (170/170 full
suite) before this document was written. Exact batch-order pairing is
therefore **achieved**, not merely attempted — no deviation entry required
for §8.

## 8. Compute staging (master brief §9)

1. Stage 1 — static validation (config validation, dataset hashes,
   evaluator identity, checkpoint round-trip, path leakage check, backend
   parity check, deterministic seed check). No GPU training.
2. Stage 2 — tiny smoke: one `ENGINEERING_SMOKE_ONLY` run per A0–A3 on a
   small subsample, `--cpu` or `--cuda`, no scientific interpretation.
3. Stage 3 — one-seed (seed 1) full-FB15K-237 pilot, A0–A3, plus the
   `gate_g_max` predictive-profile selection (§6). Verifies runtime, VRAM,
   gate diagnostics, evaluator before Stage 4 is authorized.
4. Stage 4 — complete screening: seeds 1/2/3 × A0–A3 = 12 full runs over
   the complete FB15K-237 splits. Not started if Stage 3 exposes a
   configuration error.

## 9. Primary metrics and contrasts

Primary: filtered MRR. Secondary: Hits@1/3/10, mean/median rank, head MRR,
tail MRR. Efficiency: train/eval wall time, peak VRAM, queries/sec,
parameter count, average selected edges per query. Contrasts (per seed,
then aggregated): `Δ_path_base = A1-A0`, `Δ_path_with_seion = A3-A2`,
`Δ_seion_base = A2-A0`, `Δ_seion_with_path = A3-A1`,
`Δ_interaction = A3-A2-A1+A0`, `Δ_combined = A3-A0` — computed for MRR,
Hits@1/3/10, head/tail MRR, wall time, peak VRAM. Primary contrast family
for Holm correction: `A1-A0, A2-A0, A3-A1, A3-A2, A3-A0, interaction`.
Paired bootstrap CIs computed by query with identical query ordering across
paired configs. n=3 seeds is `SCREENING_EVIDENCE`, never confirmatory.

## 10. Test-set discipline

Validation only during Stages 1–4 for model/epoch selection. Test opened
exactly once, after all 12 Stage 4 runs' best epochs are frozen from
validation. Any test re-open is logged in `deviations_log.md`.

## 11. Negative controls

C0 (gate frozen at zero — reuse `--gate_g_max 0` on an A1/A2/A3-shaped
config), C1 (random path states), C2 (shuffled query relation), C3
(queried-edge leakage sentinel — test-only, never in scientific
comparisons; the leakage-prevention mechanism itself is already covered by
`tests/kgr/test_selector.py::test_no_queried_edge_leakage_under_learned_topk`
and `tests/kgr/test_negative_controls.py`), C4 (parameter-count-matched
non-structured residual control) — executed after the primary A0–A3 matrix
completes, not before, per master brief §15's compute-ordering note.

## 12. Acceptance labels

Exact vocabulary from master brief §16: `PASS_POSITIVE_SCREENING`,
`FAIL_NO_PREDICTIVE_GAIN`, `FAIL_COMPONENT_INACTIVE`,
`INCONCLUSIVE_HIGH_VARIANCE`, `INCONCLUSIVE_PROTOCOL_FAILURE`. The overall
engineering label `PASS_GATE13_5_CAUSAL_SCREENING` is independent of which
scientific label applies, and requires only that the complete preregistered
design ran correctly.

## 13. Deviations

None as of this writing. Any change to the above after Stage 3 begins is
appended to `campaigns/gate13/deviations_log.md`, not made silently.

## 14. PROTOCOL_CORRECTION_BEFORE_STAGE4

Reason: `missing matched second-stage A0 control`.

The original seed-1 A0 execution is preserved as `PRETRAIN_BASE_SEED1` and is
not a matched second-stage control. Before Stage 4, create a seed-specific
pretraining baseline `B_s`, freeze `B_s/best.pt`, and launch A0, A1, A2, and
A3 from that same frozen checkpoint. Reset the optimizer identically for all
four arms and use the same DataLoader generator seed and batch order for all
four arms. The corrected causal contrasts are computed against the matched
second-stage A0; contrasts against the pretraining baseline are
`INVALID_FOR_CAUSAL_ATTRIBUTION`. This correction changes no branch
hyperparameters, does not open the test set, and applies to seeds 2 and 3
before any Stage 4 launch.
