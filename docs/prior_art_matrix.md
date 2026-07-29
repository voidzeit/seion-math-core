# Prior-art matrix

| Area | Known component | New component | New combination | Evidence | Limitation |
|---|---|---|---|---|---|
| Non-associative algebra | associators, Akivis/Malcev/Filippov identities | none claimed by renaming | typed defect evaluation with status metadata | `src/seion_core/algebra` | not a new identity |
| Tensor decomposition | CP factors and gauge non-uniqueness | explicit gauge-aligned certificate path | law/defect/reduction provenance | `src/seion_core/algebra/cp_law.py` | no uniqueness theorem |
| Model reduction | PCA, SVD, invariant subspaces | closure leakage as a declared diagnostic | comparable finite certificates | `src/seion_core/projectors` | empirical finite examples |
| Kernel operators | finite quadrature and Hilbert-Schmidt estimates | explicit separation of formal and discrete layers | artifact contract | `src/seion_core/kernels` | no continuous convergence theorem |
| Discrete Hodge theory | finite complexes and Laplacians | commutation-to-descent certificate | finite operator track | `src/seion_core/cohomology` | no microlocal upgrade |

Novelty is intentionally scoped to the combination and reproducibility layer; no claim of priority over established mathematics is made here.

