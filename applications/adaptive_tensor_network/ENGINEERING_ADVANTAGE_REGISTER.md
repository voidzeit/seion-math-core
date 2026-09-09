# Engineering advantage register — adaptive tensor-network allocation

Audit date: 2026-08-16  
Authority: advisory audit over registered code and executed artifacts  
Canonical scope: `applications/adaptive_tensor_network` and directly linked
TTN/KGE artifacts in this repository

This register asks whether a method saves a named resource or improves a named
outcome against a competitive baseline under an equalized budget. It is not a
leaderboard, theorem registry, or release approval. Numerical observations are
limited to their executed domains.

## Decision rule and status vocabulary

An engineering advantage exists only when all five fields are known:

1. outcome or resource improved;
2. real competitor;
3. equalized budget;
4. regime in which the comparison holds;
5. an experiment capable of falsifying it.

Statuses:

- **SUPPORTED** — the scoped claim has direct, fair executed evidence and no
  known contradictory result in that same scope;
- **DOMAIN-LIMITED** — supported only in a named restricted regime, or useful
  evidence exists but a key external-validity gate is absent;
- **REFUTED** — a fair executed comparison contradicts the proposed advantage
  in the tested scope;
- **OPEN** — not tested fairly, missing a competitive baseline, or missing the
  required cost currency.

`DOMAIN-LIMITED` never means generally supported. `REFUTED` applies to the
stated claim and tested domain, not to every possible variant of the method.

## Competitive baseline matrix

| ID | Competitor | Operational definition for this audit | Why it is required |
|---|---|---|---|
| B0 | uniform / `maxdim` | Equal rank at every allocatable node or a global maximum bond dimension | Weak sanity baseline; never sufficient alone |
| B1 | threshold-static | One-shot common discarded-weight cutoff with exact global rank budget | Standard local error-controlled compression baseline |
| B2 | threshold-adaptive | Recompute fixed-basis discarded weights after each propagated calibration state and reapply the common cutoff for the next exact-budget bundle | Closed-loop local comparator available in the synthetic model |
| B3 | local spectral/entropy | Rank by discarded singular energy, entropy, or local truncation error | Tests whether downstream measurements add value over standard local signals |
| B4 | measured first order (FO) | Measure `E(r)-E(r+e_i)` and act using the downstream objective | Cheapest downstream-aware policy in the current campaign |
| B5 | full/low-rank pairwise | Add measured second finite differences, full or rank-`q` | Tests value of modeling interaction |
| B6 | step-greedy | Exhaustively minimize the immediate objective over the action set | Exact one-step comparator, not a terminal oracle |
| B7 | rollout | Score actions by a fixed continuation policy to horizon `h` | Horizon-aware quality comparator |
| B8 | certified allocator | Minimize a finite-batch or bounded-domain computable error bound | Tests value of simultaneous output and guarantee |
| B9 | exact terminal oracle | Enumerate all admissible terminal profiles where tractable | Regret reference only, not a deployable baseline |

B1/B2 are mandatory competitive baselines, not inventions of this audit.
TT/HT rounding selects ranks from local singular values for a prescribed
accuracy ([Oseledets, TT decomposition](https://doi.org/10.1137/090752286);
[Grasedyck, hierarchical SVD](https://doi.org/10.1137/090764189)). Production
MPS software exposes discarded-weight `cutoff` together with `maxdim` and
`mindim` ([ITensor truncated SVD](https://itensor.github.io/ITensors.jl/stable/examples/ITensor.html))
and changes those controls across DMRG sweeps
([ITensor DMRG](https://docs.itensor.org/ITensorMPS/dev/faq/DMRG.html)). Dynamic
TTN work also performs rank truncation to a specified tolerance after basis
augmentation ([Ceruti, Lubich, and Sulz](https://doi.org/10.1137/22M1473790)).
The V1/V1B gate now supplies synthetic B1/B2 comparators. They retain frozen
projector bases and rank growth only, so they do not replace a library-native
TT/MPS/TTN cutoff that may refit bases and shrink ranks.

## Observed Pareto audit

The deterministic generator
[`experiments/analyze_engineering_pareto.py`](experiments/analyze_engineering_pareto.py)
reads the preserved M35b/M38 raw JSON and writes
[`results/engineering_pareto_front.csv`](results/engineering_pareto_front.csv).
All rows use the same initial allocation and six rounds of three rank additions.
The true regret reference is the exact terminal optimum for the same seed.

| m | observation at equal rank trajectory | error/evaluation conclusion |
|---:|---|---|
| 8 | FO regret 0.2298 at 60 evaluations; full pairwise 0.3867 at 228; step-greedy 0.3867 at 342 | FO strictly dominates both |
| 10 | FO regret 0.2942 at 72 evaluations; full pairwise 0.3242 at 342; step-greedy 0.3242 at 726 | FO strictly dominates both |
| 8 | rollout `h=6` regret 0.0218 at 7,897 evaluations | quality improves, cost rises; both FO and rollout remain Pareto points |
| 10 | rollout `h=6` regret 0.0705 at 20,521 evaluations | quality improves, cost rises; about 285x FO's campaign evaluation count |

The same strict FO dominance over pairwise and step-greedy is observed in raw
CPU wall time at both sizes. This is not a hardware claim: the benchmark is
small NumPy float64 synthetic execution, has five exact-oracle seeds, and does
not report FLOPs, energy, GPU utilization, or peak memory. The apparent wall
ordering between uniform and local greedy differs by milliseconds and is not
treated as meaningful without timing uncertainty.

### Decisive threshold gate

`ATN_THRESHOLD_GATE_V1` compared uniform, static threshold, adaptive threshold,
FO, pairwise, and rollout on five exact-oracle seeds at each of m=8 and m=10.
Because every paired interval crossed zero, `ATN_THRESHOLD_GATE_V1B` was
declared before execution as a fixed 30-new-seed precision extension for the
two thresholds and FO. The predeclared extension remained inconclusive. A
descriptive pooled analysis of the identical designs gives:

| m | comparison | normalized paired delta `(threshold - FO)/initial` | interpretation |
|---:|---|---:|---|
| 8 | static vs FO, n=35 | 0.0032, CI95 [-0.0384, 0.0406] | no supported separation |
| 8 | adaptive vs FO, n=35 | -0.0021, CI95 [-0.0447, 0.0369] | no supported separation |
| 10 | static vs FO, n=35 | 0.0594, CI95 [0.0099, 0.1034] | FO lower terminal error |
| 10 | adaptive vs FO, n=35 | 0.0513, CI95 [0.0044, 0.0914] | FO lower terminal error |

All comparisons have equal terminal rank. Static threshold uses one objective
forward and adaptive threshold 12, versus 60 forwards for FO at m=8 and 72 at
m=10. The memory proxy differs only through the chosen rank profile and is not
measured VRAM. Thus FO has a domain-limited terminal advantage at m=10, not a
general Pareto advantage: threshold remains the low-cost frontier point. The
global gate is `MIXED_OR_INCONCLUSIVE`, so screened rollout was not started.

## Advantage ledger

| ID | Falsifiable hypothesis | Real baseline | Primary metric | Budget to equalize | Current result and status |
|---|---|---|---|---|---|
| EA-01 | Downstream measurement beats local allocation | B1, B2, B3 | terminal regret | equal rank; evaluations and wall time reported | No separation from either threshold at m=8; lower pooled terminal error than both at m=10, but 6x--72x more forwards. **DOMAIN-LIMITED; no general GO** |
| EA-02 | FO is more sample-efficient than pairwise | B5 | regret at target quality; evaluations | identical rank trajectory and target regret | FO strictly dominates full and q4 pairwise at m=8/10. **DOMAIN-LIMITED** |
| EA-03 | FO is more sample-efficient than exact one-step optimization | B6 | regret and evaluations | identical rank trajectory | FO strictly dominates step-greedy at m=8/10. **DOMAIN-LIMITED** |
| EA-04 | Lookahead improves terminal quality | B4, B6 | exact terminal regret | identical rank trajectory; cost reported separately | `h=6` lowers regret 90.5% at m=8 and 76.0% at m=10 relative to FO in ratio-of-means terms. **DOMAIN-LIMITED** |
| EA-05 | Full rollout is economical | B4 | regret per evaluation/wall second | target terminal regret | Costs 144x base evaluations at m=8 and about 306x in the same rollout file at m=10. No economic win established. **REFUTED for current full rollout** |
| EA-06 | FO-screened top-K rollout preserves most rollout gain | B7 full action rollout | regret recovered vs evaluation reduction | same terminal quality target | Not implemented. **OPEN (high value)** |
| EA-07 | Pairwise modeling adds terminal value after FO | B4 | paired terminal error | rank, seeds, evaluation cap | No separation at m=8/10/14/31; one step-greedy exception at m=23. **REFUTED as a general stop-later rule; DOMAIN-LIMITED exception** |
| EA-08 | A stop rule can halt after FO when marginal model value is low | B5/B6 continuation | `Delta error / Delta evaluations` | common state and horizon | M8/M10 support stopping; m23 warns against a universal threshold. **DOMAIN-LIMITED** |
| EA-09 | `r_eff` predicts per-instance interaction rank requirement | fixed-q selection | under/over-allocation; `q_dec95` | held-out calibration budget | Spearman 0.710/0.776/0.749 at D=8/16/32, but computed associationally on synthetic configurations. **DOMAIN-LIMITED** |
| EA-10 | `r_eff` enables capacity planning before expensive sweeps | exhaustive q sweep | cost saved at bounded under-allocation | train/calibration split | No fitted predictor, calibration curve, or held-out decision test. **OPEN** |
| EA-11 | Pathwise certificate allocation beats standard allocation | B0/B3 | true root error | equal rank | Preregistered Level 1 loses to uniform and local greedy. **REFUTED in registered scope** |
| EA-12 | Certified allocation lowers resources at matched true error | B0/B1 | contraction units, bytes, memory, wall time | independent-test error tolerance | Shared-DAG policies used more contraction units than uniform on average and tolerance transfer was partial. **REFUTED in current probe** |
| EA-13 | Certification supplies trust even without allocator superiority | uncertified same output | violation rate and bound tightness | same output/ranks/domain | Bounded-domain and finite-batch certificates hold in declared domains; M24/M25 greatly tighten bounds. **DOMAIN-LIMITED** |
| EA-14 | A tighter certificate is a useful action-ranking surrogate | B4/B6 action ranking | top-k agreement, decision regret | same 56 actions/state | M36 top-1 agreement is 0/15 for A/B/G; regret 0.40-0.48 of spread. **REFUTED** |
| EA-15 | The rank-aware DAG certificate allocator beats its separable version | B8 rank-independent DP | error or resource reduction | equal rank/domain | Only a small change; both lose to uniform on average. **REFUTED in current diamond probe** |
| EA-16 | Advantage is robust to noise, seeds, D, topology, and distribution shift | B1-B7 | worst-case, CV, tail regret | equal resource vector | Topology/dimension diagnostics exist, but policy robustness under noisy `U_i` and shift does not. **OPEN** |
| EA-17 | A hybrid dispatcher can choose local threshold on easy cases and FO/rollout on hard cases | best single policy | regret plus dispatch overhead | nested validation/test split | Plausible from regime dependence; no dispatch rule or held-out evaluation. **OPEN** |
| EA-18 | Hardware-aware `U_i/Delta C_i` beats gain per rank | B1-B4 | error vs measured GPU cost | wall time, VRAM, FLOPs or energy | No node-specific cost model is connected to allocation. **OPEN** |
| EA-19 | Closed-loop dynamic allocation beats one-shot truncation | B2 and one-shot FO | time-integrated error and runtime | same time-step error/resource envelope | Sequential synthetic rank allocation is not a physical time integrator. **OPEN** |
| EA-20 | Resource use is predictable before execution | measured execution | calibration error for VRAM/runtime/FLOPs | held-out workloads/hardware | Analytical DAG proxies exist but are not calibrated hardware models. **OPEN** |
| EA-21 | FO has lower integration complexity | B2/B5/B7 | implementation and operational complexity score | same backend/features | Current FO needs objective evaluations but no gradients; integration cost has not been measured in a real library. **OPEN** |
| EA-22 | The allocator improves a real TT/MPS/TTN workload | B0-B3 plus library-native policy | task error, VRAM, FLOPs, wall time, energy | matched quality and hardware | No clean real-network campaign. Historical KGE predictive metrics are invalid for this purpose under blocker B-0014. **OPEN (release-critical)** |
| EA-23 | Relationwise spectral allocation yields hardware speedup | uniform/full matched executor | robust p50 and lower-bound speedup | same scores/backend/device | Observed p50 1.017x and p05 0.807x, below the 1.5x robust gate. **REFUTED at current implementation point** |
| EA-24 | Local/pathwise score superiority is general | B0/B3 | held-out root error | equal rank | Mixed/negative across Levels 1-3; no universal policy advantage. **REFUTED** |
| EA-25 | Full-horizon benefit scales without prohibitive attenuation | B4 | regret recovered and evaluations | equal rank, report evaluations | Benefit survives m=10 but shrinks (Gamma 0.122 to 0.280) while cost grows. m>=12 absent. **OPEN** |

## Confounders that block promotion

1. **Synthetic threshold boundary.** V1/V1B now implement common-cutoff static
   and propagated-state adaptive comparators with exact budgets, but keep the
   bases frozen and only grow ranks. A real library-native cutoff can refit
   bases, shrink ranks, and charge SVD/data-movement costs differently.
2. **Synthetic-domain concentration.** The FO/pairwise/rollout evidence uses
   frozen projector bases, rank-indexed evaluation, D=16 heterogeneous chains,
   six rounds, and five exact-oracle seeds at m=8/10.
3. **Cost accounting is incomplete.** Forward evaluation counts and small CPU
   wall times exist; FLOPs, peak resident memory, VRAM, energy, data movement,
   SVD cost, and parallel efficiency do not.
4. **No uncertainty on timing.** The policy JSON records one wall-clock value
   per seed/policy. It is unsuitable for small timing differences and does not
   meet a robust hardware benchmark protocol.
5. **Candidate-generation asymmetry.** Rollout evaluates all bundles while FO
   constructs much cheaper decisions. This is the mechanism of the quality/cost
   tradeoff, not a reason to hide the cost.
6. **Oracle scale boundary.** Exact enumeration costs 235,348 profiles at m=8
   and 3,039,400 at m=10; it is infeasible as a general deployment policy.
7. **Regime-dependent counterevidence.** Step-greedy improves over FO at m=23
   in one campaign, so an unconditional stop-after-FO claim is false.
8. **Certification/policy separation.** Soundness and tightness do not imply
   useful action ranking or lower resources; M36 and the DAG probes directly
   demonstrate both non-implications.
9. **KGE leakage.** B-0014 establishes held-out leakage in historical KGE
   trainers. Those predictive metrics cannot validate allocator quality until
   re-run with train-only negative filtering. Certificates about the frozen
   tensors remain statements about those tensors, not evidence of clean task
   superiority.
10. **Safety/hardware hold.** B-0012 prevents extending GPU performance claims
    from the affected session.

## Minimum falsification protocols

### P1 — threshold-static/adaptive versus FO (executed synthetic gate)

- Sizes executed: m=8 and m=10 exact-oracle cases, followed by a fixed 30-seed
  precision extension.
- Baselines: B0, B1, B2, B3, B4.
- B1 grid: discarded-weight cutoff with `mindim=1` and a common `maxdim`;
  select cutoff on calibration only.
- B2: reapply the same cutoff after every allocation round; tune only on
  calibration.
- Equalization: (a) same rank trajectory, (b) same peak memory proxy,
  (c) same forward-evaluation cap, and (d) same wall-clock cap.
- Primary endpoint: paired exact terminal regret for m<=10; paired terminal
  error for larger m.
- Outcome: no general GO. At m=8 both intervals cross zero; at m=10 pooled
  intervals favor FO in terminal error, while threshold uses far fewer
  evaluations. Any broader claim now requires held-out regime dispatch or a
  real tensor-system comparison.

### P2 — screened rollout

- Use FO to shortlist K in `{3,5,8,12}` actions from the full action set.
- Run identical horizon rollout only on that shortlist.
- Report regret recovered relative to full rollout and total evaluations,
  including screening evaluations.
- Success gate: at least 90% of full-rollout regret reduction with at most 10%
  of its evaluations on both m=8 and m=10; confirm without an oracle at m=12.
- Falsifier for EA-06: no K clears both thresholds, or shortlist misses are
  concentrated in a predeclared difficult regime.

### P3 — heterogeneity-aware dispatch and capacity planning

- Fit `q_hat` and a policy dispatcher only on calibration configurations using
  `r_eff`, baseline error, m, D, topology, spectral decay, and utility
  concentration.
- Evaluate once on held-out families and dimensions.
- Primary endpoints: under-allocation rate, over-allocation, regret, and
  evaluations saved against a fixed-q and always-FO policy.
- Falsifier for EA-10/EA-17: no held-out saving at a fixed under-allocation
  risk, or dispatcher regret exceeds the best single policy plus overhead.

### P4 — real TT/MPS/TTN engineering gate

- Workloads: at least one TT numerical problem, one MPS/DMRG problem, and one
  branched TTN problem; trained/fitted objects, not random cores only.
- Baselines: library-native `maxdim`, static cutoff, adaptive cutoff/sweep,
  local entropy/discarded weight, FO, and screened rollout.
- Hardware: same backend, kernels, precision, batching, warmup, and device.
- Report: task error, peak host memory/VRAM, FLOPs estimate, wall-time
  distribution, energy when available, evaluation count, ranks, and failures.
- Primary decision: Pareto dominance or statistically stable frontier
  improvement on independent test workloads.
- Falsifier for EA-22: FO/screened rollout never adds a Pareto point beyond B1
  or B2, or integration overhead erases the observed gain.

### P5 — robustness and resource prediction

- Perturb measured utilities with calibrated additive/multiplicative noise;
  vary seeds, D, m, topology, budgets, dtype, and distribution.
- Fit resource models on one workload split and test them on another machine or
  held-out shape regime.
- Report median, p05/p95, worst case, CV, calibration error, and failure rate.
- Falsifier for EA-16/EA-20: worse tail risk than B2 at the same median quality,
  or resource prediction misses the declared safety margin.

## Engineering-complexity score to record in the real campaign

Do not collapse the score into a universal scalar until weights are declared.
Record the vector instead:

| Dimension | Measurement |
|---|---|
| code intrusion | changed library/kernel lines and required internal hooks |
| extra decompositions | SVD/eigendecomposition count and bytes processed |
| objective access | number and type of forward evaluations |
| gradient requirement | none, first-order autodiff, or higher order |
| parallelism | achievable concurrent candidate evaluations and efficiency |
| device residency | host/device transfers and synchronization points |
| operational tuning | number of tuned hyperparameters and calibration runs |
| failure recovery | resumability, deterministic replay, and certificate output |

## Priority order

1. Validate a threshold/FO dispatcher on held-out regimes; do not promote the
   pooled m=10 result into a universal policy claim.
2. Keep screened rollout conditional: the declared global threshold gate did
   not return GO, so P2 was not started in this pass.
3. Turn M37's association into a held-out predictor under P3.
4. Move only surviving policies into P4 and measure real memory, FLOPs,
   wall time, and energy.
5. Run P5 before any robustness, predictability, or production claim.

## Bottom-line audit verdict

The strongest current engineering result is narrow but real: on the exact
m=8 and m=10 synthetic terminal landscapes, measured FO dominates pairwise
and exact one-step optimization in both terminal regret and evaluation cost,
while full-horizon rollout buys substantially lower regret at roughly two to
three orders of magnitude more objective evaluations. The strongest negative
results are equally important: pathwise/certificate allocation does not beat
simple allocation generally; certificate tightness does not yield action
ranking; and current spectral execution does not meet its hardware-speed gate.

The threshold comparison is now closed for the declared synthetic gate. It
does not support a general FO win: m=8 shows no separation, while pooled m=10
shows lower FO terminal error against both thresholds at substantially higher
evaluation cost. The strongest defensible practical conclusion is therefore a
domain-limited dispatch hypothesis, not universal FO superiority. No real
TT/MPS/TTN engineering advantage is established.
