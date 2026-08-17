"""The search harness must be able to express the extremizer it searches for.

A numerical shortfall in an adversarial search has two very different causes:
the optimizer failed to find the extremum, or the extremum is not inside the
search space at all because the feasibility projection distorts it. Only the
first is fixable by searching harder, so the distinction has to be a test and
not a judgement call.

This is the regression test for that: Theorem 3.1's witness, pushed through the
GPU harness's own feasibility pipeline, must come back with J_2 = 2 exactly.
It is also what licenses reading `gamma_S` in any class where `gamma_J` is
close to 1 (see rg_readout.py).
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
def harness():
    from rg_kernels import DTYPE, coordinate_projectors
    from rg_fused_search import (audit_admissibility, build_laws, evaluate,
                                 feasibility_factors, share_laws)
    from rg_harness_selftest import witness_leaves, witness_raw
    return {"DTYPE": DTYPE, "coordinate_projectors": coordinate_projectors,
            "audit_admissibility": audit_admissibility,
            "build_laws": build_laws, "evaluate": evaluate,
            "feasibility_factors": feasibility_factors,
            "share_laws": share_laws, "witness_leaves": witness_leaves,
            "witness_raw": witness_raw}


def _run_witness(harness, eta, strength=(18, 120)):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = harness["DTYPE"]
    eta_vec = torch.full((1,), eta, dtype=dtype, device=device)
    shared = torch.ones(1, dtype=torch.bool, device=device)
    rank = torch.full((1,), 2, dtype=torch.long, device=device)
    projector = harness["coordinate_projectors"](rank, 3, device)
    projectors = (projector, projector, projector)

    raw = harness["witness_raw"](eta, device)
    raws = dict.fromkeys(("inner_L", "inner_M", "root_L", "root_M"), raw)
    leaves = harness["witness_leaves"](device)

    with torch.no_grad():
        laws = harness["share_laws"](raws, shared)
        factors = harness["feasibility_factors"](laws, projectors, *strength)
        A_hat, PA, D, geometry = harness["evaluate"](laws, projectors, leaves,
                                                     eta_vec, factors, shared)
        built = harness["build_laws"](laws, projectors, eta_vec, factors,
                                      shared)
        op_norm, closure = harness["audit_admissibility"](built, projectors,
                                                          eta_vec, strength)
    return {"J": float(D[0].norm() / eta), "A_hat": float(A_hat[0].norm()),
            "PA_over_eta": float(PA[0].norm() / eta),
            "op_norm": float(op_norm[0]), "closure_over_eta": float(closure[0]),
            "e_L": geometry["e_L"][0], "e_M": geometry["e_M"][0]}


@pytest.mark.parametrize("eta", [0.05, 0.3, 1 / math.sqrt(2), 1.0])
def test_harness_reproduces_the_exact_witness(harness, eta):
    """If this fails, no shortfall measured by the harness is interpretable."""
    result = _run_witness(harness, eta)
    assert result["J"] == pytest.approx(2.0, abs=1e-12)


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_harness_feasibility_projection_does_not_distort_the_witness(harness,
                                                                     eta):
    """The witness saturates M and rho exactly; the pipeline must preserve it."""
    result = _run_witness(harness, eta)
    assert result["op_norm"] == pytest.approx(1.0, abs=1e-9)
    assert result["closure_over_eta"] == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("eta", [0.3, 1.0])
def test_witness_geometry_survives_the_harness(harness, eta):
    """chi = -1 and total concealment, measured through the GPU path."""
    result = _run_witness(harness, eta)
    e_L, e_M = result["e_L"], result["e_M"]
    chi = float(torch.dot(e_L, e_M) / (e_L.norm() * e_M.norm()))
    assert chi == pytest.approx(-1.0, abs=1e-9)
    assert result["A_hat"] == pytest.approx(0.0, abs=1e-12)
    assert result["PA_over_eta"] == pytest.approx(2.0, abs=1e-12)
