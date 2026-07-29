from __future__ import annotations

import numpy as np


def convergence_summary(resolutions, errors) -> dict:
    resolutions = np.asarray(resolutions, dtype=float)
    errors = np.asarray(errors, dtype=float)
    if len(resolutions) < 3:
        return {"resolutions": resolutions.tolist(), "errors": errors.tolist(), "status": "insufficient_sequence_for_limit_claim"}
    slope = float(np.polyfit(np.log(resolutions), np.log(np.maximum(errors, 1e-300)), 1)[0])
    return {"resolutions": resolutions.tolist(), "errors": errors.tolist(), "loglog_slope": slope, "status": "finite_sequence_observation"}

