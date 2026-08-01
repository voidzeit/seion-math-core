"""SEION-KGR v26 MAX — layered trainer package.

Each submodule corresponds to one phase of the build sequence in
``docs/SEION_KGR_MATHEMATICAL_CONTRACT.md`` §VIII:

    data / reproducibility / evaluate  -> Fase 3 (baseline plumbing)
    scorers                            -> Fase 3 (expert base)
    reasoner                           -> Fase 4 (path reasoner)
    kernels                            -> Fase 5 (SEION ternary residual)
    projection                         -> Fase 6 (orthogonal projection)
    rank_controller                    -> Fase 7 (adaptive rank)
    geometry                           -> Fase 8 (associator/FI curriculum)
    metaencoder                        -> Fase 9 (relation transfer)
    model / losses / train             -> wiring across all phases

This package intentionally does not re-implement anything already
proved/tested in ``docs/theorems_v3/`` or exercised by
``seion_kgr_reference_fp64.py`` — it is the batched/GPU-capable trainer
built on top of those, not a replacement for the FP64 oracle.
"""

__all__: list[str] = []
