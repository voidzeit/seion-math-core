"""Interval enclosures for explicit planar-rotation lower constructions."""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp

from .typed_tree import Leaf, Tree


@dataclass(frozen=True, slots=True)
class IntervalCertificate:
    lower: float
    upper: float
    status: str
    method: str
    precision_bits: int

    @property
    def width(self) -> float:
        return self.upper - self.lower


def rotation_comb_ratio_interval(
    internal_nodes: int,
    eta: float,
    error_type: str,
    *,
    precision_bits: int = 160,
) -> IntervalCertificate:
    """Enclose the exact ratio for a first-slot comb of gated rotations."""

    if internal_nodes < 1 or not 0.0 < eta <= 1.0:
        raise ValueError("k >= 1 and 0 < eta <= 1 are required")
    if error_type not in {"ambient", "projected", "normal"}:
        raise ValueError("unknown error type")
    old_precision = mp.iv.prec
    mp.iv.prec = precision_bits
    try:
        eta_iv = mp.iv.mpf([str(eta), str(eta)])
        tangent = mp.iv.sqrt(1 - eta_iv * eta_iv)
        # The interval context does not expose inverse trigonometric
        # functions consistently across mpmath releases.  Repeated complex
        # multiplication gives cos(k theta), sin(k theta) directly from
        # cos(theta)=tangent and sin(theta)=eta, with interval containment.
        cosine = mp.iv.mpf([1, 1])
        sine = mp.iv.mpf([0, 0])
        for _ in range(internal_nodes):
            cosine, sine = cosine * tangent - sine * eta_iv, sine * tangent + cosine * eta_iv
        reduced = tangent**internal_nodes
        if error_type == "ambient":
            ratio = mp.iv.sqrt(1 + reduced**2 - 2 * reduced * cosine) / eta_iv
        elif error_type == "projected":
            ratio = abs(cosine - reduced) / eta_iv
        else:
            ratio = abs(sine) / eta_iv
        return IntervalCertificate(
            lower=float(ratio.a),
            upper=float(ratio.b),
            status="CERTIFIED_LOWER_BOUND",
            method="mpmath interval evaluation of an explicit admissible construction",
            precision_bits=precision_bits,
        )
    finally:
        mp.iv.prec = old_precision


def rotation_tree_ratio_interval(
    tree: Tree,
    eta: float,
    error_type: str,
    *,
    precision_bits: int = 160,
) -> IntervalCertificate:
    """Enclose the gated-rotation ratio for an arbitrary ordered tree.

    The construction uses the first child as the active planar vector and the
    tangent coordinate of every other child as a scalar gate.  It is the exact
    interval analogue of :func:`extremizers.rotation_extremizer`.
    """

    if not 0.0 < eta <= 1.0:
        raise ValueError("0 < eta <= 1 is required")
    if error_type not in {"ambient", "projected", "normal"}:
        raise ValueError("unknown error type")
    old_precision = mp.iv.prec
    mp.iv.prec = precision_bits
    try:
        eta_iv = mp.iv.mpf([str(eta), str(eta)])
        tangent = mp.iv.sqrt(1 - eta_iv * eta_iv)

        def visit(item: Tree):
            if isinstance(item, Leaf):
                one = mp.iv.mpf([1, 1])
                zero = mp.iv.mpf([0, 0])
                return (one, zero), one
            children = [visit(child) for child in item.children]
            (x, y), _ = children[0]
            gate = mp.iv.mpf([1, 1])
            for (other_x, _), _ in children[1:]:
                gate *= other_x
            ambient_x = (tangent * x - eta_iv * y) * gate
            ambient_y = (eta_iv * x + tangent * y) * gate
            reduced_gate = mp.iv.mpf([1, 1])
            for _, reduced_child in children:
                reduced_gate *= reduced_child
            reduced = tangent * reduced_gate
            return (ambient_x, ambient_y), reduced

        (ambient_x, ambient_y), reduced = visit(tree)
        if error_type == "ambient":
            value = mp.iv.sqrt((ambient_x - reduced) ** 2 + ambient_y**2)
        elif error_type == "projected":
            value = abs(ambient_x - reduced)
        else:
            value = abs(ambient_y)
        ratio = value / eta_iv
        return IntervalCertificate(
            lower=float(ratio.a),
            upper=float(ratio.b),
            status="CERTIFIED_LOWER_BOUND",
            method="mpmath interval recursion for the explicit gated-rotation tree",
            precision_bits=precision_bits,
        )
    finally:
        mp.iv.prec = old_precision


def certified_gap(lower: float, upper: float) -> dict[str, float | str]:
    if lower < 0.0 or upper < lower:
        raise ValueError("invalid lower/upper bounds")
    absolute = upper - lower
    relative = absolute / upper if upper > 0.0 else 0.0
    return {
        "lower": lower,
        "upper": upper,
        "absolute_gap": absolute,
        "relative_gap": relative,
        "status": "NEAR_OPTIMAL_WITH_CERTIFIED_GAP" if relative <= 0.05 else "OPEN",
    }
