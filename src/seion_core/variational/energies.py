from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from ..algebra.associators import five_input_associator
from ..algebra.symmetry import cyclic_defect
from ..algebra.ternary_law import TernaryLaw
from ..projectors.closure import closure_leakage
from ..projectors.projector import Projector


@dataclass
class EnergyWeights:
    assoc: float = 1.0
    closure: float = 1.0
    cyclic: float = 0.0
    gji: float = 0.0
    fi: float = 0.0
    regularity: float = 0.0
    projector: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def energy_components(law: TernaryLaw, projector: Projector | None, samples: list[tuple[np.ndarray, ...]]) -> dict[str, float]:
    assoc_values = []
    cyclic_values = []
    for sample in samples:
        assoc_values.append(np.linalg.norm(five_input_associator(law, *sample[:5])) ** 2)
        cyclic_values.append(cyclic_defect(law, sample[:3]))
    values = {"assoc": float(np.mean(assoc_values)), "cyclic": float(np.mean(cyclic_values))}
    values["closure"] = closure_leakage(law, projector, samples) if projector is not None else 0.0
    values["gji"] = 0.0
    values["fi"] = 0.0
    values["regularity"] = float(np.linalg.norm(law.tensor.ravel()) ** 2)
    values["projector"] = projector.diagnostics()["idempotence_error"] if projector is not None else 0.0
    return values


def total_energy(components: dict[str, float], weights: EnergyWeights | None = None) -> float:
    weights = weights or EnergyWeights()
    return float(sum(getattr(weights, key) * value for key, value in components.items()))

