# Shared-DAG matched-tolerance probe — 2026-08-09

Status: exploratory and not preregistered. The raw output is `DAG_MATCHED_TOLERANCE_PROBE_2026-08-09.json`; the executable design is `experiments/run_dag_matched_tolerance_probe.py`.

Each method selected the least compressed-contraction proxy on a validation batch satisfying the stated sup-error tolerance. The test batch was held out until after selection. Resource values are the exact coordinate-transformed proxy, not timing measurements.

| Method | Tolerance | Available | Test reaches tolerance | Certificate holds | Mean Δ test sup vs uniform | Mean Δ contraction units vs uniform | Mean Δ parameter bytes vs uniform |
|---|---:|---:|---:|---:|---:|---:|---:|
| global_certificate_optimal | 0.05 | 0.667 | 0.625 | 1.0 | 0.018227065784548944 | -39.5 | -356.0 |
| global_certificate_optimal | 0.1 | 1.000 | 0.5 | 1.0 | 0.007363087217441081 | -23.333333333333332 | -213.33333333333334 |
| global_certificate_optimal | 0.15 | 1.000 | 0.6666666666666666 | 1.0 | -0.008145126237099076 | -22.666666666666668 | -208.0 |
| rank_aware_certificate_optimal | 0.05 | 0.667 | 0.625 | 1.0 | 0.018227065784548944 | -39.5 | -356.0 |
| rank_aware_certificate_optimal | 0.1 | 1.000 | 0.5 | 1.0 | 0.007363087217441081 | -23.333333333333332 | -213.33333333333334 |
| rank_aware_certificate_optimal | 0.15 | 1.000 | 0.6666666666666666 | 1.0 | -0.008145126237099076 | -22.666666666666668 | -208.0 |
| uniform | 0.05 | 0.750 | 0.4444444444444444 | 1.0 | n/a | n/a | n/a |
| uniform | 0.1 | 1.000 | 0.4166666666666667 | 1.0 | n/a | n/a | n/a |
| uniform | 0.15 | 1.000 | 0.75 | 1.0 | n/a | n/a | n/a |

Interpretation: matching a validation error target turns the question into a resource/error tradeoff, but this finite probe is not a policy superiority result. Positive resource reduction with a negative test error reduction is a valid context-dependent outcome and must remain reported as such.

Limitations: one synthetic topology, sampled domains, random cores, and analytical resource proxies. A technology claim would require the preregistered multi-topology train/validation/test study described in `APPLIED_VALIDATION_STATUS_2026-08-09.md`.
