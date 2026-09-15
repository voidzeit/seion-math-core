"""Heterogeneous PMT certificate bookkeeping.

The heterogeneous expression is recorded as exploratory until H1 is proved.
The uniform envelope is the conservative certificate obtained by applying the
existing uniform theorem with common worst-case bounds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from functools import reduce
from operator import mul
from typing import Iterable

from .scalar_extremization import BoxMaximum, heterogeneous_box_max, uniform_G, validate_etas


def _positive_list(values: Iterable[float], name: str) -> list[float]:
    out = [float(x) for x in values]
    if not out or any(not math.isfinite(x) or x <= 0.0 for x in out):
        raise ValueError(f"{name} must contain positive finite values")
    return out


def _nonnegative_list(values: Iterable[float], name: str) -> list[float]:
    out = [float(x) for x in values]
    if any(not math.isfinite(x) or x < 0.0 for x in out):
        raise ValueError(f"{name} must contain finite nonnegative values")
    return out


@dataclass(frozen=True)
class HeterogeneousCertificate:
    operator_norms: tuple[float, ...]
    defects: tuple[float, ...]
    leaf_product: float
    normalized_defects: tuple[float, ...]
    angles: tuple[float, ...]
    scale: float
    exploratory_box_lower: float
    exploratory_box_upper: float
    exploratory_bound: float
    uniform_safe_bound: float
    uniform_M_hat: float
    uniform_eta_hat: float
    box: BoxMaximum

    def to_dict(self) -> dict:
        out = asdict(self)
        out["box"] = asdict(self.box)
        return out


def make_certificate(
    operator_norms: Iterable[float],
    defects: Iterable[float],
    leaf_product: float,
    *,
    seed: int = 0,
    maxiter: int = 300,
) -> HeterogeneousCertificate:
    """Build an exploratory heterogeneous report plus a safe uniform bound.

    ``operator_norms`` contains all internal nodes, including the root;
    ``defects`` contains the non-root internal nodes appearing in the scalar
    product.  Thus a rooted binary tree has len(operator_norms) =
    len(defects) + 1.  The same convention is used for the proposed formula
    in the research notes.
    """
    Ms = _positive_list(operator_norms, "operator_norms")
    rhos = _nonnegative_list(defects, "defects")
    if len(Ms) != len(rhos) + 1:
        raise ValueError("expected one operator norm for the root plus one per active defect")
    if not math.isfinite(float(leaf_product)) or leaf_product < 0.0:
        raise ValueError("leaf_product must be finite and nonnegative")
    etas = validate_etas(rho / M for rho, M in zip(rhos, Ms[1:]))
    alphas = tuple(math.asin(eta) for eta in etas)
    scale = reduce(mul, Ms, 1.0) * float(leaf_product)
    box = heterogeneous_box_max(alphas, seed=seed, maxiter=maxiter)

    M_hat = max(Ms)
    rho_hat = max(rhos, default=0.0)
    eta_hat = rho_hat / M_hat if M_hat else 0.0
    uniform_safe = (M_hat ** len(Ms)) * float(leaf_product) * uniform_G(len(rhos), eta_hat)

    return HeterogeneousCertificate(
        operator_norms=tuple(Ms),
        defects=tuple(rhos),
        leaf_product=float(leaf_product),
        normalized_defects=tuple(etas),
        angles=alphas,
        scale=float(scale),
        exploratory_box_lower=box.lower_bound,
        exploratory_box_upper=box.uniform_upper_bound,
        exploratory_bound=scale * box.lower_bound,
        uniform_safe_bound=float(uniform_safe),
        uniform_M_hat=float(M_hat),
        uniform_eta_hat=float(eta_hat),
        box=box,
    )
