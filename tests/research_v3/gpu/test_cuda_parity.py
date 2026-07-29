import numpy as np
import pytest

from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import (
    evaluate_projected_numpy,
    evaluate_projected_torch,
)
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


@pytest.mark.gpu
def test_float64_cuda_matches_numpy():
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("CUDA unavailable")
    rng = np.random.default_rng(33)
    types = TypeSystem([TypedSpace.coordinate("tau", 4, 2)])
    laws = {"mu": TypedLaw("mu", ("tau", "tau", "tau"), "tau", rng.normal(size=(4, 4, 4, 4)) / 8)}
    inner = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"), Leaf(2, "tau")))
    tree = Node("mu", "tau", (inner, Leaf(3, "tau"), Leaf(4, "tau")))
    leaves = {index: rng.normal(size=2) for index in range(5)}
    numpy_value = evaluate_projected_numpy(tree, laws, types, leaves).root
    torch_value = evaluate_projected_torch(tree, laws, types, leaves).detach().cpu().numpy()
    assert np.max(np.abs(numpy_value - torch_value)) < 2e-13
