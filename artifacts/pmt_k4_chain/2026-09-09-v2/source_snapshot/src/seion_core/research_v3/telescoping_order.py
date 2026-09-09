"""Provably optimal ordering for multilinear telescoping certificates."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
import math
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class SlotBound:
    slot: int
    error: float
    reduced: float
    full: float
    gain: float = 1.0

    def __post_init__(self) -> None:
        if min(self.error, self.reduced, self.full, self.gain) < 0.0:
            raise ValueError("telescoping bounds must be nonnegative")

    @property
    def weighted_error(self) -> float:
        return self.gain * self.error

    @property
    def difference(self) -> float:
        return self.full - self.reduced


def telescoping_cost(slots: Sequence[SlotBound], order: Sequence[int]) -> float:
    """Evaluate the declared replacement-order bound exactly."""

    by_slot = {item.slot: item for item in slots}
    if len(by_slot) != len(slots) or set(order) != set(by_slot):
        raise ValueError("order must be a permutation of the distinct slot ids")
    total = 0.0
    for position, slot in enumerate(order):
        item = by_slot[slot]
        previous = order[:position]
        later = order[position + 1 :]
        total += (
            item.weighted_error
            * math.prod(by_slot[index].reduced for index in previous)
            * math.prod(by_slot[index].full for index in later)
        )
    return float(total)


def pairwise_prefers(left: SlotBound, right: SlotBound, tolerance: float = 0.0) -> bool:
    """Return whether ``left`` before ``right`` is no worse.

    The adjacent exchange calculation is

    ``w_i f_j + r_i w_j <= w_j f_i + r_j w_i``

    iff ``w_i(f_j-r_j) <= w_j(f_i-r_i)``, where ``w_i=G_i e_i``.
    """

    return (
        left.weighted_error * right.difference
        <= right.weighted_error * left.difference + tolerance
    )


def _sort_key(item: SlotBound, tolerance: float) -> tuple[int, float, int]:
    difference = item.difference
    weight = item.weighted_error
    if abs(difference) <= tolerance:
        if weight <= tolerance:
            return (-1, 0.0, item.slot)  # indifferent, deterministic first
        return (1, 0.0, item.slot)
    ratio = weight / difference
    if difference > 0.0:
        return (0, ratio, item.slot)
    return (2, ratio, item.slot)


def optimal_telescoping_order(
    slots: Iterable[SlotBound], *, tolerance: float = 1.0e-15
) -> tuple[int, ...]:
    """Return a globally optimal order by the adjacent-exchange theorem.

    Positive ``f_i-r_i`` slots precede nonzero zero-denominator slots, which
    precede negative-difference slots.  Within each same-sign class, sort
    ``G_i e_i/(f_i-r_i)`` increasingly.  Zero-error/zero-difference slots are
    indifferent and receive a deterministic leading position.
    """

    values = tuple(slots)
    if len({item.slot for item in values}) != len(values):
        raise ValueError("slot ids must be distinct")
    return tuple(item.slot for item in sorted(values, key=lambda item: _sort_key(item, tolerance)))


def brute_force_order(slots: Sequence[SlotBound]) -> tuple[tuple[int, ...], float]:
    """Independent factorial validator for small arity."""

    if len(slots) > 9:
        raise ValueError("brute-force validation is limited to at most nine slots")
    ids = tuple(item.slot for item in slots)
    best_order: tuple[int, ...] | None = None
    best_cost = math.inf
    for order in permutations(ids):
        cost = telescoping_cost(slots, order)
        if cost < best_cost:
            best_cost = cost
            best_order = order
    if best_order is None:
        return (), 0.0
    return best_order, float(best_cost)


def named_order_costs(slots: Sequence[SlotBound]) -> dict[str, object]:
    left = tuple(item.slot for item in slots)
    right = tuple(reversed(left))
    optimal = optimal_telescoping_order(slots)
    result: dict[str, object] = {
        "left_to_right": {"order": left, "cost": telescoping_cost(slots, left)},
        "right_to_left": {"order": right, "cost": telescoping_cost(slots, right)},
        "optimal": {"order": optimal, "cost": telescoping_cost(slots, optimal)},
    }
    if len(slots) <= 8:
        brute_order, brute_cost = brute_force_order(slots)
        result["brute_force"] = {"order": brute_order, "cost": brute_cost}
    return result
