# FB15K-237 TTN multi-seed robustness summary

Seeds: 42, 7, 17, 27, 37, 47, 57, 67, 77, 87

| Budget | Mean certificate | Max certificate | Max observed score error | Mean rank equality | Min rank equality | Mean CCR@10 | Violations |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.0234284 | 0.072611 | 3.42298e-05 | 0.8750 | 0.5625 | 0.0000 | 0 |
| 16 | 0.00366201 | 0.0139029 | 2.90573e-07 | 0.9922 | 0.9531 | 0.0219 | 0 |
| 32 | 0.000144723 | 0.000958138 | 3.09199e-07 | 1.0000 | 1.0000 | 0.5844 | 0 |
| 64 | 4.36579e-06 | 7.0411e-06 | 3.09199e-07 | 1.0000 | 1.0000 | 0.9328 | 0 |

All ten seeds recorded zero certificate violations and zero false certificates in their evaluated records.

Limitations: one dataset/topology; selected-budget probes for nine seeds; sampled score/CCR; no cross-dataset claim.
