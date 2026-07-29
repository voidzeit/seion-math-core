import numpy as np

from seion_core.research_v3.error_expansion import (
    exact_local_expansion,
    nonempty_subsets,
    symbolic_subset_expansion,
)
from seion_core.research_v3.local_constants import TypedLaw


def test_subset_count_and_symbolic_rendering():
    assert len(nonempty_subsets(4)) == 15
    rendered = symbolic_subset_expansion(3)
    assert "mu_v[DDD]" in rendered
    assert rendered.count("mu_v[") == 7


def test_numeric_subset_expansion_is_exact_to_roundoff():
    rng = np.random.default_rng(8)
    tensor = rng.normal(size=(4, 3, 2, 3))
    law = TypedLaw("mu", ("a", "b", "a"), "c", tensor)
    f = [rng.normal(size=3), rng.normal(size=2), rng.normal(size=3)]
    r = [rng.normal(size=3), rng.normal(size=2), rng.normal(size=3)]
    q, _ = np.linalg.qr(rng.normal(size=(4, 2)))
    p = q @ q.T
    expansion = exact_local_expansion(law, f, r, p)
    assert expansion.identity_residual < 1e-11
    assert np.allclose(expansion.projected_delta + expansion.normal_delta, expansion.ambient_delta)
    assert len(expansion.subset_terms) == 7
