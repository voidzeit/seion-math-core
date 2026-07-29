from __future__ import annotations

from .projector import Projector


def projector_certificate(projector: Projector) -> dict:
    diagnostics = projector.diagnostics()
    status = "PASS_PROJECTOR_DIAGNOSTICS" if diagnostics["idempotence_error"] < 1e-10 and diagnostics["selfadjoint_error"] < 1e-10 else "WARN_PROJECTOR_RESIDUAL"
    return {"status": status, "diagnostics": diagnostics, "epistemic_status": "numerically_verified"}

