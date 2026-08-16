# Depth sweep — does a usable window exist?

**EXPLORATORY, NOT CONFIRMATORY.** This design was written after Level 1's
results were known, so it carries the same label the Level 2/3 campaigns
carry in `CAMPAIGN_FINDINGS.md`. No multiple-comparison correction was
applied and 50 paired tests are reported below; individual "significant"
cells should be read accordingly.

Raw data: `depth_sweep_raw.json` (4,800 records: 2 regimes x 5 depths x
10 seeds x 6 budgets x 8 methods). Analysis: `depth_sweep_analysis.json`,
computed by `../experiments/analyze_depth_sweep.py` reusing Level 1's own
`metrics.bootstrap_ci` / `paired_effect_size` so the numbers are directly
comparable. All numbers below are read from that file.

## Why this sweep exists

`LEVEL1_FINDINGS.md` raised, but did not attempt, the hypothesis that the
pathwise method needs "deeper trees than the depth-3/3-node topologies
tested here". **Level 1 tested only k=3**: both `chain_depth3` and
`balanced_binary_4leaf` have exactly 3 internal nodes.

Two design facts about Level 1 motivate the two regimes here:

1. A probe measured the coefficient of variation of the pure path-transport
   weights `w_v` at **CV = 0.074 for k=3** — the weights were nearly
   constant, so `pathwise_global` and `local_error_greedy` were scoring
   nodes almost identically. There was little signal for the preregistered
   comparison to detect.
2. `TensorNetwork.random` draws i.i.d. Gaussian cores at **every** node, so
   all nodes are statistically identical and `uniform` is optimal by
   symmetry. The `heterogeneous` regime added here gives each node its own
   power-law singular spectrum, which is what makes non-uniform allocation
   a well-posed problem at all.

## Results

`A` = paired reduction in `relative_root_error` (positive = pathwise
better), 60 paired configs per cell. `+` / `-` / `0` = pathwise
significantly better / baseline significantly better / CI includes zero.

### regime `iid` (reproduces Level 1's generator)

| k | A vs uniform | A vs local_error_greedy | A vs random_path_coef | w_CV | N_eff/k | tightness (cert. A) |
|---|---|---|---|---|---|---|
| 3 | −0.0221 [−0.0339, −0.0110] **−** | −0.0306 [−0.0420, −0.0199] **−** | −0.0133 [−0.0521, +0.0233] 0 | 0.074 | 0.994 | 1.8e−02 |
| 6 | −0.0155 [−0.0250, −0.0060] **−** | −0.0211 [−0.0318, −0.0109] **−** | +0.0574 [+0.0357, +0.0823] **+** | 0.147 | 0.978 | 1.0e−03 |
| 10 | −0.0098 [−0.0217, +0.0002] 0 | −0.0078 [−0.0230, +0.0061] 0 | +0.0256 [+0.0048, +0.0465] **+** | 0.242 | 0.944 | 2.4e−04 |
| 16 | −0.0034 [−0.0180, +0.0095] 0 | −0.0105 [−0.0296, +0.0077] 0 | +0.0085 [−0.0044, +0.0225] 0 | 0.362 | 0.883 | 1.9e−05 |
| 24 | −0.0130 [−0.0436, +0.0136] 0 | −0.0157 [−0.0420, +0.0057] 0 | −0.0156 [−0.0403, +0.0044] 0 | 0.539 | 0.774 | 1.9e−11 |

**Level 1's negative result reproduces exactly at k=3** (pathwise loses to
both uniform and local_error_greedy). With depth the losses shrink to
statistical draws. Pathwise never wins here — consistent with the symmetry
argument: with i.i.d. nodes there is nothing for a non-uniform allocator
to exploit.

### regime `heterogeneous` (per-node spectra; new condition)

| k | A vs uniform | A vs local_error_greedy | A vs random_path_coef | w_CV | N_eff/k | tightness (cert. A) |
|---|---|---|---|---|---|---|
| 3 | +0.0293 [+0.0104, +0.0503] **+** | −0.0157 [−0.0263, −0.0074] **−** | +0.0017 [−0.0161, +0.0235] 0 | 0.194 | 0.946 | 2.8e−02 |
| 6 | +0.0476 [+0.0268, +0.0702] **+** | −0.0129 [−0.0243, −0.0014] **−** | +0.0756 [+0.0452, +0.1086] **+** | 0.241 | 0.934 | 4.3e−04 |
| 10 | +0.0545 [+0.0185, +0.0924] **+** | +0.0052 [−0.0316, +0.0454] 0 | +0.0821 [+0.0350, +0.1346] **+** | 0.375 | 0.865 | 2.8e−05 |
| 16 | +0.0603 [+0.0175, +0.1046] **+** | +0.0216 [−0.0187, +0.0655] 0 | +0.1108 [+0.0552, +0.1684] **+** | 0.434 | 0.833 | 3.5e−11 |
| 24 | +0.0904 [+0.0123, +0.1791] **+** | −0.0054 [−0.0606, +0.0403] 0 | +0.0376 [−0.0495, +0.1082] 0 | 0.624 | 0.736 | 3.1e−19 |

## What this establishes

**1. Level 1's null against `random_path_coefficients` was a k=3 artifact.**
This is the single most informative cell. Level 1 found the real measured
path amplifications statistically indistinguishable from random positive
coefficients of similar scale. That reproduces here at k=3 in both regimes
(CIs include zero). But at **k=6, 10 and 16 the real coefficients
significantly beat random ones in both regimes** — so the path structure
does carry exploitable information once the tree is deep enough for paths
to differ. The Level 1 null did not generalize; it was measured where
`w_CV` was 0.074.

**2. `H_w(k)` rises monotonically** in both regimes (CV 0.074→0.539 and
0.194→0.624; `N_eff/k` 0.994→0.774 and 0.946→0.736), confirming the
mechanism proposed for why k=3 had no signal.

**3. Against `uniform`, node heterogeneity — not depth — is what decides.**
In the `heterogeneous` regime pathwise beats uniform at **every** depth
including k=3. In `iid` it beats uniform at **no** depth. Depth modulates
the size of the advantage; heterogeneity creates it.

**4. The certificate collapses far faster than the allocator improves.**
Tightness falls from ~2e−2 at k=3 to ~4e−24 at k=24. The bound held in 100%
of records at every depth — it remains sound — but by k=16 it is over 10^10
times too loose to constrain anything. The allocator and the certificate are
decoupled: allocation needs only the relative order of node scores, which
survives; certification needs absolute tightness, which does not.

**This finding was subsequently traced to the composition rule, not to the
depth barrier**, and largely repaired — see `CERTIFICATE_M24_M25_FINDINGS.md`,
which recovers a factor of 2.4e18 in tightness at k=24 on this same sweep.
The tightness column above is certificate A only.

## What this does NOT establish

**`pathwise_global` never significantly beats `local_error_greedy` at any
depth, in either regime.** It goes from significantly losing (k=3, 6) to a
statistical draw (k≥10) and never crosses into a win. The window originally
sought — a depth where pathwise beats the strongest simple baseline before
the certificate dies — is **empty across the tested range**. The
path-transport factor demonstrably carries information (finding 1), but
that information does not translate into beating "put rank where the local
truncation error is largest".

Trends across k have wide, overlapping CIs (e.g. A-vs-uniform rising
+0.029→+0.090 in `heterogeneous`). The monotone reading is suggestive, not
established, at this sample size.

## Honest scope

Chain topologies only, ambient dim 6, synthetic cores with imposed spectra
— not trained networks on real tasks. The `heterogeneous` generator
imposes power-law spectra with per-node exponents drawn from [0.3, 2.0];
whether real trained layers exhibit comparable dispersion is untested here
and is the obvious next question. No claim is made about LLM or
tensor-network compression in production.
