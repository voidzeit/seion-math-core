from seion_core.symbolic.associator import symbolic_associator_expansion
from seion_core.symbolic.curvature import symbolic_curvature_identity


def test_symbolic_artifacts_are_labeled():
    assert symbolic_associator_expansion()["status"] == "general_symbolic_derivation"
    assert symbolic_curvature_identity()["identity_residual"] == "0"

