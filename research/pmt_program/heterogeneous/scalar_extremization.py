"""Scalar extremization for the proposed heterogeneous Theorem R.

The exact heterogeneous quantity suggested by the planar reduction is

    G_box(alpha) = max_{0 <= theta_i <= alpha_i}
                   |1 - prod_i cos(theta_i) exp(i theta_i)|.

The routine in this file deliberately distinguishes a numerical lower bound
from a theorem-certified upper bound.  Differential evolution and local
search can find a good point, but they do not prove global optimality.  The
simple uniform envelope is mathematically valid once the existing uniform
Theorem R is assumed and is evaluated numerically here.
"""

from __future__ import annotations

import math
import heapq
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import differential_evolution, minimize, minimize_scalar


def _as_float_list(values: Iterable[float], name: str) -> list[float]:
    out = [float(x) for x in values]
    for x in out:
        if not math.isfinite(x):
            raise ValueError(f"{name} must contain finite values")
    return out


def validate_etas(etas: Iterable[float]) -> list[float]:
    """Validate normalized defects and return a fresh list."""
    out = _as_float_list(etas, "etas")
    if any(x < 0.0 or x > 1.0 for x in out):
        raise ValueError("every normalized defect must lie in [0, 1]")
    return out


def validate_alphas(alphas: Iterable[float]) -> list[float]:
    """Validate angular caps in [0, pi/2]."""
    out = _as_float_list(alphas, "alphas")
    if any(x < 0.0 or x > math.pi / 2 + 1e-14 for x in out):
        raise ValueError("every angular cap must lie in [0, pi/2]")
    return [min(x, math.pi / 2) for x in out]


def factor(theta: float) -> complex:
    """Return w(theta) = cos(theta) exp(i theta)."""
    if not math.isfinite(theta) or theta < 0.0 or theta > math.pi / 2 + 1e-14:
        raise ValueError("theta must lie in [0, pi/2]")
    theta = min(theta, math.pi / 2)
    c = math.cos(theta)
    return c * complex(math.cos(theta), math.sin(theta))


def objective(thetas: Sequence[float]) -> float:
    """Evaluate |1 - product_i w(theta_i)|."""
    z = 1.0 + 0.0j
    for theta in thetas:
        z *= factor(float(theta))
    return abs(1.0 - z)


def _stable_objective(thetas: Sequence[float]) -> float:
    """Objective used by optimizers; avoids avoidable numpy scalar coercions."""
    return objective(thetas)


def _uniform_derivative(theta: float, n: int) -> float:
    """Derivative of |1 - w(theta)^n|^2 for the uniform envelope."""
    if n <= 0:
        return 0.0
    c, s = math.cos(theta), math.sin(theta)
    cn1 = c ** (n - 1)
    return (
        -2.0 * n * c ** (2 * n - 1) * s
        + 2.0 * n * cn1 * s * math.cos(n * theta)
        + 2.0 * n * c**n * math.sin(n * theta)
    )


def _uniform_candidates(n: int, alpha: float, grid: int = 20001) -> list[float]:
    """Find endpoints and sign-changing stationary points deterministically."""
    if n <= 0:
        return [0.0]
    if alpha <= 0.0:
        return [0.0]
    ts = np.linspace(0.0, alpha, max(3, grid))
    ds = np.array([_uniform_derivative(float(t), n) for t in ts])
    candidates = [0.0, alpha]
    for i in range(len(ts) - 1):
        if ds[i] == 0.0:
            candidates.append(float(ts[i]))
        elif ds[i] * ds[i + 1] < 0.0:
            root = minimize_scalar(
                lambda x: abs(_uniform_derivative(float(x), n)),
                bounds=(float(ts[i]), float(ts[i + 1])),
                method="bounded",
                options={"xatol": 1e-15},
            )
            candidates.append(float(root.x))
    return candidates


def uniform_G(n: int, eta: float, *, grid: int = 20001) -> float:
    """Evaluate the uniform scalar factor with n active factors.

    This is the existing Theorem R scalar expression with ``n = k - 1``.
    The expression is evaluated by endpoints plus stationary-point search.  A
    rational/exact or interval-arithmetic replay remains preferable when a
    published numerical certificate is required.
    """
    if n < 0:
        raise ValueError("n must be nonnegative")
    eta = validate_etas([eta])[0]
    if n == 0 or eta == 0.0:
        return 0.0
    alpha = math.asin(eta)
    return max(objective([theta] * n) for theta in _uniform_candidates(n, alpha, grid))


def capped_equal_angle(alphas: Iterable[float]) -> tuple[float, list[float]]:
    """Optimize the capped-equal-angle candidate curve.

    This implements the conjectural reduction theta_i=min(alpha_i, tau).  It
    is useful for diagnostics, but its result is not labelled as a global
    maximum unless it is independently checked against the box optimizer.
    """
    caps = sorted(validate_alphas(alphas))
    if not caps:
        return 0.0, []

    candidates: list[tuple[float, list[float]]] = []

    def point(tau: float) -> list[float]:
        return [min(a, tau) for a in caps]

    breakpoints = [0.0] + caps
    for left, right in zip(breakpoints[:-1], breakpoints[1:]):
        for tau in (left, right):
            candidates.append((objective(point(tau)), point(tau)))
        if right - left > 1e-14:
            result = minimize_scalar(
                lambda tau: -objective(point(float(tau))),
                bounds=(left, right),
                method="bounded",
                options={"xatol": 1e-13},
            )
            tau = float(result.x)
            candidates.append((objective(point(tau)), point(tau)))

    value, angles = max(candidates, key=lambda item: item[0])
    return float(value), angles


def _factor_rectangle(left: float, right: float) -> tuple[float, float, float, float]:
    """Rectangular enclosure of w(theta) for theta in [left, right]."""
    xl = math.cos(right) ** 2
    xu = math.cos(left) ** 2
    values = [0.5 * math.sin(2.0 * left), 0.5 * math.sin(2.0 * right)]
    if left <= math.pi / 4 <= right:
        values.append(0.5)
    yl, yu = min(values), max(values)
    # Expand by one ulp so the floating-point enclosure is outward rounded.
    return (
        math.nextafter(xl, -math.inf),
        math.nextafter(xu, math.inf),
        math.nextafter(yl, -math.inf),
        math.nextafter(yu, math.inf),
    )


def _interval_product(box: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Enclose the product of complex rectangles for all theta boxes."""
    real_lo, real_hi, imag_lo, imag_hi = 1.0, 1.0, 0.0, 0.0
    for left, right in box:
        x_lo, x_hi, y_lo, y_hi = _factor_rectangle(left, right)
        real_values = [
            a * c - b * d
            for a in (real_lo, real_hi)
            for b in (imag_lo, imag_hi)
            for c in (x_lo, x_hi)
            for d in (y_lo, y_hi)
        ]
        imag_values = [
            a * d + b * c
            for a in (real_lo, real_hi)
            for b in (imag_lo, imag_hi)
            for c in (x_lo, x_hi)
            for d in (y_lo, y_hi)
        ]
        real_lo = math.nextafter(min(real_values), -math.inf)
        real_hi = math.nextafter(max(real_values), math.inf)
        imag_lo = math.nextafter(min(imag_values), -math.inf)
        imag_hi = math.nextafter(max(imag_values), math.inf)
    return real_lo, real_hi, imag_lo, imag_hi


def _rectangle_distance_upper(rectangle: tuple[float, float, float, float]) -> float:
    """Upper bound for |1-z| over a real/imaginary rectangle."""
    real_lo, real_hi, imag_lo, imag_hi = rectangle
    return max(
        math.hypot(1.0 - real, imag)
        for real in (real_lo, real_hi)
        for imag in (imag_lo, imag_hi)
    )


@dataclass(frozen=True)
class IntervalMaximum:
    """Branch-and-bound enclosure for the scalar box maximum."""

    lower_bound: float
    upper_bound: float
    argmax: tuple[float, ...]
    boxes_processed: int
    tolerance: float
    exhausted: bool

    @property
    def gap(self) -> float:
        return max(0.0, self.upper_bound - self.lower_bound)


def interval_box_max(
    alphas: Iterable[float],
    *,
    tolerance: float = 1e-6,
    max_boxes: int = 20_000,
) -> IntervalMaximum:
    """Compute a floating-point interval enclosure by branch-and-bound.

    Each factor arc is enclosed by a rectangle, products are enclosed by
    interval complex arithmetic, and the distance maximum over the resulting
    rectangle is used as an upper bound.  The result is intentionally called
    an *interval enclosure*: it is a numerical certificate for the scalar
    relaxation, not yet a formal proof in Lean or an enclosure for the full
    PMT class.
    """
    caps = validate_alphas(alphas)
    n = len(caps)
    if n == 0:
        return IntervalMaximum(0.0, 0.0, (), 1, tolerance, True)
    if tolerance <= 0.0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be positive and finite")
    if max_boxes < 1:
        raise ValueError("max_boxes must be positive")

    initial = tuple((0.0, cap) for cap in caps)
    lower_point = np.asarray([cap for cap in caps], dtype=float)
    lower = objective(lower_point)
    best_point = lower_point
    upper = _rectangle_distance_upper(_interval_product(initial))
    queue: list[tuple[float, int, tuple[tuple[float, float], ...]]] = [(-upper, 0, initial)]
    processed = 0
    counter = 1

    while queue and processed < max_boxes:
        neg_bound, _, box = heapq.heappop(queue)
        bound = -neg_bound
        processed += 1
        if bound <= lower + tolerance:
            continue
        widths = [right - left for left, right in box]
        index = max(range(n), key=widths.__getitem__)
        left, right = box[index]
        mid = (left + right) / 2.0
        children = []
        for child_left, child_right in ((left, mid), (mid, right)):
            child = list(box)
            child[index] = (child_left, child_right)
            child_tuple = tuple(child)
            point = np.asarray([(a + b) / 2.0 for a, b in child_tuple], dtype=float)
            value = objective(point)
            if value > lower:
                lower, best_point = value, point
            child_bound = _rectangle_distance_upper(_interval_product(child_tuple))
            if child_bound > lower + tolerance:
                heapq.heappush(queue, (-child_bound, counter, child_tuple))
                counter += 1
    # Boxes pruned within `tolerance` may still contain a maximizer, so retain
    # the tolerance explicitly when the queue becomes empty. This keeps the
    # reported value an enclosure rather than merely a rounded lower bound.
    queued_upper = max((-item[0] for item in queue), default=lower)
    upper = max(lower + tolerance, queued_upper)
    exhausted = not queue
    return IntervalMaximum(float(lower), float(max(upper, lower)), tuple(float(x) for x in best_point), processed, tolerance, exhausted)


@dataclass(frozen=True)
class BoxMaximum:
    """Result of numerical box optimization.

    ``lower_bound`` is an attained numerical value at the returned point.
    ``uniform_upper_bound`` is the uniform-envelope value.  The latter is an
    upper bound for the scalar box because the heterogeneous box is contained
    in the uniform box with cap max(alphas).  ``global_optimality_proved`` is
    intentionally always false here: floating-point global optimization is not
    a proof.
    """

    alphas: tuple[float, ...]
    lower_bound: float
    uniform_upper_bound: float
    argmax: tuple[float, ...]
    capped_candidate: float
    capped_angles: tuple[float, ...]
    interval_lower_bound: float
    interval_upper_bound: float
    interval_argmax: tuple[float, ...]
    interval_boxes_processed: int
    interval_exhausted: bool
    method: str
    global_optimality_proved: bool = False

    @property
    def gap(self) -> float:
        return max(0.0, self.uniform_upper_bound - self.lower_bound)

    @property
    def interval_gap(self) -> float:
        return max(0.0, self.interval_upper_bound - self.interval_lower_bound)


def heterogeneous_box_max(
    alphas: Iterable[float],
    *,
    seed: int = 0,
    maxiter: int = 300,
    popsize: int = 12,
    polish: bool = True,
    interval_tolerance: float = 1e-6,
    interval_max_boxes: int = 20_000,
) -> BoxMaximum:
    """Numerically maximize the heterogeneous scalar objective over a box.

    The optimizer combines deterministic boundary/capped candidates with
    differential evolution and bounded local refinement.  It returns a lower
    bound on the true box maximum and the uniform Theorem R envelope as an
    upper bound.  This is designed for research exploration, not for claiming
    a proof of the heterogeneous theorem.
    """
    caps = validate_alphas(alphas)
    n = len(caps)
    if n == 0:
        return BoxMaximum((), 0.0, 0.0, (), 0.0, (), 0.0, 0.0, (), 1, True, "empty-box")

    capped_value, capped_angles = capped_equal_angle(caps)
    starts: list[np.ndarray] = [
        np.zeros(n, dtype=float),
        np.asarray(caps, dtype=float),
        np.asarray(capped_angles, dtype=float),
    ]
    # Mixed boundary points catch the most common non-monotone phase cases.
    for i in range(n):
        x = np.zeros(n, dtype=float)
        x[i] = caps[i]
        starts.append(x)
    if n <= 16:
        for mask in range(1 << n):
            starts.append(np.asarray([caps[i] if mask & (1 << i) else 0.0 for i in range(n)]))

    best_value = max(_stable_objective(x) for x in starts)
    best_point = max(starts, key=_stable_objective)

    if any(caps):
        result = differential_evolution(
            lambda x: -_stable_objective(x),
            bounds=[(0.0, a) for a in caps],
            seed=seed,
            maxiter=maxiter,
            popsize=popsize,
            polish=polish,
            workers=1,
            updating="immediate",
        )
        if -float(result.fun) > best_value:
            best_value = -float(result.fun)
            best_point = np.asarray(result.x, dtype=float)

    # Refine every strong deterministic start. This is cheap for the small
    # dimensions used in the PMT experiments and helps reproducibility.
    for start in starts[: min(len(starts), 64)]:
        result = minimize(
            lambda x: -_stable_objective(x),
            np.asarray(start, dtype=float),
            bounds=[(0.0, a) for a in caps],
            method="L-BFGS-B",
        )
        value = -float(result.fun)
        if value > best_value:
            best_value = value
            best_point = np.asarray(result.x, dtype=float)

    eta_max = math.sin(max(caps))
    upper = uniform_G(n, eta_max)
    interval = interval_box_max(caps, tolerance=interval_tolerance, max_boxes=interval_max_boxes)
    return BoxMaximum(
        alphas=tuple(caps),
        lower_bound=float(best_value),
        uniform_upper_bound=float(upper),
        argmax=tuple(float(x) for x in best_point),
        capped_candidate=float(capped_value),
        capped_angles=tuple(float(x) for x in capped_angles),
        interval_lower_bound=interval.lower_bound,
        interval_upper_bound=interval.upper_bound,
        interval_argmax=interval.argmax,
        interval_boxes_processed=interval.boxes_processed,
        interval_exhausted=interval.exhausted,
        method="deterministic-boundaries+differential-evolution+L-BFGS-B",
    )
