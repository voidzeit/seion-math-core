from __future__ import annotations

import numpy as np


def projector_transport_error(projector_n: np.ndarray, projector_m: np.ndarray, restrict, prolong) -> float:
    lhs = restrict @ projector_m @ prolong
    return float(np.linalg.norm(lhs - projector_n))


def law_transport_error(law_n, law_m, prolong, restrict, samples: list[tuple[np.ndarray, ...]]) -> float:
    values = []
    for sample in samples:
        transported = restrict @ law_m(*[prolong @ x for x in sample])
        values.append(np.linalg.norm(transported - law_n(*sample)))
    return float(np.mean(values)) if values else 0.0

