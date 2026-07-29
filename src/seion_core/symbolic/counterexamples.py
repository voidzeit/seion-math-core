from __future__ import annotations

import numpy as np


def missing_gap_snapping_counterexample() -> dict:
    return {"matrices": [np.diag([0.5 - 1e-12, 0.5 + 1e-12]).tolist(), np.diag([0.5 + 1e-12, 0.5 - 1e-12]).tolist()], "status": "refuted_continuity_without_gap"}

