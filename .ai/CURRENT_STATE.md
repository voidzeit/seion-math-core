# Current state

## 2026-08-10 postflight — accuracy-first spectral-mixture discovery runs

- Implemented and exercised the first full-entity,
  relation-adaptive spectral Tucker mixture trainer. The online miner uses
  blockwise all-entity scoring and retains only a `[B, hard_k]` frontier;
  it does not materialize `[B,N,D]` candidate tensors. Reciprocal relation
  filtering was corrected to use `heads_of_rt` for inverse ids.
- A D256 / 8-expert / 2-active / rank-64 / 4-core-basis GPU smoke passed with
  finite loss and released CUDA allocations after completion. A bounded
  23 GB-cap canary also completed without OOM or BSOD; the cap is an upper
  bound and was not forced to consume 23 GB.
- Discovery run `D256 / batch256 / hardK64 / 1024 steps` reached pilot
  validation MRR `0.114995` at step 512 and `0.090420` at step 1024 on
  256 head/tail queries. A resumed `batch512 / 2048-step` run reached pilot
  MRR `0.133131` at step 1536 and `0.109595` at step 2048; peak allocation
  was about `17.06 GB` and peak reservation about `18.23 GB`.
- A second `lr=3e-4 / hardK128 / 512-step` run reached pilot MRR
  `0.076279` on 256 queries, so it is not a quality finalist. These are
  discovery observations only: no SOTA, full-validation, test, certificate,
  or ranking-preservation claim is made. The best pilot remains far below
  the preregistered SOTA-discovery targets.
- The current gate is therefore **implementation/stability pass, quality
  gate pending**. WN18RR replication, teacher freeze, student distillation,
  compression certification, and final test evaluation remain unopened.
- No agent-side thermal threshold is used. System/driver protections remain
  authoritative, the process cap remains at most 23 GB, and the two Windows
  bugchecks in B-0012 remain preserved and unresolved.

## 2026-08-10 postflight — user-stopped 8192-step discovery continuation

- The resumed D256 run was stopped on explicit user request after checkpoint
  step `4800`; the GPU returned to `0 MiB` usage. Both `checkpoint_best.pt`
  and `checkpoint_last.pt` were preserved, together with
  `run_interrupted.json`.
- The best and latest validation record was step `4608` on a 512-query pilot:
  MRR `0.177815`, H@1 `0.152344`, H@3 `0.195313`, H@10 `0.216797`, and mean
  rank `3130.69`. This improves the earlier pilot maximum `0.133131`.
- This remains discovery-only evidence. The official full validation set,
  test set, SOTA comparison, student freeze, compression certificate, and
  hardware-speedup gates remain pending.

## 2026-08-10 postflight — SRATM paused at checkpoint 3100

- SRATM was paused on explicit user request immediately after
  `checkpoint_last.pt` reached step `3100`; CUDA usage returned to `0 MiB`.
- The preceding validation at step `3072` reached pilot MRR `0.578075`, H@1
  `0.537109`, H@3 `0.596680`, H@10 `0.657227`, with mean rank `500.70` over
  1024 queries. This is the current best pilot result.
- The run is resumable from the preserved checkpoint. It remains discovery
  evidence only; official full validation, test, certification, and hardware
  gates are not closed.

## 2026-08-10 postflight — complete SRATM audit at checkpoint 4600

- SRATM was paused after `checkpoint_last.pt` reached step `4600`; GPU usage
  returned to `0 MiB`. Full filtered validation over `35,070` queries gave
  MRR `0.611648`, H@1 `0.578072`, H@3 `0.623325`, H@10 `0.677645`, and mean
  rank `375.85`.
- Integrity checks passed: all checkpoint floating-point parameters finite,
  sample positive/candidate scores finite, candidate shape `[4,128]`, fusion
  row-sum error `1.19e-7`, and orthonormality error `8.94e-7`.
- Focused tests passed `36/36`; governance audit passed structurally with
  status `yellow` and no missing required files. Test data was intentionally
  not opened. Compression/certificate and external SOTA audit remain open.

## 2026-08-10 postflight — official full validation of SRATM step 3100

- Evaluated `checkpoint_last.pt` from step `3100` on all official FB15K-237
  validation triples with filtered tail and reciprocal head ranking: `35,070`
  queries total. Runtime was `22.38 s`; peak allocation was about `2.70 GB`.
- Full validation result: MRR `0.589047`, H@1 `0.550585`, H@3 `0.603678`,
  H@10 `0.663131`, mean rank `417.11`. Tail MRR was `0.611336` and head
  MRR was `0.566757`.
- This confirms that the pilot quality was not caused by a small favorable
  subset for this checkpoint. It remains a validation observation, not a
  test/SOTA claim; the frozen teacher and certification gates are still open.

## Safety hold — two recent Windows bugchecks

- Read-only System event inspection found bugchecks at **2026-08-09 22:30**
  (`0x00020001`, dump `C:\WINDOWS\MEMORY.DMP`) and **22:37** (`0x0000001E`,
  dump `C:\WINDOWS\Minidump\080926-21015-01.dmp`).
- GPU/driver status currently reports `OK`, but that does not establish
  stability. Since this entry was recorded, only bounded, user-authorized
  discovery/canary runs under the 23 GB process cap have been executed;
  unbounded stress and final long-run claims remain disallowed until the
  dumps/driver path are reviewed.
- WER groups the `0x00020001` event as
  `INTEL_IOMMU_TIMEOUT_IMAGE_GenuineIntel.sys`. The `0x0000001E` event is
  grouped as `AV_nt!ExpPoolTrackerChargeEntry` with access violation
  `0xC0000005`; this identifies a kernel failure bucket, not necessarily the
  original faulty driver.
- `C:\WINDOWS\MEMORY.DMP` exists and is about 15.3 GB, but is ACL-protected;
  the referenced minidumps and WER sysdata files are not readable from this
  session. No debugger is installed in PATH, so module-level stack analysis
  remains pending.
- The safe next step is documentation and crash-cause triage; experimental
  compute is paused. Existing spectral/output-compression artifacts remain
  valid observations.

## 2026-08-10 postflight — confirmatory protocol V1 frozen

- Declared and structurally validated
  `experiments/configs/CERTIFIED_KGE_CONFIRMATORY_PROTOCOL_V1.yaml`.
- The protocol fixes train-only calibration, valid-only selection, one final
  test confirmation, the full tolerance/rank grids, seed-level statistics,
  same-backend hardware timing, equivalence deltas, G0--G8 gates, staged VRAM
  limits, and the required per-run artifact contract.
- Protocol status is `declared_not_executed`; G1 remains blocked by B-0012.
  No new empirical accuracy, ranking, hardware, cross-seed, or cross-dataset
  claim is introduced by freezing the protocol.

## 2026-08-10 postflight — D128 training canary

- With explicit user permission, ran the first staged training canary only:
  D128/branch128, seed 42, batch 512, 8 negatives, 64 steps, checkpoint every
  16 steps, and a 4 GB process cap.
- Result: `TRAINING_CANARY_COMPLETE`, finite final loss `0.693249`, peak
  allocation `276,649,984` bytes, peak reservation `314,572,800` bytes,
  temperature `47 C`, and post-process `nvidia-smi` usage `0 MB`.
- This clears the short-canary subgate only. It is not evidence of model
  quality, stable long training, or scientific confirmation; B-0012 remains
  open and the next 8 GB/long stage is not launched automatically.

## 2026-08-10 postflight — sustained D128 8 GB canary

- The authorized next stage completed 2,048 D128 steps at batch 2,048 with
  64 negatives, seed 42, checkpoints every 128 steps, and an 8 GB process
  cap. Runtime was approximately 428 seconds.
- Final loss was `0.072485`; peak allocation was `754,538,496` bytes and
  peak reservation `914,358,272` bytes. Maximum observed temperature was
  84 C; post-process `nvidia-smi` usage was 0 MB.
- This passes the sustained 8 GB canary subgate only. It creates no quality,
  certificate, ranking, or hardware-speedup claim. B-0012 remains open; the
  next escalation must remain separately staged and unifactorial.

## 2026-08-09 postflight — bounded score-space executor benchmark

- Bounded diagnostics were resumed only under explicit process caps after the
  short CUDA canary; long training and stress testing remain gated by the
  unresolved dump/driver review.
- Added stable relation bucketing and device-resident relation bases to
  `benchmark_ttn_relationwise_score_space.py`. The optimized benchmark was
  run in `score-only` mode with 256 validation queries, batch size 64,
  candidate block 16,384, 3 warmups, 5 repeats, and a 20 GB process cap.
- At tolerance `0.0005`, the sampled relationwise spectral oracle still has
  `G=1.874246` in the Frobenius resource model, while the measured p50
  speedups versus the relation-grouped full executor were: uniform `0.596x`,
  spectral oracle `0.756x`, and finite-query certificate `1.046x`.
  `full_dense` was `26.50x` versus `full_matched` and is only an implementation
  reference, not compression speedup.
- The finite certificate scope is only the 256 calibration queries and all
  stored entity embeddings. The relationwise oracle is a sampled score-space
  Frobenius diagnostic. Neither result is a universal ranking, hardware, or
  cross-dataset claim. The positive `1.046x` result is exploratory and does
  not pass the planned robust-speedup gate.
- Peak allocation was `180,598,272` bytes and peak reservation
  `197,132,288` bytes; post-run `nvidia-smi` reported 0 MB used. The next
  implementation target is vectorized/static routing and candidate-GEMM
  batching before any long D128 training campaign.

## 2026-08-09 postflight — batched routing stress-size benchmark

- Implemented and tested equal-rank relation batching with offline candidate
  table stacks and `torch.bmm`; the selected tuning point was relation batch
  `32`.
- The larger benchmark used 8,192 validation queries, 512 calibration
  queries, batch size 256, one full candidate block, 3 warmups, 5 repeats,
  score-only timing, and a 20 GB process cap. This is the preferred hardware
  diagnostic over the earlier 256-query probes.
- P50 speedups versus `full_matched` were `1.011x` uniform, `1.017x` spectral
  oracle, and `1.124x` finite-query certificate. Repeat-index p05 ratios were
  `0.741x`, `0.807x`, and `1.005x`, respectively. None meets the planned
  robust gate of median `>=1.5x` with a lower bound above one.
- `full_dense` was `8.00x` versus the relation-grouped executor and remains
  an implementation reference only. The score-space resource oracle still
  reports average-rank opportunity `1.874246` on the 256-query calibration
  distribution, so the remaining loss is execution/materialization rather
  than absence of spectral heterogeneity.
- Peak allocation was `1,655,774,208` bytes and peak reservation
  `2,199,912,448` bytes; post-run `nvidia-smi` reported 0 MB used. The
  relationwise executor optimization is complete for this phase; long D128
  training remains blocked by the unresolved Windows dump/driver safety
  blocker.

## Current postflight — realizable score-space implementation and CUDA canary

- Added `seion_kgr/score_space.py` with exact candidate whitening,
  support-safe pseudoinverse handling, Ky-Fan spectral projectors, spectral
  energy ranks, linear-cost water-filling, finite prefix-knapsack DP,
  deterministic ranking certificates, and Grassmann chordal diagnostics.
- Rewired `analyze_score_spectrum.py` to use the shared whitening and
  allocator implementation. CPU algebra tests pass **13/13** together with
  the TTN tests.
- Added `benchmark_ttn_gpu_canary.py`. The post-crash canary completed on
  `cuda:0` for 32 iterations at 32 queries x 256 candidates with a 4 GB
  process cap: peak allocation 42,217,984 bytes, peak reservation
  56,623,104 bytes, 51 C temperature, and post-process `nvidia-smi` usage 0.
- This is only a stability gate, not a hardware-performance claim. Long
  training remains gated by dump/driver review and short-checkpoint policy.

## Current postflight — dense D128 spectral opportunity audit

- Extended the audit to 13 tolerances from `0.1` through `0.00001`, added
  effective-rank summaries, rank quantiles, and fixed-rank-3 Grassmann
  distances for all 237 original relations.
- The maximum observed oracle gap is now `G_spectral = 1.85055` at tolerance
  `0.0005`: uniform rank 17 versus frequency-weighted adaptive average rank
  `9.1865`, an oracle relative saving of `45.96%`.
- Effective score ranks remain concentrated (median `1.0278`, maximum
  `1.6400`), while the rank-allocation heterogeneity is concentrated in the
  tight tolerance regime. Grassmann distances are small in aggregate (median
  `0.00131`, maximum `0.0983` at fixed rank 3); this currently favors testing
  shared-basis/variable-rank compression before a large relation-specific
  dictionary.
- Peak allocation was 0.61 GB under the 8 GB staged cap and post-run GPU
  usage was 0 MB. Certificate capture and hardware realization remain open.

## Current postflight — global domain-certified allocator

- Observed on **2026-08-09T20:54:20Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `global_error_certificate` and
  `global_certificate_optimal_allocation`. For a declared leaf domain
  `||x_l||<=L_l`, the Frobenius-enclosed multilinear norms yield a separable
  downstream-weighted certificate and an exact dynamic-program optimizer.
- In a 240-record normalized-leaf probe, the certificate held on all held-out
  samples. The domain-certified allocator improved held-out RMS by `0.0148`
  (chain) and `0.0135` (balanced tree) on average versus `pathwise_global`.
- Validation: global-certificate tests passed, including exhaustive agreement
  on a small network. Results are exploratory; the Frobenius bounds are
  conservative and no universal allocator superiority was claimed.

## Current postflight — finite-batch validated certificate allocator

- Observed on **2026-08-09T20:49:14Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `TensorNetwork.validated_error_certificate`, using Frobenius
  operator-norm enclosures and a sound finite-batch sup-norm recurrence, plus
  `small_case_validated_certificate_allocation`, which minimizes that bound
  exhaustively for small networks.
- The separate 360-record probe found the validated-bound no-worse fraction
  `1.0` in both topologies and mean held-out RMS reductions of `0.2432` for
  chains and `0.2250` for balanced trees versus `pathwise_global`. The bound
  was checked only on fitting batches; held-out values remain observations.
- Validation before final gates: certificate tests passed, including exact
  zero at full rank. No allocator-optimality, universal-input, or technology
  superiority claim was promoted.

## Current postflight — exact fitted-majorant allocation probe

- Observed on **2026-08-09T20:44:35Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `pathwise_majorant_optimal_allocation`, a finite dynamic program that
  globally minimizes the fitted root-excluded pathwise majorant under an
  integer rank budget. The root is fixed at rank one because the application
  does not project it.
- The exploratory probe produced 240 paired records. The candidate was never
  worse on the fitted majorant; mean held-out error reductions versus the
  historical `pathwise_global` heuristic were `0.3400` (chain) and `0.3560`
  (balanced tree). These are observations, not a superiority theorem.
- Validation: application tests **17/17 passed**, exact optimizer test passed,
  compileall and `git diff --check` passed. Historical Level 1 records remain
  unchanged. Empirical path factors are still not validated global operator
  norms.

## Current postflight — growing-tree dimension obstruction certified

- Observed on **2026-08-09T20:37:21Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added a constructive independent-law binary-chain family showing that any
  nodewise value-preserving support compression requires rank at least
  `depth+1`; the laws have operator norm one, the proper projector has zero
  evaluated closure residual, and the values are orthogonal.
- The result is registered as `CE_V5_GROWING_TREE_NODEWISE_SUPPORT` and narrows
  `OPEN_V5_DIMENSION_RANK_REDUCTION`: no tree-size-uniform nodewise bound is
  possible in that unrestricted class. Root-only, same-law, and fixed-tree
  questions remain separate.
- Validation: focused obstruction tests **5/5 passed**, executable witness
  passed for depths 1, 2, 4, and 8, and `git diff --check` passed. No theorem
  novelty, human review, or release status was upgraded.

## Current postflight — review snapshot drift detected and repaired

- Observed on **2026-08-09T17:55:02Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- The deterministic review-manifest gate correctly rejected one stale hash
  after the requirement audit was updated. The changed audit hash was
  recomputed and the manifest refreshed; the subsequent gate passed **19/19**.
- The failed check is retained as provenance rather than hidden. This confirms
  that the review snapshot is fail-closed against post-freeze edits.
- Final validation: manifest gate, JSON/YAML parsing, and `git diff --check`
  pass; governance remains yellow. No release, push, or PR was performed.

## Current postflight — completion audit and external blocker confirmation

- Observed on **2026-08-09T17:54:07Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Updated the six-requirement audit with the current review manifest gate and
  neutral reviewer shortlist. Requirements 3 and 4 are satisfied as an
  internal draft, requirement 5 passes current internal gates, and applied
  validation remains correctly limited.
- Completion remains blocked by the same external state: no attributable human
  mathematical review and no independent expert novelty determination. The
  frozen packet and shortlist prepare that work but cannot perform it.
- Validation: review-manifest gate passes 19/19; JSON/YAML parsing and
  `git diff --check` pass. Governance remains yellow; no release, push, or PR
  was performed.

## Current postflight — neutral external-reviewer shortlist

- Observed on **2026-08-09T17:52:37Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `research/projected_trees_v5/review/EXTERNAL_REVIEWER_SHORTLIST_2026-08-09.md`.
  It maps public research profiles to the core theorem review, prior-art
  review, MOR comparison, and source-provenance comparison, with safeguards
  against implying contact, approval, or endorsement.
- Linked the shortlist from the review hub and request template. The manifest's
  template hash was recomputed after the link change.
- Validation: review-manifest gate passes after hash refresh; JSON/YAML parsing
  and `git diff --check` pass. Governance remains yellow; no release, push, or
  PR was performed.

## Current postflight — deterministic review-manifest gate

- Observed on **2026-08-09T17:50:51Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `scripts/verify_projected_trees_v5_review_manifest.ps1`, a fail-closed
  gate that parses the dated review manifest, requires all 19 rows, checks for
  duplicate or missing paths, and recomputes every SHA-256 hash.
- The gate passes: **19/19 frozen review artifact hashes verified**. It is
  reproducibility infrastructure only and does not replace proof review.
- Validation: manifest gate passed; JSON/YAML parsing and `git diff --check`
  pass. Governance remains yellow; no release, push, or PR was performed.

## Current postflight — frozen external-review artifact manifest

- Observed on **2026-08-09T17:49:19Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added `research/projected_trees_v5/review/REVIEW_ARTIFACT_MANIFEST_2026-08-09.md`,
  containing SHA-256 hashes for the manuscript, theorem registry, M8/M13--M23
  dossiers, novelty records, and review packet. The manifest explicitly uses
  file hashes rather than the dirty branch name as the snapshot identity.
- Recomputed the hashes after all review links were added; the manifest now
  matches the effective review inputs. It remains a reproducibility aid, not
  independent human approval.
- Validation: hash comparison, YAML/JSONL parsing, and `git diff --check`
  pass. Governance remains yellow; no release, push, or PR was performed.

## Current postflight — external-review normalization and scope sheet

- Observed on **2026-08-09T17:46:09Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Audited the M8/M14--M20 proof dossiers against the theorem registry and
  added `research/projected_trees_v5/review/NORMALIZATION_SCOPE_SHEET_2026-08-09.md`.
  The sheet fixes the meaning of `E^P`, `L_T`, `M`, `rho`, `eta`, and
  `C_T^P(eta)`, and maps each theorem to its exact topology, law-sharing,
  rank, field, arity, asymptotic, and exclusion conditions.
- Linked the sheet from the review hub, request template, packet, and
  requirement audit. No new mathematical inconsistency was found in the
  internal dossier cross-check; this remains preparatory material, not human
  approval.
- Validation: theorem registry YAML and JSONL ledger parse; `git diff --check`
  passes. Governance remains yellow; no release, push, or PR was performed.

## Current postflight — systematic theorem-by-theorem novelty audit expansion

- Observed on **2026-08-09T17:41:54Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Expanded the novelty record and theorem matrix with a category-based pass
  over tree-based projection/truncation, tensor-manifold step truncation,
  rank-adaptive TTN integration, bilinear MOR, semiring provenance, and
  adaptive-rank HT systems. Each V5 theorem family now has an explicit closest
  comparator, overlap, and unmatched hypothesis/constant/equality condition.
- Result: substantial adjacent prior art was confirmed, but no exact match was
  verified for the combined local closure residual, projected-root recursion,
  fixed-eta constants, and extremizer classes. `NOVELTY_NOT_ESTABLISHED`
  remains unchanged; this search is not expert novelty approval.
- Validation: novelty audit and theorem matrix updated; JSONL ledger remains
  parseable; `git diff --check` passed. Governance remains yellow; no release,
  push, or PR was performed.

## Current postflight — self-contained analytic proof spine in the main manuscript

- Observed on **2026-08-09T17:38:01Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added an analytic proof subsection to
  `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`. It records
  the Gram-matrix estimate, the scalar optimization producing `W_3(eta)`, the
  nuclear/operator-norm reduction for branching, and the finite-arity
  effective-law reduction. The main paper can now audit M13--M15 and M20
  without executing Python; the evaluator remains supplementary evidence.
- Validation: all three projected-graphs-v5 PDFs rebuilt and render-audited;
  main paper is now 9 pages; `tests/math_closure` **60/60 passed**;
  adaptive-tensor-network tests **16/16 passed**; M20/M21/M23 module entry
  points passed; `git diff --check` passed. Final governance audit passed
  non-strict with status `yellow`: 177 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and no missing required files.
- Governance remains structurally `yellow` because historical duplicate runs,
  novelty, independent human review, publication approval, and applied policy
  superiority remain unresolved. No release, push, or PR was performed.

## Current postflight — M23 exact operator reduction for strict same-law chain

- Observed on **2026-08-09T06:03:33Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- M23 proves an exact reduction for the finite real binary `k=3` chain with
  one repeated bilinear law, common projected leaf `e0`, and rank-one
  `P=span(e0)`: the projected error is
  `|<e0,A^3e0>-<e0,Ae0>^3|` for `A(x)=mu(x,e0)`. Every finite-dimensional
  contraction is realizable by a gated repeated law.
- Validation: M23 focused tests **3/3 passed**; full math-closure tests
  **59/59 passed**; non-slow KGR tests **180/180 passed**; repository
  collection is now **493 tests**. No low-eta extremal value was claimed.
- The remaining M23 operator optimization, rank-one/common-leaf branching,
  broader same-law/gated classes, novelty, human review, formalization, and
  FB15K237 performance gate remain explicitly open or blocked.

## Current postflight — FB15K237 precision/backend probe

- Observed on **2026-08-09T05:53:11Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- The reversible probe ran the preregistered FB15K237 acceptance test with
  `torch.set_float32_matmul_precision('high')`, without changing the model,
  data, seed, or acceptance configuration. The epoch completed correctly but
  took **456.6 s**, so the 300-second ceiling still fails. No backend precision
  setting was promoted into production.
- Verification after the probe: **56/56 math-closure tests passed**,
  **180/180 non-slow KGR tests passed** (7 slow tests deselected), and the
  repository collection remains **490 tests**. The low-eta rank-one/common-leaf
  same-law chain was only numerically probed; no theorem or claim was added.
- This is an engineering/resource blocker, not a correctness, mathematical,
  causal, novelty, or release result. Historical performance observations are
  preserved below rather than overwritten.

## Current postflight — KGR path-frontier reuse and FB15K237 performance gate

- Observed on **2026-08-09T05:33:52Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- The production training loop now reuses the identical path frontier for
  positive and negative readouts within each direction. Score and gradient
  equivalence tests pass, so this is an execution optimization rather than a
  model-definition change.
- Validation: **490 tests collected, 489 passed, 1 failed**. WN18RR full
  batched acceptance passed in 123.16 s. FB15K237 full batched acceptance
  completed in 424.8 s in the optimized run but failed the preregistered
  300-second ceiling; this is an open engineering performance gate, not an
  incomplete execution.
- PDFs were rebuilt/audited; JSON/YAML registries parsed; `git diff --check`
  passed; governance remains yellow with 177 historical runs, 9 unique
  scientific instances, 8 duplicate groups, and no missing required files.
- No mathematical claim, novelty status, historical artifact, release, push,
  or PR was changed by this performance follow-up.

## Current postflight — M22 high-eta rank-one/common-leaf same-law chain closure

- Observed on **2026-08-09T05:05:26Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- M22 closes the strict rank-one/common-leaf same-law binary k=3 chain in
  the high-eta regime `sqrt(2/3) <= eta <= 1`, attaining the independent-law
  value `W_3(eta)=2/(sqrt(3) eta)` with one repeated gated rotation law.
  Low-eta rank-one/common-leaf, branching, and broader gated/shared-law
  classes remain open.
- Validation: focused M13--M22 checks **26/26 passed**; **488/489 collected
  tests passed** through segmented execution and individual slow-test checks.
  WN18RR full batched training passed in 123.16 s; FB15K237 completed the
  epoch but failed the preregistered 300 s ceiling (424.8 s in the optimized
  run). Three PDFs were rebuilt/audited;
  no 'Overfull \\hbox' remains in the main paper log; JSON/YAML registries
  parsed; `git diff --check` passed.
- Current governance facts: 177 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 168 duplicate records, 177 complete artifact
  contracts, 175 'COMPLETE' and 2 'FAILED_RUNTIME' historical statuses.
- Supplemental bounded novelty search added adjacent primary sources for
  tensor-network multilinear complexity, provenance polynomials, and tensor
  renormalization; no theorem was promoted beyond `NOVELTY_NOT_ESTABLISHED`.
- Remaining boundary: low-eta rank-one/common-leaf same-law, branching and
  gated/shared-law variants, fixed-eta independent-law sharpness for k>=4,
  growing-tree uniformity, signed-forest exact constants, globally tight
  multilinear norms, novelty, human review, Lean/lake, and resource-gated
  schedules. No release, push, or PR was performed.

## Current postflight — M21 tagged same-law binary k=3 closure

- Observed on **2026-08-09T03:41:12Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- M21 proves that a single repeated bilinear law attains `W_3(eta)` for both
  binary k=3 chain and branching classes when finite orthogonal projected leaf
  tags and finite projector rank are allowed. An orthogonal direct-sum law
  simulates the M14/M15 blocks without increasing norm or closure budgets.
- Validation: focused M13--M21 checks **25/25 passed**; fresh full suite
  **487/487 passed** in 428.82s; three PDFs rebuilt/audited; no 'Overfull
  \\hbox' remains in the main paper log; JSON/YAML registries parsed;
  governance audit yellow with no missing required files; run deduplication
  completed.
- Current governance facts: 174 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 165 duplicate records, 174 complete artifact
  contracts, 172 'COMPLETE' and 2 'FAILED_RUNTIME' historical statuses.
- Remaining boundary: rank-one/common-leaf same-law, gated/variable-gate
  k=3 variants, fixed-eta independent-law sharpness for k>=4, growing-tree
  uniformity, signed-forest exact constants, globally tight multilinear norms,
  novelty, human review, Lean/lake, and resource-gated schedules. No release,
  push, or PR was performed.

## Current postflight — M20 exact k=3 all-finite-arity constant

- Observed on **2026-08-09T03:23:19Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- M20 proves that every finite ordered rooted tree with exactly three internal
  vertices and all internal arities at least two has the exact independent-law
  fixed-eta constant `C_{T,ind}^P(eta)=W_3(eta)`. Freezing unit leaf slots
  reduces the effective internal skeleton to chain or branching, and unit
  `e0` gates embed the M14/M15 witnesses into every finite arity profile.
- Validation: focused M14--M20 checks **22/22 passed**; fresh full suite
  **486/486 passed** in 430.78s; three PDFs rebuilt/audited; no 'Overfull
  \\hbox' remains in the main paper log; JSON/YAML registries parsed;
  governance audit yellow with no missing required files; run deduplication
  completed.
- Current governance facts: 173 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 164 duplicate records, 173 complete artifact
  contracts, 171 'COMPLETE' and 2 'FAILED_RUNTIME' historical statuses.
- Remaining boundary: same-law/gated k=3 variants, fixed-eta independent-law
  sharpness for k>=4, growing-tree uniformity, signed-forest exact constants,
  globally tight multilinear norms, novelty, human review, Lean/lake, and
  resource-gated schedules. No release, push, or PR was performed.

## Current postflight — M19 finite-arity asymptotic sharpness

- Observed on **2026-08-09T03:00:11Z** from branch
  'campaign/gate13-closeout' at source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'; additive changes remain
  uncommitted by design.
- M19 extends M18 to every fixed finite ordered rooted tree whose internal
  arities are at least two. On the real plane identified with C, the witness
  uses 'exp(i theta)' times the product at non-root nodes and the imaginary
  part of the root product; it gives
  'E_proj=|sin((k-1) arcsin(eta))|' and hence the asymptotic constant 'k-1'.
- Validation: focused M18/M19 checks passed; fresh full suite
  **485/485 passed** in 442.92s; three PDFs rebuilt/audited; no 'Overfull
  \hbox' remains in the main paper log; YAML/JSON registries parsed;
  'git diff --check' passed; governance audit yellow with no missing required
  files; run deduplication completed.
- Current governance facts: 172 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 172 complete artifact contracts, 170
  'COMPLETE' and 2 'FAILED_RUNTIME' historical statuses.
- Remaining boundary: fixed-eta independent-law sharpness, same-law/gated
  variants, uniformity for growing trees, signed-forest exact constants,
  globally tight multilinear norms, novelty, human review, Lean/lake, and
  resource-gated schedules. No release, push, or PR was performed.

## Current postflight — M18 finite-binary asymptotic sharpness

- Observed on **2026-08-09T02:39:46Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- M18 proves that for every fixed finite ordered full-binary tree `T` with
  `k` internal vertices, the independent-law projected-root constant obeys
  `lim_{eta downarrow 0} C_{T,ind}^P(eta)=k-1`. The explicit witness is
  two-dimensional real plane identified with C and has
  `E_proj=|sin((k-1) arcsin(eta))|`.
- Validation: focused M18 evaluator/tests passed; fresh full suite
  **483/483 passed** in 456.41s; three PDFs rebuilt/audited; no new
  `Overfull \hbox` remains; YAML/JSON registries parsed; `git diff --check`
  passed; governance audit yellow with no missing required files; run
  deduplication completed.
- Current governance facts: 171 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 171 complete artifact contracts, 169
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Remaining boundary: fixed-eta binary sharpness beyond the closed classes,
  higher-arity and growing-tree uniformity, variable-gate/arbitrary-leaf and
  non-planar shared-law variants, signed-forest exact constants, globally tight
  multilinear norms, novelty, human review, Lean/lake, and resource-gated
  schedules. No release, push, or PR was performed.

## Current postflight — M17 contractive gated-planar repeated-law closure

- Observed on **2026-08-09T02:16:47Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- M17 closes the explicitly defined repeated law
  `mu_A(x,y)=A*x*<e0,y>` with fixed gate, active planar contraction, and
  `||(I-P)A P||<=rho`: the exact normalized constant is `1`. The canonical
  orthogonal rotation remains a narrower `eta^2` subfamily.
- Validation: M17 focused test and evaluator passed; fresh full suite
  **481/481 passed** in 460.50s; three PDFs rebuilt/audited; registries
  parsed; `git diff --check` passed; governance audit yellow with no missing
  required files; run deduplication completed.
- Current governance facts: 170 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 170 complete artifact contracts, 168
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Remaining boundary: variable-gate, arbitrary-leaf, and non-planar gated
  variants; higher-arity/arbitrary finite topologies; growing-tree sharpness;
  signed-forest exact constants; globally tight norms; novelty; human review;
  Lean/lake; and resource-gated schedules. No release, push, or PR was
  performed.

## Current postflight — M16 arbitrary-node-law binary k=3 corollary

- Observed on **2026-08-09T02:03:39Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- M16 records the scope corollary that M14/M15 close the full binary `k=3`
  class with independently selectable node laws and no law-sharing constraint:
  both chain and branching constants equal `W_3(eta)`.
- Validation: focused M16/M14/M15 checks **16/16**; fresh full suite
  **480/480 passed** in 414.50s; three PDFs rebuilt/audited; registries
  parsed; `git diff --check` passed; governance audit yellow with no missing
  required files; run deduplication completed.
- Current governance facts: 169 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 169 complete artifact contracts, 167
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Remaining boundary: repeated same-law/gated subclasses, higher-arity and
  arbitrary finite topologies, growing-tree sharpness/uniformity, signed-forest
  exact constants, globally tight norms, novelty, human review, Lean/lake, and
  resource-gated schedules. No release, push, or PR was performed.

## Observation

- Observed on **2026-07-29** from branch `master` at commit
  `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`.
- The worktree was already dirty before the governance bootstrap. Existing
  generated artifacts, figures, indexes, and `.obsidian/` content are retained
  as user-owned state; this bootstrap must not be attributed to those changes.
- The repository contains typed finite-dimensional algebra modules, claim and
  theorem registries, canonical experiment configurations, run artifacts,
  deterministic generators, and a compiled-paper workflow.

## Scientific status

- The legacy `paper/main.tex` remains a broad finite-dimensional release note;
  its registered formal results are the curvature/associator expansion and
  finite cohomology descent under explicit hypotheses.
- A separate working-paper source now exists at
  `papers/foundations/main.tex`. It states and proves, within the declared
  finite-dimensional hypotheses, exact invariant reduction, a tree-level
  approximate-closure bound, associator stability, and spectral snapping with
  a no-gap counterexample. It is not yet an independently reviewed or
  release-approved mathematical contribution.
- Projector recovery, convergence, precision, and CP results are finite
  numerical observations unless their registry says otherwise.

## Operational status

- The new governance contract is local to this repository.
- Run deduplication and claim/evidence audits are required before release
  claims.
- The paper/software split has independent sources at
  `papers/foundations/main.tex` and `papers/software/main.tex`; both compile
  and render through `scripts/build_companions.ps1`.
- The latest structural audit is yellow and passes only in non-strict mode:
  all required files and run contracts are present, but duplicate historical
  runs and the paper quality flag keep release fail-closed.

## Latest postflight observation

- Observed on **2026-07-29T15:49:15Z** from branch
  `research/structure-preserving-reduction-v2` at commit
  `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`; the worktree remains dirty.
- The v2 track now has separate foundations and software sources, theorem and
  counterexample registries, a conservative prior-art matrix, 180 registered
  runs, 100 unique scientific instances, nine vector figure pairs, and
  fail-closed audit output under `artifacts/research_audit/`.
- The v2 numerical gates pass for the declared finite regime: 39 tests pass,
  all 180 rows complete, all 60 closure-bound rows respect the bound, and the
  five CPU/GPU parity rows have maximum absolute error below `1.5e-14`.
- The v2 research gate remains blocked because theorem-level novelty has not
  been established and verified author email/ORCID metadata are absent. The
  foundations PDFs are drafts/not for submission; the software companion is
  the reproducibility deliverable.
- Other repositories remain inspiration-only and were not edited.

## Final postflight observation

- Observed on **2026-07-29T15:54:40Z** from the same v2 branch and commit;
  the worktree remains dirty by design.
- The one-command rebuild completed all generation, compilation, rendering,
  and audit checks. Its exit code is `2` solely because the strict research
  gate correctly remains fail-closed on the two scientific/editorial
  blockers.
- Final regression status is 39 tests passed, 180 complete v2 runs, 100
  unique scientific instances, 60 bound checks passed, and five CPU/GPU
  parity rows with maximum absolute error `1.4210854715202004e-14`.

## V3 postflight observation

- Observed on **2026-07-29T18:13:56Z** from branch
  `research/nodewise-tree-constants-v3` at immutable source commit
  `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`.
- The v3 system implements typed ordered n-ary trees, exact and recursively
  projected evaluation, nodewise and path-sum certificates, exact subset
  expansions, telescoping-order optimization, signed forests, CP projection
  budgets, interval/SOS adapters, adversarial search, resumable experiments,
  artifact governance, and strict publication gates.
- The canonical 15-stage run completed generation, testing, CUDA parity,
  exact enumeration, the A--I base matrix, benchmark registration, vector
  figures, scientific tables, both manuscripts, page rendering, adversarial
  reviews, and technical audit. The technical audit passes.
- Verified totals are 69 passing tests, 81,445 enumerated tree occurrences,
  80,870 unique mathematical hashes, 15,493 deduplicated scientific
  instances, 1,530 exhaustive leakage masks, 18 principal vector figures,
  16 mandatory plus one supplementary table, and 37 visually inspected PDF
  pages. No registered theorem-bound violation was observed.
- Publication remains deliberately fail-closed (`FAIL_CLOSED_NOVELTY`, 9/15
  gates passing). Fixed-eta sharpness, theorem-level novelty, complete
  independent global certification, the resource-gated extended matrix, and
  independent human review remain unresolved. The pre-existing user-owned
  `.obsidian/workspace.json` modification is preserved and also keeps the
  clean-worktree gate false.
- Other repositories were used as inspiration only and were not edited.

## Update rule

This file is updated only by a postflight that records the command, environment,
commit, result, and limitation. Do not replace an old observation with an
unqualified present-tense statement.

## 2026-08-08 postflight — projected-graphs V5 completion pass

- Observed on **2026-08-08T22:25:19Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; the worktree is intentionally
  dirty with additive research, manuscript, registry, and generated-evidence
  changes.
- Completed the internally actionable portion of the follow-up: added the
  corrected growing-tree theorem under downstream-gain weighted summability;
  consolidated the finite source-polynomial/DAG calculus into its canonical
  theorem package; performed a bounded primary-source novelty audit; rebuilt
  the three V5 PDFs; and prepared an independent-review packet.
- Validation: YAML and JSON registries parsed; focused V5 tests passed
  **85/85**; `build_projected_graphs_v5_papers.ps1` completed successfully;
  `verify_projected_graphs_v5_papers.ps1` reported **3 PDFs rendered and
  audited**; a fresh full `python -m pytest -q` run completed with **450
  collected, 449 passed, and 1 pre-existing KGR negative-control failure**;
  governance audit passed non-strict with status `yellow`; run
  deduplication regenerated `artifacts/index/run_index_deduplicated.csv`.
- Current governance facts: 157 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 157 complete artifact contracts, and the
  latest full-suite history remains 450 executed / 449 passed / 1
  pre-existing out-of-scope KGR failure.
- Limitations: fixed-eta global k=3 sharpness and the strict supremum gap
  remain open; gated-planar repeated-law sharpness, dimension/rank reduction,
  arbitrary-tree and topology sharpness, globally tight multilinear norms,
  theorem-level novelty, independent human approval, Lean/lake formalization,
  and resource-gated experiments remain unresolved. This postflight does not
  authorize a release, novelty claim, push, or PR.

## 2026-08-08 postflight — M10b compactness refinement and full-suite repair

- Observed on **2026-08-08T22:52:22Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Closed the next internally available result: M10b proves a positive,
  class-dependent strict gap below `U_3(eta)` for every fixed finite
  dimension/rank class, using compactness plus M10 non-attainment. The global
  unbounded-dimension/rank supremum remains open. The declared gated-planar
  rotation value and the broader repeated-law scope were also clarified in
  the theorem and truth registries.
- Repaired the KGR leakage negative-control fixture to forward the evaluator's
  optional `context` while still forcing `training=True`; this preserves the
  intended leakage intervention rather than weakening the control.
- Validation: fresh full `python -m pytest -q` passed **450/450** in 418.75s;
  focused M2/M8/M9/M10/KGR checks passed; YAML/JSON registries parsed;
  manuscripts rebuilt and all three PDFs rendered/audited; governance audit
  passed non-strict with status `yellow` and no missing required files.
- Current governance facts: 158 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 158 complete artifact contracts.
- Limitations: no dimension/rank-uniform M10b gap, exact global fixed-eta
  `C_3^P(eta)`, arbitrary-tree sharpness, global topology sharpness, globally
  tight norms, external novelty, human review, Lean/lake, or resource-gated
  schedules are claimed closed. No release, push, or PR was performed.

## 2026-08-08 postflight — restricted Jacobiator theorem and full-suite expansion

- Observed on **2026-08-08T23:04:34Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Added a restricted exact theorem: the declared gated-planar rotation law
  has zero projected error for the three-term binary Jacobiator, independently
  of finite dimension and nontrivial coordinate-projector rank. The generic
  Jacobiator extremal constant remains separate and open.
- Added exact symbolic evaluator coverage, v3/v4 theorem-ledger entries, and
  explicit scope boundaries distinguishing the restricted law from arbitrary
  bounded multilinear laws.
- Validation: fresh full `python -m pytest -q` passed **451/451** in 405.87s;
  the exact script and focused signed-composition tests passed; YAML/JSON
  registries parsed; all three V5 PDFs rendered/audited; governance audit
  passed non-strict with status `yellow` and no missing required files.
- Current governance facts: 159 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 159 complete artifact contracts.
- Limitations: generic signed-forest constants, global k=3 sharpness,
  dimension/rank-uniform gaps, arbitrary-tree/topology sharpness, globally
  tight norms, novelty, independent human review, Lean/lake, and resource-
  gated schedules remain open or blocked. No release, push, or PR was performed.

## 2026-08-08 postflight — all-finite-k left-comb gated-rotation formula

- Observed on **2026-08-08T23:17:28Z** from branch `campaign/gate13-closeout`
  at source commit `cbb6ddb0a050882249054f9044c905e442a561ab`; additive
  changes remain uncommitted by design.
- Added and registered the exact restricted family theorem
  `E_proj=|T_k(c)-c^k|` for every finite left-comb binary chain under the
  declared homogeneous gated-planar rotation law, in the `M=L=1`
  normalization with `c=sqrt(1-eta^2)`; general-`M` scaling is `M^k`.
- Validation: exact evaluator passed; focused test passed; full
  `python -m pytest -q` passed **452/452** in 409.83s; registries parsed; all
  three V5 PDFs rendered/audited; governance audit passed yellow with no
  missing required files; run deduplication completed.
- Current governance facts: 160 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 160 complete artifact contracts.
- Limitations: global fixed-eta `C_3^P`, dimension/rank-uniform gaps,
  arbitrary-tree and non-left-comb topology sharpness, generic signed-forest
  constants, globally tight norms, novelty, human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR
  was performed.

## 2026-08-09 postflight — M11 conditional quantitative k=3 gap

- Observed on **2026-08-09T00:01:58Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Proved and registered M11 for the ordered `k=3` chain: under exact
  first-propagator operator-norm saturation at the second node, the
  normalized projected error is at most `sqrt(4-3*eta^2)` for
  `eta<=sqrt(2/3)` and `2/(sqrt(3)*eta)` thereafter. The result is a
  conditional quantitative gap below M9, not a global supremum closure.
- Validation: exact M11 script and focused test passed; fresh full
  `python -m pytest -q` passed **455/455** in 442.90s; registries parsed;
  all three V5 PDFs rendered/audited; governance audit passed non-strict with
  status `yellow` and no missing required files; run deduplication completed.
- Current governance facts: 163 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 163 complete artifact contracts.
- Limitations: unrestricted fixed-eta `C_3^P`, dimension/rank-uniform
  reduction, arbitrary-law sharpness, generic signed constants, globally
  tight norms, novelty, independent human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR
  was performed.

## 2026-08-10 postflight — SRATM G6 all-entity VALID

- Executed the frozen SRATM step4600 compression evaluator on all 35,070
  reciprocal VALID queries against all 14,541 entities, CPU-only, candidate
  blocks of 1,024 and query batches of 256. TEST was not read, hashed, or
  opened.
- Candidate-specific certificate validity passed at full scale: 0 observed
  violations over 509,952,870 candidate scores; max(error-bound) was
  `3.2186508e-06` under the declared numerical tolerance.
- Under the sealed TRAIN+VALID-only filter protocol, full-rank control MRR was
  `0.3958612331` and uniform-medium compressed MRR was `0.3674372365`
  (`delta=-0.0284239966`).
- G6 preservation against the historical teacher reference MRR `0.6116475463`
  is **BLOCKED_REFERENCE_PROTOCOL_MISMATCH** (`delta=-0.2157863132`). The
  historical reference filter provenance was not reconstructed because TEST
  remains sealed; no TEST read was used to resolve the discrepancy.
- Artifact: `runs/SRATM_CERTIFIED_COMPRESSION_V1_G6_ALL_ENTITY_VALID_FINAL2_20260810/result/`.
- Focused regression suite passed `6/6`; no hardware timing was run and
  B-0012 remains active. This is pre-test validation, not a TEST or hardware
  claim.

## 2026-08-10 postflight — historical VALID reconciliation differential audit

- Executed `HISTORICAL_VALIDATION_RECONCILIATION_V1` on 64 deterministic
  VALID rows with a 551-candidate pool including every gold entity. TEST was
  not read, hashed, or opened.
- Current SRATM branch-wise scorer and official model scorer agreed to max
  absolute error `7.15e-7`; positive-score versus candidate extraction agreed
  to `5.96e-7`; reciprocal construction had `0` errors.
- The sealed sample produced combined MRR `0.3730595` under TRAIN+VALID
  filters and `0.3440464` under TRAIN-only filters. The historical reference
  remains `0.6116475`, but its exact loader/filter/rank provenance is not
  reconstructed. Code inspection shows the historical trainer loader required
  a test path; this is evidence to investigate, not proof that the historical
  run used TEST-derived information.
- G6 is now tracked as G6A certificate scalability PASS, G6B uniform-medium
  predictive preservation FAIL, and G6C historical reconciliation BLOCKED.
- Artifact: `runs/HISTORICAL_VALIDATION_RECONCILIATION_V1_20260810_FINAL/result/`.

- Checkpoint forensics: `checkpoint_last.pt` is embedded step `4600`, SHA256
  `aae9c67b...d462f085`, and matches the hash in `audit_step4600.json`;
  `checkpoint_best.pt` is a distinct step `4608` artifact with SHA256
  `00963b77...4730d45`. The historical audit therefore points to `last`, not
  `best`.

## 2026-08-10 postflight — historical evaluator provenance forensic audit

- Executed `HISTORICAL_EVALUATOR_PROVENANCE_V1` without opening, reading, or
  hashing TEST. The historical run directory contains no launch command,
  stdout, evaluator manifest, filter counts, rank trace, or source snapshot.
- Source evidence confirms the historical SRATM trainer path required
  `--test`; its normal loader read `test_path`, built entity/relation maps from
  TRAIN+VALID+TEST, and built filters from TRAIN+VALID+TEST. The sealed
  compression loader uses TRAIN+VALID only. This is a high-priority open
  protocol discrepancy, not proof that the historical run consumed TEST.
- Checkpoint identity, current branch score path, positive/gold extraction,
  and reciprocal construction are ruled out on available evidence. Tie policy,
  historical candidate universe, exact command/runtime, and actual TEST
  consumption remain unknown.
- Artifact:
  `runs/HISTORICAL_EVALUATOR_PROVENANCE_V1_20260810/result/`.

- Verification: focused forensic/KGE suite passed **8/8**; `git diff --check`
  passed; governance audit passed non-strict with status `yellow` and no
  missing required files; run deduplication completed. No TEST, SOTA,
  generalization, or hardware claim is made.

## 2026-08-10 postflight — new sealed SRATM training from zero

- Added `SRATM_SEALED_TRAINING_V1`, a runner with no `--test` argument,
  TRAIN+VALID-only vocabulary/filters, fail-closed open sentinel, random
  initialization, frequent checkpoints, and explicit provenance.
- The new run started from random weights, reached checkpoint step `192`, was
  resumed under the same sealed protocol, and was paused immediately after
  checkpoint step `704` at user request. No historical SRATM checkpoint was
  loaded and TEST was not read, hashed, or opened.
- The completed canary evaluation at step `256` used 2,048 validation queries
  and reported pilot MRR `0.1573365927`; this is an early empirical training
  signal, not a quality claim. The authoritative current state is the paused
  step-704 checkpoint.
- Peak allocated GPU memory was `18,182,203,392` bytes (~16.93 GiB); peak
  reserved memory was `18,863,882,240` bytes (~17.57 GiB). The configured cap
  was 23 GiB. No agent thermal gate was applied.
- Artifact:
  `runs/SRATM_FB15K237_SEALED_FROM_ZERO_D256_B512_23GB_2026-08-10/`.

## 2026-08-10 postflight — full VALID audit of sealed step 704

- Executed a full filtered VALID audit on the new sealed checkpoint `step=704`
  over 35,070 queries and 14,541 entities using GPU. The checkpoint SHA256 is
  `7afd916f7171587cc74654005353734c9fcfc4f381ef720ef7464ca7d6154306`.
- Metrics under the sealed TRAIN+VALID-only protocol: MRR `0.3273196220`,
  H@1 `0.2674365637`, H@3 `0.3516110778`, H@10 `0.4477331042`, mean rank
  `2214.8643`. Tail MRR was `0.4206288457`; head MRR was `0.2340104431`.
- Relative to the reproducible historical sealed control `0.3958612331`,
  the new step-704 checkpoint is `-0.0685416110` MRR. Relative to historical
  `0.6116475463`, the delta is `-0.2843279243`, but that comparison remains
  `NOT_ESTABLISHED_PROTOCOL_MISMATCH`.
- Runtime sentinel recorded zero forbidden accesses; only TRAIN, VALID, and
  the new checkpoint were opened. No TEST was read, hashed, or opened. Peak
  audit memory was `1,146,633,216` bytes allocated and `1,713,373,184` bytes
  reserved.
- Artifact:
  `runs/SRATM_FB15K237_SEALED_FROM_ZERO_D256_B512_23GB_2026-08-10/audit_step704_full_valid/`.

## 2026-08-10 postflight — sealed teacher closure provenance gate

- The controlled resume gate inspected the step-704 checkpoint without opening,
  reading, stat-ing, or hashing TEST. The checkpoint is structurally complete:
  model, EMA teacher, optimizer, RNG, epoch, step, and sealed protocol are
  present; all persisted floating-point state is finite; no scheduler is
  configured in the runner.
- Resume was stopped fail-closed as `RESUME_PROVENANCE_FAILURE`. The run
  manifest records git `cf663bc6…`, but that commit does not contain the sealed
  trainer; the current checkout is `77f2dfe…`. The run's persisted
  `config.json` also conflicts with the checkpoint protocol (`max_steps=256`
  versus `1024`).
- No continuation, new checkpoint, convergence claim, teacher freeze, spectral
  audit, compression, or G6 result was produced from this ambiguous state.
- Evidence: `runs/SRATM_FB15K237_SEALED_FROM_ZERO_D256_B512_23GB_2026-08-10/resume_manifest.json`.
- Scientific status remains `NOT_ESTABLISHED`; the step-704 result remains
  `CLEAN_INTERMEDIATE`, not `SEALED_TEACHER_FROZEN`.

## 2026-08-10 postflight — SRATM certified compression and no-leakage audit

- Executed `SRATM_CERTIFIED_COMPRESSION_V1` on the immutable SRATM step4600
  checkpoint without reading, hashing, or opening TEST. Full-rank factor
  equivalence passed with max absolute error `7.7486e-7` and rank equality
  `1.0`. The bounded candidate-pool certificate pass had zero violations for
  uniform low/medium/high policies; official all-entity MRR preservation and
  matched GPU speedup remain open/blocked.
- Executed `SRATM_NO_LEAKAGE_AUDIT_V1D_20260810`. Runtime sentinel recorded
  train, valid, and checkpoint accesses only; forbidden TEST accesses were
  zero. Train-valid exact overlap was zero; reciprocal closure failures were
  zero. The audit is observed execution evidence, not a universal proof.
- Static scan still finds TEST defaults in alternative TTN/hardware loaders;
  those paths were not executed by the sealed SRATM campaign. Vocabulary is
  explicitly `TRAIN_PLUS_VALID` under a declared transductive-universe rule,
  not train-only. Checkpoint selector reconstruction remains pending.
- Evidence:
  `runs/SRATM_CERTIFIED_COMPRESSION_V1_20260810_CPU_OPT5/result/`,
  `runs/SRATM_NO_LEAKAGE_AUDIT_V1D_20260810/`,
  `seion_kgr/sratm_certified_compression.py`, and
  `seion_kgr/no_leakage_audit.py`.

## 2026-08-10 postflight — accuracy-first KGE discovery track

- Declared a separate exploratory `KGE_SOTA_DISCOVERY_V1` protocol. It does
  not modify the frozen certified confirmatory protocol and keeps test closed
  until validation-only finalist selection is complete.
- Added reusable discovery primitives for dynamic hard-negative mining,
  InfoNCE, weighted top-k margin loss, EMA teacher updates, and an entity
  snapshot queue in `seion_kgr/sota_discovery.py`.
- Added `seion_kgr/train_sota_discovery.py`, a bounded structural-only runner
  using an EMA teacher to mine hard negatives and an online tensor scorer to
  optimize InfoNCE plus top-k margin loss. External text is intentionally off
  until its provenance and data contract are registered.
- Validation: focused discovery, score-space, and TTN tests passed **19/19**;
  the tiny CPU discovery canary completed two steps and wrote a resumable
  checkpoint/result artifact.
- Limitations: no SOTA accuracy result, no external-text result, no WN18RR
  discovery result, and no long GPU run. B-0012 remains an execution hold for
  sustained GPU escalation.

## 2026-08-10 update — formal teacher/student boundary

- Program A and Program B are now explicit in the SOTA discovery protocol.
  Program A selects a high-capacity teacher on validation; Program B starts
  only after teacher freeze and handles distillation, spectral compression,
  certification, and hardware allocation.
- Added leakage-aware split contracts, deterministic retriever unions,
  filtered hard-negative mining, no-gradient EMA teacher, convex query gate,
  validation score normalization/ensemble, listwise loss, and margin
  distillation loss under `seion_kgr/sota/`.
- Text retrieval and contextual reranking remain disabled until a provenance
  and data-access contract exists. No SOTA claim is created.

## 2026-08-10 update — thermal safety stop during VRAM ramp

- The 12 GB repeat canary passed with the stable 8 GB workload: 2,048 steps,
  finite loss `0.0724854`, peak `754.5 MB allocated / 914.4 MB reserved`, and
  post-run GPU `0 MB`.
- The 16 GB canary with batch `4096` passed 512 steps with finite loss
  `0.11931`, peak `1.37 GB allocated / 1.75 GB reserved`, and post-run GPU
  `0 MB`.
- The 20 GB / batch `8192` canary reached `89 C` at `92%` utilization, above
  the declared `85 C` thermal gate. It was terminated, its partial checkpoint
  and logs were preserved, and the post-termination GPU returned to `0 MB` and
  `72 C`. No BSOD or OOM occurred in this attempt.
- The agent-side thermal threshold has been removed per user instruction. A
  bounded 23 GB canary may use the system/driver protections only; long runs
  remain subject to B-0012 review.
- Added the first `SpectralConditionalTensorMixture` scorer with sparse
  relation routing, orthonormal spectral bases, Tucker core mixtures and
  log-sum-exp fusion. CPU shape/parity/Lipschitz/gradient tests passed `28/28`;
  a D256 GPU smoke test with 8 experts and 1,024 candidates also completed.

## 2026-08-10 update — 23 GB-cap system-managed canary

- With the agent-side thermal threshold removed, a bounded 23 GB-cap canary
  ran for 256 steps at batch `8192` without OOM, BSOD, or non-finite loss.
- Result: loss `0.17527`, duration `92.8 s`, peak `2.61 GB allocated / 3.38 GB
  reserved`, and post-run GPU `0 MB` at `71 C`.
- This validates only bounded execution under the system/driver protections;
  the cap did not force 23 GB allocation and no quality/SOTA claim follows.

## 2026-08-09 postflight — matched-tolerance DAG resource study

- Added exact compressed-coordinate execution and a deterministic resource
  proxy to the shared-DAG backend. The compressed path agrees with the
  projected ambient path algebraically; shared nodes are counted once in the
  contraction and activation schedule.
- Executed the exploratory matched-tolerance probe: 12 seeds, 180 candidate
  allocations, 97 validation-selected allocations, three tolerances, and an
  independent test batch. The result is reproducible (SHA-256
  `BC3C7C50B87EA188AB1696CD195EF8AD07F47CC430EFC607265D0463A1ADB3B6`).
- All selected global and rank-aware certificates held on the test cases, but
  test tolerance transfer was partial (0.50--0.667 for certificate methods at
  the reported thresholds), and certificate policies had negative mean
  contraction-unit reduction versus uniform. This directly evaluates the
  error/resource tradeoff while remaining a negative/context-dependent
  applied result.
- Validation: adaptive application tests **33/33**, DAG/path/math tests
  **77/77**, compilation, deterministic rerun, registry parsing, governance
  audit, run deduplication, and `git diff --check` passed. Analytical resource
  proxies are not hardware timing; multi-topology structured-network utility,
  novelty, human review, and formal verification remain open.

## 2026-08-09 postflight — finite DAG domain certificate and rank allocation

- Implemented `src/seion_core/research_v5/dag_domain_certificate.py` for
  finite multilinear DAGs with bounded leaf domains, operator enclosures, and
  rank-indexed normal-residual enclosures. Shared nodes are computed once;
  repeated input slots and downstream fan-out retain their multiplicities.
- Added reverse downstream gains and an exact finite knapsack DP for rank
  allocation under rank-independent enclosures, plus proof, theorem-registry,
  and truth-ledger artifacts. This is a finite enclosure theorem, not a sharp
  extremal constant or a universal certificate for empirical norm estimates.
- Validation: focused DAG plus `tests/math_closure` passed **69/69**;
  `applications/adaptive_tensor_network/tests` passed **22/22**; full
  `python -m pytest -q` passed **502/503**. The sole failure is the existing
  FB15K-237 batched performance ceiling: completed in **406.3 s** against the
  300 s threshold. Registry parsing, governance audit, deduplication, and
  `git diff --check` passed. No release, push, or PR was performed.

## 2026-08-09 postflight — shared-DAG tensor-network validation

- Added `applications/adaptive_tensor_network/src/dag.py`,
  `dag_network.py`, and `dag_allocation.py`: a numerical DAG backend with
  shared-node evaluation, projection/truncation, global domain certification,
  and certificate-driven rank allocation.
- Added a rank-aware DAG certificate that tracks projected operator norms,
  approximate values, and mixed telescoping factors; its small-DAG exhaustive
  allocator is kept separate from the scalable rank-independent DP.
- Extended the diamond probe to 420 records with 20 seeds and three methods.
  Both certificates held on **140/140** matched cases. The rank-aware
  allocator beat uniform on **16.4%** of held-out sup-error comparisons and
  had mean reduction **-0.007448**; no applied superiority claim is supported.
- Validation: adaptive application tests **28/28**, math-closure plus DAG
  certificate tests **70/70**, artifact parsing passed. No release, push, or
  PR was performed.

## 2026-08-09 postflight — exact nonnegative DAG path constant

- Added `src/seion_core/research_v5/dag_path_constant.py` and the proof note
  `research/math_closure/dag/exact_path_constant.tex`. For the declared
  nonnegative first-order channel envelope, the exact root constant is the sum
  of local source bounds weighted by all source-to-root path products; shared
  fan-out and parallel repeated slots are counted exactly.
- Registered `THM_V5_EXACT_NONNEGATIVE_DAG_PATH_CONSTANT` with sharpness scoped
  to the channel class. Simultaneous attainment in the original multilinear
  operator class remains a separate open compatibility problem.
- Validation: DAG/path/math suite **73/73**, registry parsing passed. No
  release, push, or PR was performed.

## 2026-08-09 postflight — shared-diamond DAG asymptotic sharpness

- Closed a nontrivial full multilinear DAG class asymptotically: for the fixed
  independent-law diamond with one shared projected node, two projected
  branches, and an unprojected root, the universal path coefficient is 4.
- The complex-plane law `mu_theta(z,w)=exp(i theta) z w`, with
  `theta=arcsin(eta)`, has exact witness error
  `|exp(4 i theta)-cos(theta)^4|`, proving the normalized ratio tends to 4 as
  eta decreases to zero. Fixed-eta and arbitrary-DAG sharpness remain open.
- Validation: dedicated diamond tests **2/2**, combined DAG/path/math suite
  **75/75**, registries parse. No release, push, or PR was performed.

## 2026-08-09 postflight — fixed-DAG independent-law asymptotic sharpness

- Generalized the diamond witness to every fixed finite ordered acyclic DAG.
  If `K(G)` is the total projected source-to-root slot-path multiplicity, the
  universal recurrence gives `E <= K(G) eta`, and complex product laws give
  exact witness error `|exp(i K(G) theta)-cos(theta)^K(G)|` with
  `theta=arcsin(eta)`. Hence the independent-law asymptotic constant is
  exactly `K(G)` for every fixed DAG in the declared class.
- Validation: combined DAG/path/math suite **77/77**, registry parsing passed.
  Fixed-eta equality, unbounded-DAG uniformity, and same-law/gated variants
  remain open. No release, push, or PR was performed.

## 2026-08-09 postflight — numerical verification of the fixed-DAG witness

- Added real tensor-core tests for the general complex-product witness on a
  chain, shared diamond, and repeated-slot DAG. Observed root errors match the
  exact `K(G)` witness formula to numerical tolerance.
- Validation: adaptive application suite **31/31**, theory DAG/path suite
  **77/77**, compile and registry checks passed. No release, push, or PR was
  performed.

## 2026-08-09 postflight — manuscript, novelty, and independent-review refresh

- Observed on **2026-08-09T17:15:57Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- The mathematical manuscript now presents the universal `k-1` theorem,
  `k=2` equality/sharpness, M14--M20 finite-arity spine, and M21--M23 as a
  later, explicitly scoped same-law/shared-operator section. It states that
  independent laws, same-law reuse, rank-one/common-leaf constraints, and
  fixed finite topology are distinct classes.
- The bounded theorem-to-theorem novelty audit was broadened to hierarchical
  tensor truncation, tree-tensor dynamics/stability, randomized TT rounding,
  and projection-based MOR. The result remains `NOVELTY_NOT_ESTABLISHED`.
- Validation: math-closure **59/59** and focused V5 regression **85/85**;
  all three projected-graphs-v5 PDFs rebuilt and audited; governance audit
  passed non-strict with status `yellow` and no missing required files; run
  deduplication completed; `git diff --check` passed.
- Limitations: this is preparation for independent review, not independent
  approval. Low-eta M23 value, broader same-law/gated classes, fixed-eta
  sharpness for `k>=4`, growing-tree uniformity, theorem-level novelty,
  publication approval, applied allocator superiority, and Lean/lake remain
  open or blocked. No release, push, or PR was performed.

## 2026-08-09 postflight — internal theorem audit and M21 certificate repair

- Observed on **2026-08-09T17:22:32Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- The pre-review audit checked the universal theorem and M8/M14--M23 against
  their proof dossiers, registries, witnesses, and tests. M20 now states the
  effective-law reduction and explicitly shows that freezing unit projected
  leaves cannot increase operator or closure-defect budgets.
- M21's structural direct-sum certificate is now computed from block norms and
  defect blocks. A first strict test exposed and then corrected the distinction
  between realized defect `min(eta,sqrt(2/3))` and external cap `eta`.
- Validation: focused M20/M21/M23 **6/6**; full math-closure **60/60**;
  module entry points for M20/M21/M23 passed; theorem registry YAML, ledger
  JSON, and `git diff --check` passed.
- The internal audit is evidence preparation only. Independent human review,
  novelty determination, publication approval, applied allocator superiority,
  low-eta M23 optimization, broader same-law/gated classes, and formalization
  remain open or blocked. No release, push, or PR was performed.

## 2026-08-09 postflight — exact-phrase novelty search extension

- A bounded formula-oriented search added primary/publisher comparators for TTN
  dynamics, stochastic tensor-network projection, and tensor-network/multilinear
  contraction theory to the novelty audit.
- No exact theorem match for the V5 `W_3`/projected-root/local-residual package
  was verified in that search. This does not establish novelty; the status
  remains `NOVELTY_NOT_ESTABLISHED` pending expert theorem-to-theorem review.

## 2026-08-09 postflight — six-requirement completion audit

- The objective was audited requirement-by-requirement in
  `research/projected_trees_v5/review/OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md`.
- Internal draft readiness is supported for the concentrated manuscript,
  scope definitions, and reproducibility gates. Independent review and
  exhaustive novelty remain explicitly unsatisfied; applied results remain
  limited to predictive/correlation evidence rather than allocator superiority.
- Local evidence paths were checked, focused M20/M21/M23 tests passed **6/6**,
  and all three PDFs passed the render audit. No scientific status was upgraded.

## 2026-08-09 postflight — external review request template

- A ready-to-send external review request now defines the minimum reading set,
  theorem-by-theorem questions, verdict vocabulary, and separate novelty review
  fields in `research/projected_trees_v5/review/EXTERNAL_REVIEW_REQUEST_TEMPLATE.md`.
- It remains intentionally unfilled: no reviewer, novelty decision, or
  publication recommendation has been supplied.

## 2026-08-09 postflight — canonical review hub

- `research/projected_trees_v5/review/README.md` is now the canonical index for
  the external-review request, packet, objective audit, theorem sources,
  novelty records, and verification commands. The hub is preparation only and
  leaves all reviewer fields unfilled.

## 2026-08-09 postflight — applied validation status

- The application track now has a canonical status note at
  `applications/adaptive_tensor_network/results/APPLIED_VALIDATION_STATUS_2026-08-09.md`.
- The registered Level 1 analysis was rerun from raw records: Pearson
  `0.9334132264`, Spearman `0.9216239741`; `pathwise_global` supports only the
  comparison against `singular_energy`, not against `uniform` or
  `local_error_greedy`. Application tests passed **16/16**.
- No technology-superiority claim was added; matched-error memory/runtime
  validation remains a future requirement.

## 2026-08-09 postflight — M14/M15 exact independent-law k=3 constants

- Observed on **2026-08-09T01:26:56Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Closed the fixed-eta independent-law constants for both binary `k=3`
  topologies: `C_3,ind,chain^P(eta)=W_3(eta)` by M14, and
  `C_3,ind,branch^P(eta)=W_3(eta)` by M15 nuclear/operator-norm duality.
  The exact value is `sqrt(4-3*eta^2)` up to `sqrt(2/3)` and
  `2/(sqrt(3)*eta)` thereafter. M10 is now explicitly scoped to the chain;
  its former branching extension is preserved as historical provenance.
- Validation: M13/M14/M15 and regression tests passed; fresh full
  `python -m pytest -q` passed **478/478** in 416.33s; registries parsed;
  `git diff --check` passed; all three V5 PDFs rebuilt, rendered, and audited;
  governance audit passed non-strict with status `yellow` and no missing
  required files; run deduplication completed.
- Current governance facts: 167 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 167 complete artifact contracts, 165
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Limitations: same-law/gated subclasses, arbitrary-tree `(k-1)` sharpness,
  globally tight norms beyond current finite enclosures, theorem-level novelty,
  independent human review, Lean/lake, and resource-gated schedules remain
  open or blocked. No release, push, or PR was performed.

## 2026-08-09 postflight — M13 unconditional chain quantitative envelope

- Observed on **2026-08-09T01:00:23Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Proved and registered the unconditional chain-only envelope
  `C_3,ind,chain^P(eta) <= W_3(eta)`, with
  `W_3=sqrt(4-3*eta^2)` for `eta<=sqrt(2/3)` and
  `W_3=2/(sqrt(3)*eta)` thereafter. The explicit comparison gives
  `W_3<U_3` for every `0<eta<=1`.
- Validation: focused M13/M10/support/source-calculus tests passed; fresh
  full `python -m pytest -q` passed **463/463** in 470.42s; registries parsed;
  `git diff --check` passed; all three V5 PDFs rebuilt, rendered, and audited;
  governance audit passed non-strict with status `yellow` and no missing
  required files; run deduplication completed.
- Current governance facts: 166 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 166 complete artifact contracts, 164
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Limitations: M13 is chain-only and not asserted sharp; branching's tightened
  envelope, exact chain/branching constants, unbounded-tree uniformity,
  signed-forest constants, novelty, independent human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR was
  performed.

## 2026-08-09 postflight — finite source calculus and endpoint k=3 gap

- Observed on **2026-08-09T00:41:29Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Closed and registered the finite source-resolved error calculus: exact
  multi-index DAG polynomials, topological/recursive agreement, same-source
  first-order recombination, finite truncation remainder bounds, and signed
  inequalities `B_actual <= B_signed <= B_treewise`.
- Extended M10 to `eta=1`: the M9 optimizer is interior at
  `q*=M/sqrt(2)`, so non-attainment persists; finite support compression and
  compactness give `C_3,ind^P(1) < U_3(1)=sqrt(2)`. Together with the prior
  interval result, the strict global gap now holds for `0<eta<=1`.
- Validation: full `python -m pytest -q` passed **461/461** in 411.30s;
  focused source-calculus and endpoint checks passed; all three V5 PDFs were
  rebuilt and audited; registries parsed; `git diff --check` passed;
  governance audit passed non-strict with status `yellow` and no missing
  required files; run deduplication completed.
- Current governance facts: 165 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 165 complete artifact contracts, 163
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Remaining limits: exact `C_3^P(eta)`, explicit quantitative gap, gated
  repeated-law sharpness, arbitrary-tree `(k-1)` sharpness, unbounded-tree
  uniformity, globally tight norms, novelty, independent human review,
  Lean/lake, and resource-gated schedules remain open or blocked. No release,
  push, or PR was performed.

## 2026-08-09 postflight — fixed-tree support compression and global k=3 gap

- Observed on **2026-08-09T00:20:31Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Proved and registered projector-invariant support compression for every
  fixed finite typed tree, with
  `dim(W_tau) <= 2*(leaf_count_tau + 2*node_count_tau)` per type. The binary
  `k=3` one-type support bound is `20`, or `22` with proper-projector padding.
- Combined this finite reduction with M10 pointwise non-attainment and
  compactness to close the global strict supremum gap
  `C_3,ind^P(eta) < U_3(eta)` for `0 < eta < 1` in the declared independent-law
  binary chain and branching classes.
- Validation: exact support-compression script and focused tests passed;
  fresh full `python -m pytest -q` passed **457/457** in 410.61s; registries
  parsed; `git diff --check` passed; all three V5 PDFs rendered/audited;
  governance audit passed non-strict with status `yellow` and no missing
  required files; run deduplication completed.
- Current governance facts: 164 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 164 complete artifact contracts, 162
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Limitations: exact `C_3^P(eta)`, an explicit quantitative gap, endpoint
  `eta=1`, uniform dimension/rank control for unbounded tree size/arity,
  same-law/gated global sharpness, arbitrary-tree `(k-1)` sharpness, signed
  forest constants, globally tight multilinear norms, novelty, independent
  human review, Lean/lake, and resource-gated schedules remain open or
  blocked. No release, push, or PR was performed.

## 2026-08-09 postflight — k=2 class-A closure and final M14/M15 verification

- Observed on **2026-08-09T01:48:13Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Closed the declared finite-dimensional real binary `k=2` class-level
  constant: `C_{2,A}^P(eta)=1` for `0<eta<=1`. The universal upper bound and
  the explicit embedded repeated-law rank-two witness match exactly.
- Corrected current ledger fields that still described the superseded M10
  strict-gap formulation as current; historical sections remain preserved and
  now point explicitly to M14/M15.
- Validation: focused checks passed **18/18**; fresh full
  `python -m pytest -q` passed **479/479** in 426.02s; YAML/JSON registries
  parsed; all three V5 PDFs rebuilt/audited; governance audit passed non-strict
  with status `yellow`; run deduplication completed.
- Current governance facts: 168 historical runs, 9 unique scientific
  instances, 8 duplicate groups, 168 complete artifact contracts, 166
  `COMPLETE` and 2 `FAILED_RUNTIME` historical statuses.
- Remaining boundary: broader gated-planar repeated-law classes, same-law/gated
  `k=3`, arbitrary-tree independent-law sharpness, unbounded-tree uniformity,
  globally tight norms, novelty, independent human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR was
  performed.

## 2026-08-08 postflight — topology-wide and variable-arity gated-rotation closure

- Observed on **2026-08-08T23:44:28Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Closed and registered the exact recursive `a(T),d(T)` formula for every
  finite ordered full-binary topology, then extended it to every finite
  ordered rooted tree with arity at least two under arity-compatible
  homogeneous gated-planar rotations. These are restricted-family results,
  not global arbitrary-law sharpness results.
- Validation: exact scripts and focused tests passed; fresh full
  `python -m pytest -q` passed **454/454** in 437.57s; registries parsed;
  PDF render/audit passed for all three V5 PDFs; governance audit passed
  non-strict with status `yellow` and no missing required files; run
  deduplication completed.
- Current governance facts: 162 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 162 complete artifact contracts.
- Limitations: global fixed-eta independent-law sharpness, dimension/rank-
  uniform reduction, arbitrary-law and independent topology sharpness,
  generic signed-forest constants, globally tight norms, novelty, independent
  human review, Lean/lake, and resource-gated schedules remain open or
  blocked. No release, push, or PR was performed.

## 2026-08-09 postflight — M11 conditional quantitative k=3 gap

- Observed on **2026-08-09T00:00:08Z** from branch
  `campaign/gate13-closeout` at source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`; additive changes remain
  uncommitted by design.
- Proved and registered M11 for the ordered `k=3` chain: under exact
  first-propagator operator-norm saturation at the second node, the
  normalized projected error is at most `sqrt(4-3*eta^2)` for
  `eta<=sqrt(2/3)` and `2/(sqrt(3)*eta)` thereafter. The result is a
  conditional quantitative gap below M9, not a global supremum closure.
- Validation: exact M11 script and focused test passed; fresh full
  `python -m pytest -q` passed **455/455** in 442.90s; registries parsed;
  all three V5 PDFs rendered/audited; governance audit passed non-strict with
  status `yellow` and no missing required files; run deduplication completed.
- Current governance facts: 163 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and 163 complete artifact contracts.
- Limitations: unrestricted fixed-eta `C_3^P`, dimension/rank-uniform
  reduction, arbitrary-law sharpness, generic signed constants, globally
  tight norms, novelty, independent human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR
  was performed.
