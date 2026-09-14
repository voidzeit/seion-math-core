# M35b — horizon-aware sequential rank allocation

**EXPERIMENTAL. Nothing here is a theorem.** Phases A and B complete; Phases
C–E not run. All four m values carry 10 seeds (20 at m = 8).

Artifacts: `terminal_oracle_m8_raw.json`, `terminal_oracle_m8_values_seed*.npy`,
`policy_scaling_m8.json`, `policy_scaling_raw.json`, `m35b_analysis.json`,
`m35b_policy_table.csv`. Corrections in `m33_m35_interpretation_correction.md`.

## 1. Executive result

Two things separate cleanly, and one does not.

**Measuring separates.** Policies that measure `U_v` beat policies that do not,
by 13–23% of the initial error at m = 14 and m = 23, on every seed, with
comfortable confidence intervals.

**Modelling does not separate.** Among the measurement-based policies —
measured first order, full pairwise, rank-4 pairwise, and exhaustive one-step
greedy on the true objective — no difference is significant at m = 8 or m = 14,
despite a 4× to 36× spread in evaluation cost. The single exception is
step-greedy beating first order at m = 23 (+0.0295, CI [+0.0056, +0.0569]).

**The one-step reference is now genuine at m = 8.** Over all 235,348 admissible
terminal profiles the exact finite-horizon optimum is computed, and every
policy's terminal state is located within that landscape.

## 2. Gate A — reproducibility: PASS

Seed 0's enumeration was recomputed in a separate invocation and returned
`E* = 1.154480` identically. No process-salted hash enters any RNG seed; pools
are built from explicit integer seeds (`seed*100003 + step*97 + 17`). Every
configuration, seed, batch size, dtype and command line is recorded in the raw
payloads.

Two defects were found and fixed during this campaign:

- the M35 pool RNG was seeded with `hash(method)`, salted per process;
- the terminal-oracle script rebuilt its output payload from scratch on each
  invocation, so a second run silently discarded the first run's seeds. It now
  merges. Seed 0 was recomputed to restore it.

## 3. Gate B — true terminal reference at m = 8: PASS

- **Path independence: maximum spread `0.000e+00`** across 20 random terminal
  profiles, each realized by 4 distinct action sequences. This is structural —
  `reduced_forward` is a pure function of `(leaf_batch, ranks)` — but was
  tested rather than assumed, since assuming a property is exactly how M35
  failed.
- **Enumeration verified**: the prefix-memoized depth-first walk agrees with
  direct `reduced_forward` to `0.000e+00` maximum absolute error over 150
  samples per seed.
- **235,348 profiles**, matching an independent DP count, against
  `C(8,3)^6 = 3.08e10` action sequences.
- Every seed has a **unique** optimum (no ties).

| seed | E* | base | median profile | worst |
|---|---|---|---|---|
| 0 | 1.154480 | 2.088285 | 1.733602 | 2.557736 |
| 1 | 3.939383 | 5.837402 | 5.135816 | 6.088431 |
| 2 | 1.173593 | 1.791608 | 1.731943 | 2.486071 |
| 3 | 2.303639 | 2.615379 | 2.529237 | 2.738046 |
| 4 | 1.266994 | 1.689567 | 1.856824 | 2.843684 |

## 4. m = 8 against the true terminal optimum (n = 5 seeds)

| policy | true terminal regret | profile rank | percentile | evals |
|---|---|---|---|---|
| uniform | 0.6355 | 119,048 | 50.6% | 6 |
| local_greedy | 0.3530 | 37,591 | 16.0% | 6 |
| **measured_first_order** | **0.2298** | **24,148** | **10.3%** | 60 |
| full_pairwise | 0.3867 | 40,073 | 17.0% | 228 |
| lowrank_pairwise_q4 | 0.3804 | 38,913 | 16.5% | 228 |
| step_greedy | 0.3867 | 40,073 | 17.0% | 342 |

**Uniform lands near the median of the admissible terminal landscape** (50.6
mean percentile over 5 seeds). Calling it indistinguishable from random would
require comparing against an explicit distribution of random policies, which
was not done. Every other policy is in the top 10–17%. No policy is close to
the optimum.

**Full pairwise and step-greedy reach identical terminal profiles** — the same
regret and the same rank, in all five seeds. Since `E` is path-independent,
identical terminal profiles do **not** establish identical action sequences:
two different trajectories can reach the same final rank vector. The
per-step action-agreement rate

    A_action = (1/T) * sum_t 1{ Delta_t^pair == Delta_t^greedy }

has not been measured, so the supportable claim is *convergence to the same
terminal profile*, not *the same policy*. The suggestive reading — that a
surrogate built to approximate the one-step optimum inherits the one-step
optimum's myopia — remains a hypothesis pending `A_action`.

## 5. Policy scaling (Gate D: 20 seeds at m = 8, 10 at m = 14 and 23)

Terminal error normalized by each instance's initial error; seed-matched
differences against measured first order.

| m | uniform | local_greedy | first_order | full_pairwise | lowrank_q4 | step_greedy |
|---|---|---|---|---|---|---|
| 8 | 0.9249 | 0.7673 | 0.7923 | 0.8123 | 0.8161 | 0.8122 |
| 14 | 1.1010 | 0.9974 | 0.8684 | 0.8629 | 0.8611 | 0.8656 |
| 23 | 0.9951 | 1.0207 | 0.8551 | 0.8418 | 0.8420 | **0.8256** |
| 31 | 1.0010 | 1.0118 | 0.9615 | 0.9525 | 0.9533 | 0.9520 |

m = 31 reproduces the pattern: measurement separates from non-measurement
(~4–5%), and the measurement-based policies do not separate from each other.

Seed-matched, positive means better than measured first order:

| m | uniform | local_greedy | full_pairwise | lowrank_q4 | step_greedy |
|---|---|---|---|---|---|
| 8 | −0.133 **−** | +0.025 (0) 11/0/9 | −0.020 (0) 8/3/9 | −0.024 (0) 8/4/8 | −0.020 (0) 7/3/10 |
| 14 | −0.233 **−** | −0.129 **−** | +0.006 (0) 7/0/3 | +0.007 (0) 6/2/2 | +0.003 (0) 7/0/3 |
| 23 | −0.140 **−** | −0.166 **−** | +0.013 (0) 6/1/3 | +0.013 (0) 6/1/3 | **+0.030 +** 6/1/3 |

m = 8 behaves differently from the larger cases: `local_greedy` is competitive
there and clearly bad at m = 14 and 23. Cross-m raw errors are not compared;
only the normalized within-m differences above are meaningful.

## 6. A retracted result from within this campaign

An earlier read of m = 8 at **five** seeds reported measured first order
beating full pairwise and step-greedy with W/T/L = 0/0/5 and significant
intervals. At **twenty** seeds those become 8/3/9 and 7/3/10 with intervals
spanning zero. **The effect did not survive.** It is recorded here rather than
dropped.

Relatedly, seed 0's profile rank of 98 (0.042 percentile) is a severe outlier:
the five-seed mean is 24,148 (10.3 percentile). Single-instance ranks in a
235,348-point landscape are not informative.

## 7. What is PROVED / EXPERIMENTAL / OPEN

**Proved (unchanged from earlier work):** the M24/M25 certificate hierarchy.
Nothing in M35b is proved.

**Experimental, this campaign:**
- path independence of `E` on the terminal rank vector, at machine precision;
- the exact finite-horizon optimum at m = 8, with unique optima in 5 instances;
- measurement-based policies beat non-measurement ones by 13–23% at m = 14, 23;
- no significant difference among measurement-based policies except
  step-greedy at m = 23;
- full pairwise and step-greedy select identical terminal profiles at m = 8.

**Open:**
- Phases C (causal horizon counterfactuals with a common continuation policy),
  D (horizon ranking inversions, `H_flip`), and E (mechanism of greedy myopia)
  are not run;
- no terminal reference exists above m = 8;
- `A_action` between `full_pairwise` and `step_greedy` is unmeasured, so their
  identical terminal profiles remain unexplained at the action level;
- everything remains synthetic — no trained network, no real HT/TTN.

Rollout (Phase G) was subsequently run at m = 8 — see
`ROLLOUT_CALIBRATION_M35C_FINDINGS.md`.

## 8. Next hypotheses

The identity of full-pairwise and step-greedy terminal profiles suggests the
sharpest available question is not about better one-step models at all. It is
whether a **rollout** policy — evaluate each candidate's terminal error after a
fixed base continuation, then choose — separates from step-greedy. That is
Phase G's `Q_hat(r,a)`, it is horizon-aware without solving the dynamic
program, and it is the first policy in this campaign that would not be
approximating the immediate objective.
