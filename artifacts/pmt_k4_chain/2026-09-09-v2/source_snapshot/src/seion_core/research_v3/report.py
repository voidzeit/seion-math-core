"""Aggregation, deduplication, uncertainty, and v3 report helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


def summary_statistics(values: Iterable[float]) -> dict[str, float | int]:
    data = np.asarray(list(values), dtype=float)
    if data.size == 0:
        return {key: float("nan") for key in ("mean", "std", "median", "q1", "q3", "min", "max", "ci95_low", "ci95_high")} | {"count": 0}
    mean = float(np.mean(data))
    std = float(np.std(data, ddof=1)) if data.size > 1 else 0.0
    half = 1.96 * std / np.sqrt(data.size) if data.size > 1 else 0.0
    return {
        "count": int(data.size),
        "mean": mean,
        "std": std,
        "median": float(np.median(data)),
        "q1": float(np.quantile(data, 0.25)),
        "q3": float(np.quantile(data, 0.75)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "ci95_low": mean - half,
        "ci95_high": mean + half,
    }


def bootstrap_max_interval(
    values: Iterable[float], *, seed: int = 0, samples: int = 2000
) -> tuple[float, float]:
    data = np.asarray(list(values), dtype=float)
    if data.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    maxima = np.max(rng.choice(data, size=(samples, data.size), replace=True), axis=1)
    return float(np.quantile(maxima, 0.025)), float(np.quantile(maxima, 0.975))


def flatten_dataclass(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("expected a dataclass or mapping")


def collect_run_rows(run_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for manifest_path in sorted(run_root.glob("*/run_manifest.json")):
        run_dir = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metrics = json.loads((run_dir / "final_metrics.json").read_text(encoding="utf-8"))
        certificate = json.loads((run_dir / "certificate.json").read_text(encoding="utf-8"))
        rows.append({**manifest, **metrics, **{f"certificate_{k}": v for k, v in certificate.items() if not isinstance(v, (dict, list))}, "run_path": str(run_dir)})
    return pd.DataFrame(rows)


def deduplicate_scientific_instances(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return frame.copy(), frame.copy()
    key = "scientific_instance_hash"
    ordered = frame.sort_values([key, "generated_utc", "run_id"])
    deduplicated = ordered.drop_duplicates(key, keep="last")
    duplicates = ordered[ordered.duplicated(key, keep=False)]
    return deduplicated.reset_index(drop=True), duplicates.reset_index(drop=True)


def write_frame(frame: pd.DataFrame, csv_path: Path, parquet_path: Path | None = None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False)
    if parquet_path is not None:
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(parquet_path, index=False)
