import numpy as np

from seion_core.examples.random_laws import random_ternary_law


def test_multilinearity_across_all_slots():
    law = random_ternary_law(3, seed=19)
    rng = np.random.default_rng(20)
    values = tuple(rng.normal(size=3) for _ in range(3))
    for slot in range(3):
        assert law.multilinearity_residual(values, slot, alpha=-0.73) < 1e-12

