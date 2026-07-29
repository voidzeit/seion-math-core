import numpy as np

from seion_core.research_v3.telescoping_order import (
    SlotBound,
    brute_force_order,
    optimal_telescoping_order,
    pairwise_prefers,
    telescoping_cost,
)


def test_exchange_condition_matches_two_slot_cost():
    left = SlotBound(0, error=0.4, reduced=1.2, full=2.1, gain=0.7)
    right = SlotBound(1, error=0.9, reduced=0.5, full=1.7, gain=1.4)
    prefers = pairwise_prefers(left, right)
    observed = telescoping_cost([left, right], (0, 1)) <= telescoping_cost(
        [left, right], (1, 0)
    )
    assert prefers == observed


def test_sorted_order_equals_brute_force_for_positive_zero_and_negative_differences():
    rng = np.random.default_rng(119)
    for arity in range(2, 8):
        for _ in range(30):
            slots = []
            for slot in range(arity):
                reduced = float(rng.uniform(0.0, 2.0))
                difference = float(rng.uniform(-1.0, 1.0))
                full = max(0.0, reduced + difference)
                slots.append(
                    SlotBound(
                        slot,
                        error=float(rng.uniform(0.0, 1.0)),
                        reduced=reduced,
                        full=full,
                        gain=float(rng.uniform(0.0, 2.0)),
                    )
                )
            order = optimal_telescoping_order(slots)
            brute_order, brute_cost = brute_force_order(slots)
            assert telescoping_cost(slots, order) <= brute_cost + 1e-12
            assert set(order) == set(brute_order)


def test_zero_denominator_nonzero_error_sits_between_sign_classes():
    slots = [
        SlotBound(0, 1.0, reduced=1.0, full=2.0),
        SlotBound(1, 1.0, reduced=1.0, full=1.0),
        SlotBound(2, 1.0, reduced=2.0, full=1.0),
    ]
    assert optimal_telescoping_order(slots) == (0, 1, 2)
