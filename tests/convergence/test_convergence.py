import numpy as np

from seion_core.kernels.convergence import loglog_slope


def test_known_second_order_slope():
    resolutions = [8, 16, 32, 64]
    errors = [1 / n**2 for n in resolutions]
    assert abs(loglog_slope(resolutions, errors) + 2) < 1e-12

