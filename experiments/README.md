# Experiments

Experiment configurations are machine-readable YAML. The finite vertical slice is `configs/finite_ternary_v1.yaml`. The canonical matrix registers the broader research program and labels rows that require extended hardware or analytic work.

The adaptive tensor-network majorant comparison is an explicitly exploratory
follow-up, registered in
`configs/majorant_optimizer_probe_2026-08-09.yaml`; it does not alter the
preregistered Level 1 records or support a superiority claim.

The branching TTN/FB15K-237 protocol is recorded in
`configs/ttn_fb15k237_branching_k3_protocol_2026-08-09.yaml`. It fixes the
train-only projector fit, frozen full-rank model, transformed-core execution,
filtered ranking metrics, certificate-vs-observation separation, and the
limitations of the first exploratory slice before any valid campaign is run.

The confirmatory campaign is frozen in
`configs/CERTIFIED_KGE_CONFIRMATORY_PROTOCOL_V1.yaml`. It extends the pilot
into explicit G0--G8 gates, train-only calibration, valid-only selection,
single final test confirmation, same-backend hardware comparisons, seed-level
replication, WN18RR replication, and a mandatory run artifact contract. Its
status is `declared_not_executed`; the current B-0012 Windows stability hold
prevents long GPU training until dump/driver review is resolved.
## 2026-08-09 — shared-DAG certificate probe

The exploratory shared-DAG tensor-network probe is defined by
`configs/dag_certificate_probe_2026-08-09.yaml` and executed by
`applications/adaptive_tensor_network/experiments/run_dag_certificate_probe.py`.
Its raw records and negative allocator comparison are documented in
`applications/adaptive_tensor_network/results/DAG_CERTIFICATE_PROBE_2026-08-09.md`.
It is not preregistered evidence of universal allocator superiority.

## 2026-08-09 — shared-DAG matched-tolerance probe

The exploratory resource/error study is defined by
`configs/dag_matched_tolerance_probe_2026-08-09.yaml` and executed by
`applications/adaptive_tensor_network/experiments/run_dag_matched_tolerance_probe.py`.
It selects allocations using validation sup-error and evaluates them on an
independent test batch. Its resource values are exact compressed-coordinate
proxies, not hardware timings; the resulting comparison remains
context-dependent and does not support a superiority claim.
