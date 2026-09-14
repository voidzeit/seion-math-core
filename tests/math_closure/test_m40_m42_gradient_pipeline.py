"""The backward pass must differentiate the function the forward evaluates.

The search divides a raw law by a scale factor built from its own operator norm
and closure defect. Computing that factor under `no_grad` and then treating it
as a constant makes autograd see

    Ftilde_{mu0}(mu) = J( mu / s(mu0) )   rather than   F(mu) = J( mu / s(mu) )

and the two disagree in the one direction that a homogeneous problem cares
about. Before normalization the same-law objective is degree-2 homogeneous, so
Euler gives <grad J(mu), mu> = 2 J(mu) > 0, while the normalized objective is
scale invariant and therefore has DF(mu)[mu] = 0 exactly. A frozen denominator
hands the optimizer a large radial ascent direction that the normalization
cancels -- which is why the search walked away from a configuration valued at
1.9997 out of 2.

These are the regression tests for that. They are cheap, and each pins one
specific way the pipeline can silently revert.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "rebracketing_geometry"))

torch = pytest.importorskip("torch")


@pytest.fixture(scope="module")
def checks():
    from rg_gradient_checks import (build_case, envelope_check,
                                    finite_difference_check, radial_check,
                                    scale_invariance_check)
    return {"build_case": build_case, "envelope_check": envelope_check,
            "finite_difference_check": finite_difference_check,
            "radial_check": radial_check,
            "scale_invariance_check": scale_invariance_check}


def _device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test_operator_norm_carries_a_gradient(checks):
    """Contracting the maximizer against a DETACHED tensor returns grad = 0.

    That is the regression that hid inside the restart-batched kernel: the
    search vectors may be detached, the tensor they are contracted against may
    not.
    """
    smallest, euler_gap = checks["envelope_check"](3, 16, _device(), 5)
    assert smallest > 1e-9, "operator norm is detached from the graph"
    # ||.||_op is homogeneous of degree 1, so Euler gives <grad N, mu> = N
    assert euler_gap < 1e-9


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_normalized_objective_has_no_radial_derivative(checks, eta):
    """The sharp test: F(c mu) = F(mu), hence DF(mu)[mu] = 0 exactly."""
    case = checks["build_case"](3, 2, eta, 16, _device(), seed=int(100 * eta))
    radial, magnitude = checks["radial_check"](case, (32, 40),
                                               differentiable=True)
    assert radial < 1e-9 * max(magnitude, 1.0)


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_frozen_normalization_is_detectably_wrong(checks, eta):
    """The bug must remain DETECTABLE, or the test above proves nothing.

    If this ever starts passing with a small radial derivative, the frozen mode
    has silently become differentiable and the guard above has lost its teeth.
    """
    case = checks["build_case"](3, 2, eta, 16, _device(), seed=int(100 * eta))
    radial, _ = checks["radial_check"](case, (32, 40), differentiable=False)
    assert radial > 1e-3, "frozen mode no longer exhibits the radial artifact"


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_forward_is_scale_invariant_in_both_modes(checks, eta):
    """The forward was never the problem; only the backward was."""
    case = checks["build_case"](3, 2, eta, 16, _device(), seed=int(100 * eta))
    for differentiable in (False, True):
        gap = checks["scale_invariance_check"](case, (32, 40), differentiable)
        assert gap < 1e-12


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_autograd_matches_finite_differences(checks, eta):
    """At a point where no constraint is exactly active, the objective is
    smooth and float64 central differences should agree closely."""
    case = checks["build_case"](3, 2, eta, 16, _device(), seed=int(100 * eta))
    relative = checks["finite_difference_check"](case, (32, 40),
                                                 differentiable=True,
                                                 epsilon=1e-6, seed=17)
    assert relative < 1e-3
