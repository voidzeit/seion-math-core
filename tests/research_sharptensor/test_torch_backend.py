import math

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from research.pmt_program.sharptensor.certificate import certify
from research.pmt_program.sharptensor.models import MpoMpsChain
from research.pmt_program.sharptensor.torch_backend import CertifiedMpoMpsApply


def test_torch_cpu_matches_numpy_certificate():
    model = MpoMpsChain(sites=8, chi=6, eps=0.05, seed=11)
    ranks = {n: 10 for n in model.internal}
    ref = model.execute(ranks)
    cref = certify(ref.run, actual_error=ref.actual_error)

    mod = CertifiedMpoMpsApply(model.W, device="cpu")
    cores, S = mod(ranks)
    ctorch = certify(mod.last_run)
    for k in ("amplitude_compact", "slotwise"):
        assert math.isclose(cref["bounds"][k], ctorch["bounds"][k], rel_tol=1e-8, abs_tol=1e-12)
    F = torch.as_tensor(model.dense_exact())
    actual = float(torch.linalg.norm(F - mod.dense(cores, S)))
    assert math.isclose(actual, ref.actual_error, rel_tol=1e-6, abs_tol=1e-12)
    assert actual <= ctorch["absolute_error_upper"] * (1 + 1e-9) + 1e-12


def test_torch_backward_runs():
    model = MpoMpsChain(sites=6, chi=4, eps=0.05, seed=12)
    mod = CertifiedMpoMpsApply(model.W, device="cpu")
    cores, S = mod({n: 6 for n in model.internal})
    loss = torch.linalg.norm(S)
    loss.backward()
    assert all(p.grad is not None for p in mod.W)
