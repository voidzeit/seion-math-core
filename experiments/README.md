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

The accuracy-first discovery track is separately declared in
`configs/KGE_SOTA_DISCOVERY_V1.yaml`. It permits larger models, dynamic hard
negatives, momentum queues, structural context, and later teacher/student
distillation. It is exploratory: its targets are not claims, it cannot alter
the confirmatory protocol, and test remains closed until finalists are frozen.
The current implementation exposes the Program-A primitives (split contract,
hard-negative filtering, EMA teacher, retriever union, query gate, ensemble
normalization, and listwise/margin distillation losses). Text retrieval and a
contextual reranker remain explicitly disabled until their data provenance is
registered.
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

## 2026-08-16 — engineering-advantage audit

The canonical candidate-claim ledger is
`applications/adaptive_tensor_network/ENGINEERING_ADVANTAGE_REGISTER.md`.
It distinguishes supported, open, refuted, and domain-limited advantages and
requires competitive cutoff/adaptive-cutoff baselines before any general
allocator-superiority claim. The observed M35b/M38 error-cost table is rebuilt
from raw JSON by
`applications/adaptive_tensor_network/experiments/analyze_engineering_pareto.py`;
the CSV is descriptive evidence, not a hardware or production claim.

## 2026-08-16 — static/adaptive threshold gate

The decisive synthetic cutoff comparison is frozen in
`configs/ATN_THRESHOLD_GATE_V1.yaml`. It evaluates uniform, common-cutoff
static threshold, propagated-state adaptive threshold, measured first order,
pairwise, and rollout at m=8 and m=10 with exact terminal oracles and records
rank, objective-forward count, an analytical memory proxy, and CPU wall time.
V1 was inconclusive at five seeds, so the fixed 30-new-seed precision extension
`configs/ATN_THRESHOLD_GATE_V1B.yaml` was declared before its execution.

The preregistered V1B gate remained `MIXED_OR_INCONCLUSIVE`. Descriptively
pooling the identical designs, FO does not separate from either threshold at
m=8 and has lower terminal error at m=10, while thresholds use far fewer
forwards. The canonical conclusion is
`DOMAIN_LIMITED_FO_ADVANTAGE_AT_M10_NO_GENERAL_GO`; screened rollout was not
started. Raw data, deterministic summaries, and limitations are in
`applications/adaptive_tensor_network/results/threshold_gate_*` and
`applications/adaptive_tensor_network/results/THRESHOLD_GATE_V1B_FINDINGS.md`.
