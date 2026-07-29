from __future__ import annotations

import sys

import numpy as np


def cast_for_precision(value, precision: str):
    mapping = {"float32": np.float32, "float64": np.float64, "complex64": np.complex64, "complex128": np.complex128}
    if precision not in mapping:
        raise ValueError(f"precision {precision!r} is not a fixed NumPy precision")
    return np.asarray(value, dtype=mapping[precision])


def precision_info(precision: str) -> dict:
    dtype = np.dtype({"float32": np.float32, "float64": np.float64, "complex64": np.complex64, "complex128": np.complex128}[precision])
    real_dtype = np.empty((), dtype=dtype).real.dtype
    return {"precision": precision, "dtype": str(dtype), "machine_epsilon": float(np.finfo(real_dtype).eps), "itemsize": int(dtype.itemsize), "python": sys.version.split()[0]}

