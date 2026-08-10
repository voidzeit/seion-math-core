# Exploratory finite-batch certificate-allocation probe

This probe compares `pathwise_global`, the exact fitted-majorant optimizer,
and the small-case allocator that exhaustively minimizes the validated
finite-batch root bound. It uses two topologies, ten seeds, six budgets, a
fitting batch of 80 samples, and a separate held-out batch of 300 samples.

The raw result is `validated_certificate_probe_2026-08-09.json`. The command is
`python applications/adaptive_tensor_network/experiments/run_validated_certificate_probe.py`.
The result must be read from that JSON artifact; this note is only a compact
provenance and limitation record. No preregistered Level 1 result is changed.

Observed summary from the generated artifact:

| Topology | Pairs | Mean held-out RMS reduction vs `pathwise_global` | Candidate better fraction | Validated-bound no-worse fraction |
|---|---:|---:|---:|---:|
| chain depth 3 | 60 | 0.2432 | 0.6000 | 1.0000 |
| balanced binary, 4 leaves | 60 | 0.2250 | 0.6333 | 1.0000 |

The bound was verified on the fitting batch for every candidate record. The
held-out errors are used only for this exploratory comparison; the fitting
certificate is not asserted to bound the held-out batch.
