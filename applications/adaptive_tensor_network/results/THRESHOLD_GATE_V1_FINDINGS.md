# ATN threshold gate V1 findings

Status: **EXPERIMENTAL, FIXED-BASIS SYNTHETIC GATE**. Nothing here is a theorem or a real-system hardware claim.

Overall preregistered gate: **MIXED_OR_INCONCLUSIVE**.

## Primary paired comparison

Positive delta means FO has lower terminal error. Deltas are normalized by each instance's initial error.

| m | threshold | mean normalized delta | paired CI95 | all seeds FO-better | verdict |
|---:|---|---:|---:|---:|---|
| 8 | threshold_static | 0.059219 | [-0.022863, 0.151059] | false | INCONCLUSIVE |
| 8 | threshold_adaptive | 0.050008 | [-0.030760, 0.141629] | false | INCONCLUSIVE |
| 10 | threshold_static | 0.091189 | [-0.030673, 0.208352] | false | INCONCLUSIVE |
| 10 | threshold_adaptive | 0.079836 | [-0.036018, 0.187284] | false | INCONCLUSIVE |

## Error-cost means

All policies have the same terminal rank budget within each problem size.

| m | policy | regret | evals | memory proxy (bytes) | wall s | Pareto eval | Pareto memory | Pareto wall |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | uniform | 0.635528 | 6.0 | 334912.0 | 0.019891 | false | false | false |
| 8 | threshold_static | 0.403013 | 1.0 | 335385.6 | 0.003481 | true | false | true |
| 8 | threshold_adaptive | 0.349360 | 12.0 | 335897.6 | 0.043833 | true | false | true |
| 8 | measured_first_order | 0.229771 | 60.0 | 337164.8 | 0.208740 | true | false | true |
| 8 | full_pairwise | 0.386681 | 228.0 | 338624.0 | 0.776352 | false | false | false |
| 8 | rollout_first_order_h6 | 0.021841 | 7897.0 | 334489.6 | 27.213349 | true | true | true |
| 10 | uniform | 0.859685 | 6.0 | 386048.0 | 0.026653 | false | false | false |
| 10 | threshold_static | 0.659423 | 1.0 | 389632.0 | 0.005202 | true | false | true |
| 10 | threshold_adaptive | 0.617981 | 12.0 | 390156.8 | 0.053851 | true | false | true |
| 10 | measured_first_order | 0.294210 | 72.0 | 385830.4 | 0.311316 | true | false | true |
| 10 | full_pairwise | 0.324201 | 342.0 | 384524.8 | 1.469795 | false | false | false |
| 10 | rollout_first_order_h6 | 0.070506 | 20521.0 | 383347.2 | 87.245914 | true | true | true |

## Interpretation boundary

- `GO_FO_EQUAL_RANK` means a terminal-quality advantage over both cutoff variants at the same rank budget in both exact synthetic landscapes.
- It does not mean FO dominates cutoff in evaluations or wall time; those currencies remain explicit Pareto tradeoffs.
- Adaptive cutoff changes its local energy signal but not the projector bases, because basis refitting would invalidate the exact terminal oracle.
- The memory quantity is an analytical compressed-coordinate proxy, not measured RSS or VRAM.
- Wall times are single CPU observations and do not support small-difference or hardware claims.
- A production basis-refitting cutoff and real TT/MPS/TTN workload remain mandatory before a technology claim.

Raw source: `threshold_gate_m8_m10_raw.json`. Registered design: `experiments/configs/ATN_THRESHOLD_GATE_V1.yaml`.
