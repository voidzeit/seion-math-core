import numpy as np

from seion_core.examples.invariant_subspace import invariant_subspace_law
from seion_core.numerics.sampling import tuple_samples
from seion_core.projectors.closure import closure_leakage
from seion_core.projectors.reduced_law import reduced_law


def test_known_invariant_subspace_closes():
    law, projector = invariant_subspace_law()
    samples = tuple_samples(4, 3, 20, seed=2)
    assert closure_leakage(law, projector, samples) < 1e-12
    reduced = reduced_law(law, projector)
    assert reduced.tensor.shape == (2, 2, 2, 2)

