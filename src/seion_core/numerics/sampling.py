from __future__ import annotations

import numpy as np


def gaussian_samples(dimension: int, count: int, seed: int = 0, complex_values: bool = False) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    samples = [rng.normal(size=dimension) for _ in range(count)]
    if complex_values:
        samples = [x + 1j * rng.normal(size=dimension) for x in samples]
    return samples


def tuple_samples(dimension: int, arity: int, count: int, seed: int = 0, complex_values: bool = False) -> list[tuple[np.ndarray, ...]]:
    rng = np.random.default_rng(seed)
    result = []
    for _ in range(count):
        values = tuple(rng.normal(size=dimension) for _ in range(arity))
        if complex_values:
            values = tuple(v + 1j * rng.normal(size=dimension) for v in values)
        result.append(values)
    return result

