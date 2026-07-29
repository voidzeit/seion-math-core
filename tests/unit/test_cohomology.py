import numpy as np

from seion_core.cohomology.chain_complex import ChainComplex
from seion_core.cohomology.compatibility import descends_to_cohomology


def test_finite_cohomology_descent_compatibility():
    d = np.array([[0.0, 1.0], [0.0, 0.0]])
    complex_ = ChainComplex([d], dimensions=(2, 2))
    assert complex_.verify_d_squared_zero()["passed"]
    identity = np.eye(2)
    assert descends_to_cohomology(identity, complex_)["descends"]
    swap = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert not descends_to_cohomology(swap, complex_)["descends"]

