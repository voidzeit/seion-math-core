"""AI5 metrics computation, shared across experiment levels."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def rms_norm(diff: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))


def spearman_corr(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation, computed without scipy (Pearson
    correlation of the rank-transformed values - exactly equivalent to
    the standard definition, avoids adding a scipy dependency for one
    function)."""

    if len(x) < 2:
        return float("nan")
    rank_x = _rank(x)
    rank_y = _rank(y)
    return pearson_corr(rank_x, rank_y)


def pearson_corr(x: list[float], y: list[float]) -> float:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if len(x_arr) < 2 or np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return float("nan")
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def _rank(values: list[float]) -> list[float]:
    order = np.argsort(values)
    ranks = np.empty(len(values))
    ranks[order] = np.arange(1, len(values) + 1)
    return ranks.tolist()


def bootstrap_ci(values: list[float], *, n_resamples: int = 2000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float, float]:
    """Returns (mean, ci_lower, ci_upper) via percentile bootstrap."""

    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")
    resample_means = np.array([
        rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_resamples)
    ])
    lower = float(np.percentile(resample_means, 100 * alpha / 2))
    upper = float(np.percentile(resample_means, 100 * (1 - alpha / 2)))
    return float(arr.mean()), lower, upper


def paired_effect_size(a: list[float], b: list[float]) -> float:
    """Cohen's d for paired differences (a - b), the effect size for
    "method a has lower error than method b at equal budget."""

    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    sd = diff.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(diff.mean() / sd)


@dataclass
class SeedResult:
    method: str
    seed: int
    budget: int
    true_root_error: float
    predicted_majorant: float
    rank_cost: int
    config_id: str
