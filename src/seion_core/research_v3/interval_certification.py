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


#: Mutually exclusive outcomes of comparing a certified lower bound against a proved
#: upper bound for a nonnegative extremal constant.
#:
#: The previous vocabulary conflated three distinct situations under names whose plain
#: meaning was inverted: a pair ``lower == upper == 0`` was reported as an exactly
#: determined optimal constant even though it is the vacuous case forced by the theorem,
#: while a pair ``lower == upper > 0`` -- the genuinely determined case -- was reported
#: as merely "near optimal". A lower bound of exactly zero was additionally reported as a
#: "certified lower bound", which is vacuous for a quantity that is nonnegative by
#: definition. These four states replace that vocabulary.
EXACTLY_DETERMINED_POSITIVE = "EXACTLY_DETERMINED_POSITIVE"
EXACTLY_ZERO_BY_THEOREM = "EXACTLY_ZERO_BY_THEOREM"
POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP = "POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP"
NO_POSITIVE_LOWER_BOUND_OBTAINED = "NO_POSITIVE_LOWER_BOUND_OBTAINED"

OPTIMALITY_CLASSES = (
    EXACTLY_DETERMINED_POSITIVE,
    EXACTLY_ZERO_BY_THEOREM,
    POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP,
    NO_POSITIVE_LOWER_BOUND_OBTAINED,
)

DEFAULT_OPTIMALITY_TOLERANCE = 1.0e-10


def classify_optimality(
    lower: float,
    upper: float,
    tolerance: float = DEFAULT_OPTIMALITY_TOLERANCE,
) -> str:
    """Classify a certified enclosure of a nonnegative extremal constant.

    ``lower`` is a rigorous lower bound obtained from an explicit admissible
    construction; ``upper`` is the proved universal upper bound. Both are assumed
    nonnegative with ``lower <= upper``.

    The four outcomes are mutually exclusive and exhaustive:

    ``EXACTLY_ZERO_BY_THEOREM``
        ``upper`` vanishes, so the constant is zero and nothing was optimised. In the
        projected-error setting this is exactly the single-internal-vertex case, where
        the coefficient ``k - 1`` is zero and the theorem already forces the value.
    ``EXACTLY_DETERMINED_POSITIVE``
        ``lower`` and ``upper`` agree to within ``tolerance`` at a positive value: the
        constant is determined.
    ``POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP``
        A positive lower bound was obtained but does not meet the upper bound.
    ``NO_POSITIVE_LOWER_BOUND_OBTAINED``
        No positive lower bound was obtained. The only lower bound available is the
        trivial one implied by nonnegativity, so the admissible range spans the whole
        interval from zero to the proved upper bound. This is *not* a certified lower
        bound in any informative sense.
    """
    if lower < 0.0 or upper < lower:
        raise ValueError("invalid lower/upper bounds")
    if upper <= 0.0:
        return EXACTLY_ZERO_BY_THEOREM
    # The agreement test is relative to the upper bound, which is the same test the
    # previous implementation applied. Only the assignment of names is corrected, so the
    # partition of the registry is directly comparable with the earlier one.
    relative = (upper - lower) / upper
    if relative <= tolerance:
        return EXACTLY_DETERMINED_POSITIVE
    if lower > 0.0:
        return POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP
    return NO_POSITIVE_LOWER_BOUND_OBTAINED


def certified_gap(
    lower: float,
    upper: float,
    tolerance: float = DEFAULT_OPTIMALITY_TOLERANCE,
) -> dict[str, float | str]:
    """Absolute and relative gap between a lower construction and a proved upper bound.

    ``relative_gap`` is normalised by the *upper* bound, so ``relative_gap == 1``
    means ``lower == 0``: no positive lower bound was obtained. It must never be
    reported as a small residual discrepancy.
    """
    if lower < 0.0 or upper < lower:
        raise ValueError("invalid lower/upper bounds")
    absolute = upper - lower
    relative = absolute / upper if upper > 0.0 else 0.0
    return {
        "lower": lower,
        "upper": upper,
        "absolute_gap": absolute,
        "relative_gap": relative,
        "status": classify_optimality(lower, upper, tolerance=tolerance),
    }
