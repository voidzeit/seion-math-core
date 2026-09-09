# ATN threshold gate V1B findings

V1B was declared after V1 returned an inconclusive five-seed interval and before these 30 new seeds were executed. It is a fixed-size precision extension, not optional stopping.

Preregistered V1B extension gate: **MIXED_OR_INCONCLUSIVE**.  
Combined project decision: **DOMAIN_LIMITED_FO_ADVANTAGE_AT_M10_NO_GENERAL_GO**.

Positive delta means FO has lower terminal error. Values are normalized by initial error.

## V1B new seeds only

| m | threshold | n | mean delta | median | CI95 | FO wins | threshold wins | verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 8 | threshold_static | 30 | -0.006172 | 0.012684 | [-0.051960, 0.033796] | 17 | 13 | INCONCLUSIVE |
| 8 | threshold_adaptive | 30 | -0.010779 | -0.009063 | [-0.057980, 0.031319] | 14 | 16 | INCONCLUSIVE |
| 10 | threshold_static | 30 | 0.054050 | 0.060622 | [-0.000227, 0.101039] | 25 | 5 | INCONCLUSIVE |
| 10 | threshold_adaptive | 30 | 0.046568 | 0.053446 | [-0.005124, 0.089078] | 23 | 7 | INCONCLUSIVE |

## Pooled V1 + V1B, identical design

These rows improve precision but do not retroactively change V1's preregistered outcome.

| m | threshold | n | mean delta | median | CI95 | FO wins | threshold wins | verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 8 | threshold_static | 35 | 0.003169 | 0.019661 | [-0.038424, 0.040642] | 21 | 14 | INCONCLUSIVE |
| 8 | threshold_adaptive | 35 | -0.002095 | 0.017730 | [-0.044667, 0.036858] | 18 | 17 | INCONCLUSIVE |
| 10 | threshold_static | 35 | 0.059356 | 0.063148 | [0.009856, 0.103360] | 29 | 6 | FO_WINS |
| 10 | threshold_adaptive | 35 | 0.051320 | 0.054164 | [0.004389, 0.091442] | 27 | 8 | FO_WINS |

## Decision

FO does **not** clear the requested general gate: at m=8 its mean advantage is essentially zero and both intervals remain inconclusive. In the pooled m=10 sample, FO has a positive mean advantage over both thresholds with intervals above zero, so the value is regime-dependent rather than absent.

Threshold remains dramatically cheaper (1 forward static, 12 adaptive, versus 60/72 for FO) and is itself Pareto-optimal. Consequently Paper C cannot claim that FO generally beats a real cutoff. The defensible engineering conclusion is a dispatch hypothesis: cutoff for the smaller/easier regime and FO only where downstream complexity justifies its measurement cost. That hypothesis requires held-out dispatch validation before promotion.

Per the declared order, screened rollout is not started in this pass because the global FO-versus-threshold gate did not return GO.
