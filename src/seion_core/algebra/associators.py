"""Associator conventions, exact contractions, and sampled defect summaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from ..exceptions import ConventionError
from .nary_law import NaryLaw
from .ternary_law import TernaryLaw


@dataclass
class DefectSummary:
    convention: str
    squared_energy: float
    normalized_defect: float
    samples: int
    seed: int | None
    dtype: str
    exact: bool
    input_distribution: str
    normalization: str

    def to_dict(self) -> dict:
        return asdict(self)


def five_input_associator(law: TernaryLaw, *vectors: np.ndarray) -> np.ndarray:
    if len(vectors) != 5:
        raise ConventionError("five-input ternary associator requires exactly five vectors")
    return law.five_input_associator(*vectors)


def anchored_associator(
    law: TernaryLaw, anchor: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> np.ndarray:
    return law.anchored_associator(anchor, x, y, z)


def normalized_defect(residuals: np.ndarray, scales: np.ndarray | None = None, eps: float = 1e-15) -> float:
    residuals = np.asarray(residuals)
    numerator = float(np.mean(np.abs(residuals) ** 2))
    denominator = float(np.mean(np.abs(scales) ** 2)) if scales is not None else 1.0
    return numerator / max(denominator, eps)


def sample_associator_defect(
    law: TernaryLaw,
    convention: str = "five_input",
    samples: int = 128,
    seed: int = 0,
    dtype: str | np.dtype | None = None,
    anchor: np.ndarray | None = None,
    distribution: str = "standard_normal",
) -> DefectSummary:
    if law.input_dims != (law.output_dim,) * 3:
        raise ConventionError("sampled internal associator requires a common space")
    rng = np.random.default_rng(seed)
    work = law.astype(dtype) if dtype is not None else law
    vectors = [rng.normal(size=(samples, law.output_dim)) for _ in range(5)]
    if np.iscomplexobj(work.tensor):
        vectors = [v + 1j * rng.normal(size=v.shape) for v in vectors]
    residuals = []
    scales = []
    if convention == "five_input":
        for row in zip(*vectors):
            residuals.append(five_input_associator(work, *row))
            scales.append(work(*row[:3]))
    elif convention == "anchored":
        if anchor is None:
            anchor = np.zeros(law.output_dim, dtype=work.tensor.dtype)
            anchor[0] = 1
        for row in zip(*vectors[:3]):
            residuals.append(anchored_associator(work, anchor, *row))
            scales.append(work(row[0], row[1], anchor))
    else:
        raise ConventionError(f"unknown associator convention: {convention}")
    residual_array = np.asarray(residuals)
    scale_array = np.asarray(scales)
    return DefectSummary(
        convention=convention,
        squared_energy=float(np.mean(np.abs(residual_array) ** 2)),
        normalized_defect=normalized_defect(residual_array, scale_array),
        samples=samples,
        seed=seed,
        dtype=str(work.tensor.dtype),
        exact=False,
        input_distribution=distribution,
        normalization="mean residual energy / mean intermediate output energy",
    )

