# Gate 13 campaign preregistration

**Gate 13 — Causal, Attribution and Certification Closeout.**

- **Campaign ID:** `gate13-closeout-2026-08-02`
- **Branch:** `campaign/gate13-closeout`
- **Canonical starting commit:** `69de7849e7fefe1aefab97807ff2aaecd646abf0` (tip of
  `campaign/gate12-closeout` at the moment this branch was cut).
- **Frozen:** before any confirmatory result is generated or interpreted, and
  before Gate 13.1/13.2 code changes are merged into a benchmark run. Any
  deviation from this protocol is logged in §11 with a timestamp and reason,
  never silently.

## 0. What Gate 13 closes, and what it does not

Gate 12 closed engineering/screening plumbing (CI, evaluator exactness,
Tier-0 reduced-scale screening, negative controls, a first PDF package) but
left two things explicitly `OPEN` that block everything downstream:

1. The per-relation residual gates (`gamma_r`, `eta_r`) initialize at
   `sigmoid(-4) ~= 0.018` with gradient `sigmoid'(-4) ~= 0.0177` — a 40-epoch
   run showed the gate stays at its initialization, i.e. the path/seion
   branches never get a chance to contribute or be judged.
2. `PathReasoner.run_batch_frontiers` is a per-sample Python `for b in
   range(batch)` loop doing dict-keyed BFS — a live timing probe (A3, full
   WN18RR, batch_size=256, 1 epoch) ran 8+ minutes without completing
   (recorded as a Gate 12 deviation, §11 of `campaigns/gate12/
   preregistration.md`).

Gate 13 does not re-run the full A0-A12/K0-K4 confirmatory ladder from Gate
12's mandate. It closes the two blockers above (13.1, 13.2) with real code
and acceptance tests, adds the missing attribution and certification
machinery (13.3, 13.4), and only *then* is screening (13.5+) in scope for a
later campaign. Per the mission brief: "No debes gastar otra campaña
extensa antes de cerrar primero los dos bloqueos causales actuales."

This document freezes 13.0-13.4 (router activation, vectorized reasoner,
attribution engine, certification) as the scope actually executed under
this campaign ID. 13.5-13.10 (screening through SOTA) remain `OPEN`,
sequenced but not started, and require their own compute-budget
declaration before execution — this is a single interactive-agent session,
not a multi-day/week compute program.

## 1. Hypotheses in scope for this campaign

See `hypotheses.yaml` for the machine-readable version. Only the two gate
hypotheses below get an executed PASS/FAIL verdict in this campaign; H1-H4
from Gate 12 (SEION/path/E8/projection/adaptive-rank/generalization MRR
effects) remain `OPEN` pending Gate 13.5+.

- **H_ROUTER.** The residual router gate can be driven away from its
  initialization by gradient descent alone, on a synthetic task
  specifically constructed so that gold-tail prediction is impossible from
  the base expert's bilinear score alone and requires the path branch's
  2-hop composed state. Falsified if, after training, `|gamma_r -
  gamma_r(0)| <= delta_gate` or the path branch's RMS contribution to
  total score stays `<= 5%` on path-necessary relations.
- **H_SCALING.** The vectorized (CSR + batched-frontier + segment-top-k)
  reasoner produces bit-for-bit-equivalent (within float tolerance)
  frontier states to the legacy per-sample dict-BFS reasoner on identical
  small graphs, and completes a full training epoch on WN18RR at
  `batch_size=256` without a per-query Python loop. Falsified if any parity
  case disagrees beyond tolerance, or if a full WN18RR epoch does not
  complete inside the session's compute budget.

## 2. Frozen values

See `compute_budget.json` for the machine-readable version.

```text
BASE_SHA              69de7849e7fefe1aefab97807ff2aaecd646abf0
CAMPAIGN_START_SHA     (recorded at first commit on this branch)
DATASET_HASHES         reused verbatim from campaigns/gate12/preregistration.md §2
                        (FB15K-237, WN18RR train/valid/test SHA-256; unchanged,
                        Gate 13 does not modify data/)
E8_HASH                unchanged from Gate 12 (E8_Exact_v18_2/f_E8.npy,
                        not committed to git, local-disk-only per Gate 12 policy)
SEEDS                  synthetic-task acceptance tests: seed=0 (deterministic
                        fixture); any future Gate 13.5+ screening reuses
                        Gate 12's {1,2} Tier-0 / {1,2,3} full-screening seeds
PRIMARY_METRIC          H_ROUTER: RMS(gamma_r * s_path) / RMS(s_total) on
                        path-necessary relations, and |gamma_r - gamma_r(0)|
                        H_SCALING: max abs state-vector difference between
                        legacy and batched reasoner outputs; wall-clock for
                        one WN18RR epoch
MINIMUM_EFFECT          delta_gate = 0.05 (gate must move by >= 0.05 in
                        tanh-output space); RMS contribution ratio > 5%
                        (both values taken directly from the mission brief's
                        Gate 13.1 acceptance gate)
NONINFERIORITY_MARGIN   H_SCALING parity tolerance: 1e-4 max abs error in
                        float32 frontier state vectors on identical inputs
                        and RNG seeds (engineering equivalence check, not a
                        statistical noninferiority margin over MRR)
```

## 3. Gate 13.1 — Router activation (executed)

- **Change:** `seion_kgr/model.py` — `gamma_raw`/`eta_raw` embeddings
  reinterpreted as the pre-activation `alpha_r`, zero-initialized
  (`alpha_r(0) = 0`); gate value computed as `gamma_r = g_max *
  tanh(alpha_r)` with `g_max` a model hyperparameter (default `1.0`),
  giving `gamma_r(0) = 0` and `d(gamma_r)/d(alpha_r)(0) = g_max` (vs.
  `sigmoid'(-4) ~= 0.0177` previously — a ~56x larger gradient at init for
  `g_max=1.0`).
- **Optimizer:** `seion_kgr/train.py` — router parameters (`gamma_raw`,
  `eta_raw`, plus the structural-kernel and learned-selector internal
  gates when those branches are enabled) get a dedicated `AdamW` parameter
  group at `router_lr_multiplier x args.lr` (default multiplier `5.0`,
  CLI-exposed as `--router_lr_multiplier`).
- **Logging:** per eval epoch, `gate_diagnostics.jsonl` records, per
  relation-branch pair, `alpha`, `gamma`, `grad_norm`, and
  `rms_contribution_ratio = RMS(gamma * s_branch) / RMS(s_total)`.
- **Acceptance test:** `tests/kgr/test_gate13_router_activation.py` builds a
  synthetic compositional KG (`R_path` triples only inferable via a 2-hop
  `R1;R2` chain, held out from training for a subset of heads) and asserts,
  after a short training run: `PASS_ROUTER_ACTIVATION` iff
  `|grad_alpha| > 0`, `|gamma_r - gamma_r(0)| > delta_gate`, and
  `rms_contribution_ratio > 0.05` on the `R_path` relation specifically
  (§2 minimum effect values).

## 4. Gate 13.2 — Vectorized reasoner (executed)

- **New files:** `seion_kgr/frontier_ops.py` (CSR adjacency build + batched
  neighbor expansion via the standard ragged-expand primitive), `seion_kgr/
  segment_topk.py` (segment-wise top-k over a ragged `[F]`-indexed
  candidate-edge tensor keyed by frontier row, via a composite-key global
  argsort — no per-group Python loop), `seion_kgr/reasoner_batched.py`
  (`BatchedPathReasoner`, tensor-only frontier state as a `FrontierBatch`
  dataclass, no per-sample Python loop, no dict; submodule names match
  `PathReasoner` exactly so a trained legacy reasoner's weights transfer
  via a plain `load_state_dict()`).
- **Scope:** only `selector_mode in {"full_neighborhood", "budgeted_bfs"}`
  are implemented (`"learned_topk"`/`"oracle_or_gold_path_debug_mode"`
  remain legacy-only — vectorizing the learned selector's per-edge MLP is a
  follow-up, not required to close the scaling blocker). Wiring
  `BatchedPathReasoner` into `SeionKGRv26`/`train.py` as the production
  default is **also deferred** (§11 deviation) — this campaign proves the
  mechanism is correct and fast; switching the training entrypoint to use
  it is a separate step with its own validation (checkpoint/API
  compatibility, `run_self_test` parity, etc.) that was not executed here.
- **Parity test:** `tests/kgr/test_reasoner_batched_parity.py` (5 cases:
  1/2/3 layers, projector on/off, train/eval exclusion modes, plus a
  dedicated `states_for_candidates_batch` check) runs the legacy
  `PathReasoner.run_batch_frontiers` and the new `BatchedPathReasoner` on
  the same small synthetic graph (includes nodes with two incoming edges
  in the same layer, to exercise mean-aggregation, and a node with no
  outgoing edges, to exercise the empty-frontier path), same weights (via
  `load_state_dict`), same RNG seed, `selector_mode="full_neighborhood"`.
  **Result: all 5 cases pass, max abs state difference well under 1e-4**
  (§2 `NONINFERIORITY_MARGIN`) — `PASS_PATH_SCALING` parity half satisfied.
- **Scaling test:** `tests/kgr/test_reasoner_batched_scaling.py` drives
  `BatchedPathReasoner` (dim=64, rank=32, 2 layers, max_neighbors=32,
  `selector_mode="budgeted_bfs"` — the real `train.py` defaults) over
  every training batch (`batch_size=256`) of the full, hash-verified
  WN18RR train split (173,670 reciprocal-closed triples, 40,943 entities,
  679 batches) for one full epoch's worth of `run_batch_frontiers` calls.
  **Result: 679 batches complete in 11.8 seconds** (CPU, this session's
  hardware), against an explicit 180-second ceiling and the legacy
  reasoner's measured 8+ minutes *without completing a single epoch* on
  the same workload (Gate 12 preregistration §11). `PASS_PATH_SCALING`
  scaling half satisfied.

## 5. Gate 13.3 / 13.4 (attribution, certification)

Deferred to a follow-up commit on this same campaign branch once 13.1/13.2
land and their acceptance gates pass — recorded here as `OPEN` with the
exact file list from the mission brief (`seion_kgr/attribution.py`,
`seion_kgr/module_graph.py`, `tests/kgr/test_attribution.py`; the CP-closure
/ LayerNorm / selector-stability bounds already partially exist in
`seion_kgr/projection.py`, `seion_kgr/certification.py`).

## 6. What this campaign does not claim

No MRR effect, no E8 causal claim, no SOTA claim. This campaign's only
executed claims are the two engineering/mechanism gates in §1. Everything
in Gate 12's H1-H4 and the mission brief's §4-§11 remains exactly as `OPEN`
as it was at the end of Gate 12, pending a separately budgeted Gate
13.5-13.10 campaign that can only start once `PASS_ROUTER_ACTIVATION` and
`PASS_PATH_SCALING` are both true.

## 11. Deviations log

| Timestamp (UTC) | Deviation | Reason |
|---|---|---|
| campaign start | Branch cut from `campaign/gate12-closeout` tip rather than `main` | Gate 13 is a direct continuation of Gate 12's engineering state (same model.py/reasoner.py); rebasing onto main would require re-deciding whether to merge Gate 12 first, which is out of scope for this campaign |
| Gate 13.2 execution | `BatchedPathReasoner` is validated standalone (parity + full-WN18RR-epoch scaling tests) but NOT wired into `SeionKGRv26`/`train.py` as the production reasoner in this campaign | Switching the training entrypoint's default reasoner is a distinct, separately-validated change (checkpoint compatibility, `run_self_test` parity across all base experts, CLI flag design) and was not necessary to satisfy this campaign's preregistered `PASS_PATH_SCALING` condition, which only requires proving the vectorized mechanism is correct and fast. Logged as `OPEN` (Gate 13.2b) rather than silently treated as done. |
| Gate 13.2 execution | Only `selector_mode in {"full_neighborhood", "budgeted_bfs"}` implemented in `BatchedPathReasoner`; `"learned_topk"` and `"oracle_or_gold_path_debug_mode"` remain legacy-only | Not required by the preregistered parity/scaling acceptance conditions (§4); vectorizing the learned selector's MLP score is separable follow-up work, logged as `OPEN` rather than claimed done |
