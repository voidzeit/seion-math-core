"""Evaluation of the heterogeneous box constant ``gBox``.

Mathematical basis (machine-checked in ``research/pmt_program/lean``):

* ``PMT.gBox_eq_capped`` / ``PMT.capped_equal_angle`` (H3): for defects ``η_i ≥ 0``
  with ``α_i = arcsin η_i`` (``= π/2`` when ``η_i ≥ 1``),
  ``gBox(η) = sup_{τ ∈ [0, π/2]} V(τ)`` where
  ``V(τ)² = 1 + C(τ)² − 2 C(τ) cos Θ(τ)``,
  ``C(τ) = ∏ cos min(α_i, τ)`` and ``Θ(τ) = Σ min(α_i, τ)``.
* ``PMT.gBox_le_sum``: ``gBox(η) ≤ Σ η_i``.
* ``PMT.gBox_le_uniform_fallback``: ``gBox(η) ≤ sup_{τ ≤ arcsin max η} |1 − w(τ)^n|``.

Two evaluators:

* :func:`gbox_float` — fast float estimate used for planning. Not a certificate.
* :func:`gbox_certified` — rigorous enclosure ``L ≤ gBox(η) ≤ U`` by interval arithmetic
  (``mpmath.iv``, outward rounding) and branch-and-bound over ``τ``. Soundness relies on H3 (Lean)
  and on the correctness of ``mpmath.iv`` (not formally verified).

Rounding audit (every float↔interval boundary):

* float → interval: ``iv.mpf(x)`` is exact for binary floats.
* ``arcsin``: no ``iv.asin``; the enclosure is verified with ``iv.sin`` (monotone on ``[0, π/2)``);
  ``η ≥ 1`` uses ``iv.pi / 2``.
* cell enclosures use the endpoints of the ``α_i`` intervals; ``min`` of intervals is taken
  endpoint-wise (exact).
* interval upper endpoints are converted with :func:`_round_up`, lower endpoints and square roots
  with :func:`_round_down`; ``t_max`` is rounded up; pruning compares against a rounded-down ``L²``.
* the mean-value form is used only on cells whose saturation pattern is fixed for every ``α`` in
  its interval, and is intersected with the monotone enclosure.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from mpmath import iv, mpf

HALF_PI = math.pi / 2


def _check(etas):
    etas = [float(e) for e in etas]
    for e in etas:
        if not math.isfinite(e) or e < 0:
            raise ValueError("defects must be finite and nonnegative")
    return etas


def alpha(e: float) -> float:
    """Float ``arcsin`` saturating at ``π/2`` (not rigorous)."""
    return HALF_PI if e >= 1.0 else math.asin(e)


def capped_value(alphas, tau: float) -> float:
    """``V(τ) = |1 − ∏ w(min(α_i, τ))|`` in floating point."""
    c = 1.0
    s = 0.0
    for a in alphas:
        t = a if a < tau else tau
        c *= math.cos(t)
        s += t
    return math.sqrt(max(0.0, 1.0 - 2.0 * c * math.cos(s) + c * c))


def gbox_float(etas, grid: int = 2048) -> tuple[float, float]:
    """Float estimate ``(value, τ*)`` of ``gBox`` via H3 (grid plus golden-section refinement)."""
    etas = _check(etas)
    if not etas:
        return 0.0, 0.0
    alphas = [alpha(e) for e in etas]
    hi = max(alphas)
    if hi == 0.0:
        return 0.0, 0.0
    best_v, best_t = -1.0, 0.0
    for g in range(grid + 1):
        t = hi * g / grid
        v = capped_value(alphas, t)
        if v > best_v:
            best_v, best_t = v, t
    lo_t, hi_t = max(0.0, best_t - hi / grid), min(hi, best_t + hi / grid)
    for _ in range(80):
        m1 = lo_t + (hi_t - lo_t) / 3
        m2 = hi_t - (hi_t - lo_t) / 3
        if capped_value(alphas, m1) < capped_value(alphas, m2):
            lo_t = m1
        else:
            hi_t = m2
    t = (lo_t + hi_t) / 2
    v = capped_value(alphas, t)
    if v > best_v:
        best_v, best_t = v, t
    return best_v, best_t


def additive_bound(etas) -> float:
    """``Σ η_i`` — certified upper bound of ``gBox`` (``PMT.gBox_le_sum``)."""
    return math.fsum(_check(etas))


def uniform_fallback(etas, grid: int = 4096) -> float:
    """Float estimate of the uniform fallback at the largest defect (``gBox_le_uniform_fallback``)."""
    etas = _check(etas)
    if not etas:
        return 0.0
    n = len(etas)
    a = alpha(max(etas))
    best = 0.0
    for g in range(grid + 1):
        t = a * g / grid
        c = math.cos(t) ** n
        best = max(best, math.sqrt(max(0.0, 1.0 - 2.0 * c * math.cos(n * t) + c * c)))
    return best


# ---------------------------------------------------------------------------
# certified enclosure
# ---------------------------------------------------------------------------


def _alpha_interval(e: float):
    """Rigorous interval containing ``arcsin e`` (``π/2`` for ``e ≥ 1``)."""
    if e >= 1.0:
        return iv.pi / 2
    if e == 0.0:
        return iv.mpf(0)
    a = math.asin(e)
    delta = 1e-12 * max(1.0, a)
    while True:
        lo = max(0.0, a - delta)
        hi = min(a + delta, 1.5707963267948966)  # below π/2, where sin is increasing
        ok_lo = lo == 0.0 or iv.sin(iv.mpf(lo)).b <= e
        ok_hi = iv.sin(iv.mpf(hi)).a >= e
        if ok_lo and ok_hi:
            return iv.mpf([lo, hi])
        if hi >= 1.5707963267948966:
            return iv.mpf([lo, iv.pi.b / 2])
        delta *= 16


def _imin(a, t):
    return iv.mpf([min(a.a, t.a), min(a.b, t.b)])


def _cell_enclosure(alphas, t0, t1):
    """Interval enclosure of ``V(τ)²`` over ``τ ∈ [t0, t1]`` and ``α_i`` in their intervals.

    ``C`` is nonincreasing and ``Θ`` nondecreasing in ``τ``, so the endpoint values bound them.
    """
    T0 = iv.mpf(t0)
    T1 = iv.mpf(t1)
    c_lo = iv.mpf(1)
    c_hi = iv.mpf(1)
    th_lo = iv.mpf(0)
    th_hi = iv.mpf(0)
    for a in alphas:
        lo_angle = _imin(iv.mpf(a.a), T0)
        hi_angle = _imin(iv.mpf(a.b), T1)
        c_hi = c_hi * iv.cos(lo_angle)
        c_lo = c_lo * iv.cos(hi_angle)
        th_lo = th_lo + lo_angle
        th_hi = th_hi + hi_angle
    C = iv.mpf([min(c_lo.a, c_hi.a), max(c_lo.b, c_hi.b)])
    TH = iv.mpf([min(th_lo.a, th_hi.a), max(th_lo.b, th_hi.b)])
    naive = 1 + C * C - 2 * C * iv.cos(TH)
    # Mean-value form on cells where the saturation pattern is fixed:
    # V² = 1 + C² − 2C cos Θ, C = A cos^m τ, Θ = B + m τ,
    # d/dτ V² = 2 m A cos^{m−1} τ · (sin(Θ + τ) − C sin τ).
    sat = [a for a in alphas if a.b <= t0]
    unsat = [a for a in alphas if a.a >= t1]
    if len(sat) + len(unsat) != len(alphas):
        return naive
    m = len(unsat)
    A = iv.mpf(1)
    B = iv.mpf(0)
    for a in sat:
        A = A * iv.cos(a)
        B = B + a
    T = iv.mpf([t0, t1])
    c = 0.5 * (t0 + t1)
    Cm = iv.mpf(c)
    Cc = A * iv.cos(Cm) ** m
    fc = 1 + Cc * Cc - 2 * Cc * iv.cos(B + m * Cm)
    if m == 0:
        mv = fc
    else:
        CT = A * iv.cos(T) ** m
        fp = 2 * m * A * iv.cos(T) ** (m - 1) * (iv.sin(B + m * T + T) - CT * iv.sin(T))
        mv = fc + fp * (T - Cm)
    return iv.mpf([max(naive.a, mv.a), min(naive.b, mv.b)])


def _point_lower(alphas, t):
    """Rigorous lower bound of ``V(τ)`` at the point ``τ = t`` (``α_i`` in their intervals)."""
    T = iv.mpf(t)
    C = iv.mpf(1)
    TH = iv.mpf(0)
    for a in alphas:
        ang = iv.mpf([min(a.a, T.a), min(a.b, T.b)])
        C = C * iv.cos(ang)
        TH = TH + ang
    g2 = 1 + C * C - 2 * C * iv.cos(TH)
    lo = g2.a
    if lo <= 0:
        return 0.0
    return _round_down(iv.sqrt(iv.mpf(lo)).a)


@dataclass(frozen=True)
class GBoxEnclosure:
    """Certified enclosure ``lower ≤ gBox(η) ≤ upper``."""

    lower: float
    upper: float
    tau: float
    cells: int
    method: str = "H3 (PMT.gBox_eq_capped) + mpmath.iv branch-and-bound"

    @property
    def width(self) -> float:
        return self.upper - self.lower


def _round_up(x) -> float:
    """A float ``≥ x`` (``x`` an mpmath ``mpf``)."""
    f = float(x)
    return f if mpf(f) >= x else math.nextafter(f, math.inf)


def _round_down(x) -> float:
    """A float ``≤ x`` (``x`` an mpmath ``mpf``)."""
    f = float(x)
    return f if mpf(f) <= x else math.nextafter(f, -math.inf)


def gbox_certified(etas, tol: float = 1e-9, max_cells: int = 200000, dps: int = 30) -> GBoxEnclosure:
    """Rigorous ``L ≤ gBox(η) ≤ U`` with ``U − L ≤ tol`` (or ``max_cells`` reached)."""
    etas = _check(etas)
    if not etas or max(etas) == 0.0:
        return GBoxEnclosure(0.0, 0.0, 0.0, 0)
    old = iv.dps
    iv.dps = dps
    try:
        alphas = [_alpha_interval(e) for e in etas]
        # τ beyond every cap leaves V constant, so [0, t_max] with t_max ≥ every α_i suffices
        t_max = _round_up(max(a.b for a in alphas))
        # lower bound from the float optimum and the breakpoints
        _, t_star = gbox_float(etas, grid=512)
        best_lower, best_tau = _point_lower(alphas, t_star), t_star
        for a in alphas:
            v = _point_lower(alphas, float(a.a))
            if v > best_lower:
                best_lower, best_tau = v, float(a.a)
        # branch-and-bound on V² over [0, t_max]
        n0 = 32
        heap = []
        cells = 0
        for k in range(n0):
            t0 = t_max * k / n0
            t1 = t_max * (k + 1) / n0
            enc = _cell_enclosure(alphas, t0, t1)
            cells += 1
            heapq.heappush(heap, (-_round_up(enc.b), t0, t1))
        lower_sq = math.nextafter(best_lower * best_lower, -math.inf) if best_lower > 0 else 0.0
        upper_sq = -heap[0][0]
        while heap and cells < max_cells:
            neg_ub, t0, t1 = heapq.heappop(heap)
            ub = -neg_ub
            if ub <= lower_sq:
                continue
            upper_sq = max(ub, -heap[0][0]) if heap else ub
            if math.sqrt(max(upper_sq, 0.0)) - best_lower <= tol:
                heapq.heappush(heap, (neg_ub, t0, t1))
                break
            mid = 0.5 * (t0 + t1)
            v = _point_lower(alphas, mid)
            if v > best_lower:
                best_lower, best_tau = v, mid
                lower_sq = math.nextafter(v * v, -math.inf)
            for a, b in ((t0, mid), (mid, t1)):
                enc = _cell_enclosure(alphas, a, b)
                cells += 1
                heapq.heappush(heap, (-_round_up(enc.b), a, b))
        remaining = [-h[0] for h in heap if -h[0] > lower_sq]
        upper_sq_final = max(remaining) if remaining else lower_sq
        upper = _round_up(iv.sqrt(iv.mpf(max(upper_sq_final, 0.0))).b)
        return GBoxEnclosure(best_lower, upper, best_tau, cells)
    finally:
        iv.dps = old
