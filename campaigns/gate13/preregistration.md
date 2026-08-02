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

## 4b. Gate 13.2b — Production integration (executed)

Closes the deviation logged in §11 above: `BatchedPathReasoner` is now the
model's actual path branch when requested, not just a standalone-tested
component.

- **New file:** `seion_kgr/path_reasoner_output.py` — a single
  `PathReasonerOutput(query_ids, node_ids, states, num_nodes,
  unreached_state)` representation with `state_for()`/
  `states_for_candidates()`/`reached_mask()`, plus adapters from the legacy
  dict-frontier list and from `BatchedPathReasoner`'s `FrontierBatch`.
  `BatchedPathReasoner`'s own `state_for_node_batch`/
  `states_for_candidates_batch` now delegate to it (single implementation,
  no duplicated searchsorted logic). Scope cut from the mission brief's
  fuller schema: `selector_scores`/`selector_margins`/`reached_gold` are
  NOT implemented (would be unused plumbing until Gate 13.3's attribution
  work and learned-selector vectorization exist) — logged as `OPEN`, not
  silently dropped.
- **`model.py`:** `SeionKGRv26(path_backend="legacy"|"batched", ...)`.
  Both backends already used identical submodule names (`mu`, `U`, `V`,
  `W`, `projector`, `ln`, `unreached_state`) from Gate 13.2, so
  checkpoints trained with one load directly into the other via a plain
  `load_state_dict()` — verified, not just assumed (see below). A single
  `_run_path_reasoner()` call site dispatches to whichever backend is
  active and returns a `PathReasonerOutput`; `score_positive`/
  `score_tail_candidates` now contain exactly ONE readout implementation
  regardless of backend (the previous per-sample `[... for b in
  range(batch)]` list-comprehension readout loops in `model.py` itself
  are gone for both backends, not just for the batched one).
- **`train.py`:** `--path_backend {legacy,batched}` (default `legacy`),
  builds the matching adjacency representation (`Adjacency` or
  `CSRAdjacency`) once per run and moves the CSR one to the model's device
  (`CSRAdjacency.to(device)`, new method — see the real bug found below).
  Adds `compute_path_reasoner_perf()` -> `path_reasoner_perf.jsonl` per
  eval epoch: `path_backend`, `wall_seconds`, `queries_per_second`,
  `mean_frontier_size`, `p95_frontier_size`, `gold_reach_rate`,
  `cpu_ram_mb` (coarse before/after-max proxy via `psutil`, not a true
  continuous peak), `gpu_allocated_peak_mb` (true peak via
  `torch.cuda.max_memory_allocated`). `expanded_edges_per_second` and
  `selector_keep_ratio` are logged as `null` — not exposed by the current
  reasoner APIs, honestly reported rather than approximated.
- **Real bug found and fixed during this integration:** running the
  batched backend on GPU (`--cpu` not passed) crashed with `RuntimeError:
  indices should be either on cpu or on the same device as the indexed
  tensor` — `build_csr_adjacency` always builds CPU tensors (real,
  Python-level dict traversal that gains nothing from a GPU) but was never
  moved to the model's device, and separately, `BatchedPathReasoner`'s
  `budgeted_bfs` RNG used a hardcoded `torch.Generator(device="cpu")`,
  which PyTorch refuses to use for generating a CUDA tensor
  (`torch.rand(..., generator=cpu_gen, device='cuda')` raises). Fixed by
  adding `CSRAdjacency.to(device)` (called once in `train.py`, same
  pattern as `model.to(device)`) and constructing the RNG generator on
  `head_ids.device` instead of a hardcoded `"cpu"`. This was caught
  precisely because the acceptance run (below) exercises the real GPU
  path — none of the earlier Gate 13.2/13.2b CPU-only tests would have
  caught it, which is itself evidence for why an end-to-end acceptance run
  through the real CLI entrypoint (not just unit tests) was worth doing.
- **Score/gradient/checkpoint parity tests:**
  `tests/kgr/test_gate13_2b_production_integration.py` (7 tests, all
  model-level, not bare-reasoner): score parity legacy vs batched (full
  neighborhood train/eval, with projector+seion enabled, and a
  budgeted_bfs case constructed so no node's degree exceeds the budget —
  active random-cut parity is explicitly out of scope, see below);
  queried-edge-removal exclusion mechanism (via direct
  `_run_path_reasoner`/`PathReasonerOutput` reads, not total score, since
  a freshly-initialized zero gate would multiply away any score-level
  difference regardless of whether exclusion works); gradient parity
  across every shared named parameter (CP law, U/V/W, projector, relation
  embeddings, entity embeddings, router gate — max abs diff and cosine
  similarity, both within tolerance for every checked parameter);
  checkpoint cross-backend load after 10 real optimizer steps on the
  legacy backend. **All 7 pass.**
- **Scope note on `budgeted_bfs` parity:** legacy uses `numpy`
  `rng.choice`, batched uses `torch.rand` + segment top-k — different RNG
  streams. These are NOT expected to select the same random subset when a
  real budget cut is active; what is tested (and holds) is that math is
  identical whenever the SAME set of edges is kept (which is exactly what
  happens when no frontier row's degree exceeds `max_neighbors`, the
  fast-path both implementations share). Parity under an actively
  different random subset is out of scope — not a claim made here.
- **`selector_gradient_connected`:** only meaningful for `learned_topk`,
  which `BatchedPathReasoner` does not implement (Gate 13.2's stated
  scope cut, unchanged). Already covered on the legacy backend by the
  pre-existing `tests/kgr/test_selector.py` suite; not re-verified here
  for the batched backend since the mode doesn't exist there.
- **Real acceptance run:** `tests/kgr/test_gate13_2b_acceptance_run.py`
  drives the actual `seion_kgr.train.train()` entrypoint (not a bespoke
  script) with `--path_backend batched`, `--dim 64`, real 2-layer path
  reasoner, `budgeted_bfs`, one full training epoch (forward + backward +
  optimizer step over every batch) plus a capped (`--eval_max_queries
  200`) validation/test evaluation, on real hash-verified data, on this
  session's actual hardware (CUDA available, RTX-class GPU). **Results:**
  WN18RR (173,670 triples) completed in **48.0s**; FB15K-237 (544,230
  triples) completed in **218.1s** — both against a 300s ceiling.
  `path_reasoner_perf.jsonl` and `gate_diagnostics.jsonl` both produced
  correctly for both runs. This is an ENGINEERING completion check, not a
  confirmatory MRR result — the MRR/Hits numbers printed during these
  runs are single-seed, one-epoch, capped-eval numbers and carry no
  statistical weight; they are not cited as evidence for or against any
  Gate 13.5+ hypothesis.
- **`PASS_PATH_PRODUCTION_INTEGRATION`:** `full_epoch_completed=true`,
  `legacy_batched_score_parity=PASS`, `legacy_batched_gradient_parity=PASS`,
  `checkpoint_cross_backend=PASS`, `queried_edge_removal=PASS`,
  `selector_gradient_connected=PASS (legacy only, batched N/A — mode not implemented)`,
  `tests_failed=0` (137/137 across the full `tests/kgr` suite, including
  the two full-scale acceptance runs).
- **Still deferred, logged `OPEN`:** `path_backend` default remains
  `"legacy"` (not flipped to `"batched"`) — the mission brief's own
  sequencing ("Después de cerrar toda la paridad... default = batched")
  implies flipping the default is a distinct decision after this evidence
  is reviewed, not an automatic consequence of the tests passing; `learned_topk`
  vectorization; the fuller `PathReasonerOutput` schema
  (`selector_scores`/`selector_margins`/`reached_gold`);
  `expanded_edges_per_second`/`selector_keep_ratio` perf fields.

## 4c. Precisions applied before Gate 13.3 (executed)

Three corrections made after reviewing the Gate 13.2b evidence, before
starting attribution work:

1. **Explicit rejection, not silent fallback.** `train.py`'s `train()` now
   raises `NotImplementedError("learned_topk is not yet supported by the
   batched path backend")` immediately (before any dataset load or model
   construction) when `--path_backend batched --path_selector_mode
   learned_topk` are combined — this complements (does not replace)
   `BatchedPathReasoner`'s own constructor-level `ValueError` for the same
   combination. Tested in
   `tests/kgr/test_gate13_2b_production_integration.py::test_batched_backend_with_learned_topk_is_explicitly_rejected`.
   `path_backend` stays `"legacy"` by default; only flip it once
   `learned_topk` has parity+scaling evidence on the batched backend too.
2. **Signed-gate declaration.** `model.py`'s module docstring now states
   explicitly: **the Gate 13 routers are signed residual gates
   (`gamma_r in (-gate_g_max, gate_g_max)`), not `(0,1)` convex-mixing
   weights** — a trained `gamma_r < 0` means the branch learned to
   SUBTRACT a residual correction, not a failure mode. `score_positive`'s
   `return_breakdown` now additionally exposes each branch's RAW (pre-gate)
   score and the base score (`s_base`, `gamma_path_raw`, `eta_seion_raw`,
   `kernel_structural_raw`/`kernel_structural`/`kernel_structural_gate` —
   the kernel branch's own `StructuralKernelResidual.forward` also grew a
   `return_breakdown` option to expose its pre-gate output). `train.py`'s
   `compute_gate_diagnostics` now reports, per branch (path, seion, AND
   structural kernel — previously only path/seion were logged):
   `gate_signed_mean`, `gate_absolute_mean`, `branch_score_rms`,
   `signed_branch_contribution`, `absolute_branch_contribution`,
   `correlation_with_base_score`, alongside the existing `alpha_mean`,
   `rms_contribution_ratio`, `grad_alpha_norm`. Schema updated in
   `artifact_schema.json`.
3. **Per-branch router activation micro-tests.** `PASS_ROUTER_ACTIVATION`
   (Gate 13.1) was demonstrated on the path branch only.
   `tests/kgr/test_gate13_seion_router_activation.py` and
   `tests/kgr/test_gate13_structural_kernel_router_activation.py` add
   `PASS_SEION_ROUTER_ACTIVATION` and
   `PASS_STRUCTURAL_KERNEL_ROUTER_ACTIVATION`: a frozen "teacher" of the
   SAME functional form as each branch (a `SeionicScalarScorer` for the
   seion test; a `StructuralKernelResidual` sharing the SAME frozen kernel
   tensor `K` as the student, since `K` is a non-trainable buffer — only
   the teacher's adapters/gate differ, and its gate must be manually
   opened away from its own 0-init to have any preference to teach)
   generates gold-tail labels a bare ComplEx base cannot represent in
   general. Both tests pass: SEION gate reaches `eta in [-0.297,
   -0.255]` across the two relations after 200 epochs; structural-kernel
   gate reaches `eps in [-0.352, -0.120]` — both `> delta_gate=0.05` in
   absolute value, both with nonzero router gradient, both with RMS
   contribution ratio `> 0.05`. Unlike the path test, neither attempts a
   held-out-generalization claim: SEION/structural-kernel have no graph
   structure to exploit independently of direct supervision (unlike the
   path branch, whose entities receive indirect structural signal from
   OTHER edges even for held-out queries), so that framing does not apply
   — the acceptance conditions tested are exactly the three the mission
   brief states (nonzero gradient, displacement, RMS ratio), no more.

## 5. Gate 13.3 — Attribution Engine (executed, scoped)

**Scope decision (read first):** the mission brief's per-layer module list
(`path.layer_0.message`, `path.layer_1.projector`, ...) does not map onto
this codebase — every reasoning layer reuses the SAME `mu`/`U`/`V`/`W`/
`projector` weights (`PathReasoner.message` is called identically at
every layer), so per-layer components are not independently ablatable
parameters. Two decompositions are implemented instead:

- **Path-internal** (`mu`, `residual`=`U+V+W`, `projector`) — genuinely
  nonlinear: components are mean-aggregated across incoming edges then
  passed through `LayerNorm(tanh(.))` at every hop, so telescoping here is
  order-dependent in general and Shapley's averaging is doing real work.
- **Branch-level** (`path`, `seion`, `structural_kernel`) — the total
  score is a plain sum (`s = s_base + gamma*s_path + eta*s_seion +
  s_kernel`), so this decomposition is EXACTLY order-independent by
  construction — reported as a verified structural property, not
  something attribution needed to discover.

**New files:** `seion_kgr/module_graph.py` (module registry +
`ablate_path_components`/`corrupt_module` context managers, both
try/finally-safe), `seion_kgr/attribution.py` (`local_innovation`,
`path_internal_score`, `path_internal_telescoping`, `path_internal_shapley`,
`branch_level_telescoping`, `rank_flip_attribution`).

**A real masking bug found while building this (same family as Gate
13.2b's queried-edge fixture bug):** `path_internal_score` originally read
the GATED total score; at a freshly-initialized model the router gate is
exactly 0 (Gate 13.1), which multiplies away ALL internal-composition
differences identically across every ablation subset, making every
telescoping/Shapley number trivially zero regardless of what the
internal components actually compute. Fixed by reading
`breakdown["gamma_path_raw"]` (the PRE-gate path score) instead — the
router gate itself is already separately tested
(`PASS_ROUTER_ACTIVATION`); attribution over path-internal composition is
a different question and must not be re-masked by the same gate.
`rank_flip_attribution` legitimately DOES need the gated total score
(real-world ranking), so its test manually opens the gate first rather
than bypassing it in the function itself.

**A second real finding — Shapley diffusion under multiplicative
interaction:** corrupting the projector (via the coalition/Shapley game)
made `mu`, not `projector`, receive the largest Shapley value. This is not
a bug: the projector is a TRANSFORM applied to `mu+residual`'s sum, not a
third additive term, so corrupting it creates genuine interaction that
Shapley's averaged-over-orderings marginal contribution partly diffuses
onto whatever the corrupted transform is applied to. The corrupted-module
negative control test therefore uses `local_innovation` (each component's
own direct, un-gated output magnitude) instead of Shapley for
localization — Shapley remains the right tool for the conservation/
efficiency/dummy-module properties, which don't hit this issue. A third
finding: scaling the projector's `raw` parameter does NOT corrupt it,
because `StiefelProjector.Q()`'s QR retraction is scale-invariant
(`qr(c*raw)` gives the same `Q` as `qr(raw)` for any `c>0`) — `corrupt_module`
corrupts the projector by monkeypatching `.apply` instead.

**Tests** (`tests/kgr/test_gate13_attribution.py`, 7 tests, all pass):
telescoping conservation (state+score, all 3! path-internal orders, all
3! branch-level orders — max reconstruction error `< 1e-5`, the FP32
tolerance frozen in the mission brief §13.3.3); Shapley efficiency
(`sum(phi_i) == F_full - F_empty`, same tolerance); a dummy
(zero-weight) module receiving exactly-zero attribution; the corrupted-
module negative control for ALL THREE path-internal modules (not just
one example), each correctly localized via `local_innovation`'s relative
increase, each restoring to its EXACT pre-corruption value; rank-flip
attribution (structure + at least one real flip across the fixture); and
legacy/batched attribution parity (`path_internal_shapley` agrees to
`< 1e-5` between backends — verified, since `ablate_path_components` only
monkeypatches `.message()`, present with an identical signature on both
`PathReasoner` and `BatchedPathReasoner`).

**`PASS_ATTRIBUTION_CONSERVATION`:** `telescoping_state_conservation=PASS`,
`telescoping_score_conservation=PASS`, `shapley_efficiency=PASS`,
`dummy_module_attribution_zero=PASS`, `corrupted_module_localization=PASS`,
`signed_gate_attribution=PASS` (via the Gate 13.1 precision's signed-gate
diagnostics, §4c), `legacy_batched_attribution_parity=PASS`,
`rank_flip_reconstruction=PASS`, `tests_failed=0` (145/145 across
`tests/kgr`, this file's 7 included).

**Explicitly deferred, logged `OPEN` (Gate 13.3b, a follow-up analogous to
13.2b):**
- The `runs/<run_id>/{module_error_attribution,query_error_attribution,
  rank_flip_attribution,shapley_attribution}.jsonl` +
  `{module_interactions,attribution_summary,attribution_manifest}.json` +
  `bound_vs_observed.csv` output-file pipeline. The COMPUTATION functions
  that would produce these exist and are tested; there is no CLI
  entrypoint yet that runs attribution over a real trained checkpoint on
  a real dataset and writes them to disk (this campaign's attribution
  work is exercised entirely through small synthetic-fixture unit tests,
  same convention as Gate 13.1/13.2's acceptance tests before their own
  13.2b production-integration follow-up).
- `certified_bound_contribution` / `bound_vs_observed.csv` (mission brief
  §13.3.6): this requires the CP-closure/LayerNorm/selector-stability
  bound machinery that is Gate 13.4's subject (`projection.py`,
  `certification.py` already have partial building blocks) — not
  duplicated here, per the mission brief's own phase separation
  (13.3 attribution, THEN 13.4 certification).
- Monte Carlo Shapley (64-256 permutations) for `m > 8` modules — not
  needed yet since the current module sets (`3` path-internal, `3`
  branch-level) are small enough for full enumeration (`3! = 6`).

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
| Gate 13.2 execution | `BatchedPathReasoner` is validated standalone (parity + full-WN18RR-epoch scaling tests) but NOT wired into `SeionKGRv26`/`train.py` as the production reasoner in this campaign | Switching the training entrypoint's default reasoner is a distinct, separately-validated change (checkpoint compatibility, `run_self_test` parity across all base experts, CLI flag design) and was not necessary to satisfy this campaign's preregistered `PASS_PATH_SCALING` condition, which only requires proving the vectorized mechanism is correct and fast. Logged as `OPEN` (Gate 13.2b) rather than silently treated as done. **RESOLVED in Gate 13.2b (§4b): `--path_backend {legacy,batched}` is now wired end-to-end through `train.py`/`model.py`, with model-level score/gradient/checkpoint parity tests and a real full-epoch acceptance run on WN18RR + FB15K-237.** |
| Gate 13.2b execution | A real device-placement bug (CSR adjacency tensors stuck on CPU; `budgeted_bfs`'s RNG generator hardcoded to a CPU device) was found only when the acceptance run exercised the actual CUDA path — every earlier Gate 13.2/13.2b test ran on CPU and would not have caught it | Fixed: `CSRAdjacency.to(device)` (new method, called once in `train.py` alongside `model.to(device)`), and the `budgeted_bfs` generator is now constructed on `head_ids.device` instead of a hardcoded `"cpu"`. Recorded here as a concrete argument for why an end-to-end real-hardware acceptance run matters beyond unit-level parity tests. |
| Gate 13.2b execution | `path_backend` default left at `"legacy"`, NOT flipped to `"batched"` | The mission brief's own sequencing treats "flip the default" as a decision made only after parity evidence is reviewed, not an automatic consequence of tests passing — deliberately left as a separate, explicit follow-up decision, logged `OPEN` |
| Gate 13.2 execution | Only `selector_mode in {"full_neighborhood", "budgeted_bfs"}` implemented in `BatchedPathReasoner`; `"learned_topk"` and `"oracle_or_gold_path_debug_mode"` remain legacy-only | Not required by the preregistered parity/scaling acceptance conditions (§4); vectorizing the learned selector's MLP score is separable follow-up work, logged as `OPEN` rather than claimed done |
| Gate 13.3 execution | Module granularity scoped to path-internal (`mu`/`residual`/`projector`) + branch-level (`path`/`seion`/`structural_kernel`), NOT the mission brief's per-layer list (`path.layer_0.message`, etc.) | Every reasoning layer reuses the SAME `mu`/`U`/`V`/`W`/`projector` weights in this codebase — per-layer components are not independently ablatable parameters as written; attributing to the components that ARE independently ablatable is the honest scope |
| Gate 13.3 execution | `path_internal_score`/`path_internal_telescoping`/`path_internal_shapley` read the PRE-gate `gamma_path_raw` breakdown field, not the gated total score | The router gate is exactly 0 at a fresh model (Gate 13.1), which would multiply away every ablation subset's difference identically, masking the entire internal-composition question this machinery exists to answer — the gate itself is already separately tested |
| Gate 13.3 execution | The corrupted-module negative control uses `local_innovation` (direct per-component magnitude), not `path_internal_shapley`, to test localization | Verified empirically: corrupting the projector via the Shapley coalition game made `mu`, not `projector`, receive the largest Shapley value — a real diffusion effect under multiplicative interaction (the projector is a TRANSFORM applied to mu+residual's sum, not a third additive term), not an implementation bug. Shapley remains correct and used for conservation/efficiency/dummy-module properties, which don't hit this issue |
| Gate 13.3 execution | The `runs/<run_id>/*.jsonl`/`*.json`/`*.csv` output-file pipeline from the mission brief §13.3.4-13.3.6 is NOT implemented — the underlying computation functions are, and are tested via synthetic fixtures only | Same pattern as Gate 13.2 before its own 13.2b production-integration follow-up: proving the mechanism is correct comes before wiring it into a real run-producing CLI entrypoint. Logged `OPEN` as Gate 13.3b |
| Gate 13.3 execution | `certified_bound_contribution`/`bound_vs_observed.csv` (mission brief §13.3.6) not implemented here | That machinery is Gate 13.4's subject (CP-closure/LayerNorm/selector-stability bounds) per the mission brief's own phase ordering (13.3 attribution, then 13.4 certification) — not duplicated ahead of that gate |
